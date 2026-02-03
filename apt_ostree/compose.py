"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""
import logging
import pathlib
import shutil
import sys


from rich.console import Console

from apt_ostree.deploy import Deploy
from apt_ostree.ostree import Ostree
from apt_ostree.repo import Repo


class Compose:
    def __init__(self, state):
        self.logging = logging.getLogger(__name__)
        self.state = state
        self.ostree = Ostree(self.state)
        self.repo = Repo(self.state)
        self.deploy = Deploy(self.state)
        self.console = Console()

        self.workspace = self.state.workspace
        self.workdir = self.state.workspace.joinpath("deployment")
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.rootfs = None

    def create(self):
        """Create an OSTree repository."""
        if self.state.repo.exists():
            self.logging.error(
                f"Repository already exists: {self.state.repo}")
            sys.exit(1)

        self.logging.info(f"Found ostree repository: {self.state.repo}")
        self.ostree.init()

    def rollback(self, commit):
        """Rolling back to a previous commit."""
        self.logging.info(f"Rollback back to {commit}.")
        self.ostree.ostree_rollback(commit)

        self.ostree.ostree_summary_update()

    def enablerepo(self):
        """Enable Debian package feed."""
        try:
            self.repo.add_repo()
        except Exception as e:
            self.logging.error(f"Failed to add repo: {e}")
            sys.exit(1)

    def disablerepo(self):
        self.repo.disable_repo()

    def checkout(self, rootfs):
        rootfs = pathlib.Path(rootfs)
        if rootfs.exists():
            self.logging.error(f"Directory already exists: {rootfs}")
            sys.exit(1)

        self._checkout(rootfs, self.state.branch)
        self.deploy.prestaging(rootfs)

    def commit(self, rootfs):
        """Commit changes to an ostree repo."""
        rootfs = pathlib.Path(rootfs)
        if not rootfs.exists():
            self.logging.error(f"Directory doesnt exists: {rootfs}")
            sys.exit(1)
        self.deploy.poststaging(rootfs)
        with self.console.status(f"Commiting to branch {self.state.branch}."):
            r = self.ostree.ostree_commit(
                rootfs,
                branch=self.state.branch,
                repo=self.state.repo,
                subject="apt-ostree compose commit",
                msg=f"apt-ostree compose commit"
            )
            if r.returncode != 0:
                self.logging.error("Failed to commit.")
                sys.exit(1)
            r = self.ostree.ostree_summary_update()
            if r.returncode != 0:
                self.logging.error("Failed to update summary.")
                sys.exit(1)


    def pull_local(self, child):
        """Pull changes from parent repo to child repo."""
        child = pathlib.Path(child)
        if not child.exists():
            self.logging.error("Ostree import repo does not exist")
            sys.exit(1)

        # Copy the existing branch from one repository to another.
        self.logging.info(
            f"Pulling from {self.state.branch} to {child}.")
        with self.console.status(f"Commiting to branch {self.state.branch}."):
            r = self.ostree.ostree_pull(child)
            if r.returncode != 0:
                self.logging.error("Failed to pull.")
                sys.exit(1)
            r = self.ostree.ostree_summary_update(child)
            if r.returncode != 0:
                self.logging.error("Failed to update summary.")
                sys.exit(1)

    def _checkout(self, rootfs=None, branch=None):
        """Checkout a commit from an ostree branch."""
        if branch is not None:
            rev = self.ostree.ostree_ref(branch)

        with self.console.status(f"Checking out {rev[:10]}..."):
            self.workdir = self.workdir.joinpath(branch)
            if rootfs:
                if rootfs.exists():
                    shutil.rmtree(rootfs)
                self.rootfs = rootfs
            else:
                self.workdir.mkdir(parents=True, exist_ok=True)
                self.rootfs = self.workdir.joinpath(rev)
                if self.rootfs.exists():
                    shutil.rmtree(self.rootfs)
            self.ostree.ostree_checkout(branch, self.rootfs)
        return rev
