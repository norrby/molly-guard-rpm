# Molly Guard RPM Package

Molly-guard is a well known reboot protector. It was constructed for Debian
systems and not for RHEL/Centos.

This is an RPM repackaging *molly-guard* using the `.deb` source
package as a base. Some effort has been put in actually using RPM
triggers and features in order to make it as much RHEL/like as possible.

The tough part of creating a working RPM package was to dodge all other
packages and upgrades. A `systemd` upgrade, for example, will replace the
symlinked protection scripts by its own binaries. This spec file will
reacto to that and immediately reinstate the molly-guard scripts and
links after the other package is finished.

## How to install

Molly guard may be installed like so:
```sh
sudo rpm -ivh path/to/local/copy/of/molly-guard-<version>.noarch.rpm
```

## General info

This RPM will re-establish its protection when any program in `/usr/sbin` is
updated. This is necessary if, for example, `systemd` is upgraded, since
it then eill re-install the shutdown binaries/symlinks in `/usr/sbin`.

## Building the RPM

The spec file in this directory relies on two facts:

1. You are building the RPM on a machine that can use `apt` tools.
2. On that machine you must also install the `rpmbuild` tools.

### Preparation

Enable sources for your deb distribution. Either use Synaptic and tick
the checkbox or edit sources.list manually.

Then edit the spec file to match the current version of the RPM. And
make sure the debscripts are installed as well as the rpmbuild tools:
```sh
sudo apt install devscripts rpm
```

### RPM construction

Then the spec file will do all the work (leaving the actual work
with building and making docs to the debuild tool).
```sh
rpmbuild -v --define "_topdir `pwd`/rpm" -ba molly-guard.spec
```
It will actually just tell the debuild tool to write its results
to a directory where rpmbuild will look for its artifacts.

The constructed RPM file will end up in `rpm/RPMS`.

## LICENSE

Use the spec file as you see fit as far as the GNU GPL 2.0 goes.
