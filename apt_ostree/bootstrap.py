"""
Copyright (c) 2023 Wind River Systems, Inc.
Modified 2026 Ivan Ucherdzhiev

SPDX-License-Identifier: Apache-2.0

"""

import hashlib
import logging
import os
import shutil
import sys
import yaml

import apt
from rich.console import Console

from apt_ostree.constants import excluded_packages
from apt_ostree import exceptions
from apt_ostree.ostree import Ostree
from apt_ostree.utils import run_command


class Bootstrap:
    def __init__(self, state):
        self.logging = logging.getLogger(__name__)
        self.console = Console()
        self.state = state
        self.ostree = Ostree(self.state)

    def create_rootfs(self):
        """Create a Debian system from a configuration file."""
        if not self.state.base.exists():
            self.logging.error("Configuration directory does not exist.")
            sys.exit(1)
        self.logging.info(f"Found configuration directory: {self.state.base}")

        config = self.state.base.joinpath("bootstrap.yaml")
        if not config.exists():
            self.logging.error("bootstrap.yaml does not exist.")
            sys.exit(1)
        else:
            self.logging.info("Found configuration file bootstrap.yaml.")

        with self.console.status(
                f"Setting up workspace for {self.state.branch}."):
            workspace = self.state.workspace
            workdir = workspace.joinpath(f"build/{self.state.branch}")
            rootfs = workdir.joinpath("rootfs")

            self.logging.info(f"Building workspace for {self.state.branch} "
                              f"in {workspace}")
            if workdir.exists():
                self.logging.info("Found working directory from "
                                  "previous run...removing.")
                shutil.rmtree(workdir)

        shutil.copytree(self.state.base, workdir)

        cfg = workdir.joinpath("bootstrap.yaml")
        if not cfg.exists():
            msg = "Unable to find bootstrap.yaml in %s." % workdir
            raise exceptions.ConfigError(msg)
        with open(cfg, "r") as f:
            try:
                config = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                if hasattr(exc, 'problem_mark'):
                    mark = exc.problem_mark
                    line = mark.line+1
                    col = mark.column+1
                    msg = \
                        f"Error in bootstrap.yaml at ({line}:{col})"
                    raise exceptions.ConError(msg)
                msg = f"Failed to parse bootstrap yaml {exc}"
                raise exceptions.ConfigError(msg)

        config = config.get("mmdebstrap", None)
        if config is None:
            msg = \
                "Error reading bootstrap.yaml. Mmdebstrap section missing."
            raise exceptions.ConfigError(msg)
        if not shutil.which("mmdebstrap"):
            raise exceptions.CommandError(
                "Command not found: mmdebstrap.")

        cmd = ["mmdebstrap"]
        if self.state.debug:
            cmd += ["--debug"]
        else:
            cmd += ["-v"]

        # Doesnt create a "/dev"
        cmd += ["--mode=unshare"]

        # If the suite is not specified then it will use the
        # current running Debian version.
        suite = config.get("suite")
        if suite:
            cmd += [suite]

        # If the architecture is not specified it will use the
        # same as the host.
        architecture = config.get("architectures", None)
        if architecture:
            cmd += [f"--architectures={architecture}"]

        variant = config.get("variant", None)
        if variant:
            cmd += [f"--variant={variant}"]
            
        aptopt = config.get("aptopt", None)        
        if aptopt:
            cmd += [f"--aptopt={aptopt}"]

        # Add additional archive pockets.
        components = config.get("components", None)
        if components is None:
            raise exceptions.ConfigError(
                "Unable to determine package archive components.")
        cmd += [f"--components={','.join(components)}"]

        # Generate the target rootfs
        rootfs = workdir.joinpath("rootfs")
        cmd += [str(rootfs)]

        # Include additional Debian packages
        packages = config.get("packages", None)
        if packages:
            cmd += [f"--include={','.join(packages)}"]

        # Run addtional scripts or copy addtional files into
        # target.
        setup_hooks = config.get("setup-hooks", None)
        if setup_hooks:
            cmd += [f"--setup-hook={hook}" for hook in setup_hooks]
            
        extract_hooks = config.get("extract-hooks", None)
        if extract_hooks:
            cmd += [f"--extract-hook={hook}" for hook in extract_hooks]
            
        customize_hooks = config.get("customize-hooks", None)
        if customize_hooks:
            cmd += [f"--customize-hook={hook}" for hook in customize_hooks]
            
        hook_directories = config.get("hook_directories", None)
        if hook_directories:
            cmd += [f"--hook-directory={direcroty}" for direcroty in hook_directories]

        self.logging.info("Running mmdebstrap.")
        run_command(cmd, cwd=workdir)

        self.ostree.init()
        self.logging.info(f"Found ostree branch: {self.state.branch}")
        self.create_ostree(rootfs)
        r = self.ostree.ostree_commit(
            rootfs,
            branch=self.state.branch,
            repo=self.state.repo,
            subject="Commit by apt-ostree",
            msg="Initialized by apt-ostree.")
        if r.returncode != 0:
            self.logging.info(f"Failed to commit {self.state.branch} to "
                              f"{self.state.repo}.")
        else:
            self.logging.info(f"Commited {self.state.branch} to "
                              f"{self.state.repo}.")
            self.ostree.ostree_summary_update(self.state.repo)

    def create_ostree(self, rootdir):
        """Create an ostree branch from a rootfs."""
        self.logging.info("Setting up kernel and initramfs")
        self.setup_boot(rootdir,
                        rootdir.joinpath("boot"),
                        rootdir.joinpath("usr/lib/modules"))
        self.logging.info("Create tmpfiles")
        self.create_tmpfile_dir(rootdir)
        self.logging.info("Convert to ostree")
        self.convert_to_ostree(rootdir)
        self.logging.info("Ostree file structure created succesfully!")

    def convert_to_ostree(self, rootdir):
        """Convert rootfs to ostree."""
        CRUFT = ["boot/initrd.img", "boot/vmlinuz",
                 "initrd.img", "initrd.img.old",
                 "vmlinuz", "vmlinuz.old"]
        assert rootdir is not None and rootdir != ""

        with self.console.status(f"Converting {rootdir} to ostree."):
            dir_perm = 0o755
            # Copying /var
            self.sanitize_usr_symlinks(rootdir)
            self.logging.info("Moving /var to /usr/rootdirs.")
            os.mkdir(rootdir.joinpath("usr/rootdirs"), dir_perm)
            # Make sure we preserve file permissions otherwise
            # bubblewrap will complain that a file/directory
            # permisisons/onership is not mapped correctly.
            shutil.copytree(
                rootdir.joinpath("var"),
                rootdir.joinpath("usr/rootdirs/var"),
                symlinks=True
            )
            shutil.rmtree(rootdir.joinpath("var"))
            os.mkdir(rootdir.joinpath("var"), dir_perm)

            # Remove unecessary files
            self.logging.info("Removing unnecessary files.")
            for c in CRUFT:
                try:
                    os.remove(rootdir.joinpath(c))
                except OSError:
                    pass

            # Setup and split out etc
            self.logging.info("Moving /etc to /usr/etc.")
            shutil.move(rootdir.joinpath("etc"),
                        rootdir.joinpath("usr"))

            self.logging.info("Setting up /ostree and /sysroot.")
            try:
                rootdir.joinpath("ostree").mkdir(
                    parents=True, exist_ok=True)
                rootdir.joinpath("sysroot").mkdir(
                    parents=True, exist_ok=True)
            except OSError:
                pass

            self.logging.info("Setting up symlinks.")
            TOPLEVEL_LINKS = {
                "home": "var/home",
                "media": "run/media",
                "mnt": "var/mnt",
                "opt": "var/opt",
                "ostree": "sysroot/ostree",
                "root": "var/roothome",
                "srv": "var/srv",
                "usr/local": "../var/usrlocal",
            }
            fd = os.open(rootdir, os.O_DIRECTORY)
            for l, t in TOPLEVEL_LINKS.items():
                shutil.rmtree(rootdir.joinpath(l))
                os.symlink(t, l, dir_fd=fd)

    def sanitize_usr_symlinks(self, rootdir):
        """Replace symlinks from /usr pointing to /var"""
        usrdir = os.path.join(rootdir, "usr")
        for base, dirs, files in os.walk(usrdir):
            for name in files:
                p = os.path.join(base, name)

                if not os.path.islink(p):
                    continue

                # Resolve symlink relative to root
                link = os.readlink(p)
                if os.path.isabs(link):
                    target = os.path.join(rootdir, link[1:])
                else:
                    target = os.path.join(base, link)

                rel = os.path.relpath(target, rootdir)
                # Keep symlinks if they're pointing to a location under /usr
                if os.path.commonpath([target, usrdir]) == usrdir:
                    continue

                toplevel = self.get_toplevel(rel)
                # Sanitize links going into /var, potentially
                # other location can be added later
                if toplevel != 'var':
                    continue

                try :
                    os.remove(p)
                    if os.path.isfile(target):
                        os.link(target, p)
                    elif os.path.isdir(target):
                        shutil.copytree(target, p,symlinks=True)
                    
                except Exception as e:
                    self.logging.info(f"Error moving file: {e}")
                    sys.exit(1)

    def get_toplevel(self, path):
        """Get the top level diretory."""
        head, tail = os.path.split(path)
        while head != '/' and head != '':
            head, tail = os.path.split(head)

        return tail

    def setup_boot(self, rootdir, bootdir, targetdir):
        """Setup up the ostree bootdir"""
        vmlinuz = None
        initrd = None
        dtbs = None
        version = None
        
        try:
            os.mkdir(targetdir)
        except OSError:
            pass

        for item in os.listdir(bootdir):
            if item.startswith("vmlinuz"):
                assert vmlinuz is None
                vmlinuz = item
                _, version = item.split("-", 1)
            elif item.startswith("initrd.img") or item.startswith("initramfs"):
                assert initrd is None
                initrd = item
            elif item.startswith("dtbs"):
                assert dtbs is None
                dtbs = os.path.join(bootdir, item)
            elif item.startswith("System.map"):
                # Move all other artifacts as is
                try : 
                    shutil.move(os.path.join(bootdir, item), targetdir)
                except Exception as e:
                    self.logging.info(f"Error moving file: {e}")
        assert vmlinuz is not None

        try:
            os.rename(os.path.join(bootdir, vmlinuz),
                      os.path.join(targetdir, version ,"vmlinuz"))
        except Exception as e:
                    self.logging.info(f"Error moving file: {e}")
                    sys.exit(1)

        if initrd is not None:
            try:
                os.rename(os.path.join(bootdir, initrd),
                          os.path.join(targetdir,version,"initramfs.img"))
            except Exception as e:
                        self.logging.info(f"Error moving file: {e}")
                        sys.exit(1)
            

    def create_tmpfile_dir(self, rootdir):
        """Ensure directoeies in /var are created."""
        with self.console.status("Creating systemd-tmpfiles configuration"):
            cache = apt.cache.Cache(rootdir=rootdir)
            dirs = []
            for pkg in cache:
                if "/var" in pkg.installed_files and \
                        pkg.name not in excluded_packages:
                    dirs += [file for file in pkg.installed_files
                             if file.startswith("/var")]
            if len(dirs) == 0:
                return
            conf = rootdir.joinpath(
                "usr/lib/tmpfiles.d/ostree-integration-autovar.conf")
            if conf.exists():
                os.unlink(conf)
            with open(conf, "w") as f:
                f.write("# Auto-genernated by apt-ostree\n")
                for d in (dirs):
                    if d not in [
                            "/var",
                            "/var/lock",
                            "/var/cache",
                            "/var/spool",
                            "/var/log",
                            "/var/lib"]:
                        f.write(f"L {d} - - - - ../../usr/rootdirs{d}\n")
