# Molly Guard RPM Package

*Molly-guard* is a well known reboot protector. It was constructed for Debian
systems and not for RHEL, Rocky Linux, AlmaLinux or CentOS.

This is an RPM repackaging of *molly-guard* using the `.deb` source
package as a base. Some effort has been put in actually using RPM
triggers and features in order to make it as much RHEL/like as possible.

A complicated part of creating a working RPM package was to dodge all other
packages and upgrades. A `systemd` upgrade, for example, will replace the
symlinked protection scripts by its own binaries. This spec file will
react to that and immediately reinstate the molly-guard scripts and
links after the other package is finished.

## Reboot hangs in dracut's debug shell

With releases before 0.8.5-13, a `reboot` on a systemd host with dracut
shut the OS down cleanly and then stopped like this, with the host waiting
in a shell nobody can reach:

```
dracut Warning: reboot failed!
...
Dropping to debug shell.
shutdown:/#
```

dracut copies `/usr/sbin/reboot`, which is the molly-guard wrapper, into
its shutdown initramfs but not the renamed real command. Release 0.8.5-13
and later ship a `dracut.conf.d` entry that brings it along and rebuild the
initramfs on install. Upgrade the package and the next reboot works.

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

The spec file in this directory relies on a Debian or Ubuntu build host
with the `rpmbuild` tools installed.

### Preparation

Install the RPM tools, the Debian packaging tools and molly-guard's own
build dependencies:
```sh
sudo apt install rpm devscripts debhelper docbook-xsl xsltproc
```
The source is fetched from Debian's pool, so the build host's own
distribution and its apt sources do not matter.

### RPM construction

Then the spec file will do all the work (leaving the actual work
with building and making docs to the debuild tool).
```sh
rpmbuild -v --define "_topdir `pwd`/rpm" -ba molly-guard.spec
```
It will actually just tell the debuild tool to write its results
to a directory where rpmbuild will look for its artifacts.

The constructed RPM file will end up in `rpm/RPMS`.

## USE AT YOUR OWN RISK

I have really tried making the install/uninstall parts safe. But you
never know. And the code is free to read. So please read through this
repository and perhaps also the originating `.deb` package source
before using this package and/or packaging tool and the packaged
product. Use it at your own risk.

## LICENSE

Use the spec file as you see fit as far as the GNU GPL 2.0 goes.
