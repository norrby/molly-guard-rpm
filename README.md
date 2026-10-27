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

The spec file builds from molly-guard's source tarball with plain
`rpmbuild`, fetching the tarball from Debian's pool. On Rocky Linux, RHEL
or AlmaLinux:
```sh
sudo dnf install rpm-build make libxslt docbook-style-xsl docbook-dtds
mkdir -p ~/rpmbuild/SOURCES
rpmbuild -ba --undefine=_disable_source_fetch molly-guard.spec
```
The RPM ends up in `~/rpmbuild/RPMS/noarch`. `rpmbuild` does not create
`SOURCES` itself, and without it the download fails.

It also builds on Debian or Ubuntu, where the RHEL package names in
`BuildRequires` are unknown to rpm:
```sh
sudo apt install rpm make xsltproc docbook-xsl docbook-xml
mkdir -p ~/rpmbuild/SOURCES
rpmbuild -ba --nodeps --undefine=_disable_source_fetch molly-guard.spec
```

To package a new upstream version, change `Version`, reset `Release` to 1
and add a `%changelog` entry.

## USE AT YOUR OWN RISK

I have really tried making the install/uninstall parts safe. But you
never know. And the code is free to read. So please read through this
repository and perhaps also the originating `.deb` package source
before using this package and/or packaging tool and the packaged
product. Use it at your own risk.

## LICENSE

Use the spec file as you see fit as far as the GNU GPL 2.0 goes.
