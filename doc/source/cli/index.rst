.. _manpage:

=====================
:program:`apt-ostree`
=====================

Hybrid package/image manager for ostree

SYNOPSIS
========

:program:`apt-ostree` [<global-options>] <command> [<command-arguments>]

:program:`apt-ostree help` <command>

DESCRIPTION
===========

:program:`apt-ostree` provides a common commandline-interface to apt and
ostree. It is generally equivalent to the CLI provided by ostree and apt,
but with a distinct and consistent command structure.

OPTIONS
=======

:program:`apt-ostree` takes global options that control overall behaviour and command-specific
 options that control the command operation. Most global options have a
 corresponding environment variable that may also be used to set the value.
 If both are present, the command-line option takes priority. The environment
 variable names are derived from the option name by dropping the leading dashes
 ('--'), converting each embedded dash ('-') to an underscore ('_'),
 and converting to upper case.

:program:`apt-ostree` recognizes the following global options:

.. option:: --debug

   Show tracbacks on errors and set verbosity to debug.

.. option:: --workspace

   :program:`openstack` will create a default workspace to build images from.
   The default is '/var/tmp/apt-ostree'.


COMMANDS
========

To get a list of the available commands::

    apt-ostree --help

To get a description of a specific command::

    apt-ostree help <command>

Command Objects
---------------

The list of command objects is growing longer with the addition of apt-ostree
project support.  The object names may consist of multiple words to compose a
unique name.

Command Actions
---------------

The actions used by apt-ostree are defined with specific meaning to
provide a consistent behavior for each object. Some actions have
logical opposite actions,and those pairs wil
always match for any object that uses them.

EXAMPLES
========

Create an ostree repository and branch::

      apt-ostree \
         --repo /home/user/ostree_repo \
         --base config/debian/bookworm \
         debian/bookworm

Create an ostree image based off a ostree branch::

      apt-ostree \
         --repo /home/user/ostree-repo \
         --base config/debian/bookworm/image \
         debian/bookworm

BUGS
====

Bug reports are accepted at the python-openstackclient StoryBoard project
"https://storyboard.openstack.org/#!/project/975".


AUTHORS
=======

Please refer to the AUTHORS file distributed with apt-ostree.


COPYRIGHT
=========

Copyright 2023 Wind River Inc and the authors listed in the AUTHORS file.


LICENSE
=======

http://www.apache.org/licenses/LICENSE-2.0
