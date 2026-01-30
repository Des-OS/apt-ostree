"""
Copyright (c) 2023-2025 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import logging
import os
import subprocess

from apt_ostree import constants
from apt_ostree import exceptions

LOG = logging.getLogger(__name__)


def is_stx_system():
    """Return True if running in a host running StarlingX"""

    try:
        if not os.path.exists(constants.STX_BUILD_INFO_FILE):
            return False

        with open(constants.STX_BUILD_INFO_FILE, 'r') as file:
            build_info_content = file.read()

        for keyword in constants.STX_KEYWORDS:
            if keyword in build_info_content.lower():
                return True

        return False

    except Exception:
        msg = "Failed to determine if apt-ostree " \
              "is running on a StarlingX host"
        LOG.error(msg)
        raise


def is_pre_stx_bootstrap():
    """Return True if in STX system pre-bootstrap

    Check if apt-ostree is running inside a StarlingX system
    and STX bootstrap has not been executed yet.
    """

    return is_stx_system() and \
        not os.path.exists(constants.STX_CONFIG_COMPLETE_FLAG)


def parse_subprocess_result(result):
    """Extracting info from subprocess.run() output for logging"""

    msg = "Results:\n"

    try:
        # If RC == 0, no need to log it
        if result.returncode:
            msg += f"==> RETURN_CODE: {result.returncode} \n"
    except Exception:
        pass

    try:
        if result.stdout:
            msg += f"==> STDOUT: \n {result.stdout.decode('utf-8')} \n"
    except Exception:
        pass

    try:
        if result.stderr:
            msg += f"==> STDERR: \n {result.stderr.decode('utf-8')} \n"
    except Exception:
        pass

    return msg


def run_command(cmd,
                debug=False,
                stdin=None,
                stdout=None,
                stderr=None,
                check=True,
                env=None,
                cwd=None):
    """Run a command in a shell."""
    _env = os.environ.copy()
    if env:
        _env.update(env)
    try:
        subprocess_result = subprocess.run(
            cmd,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            env=_env,
            cwd=cwd,
            check=check,
        )

        msg = parse_subprocess_result(subprocess_result)
        LOG.info(msg)

        return subprocess_result

    except FileNotFoundError:
        msg = "%s is not found in $PATH" % cmd[0]
        LOG.error(msg)
        raise exceptions.CommandError(msg)

    except subprocess.CalledProcessError as e:
        msg = "SHELL EXECUTION ERROR:\n" + parse_subprocess_result(e)
        LOG.error(msg)
        raise exceptions.CommandError(msg)


def run_sandbox_command(
    args,
    rootfs,
    stdin=None,
    stdout=None,
    stderr=None,
    check=True,
    env=None
):
    """Run a shell wrapped with bwrap."""
    cmd = [
        "bwrap",
        "--proc", "/proc",
        "--dev", "/dev",
        "--dir", "/run",
        "--bind", "/sys", "/sys",
        "--bind", "/tmp", "/tmp",
        "--bind", f"{rootfs}/boot", "/boot",
        "--bind", f"{rootfs}/usr", "/usr",
        "--bind", f"{rootfs}/etc", "/etc",
        "--bind", f"{rootfs}/var", "/var",
        "--symlink", "/usr/lib", "/lib",
        "--symlink", "/usr/lib64", "/lib64",
        "--symlink", "/usr/bin", "/bin",
        "--symlink", "/usr/sbin", "/sbin",
        "--dir", "/var/rootdirs/scratch",
        "--symlink", "/var/rootdirs/scratch", "/scratch",
        "--share-net",
        "--die-with-parent",
        "--chdir", "/",
    ]

    if is_pre_stx_bootstrap():
        cmd += ["--bind", "/var/www/pages/updates", "/var/www/pages/updates"]

    cmd += args

    return run_command(
        cmd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        check=check,
        env=env,
    )


def check_and_append_component(config_path, component):
    with open(config_path, 'r') as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        if line.startswith("Components:"):
            components = line.split()[1:]
            if component not in components:
                lines[i] = line.strip() + f" {component}\n"
            break

    with open(config_path, 'w') as file:
        file.writelines(lines)


def remove_component_from_config(config_path, component):
    try:
        with open(config_path, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        msg = "The file %s does not exist." % config_path
        LOG.error(msg)
        return False

    updated_lines = []
    component_found = False
    for line in lines:
        if line.startswith("Components:"):
            components = line.split()[1:]
            if component in components:
                components.remove(component)
                component_found = True

                updated_line = "Components: " + " ".join(components) + "\n"
                updated_lines.append(updated_line)
        else:
            updated_lines.append(line)

    if not component_found:
        msg = "Component %s not found in the configuration." % component
        LOG.error(msg)
        return False

    with open(config_path, 'w') as file:
        file.writelines(updated_lines)

    LOG.info("Component %s removed from %s successfully"
             % (component, config_path))
    return True
