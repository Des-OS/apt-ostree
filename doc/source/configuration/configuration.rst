:orphan:

=======================
Bootstrap configuration
=======================

This document describes the expected data-structure hierarchy of the YAML
configuration file(s). The top-level structure is expected to be a mapping.
The top-level mapping may contain the following keys:

### env

mapping of environment variables names to their values. Environment variables
can be overridden by specifying them with **\--env** using the same name. These
environment variable are set before calling the hooks.

### name

String. Name of the generated image. Can be overridden by **\--name**.

### mmdebstrap

mapping. The values here are passed to mmdebstrap(1). Following keys may
be specified:

**aptopts**
:   list of arbitrary options or configuration files (string) to apt.
Additional apt options can be specified with **\--aptopt**.


**architectures**
:   list of architectures (string). The first architecture is the native
architecture inside the chroot.

**components**
:   list of components (string) like main, contrib and non-free which will be
used for all URI-only *MIRROR* arguments.

**dpkgopts**
:   list of arbitrary options or configuration files (string) to dpkg.

**format**
:   Choose the output format. It needs to be one of *auto*, *directory*, *dir*,
*tar*, *squashfs*, *sqfs*, *ext2*, *null*. See mmdebstrap(1) for details.

**hostname**
:   String. If specified, write the given *hostname* into */etc/hostname* in
the target chroot. This parameter does not exist in **mmdebstrap** and is
implemented as customize hook for **mmdebstrap**.

**install-recommends**
:   Boolean. If set to *True*, the APT option *Apt::Install-Recommends "true"*
is passed to **mmdebstrap** via **\--aptopt**.

**keyrings**
:   list of default keyring to use by apt.

**mirrors**
:   list of mirrors (string).

**mode**
:   Choose how to perform the chroot operation and create a filesystem with
ownership information different from the current user. It needs to be one
of *auto*, *sudo*, *root*, *unshare*, *fakeroot*, *fakechroot*, *proot*, or
*chrootless*. See mmdebstrap(1) for details.

**packages**
:   list of packages (string) which will be installed in addition to the
packages installed by the specified variant. This setting is passed to
**mmdebstrap** using the **\--include** parameter.

**setup-hooks**
:   list of setup hooks (string). Execute arbitrary commands right after
initial setup (directory creation, configuration of apt and dpkg, ...) but
before any packages are downloaded or installed. At that point, the chroot
directory does not contain any executables and thus cannot be chroot-ed
into. See **HOOKS** in mmdebstrap(1) for more information and examples.

**essential-hooks**
:   list of essential hooks (string). Execute arbitrary commands after the
Essential:yes packages have been installed, but before installing the
remaining packages. See **HOOKS** in mmdebstrap(1) for more information and
examples.

**customize-hooks**
:   list of customize hooks (string). Execute arbitrary commands after the
chroot is set up and all packages has been installed but before final cleanup
actions are carried out. See **HOOKS** in mmdebstrap(1) for more
information and examples.

**cleanup-hooks**
:   list of cleanup hooks (string). Cleanup hooks are just hooks that are run
directly after all other customize hooks. See **customize-hooks** above.

**suite**
:   String. The suite may be a valid release code name (eg, sid, stretch,
jessie) or a symbolic name (eg, unstable, testing, stable, oldstable).

**target**
:   String. The target argument can either be the path to a directory, the path
to a tarball filename, the path to a squashfs image or *-*.

**variant**
:   Choose which package set to install. It needs to be one of *extract*,
*custom*, *essential*, *apt*, *required*, *minbase*, *buildd*, *important*,
*debootstrap*, *-*, *standard*. See mmdebstrap(1) for details.

More details for mmdebstrap syntax can be found in the mmdebstrap man page.
