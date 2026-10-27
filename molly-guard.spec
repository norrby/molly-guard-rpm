Name: molly-guard
Version: 0.8.6
Release: 2
Summary: Protects machines from accidental shutdowns and reboots
License: Artistic-2.0
URL: https://salsa.debian.org/debian/molly-guard
# molly-guard is a native Debian package, so the tarball is the whole source.
Source0: https://deb.debian.org/debian/pool/main/m/molly-guard/molly-guard_%{version}.tar.xz
BuildArch: noarch
BuildRequires: make sed libxslt docbook-style-xsl docbook-dtds
Requires: /usr/sbin/reboot
# The wrapper finds its checks with run-parts. Without it the loop is empty
# and every reboot goes through unasked. Provided by crontabs on RHEL.
Requires: /usr/bin/run-parts

%description
The package installs a shell script that overrides the existing
shutdown/reboot/halt/poweroff/coldreboot/pm-hibernate/pm-suspend* commands
and first runs a set of scripts, which all have to exit successfully,
before molly-guard invokes the real command.

One of the scripts checks for existing SSH sessions. If any of the four
commands are called interactively over an SSH session, the shell script
prompts you to enter the name of the host you wish to shut down. This should
adequately prevent you from accidental shutdowns and reboots.

molly-guard renames the real binaries to /usr/sbin/<command>.no-molly-guard.
You can bypass molly-guard by running those binaries directly.

%prep
%setup -q

%build
# The Makefile hard-codes Debian's path to the DocBook stylesheet. The
# canonical URL resolves offline through the XML catalog on both Debian and
# RHEL, so the man page builds on either.
make shutdown molly-guard.8 \
    DB2MAN=http://docbook.sourceforge.net/release/xsl/current/manpages/docbook.xsl

%install
# Not "make install": it creates the /usr/sbin symlinks, which belong to
# systemd and are set up by the scriptlets below instead, and it runs
# install -o root, which needs a root build.
install -D -m 0755 shutdown %{buildroot}%{_prefix}/lib/molly-guard/molly-guard
install -D -m 0644 rc %{buildroot}%{_sysconfdir}/molly-guard/rc
install -D -m 0755 -t %{buildroot}%{_sysconfdir}/molly-guard/run.d run.d/*
install -d -m 0755 %{buildroot}%{_sysconfdir}/molly-guard/messages.d
install -D -m 0644 molly-guard.8 %{buildroot}%{_mandir}/man8/molly-guard.8

# dracut copies /usr/sbin/reboot (and friends) into the shutdown initramfs
# (/run/initramfs) and runs it from there to finish a reboot. It follows the
# molly-guard symlink but has no reason to bring the renamed original along,
# so without this the wrapper finds no reboot.no-molly-guard, exits with
# "E: not a regular file:" and dracut drops into its debug shell instead of
# rebooting.
install -d -m 0755 %{buildroot}%{_sysconfdir}/dracut.conf.d
cat > %{buildroot}%{_sysconfdir}/dracut.conf.d/molly-guard.conf <<'EOC'
# Installed by the molly-guard RPM. The shutdown initramfs gets the molly-guard
# wrapper as /usr/sbin/reboot etc.; give it the real commands too.
install_items+=" /usr/sbin/reboot.no-molly-guard /usr/sbin/poweroff.no-molly-guard /usr/sbin/halt.no-molly-guard /usr/sbin/shutdown.no-molly-guard "
EOC

%pre
set -e

if [ "$(readlink -e /sbin)" != /usr/sbin ]; then
    echo "Only systems with /sbin symlinked to /usr/sbin are supported" >&2
    exit 242
fi

for cmd in halt poweroff reboot shutdown coldreboot pm-hibernate pm-suspend pm-suspend-hybrid; do
    cmd_orig=/usr/sbin/$cmd
    cmd_renamed=$cmd_orig.no-molly-guard
    test -e $cmd_orig -o -h $cmd_orig || continue #if $cmd does not even exist in /usr/sbin
    test ../lib/molly-guard/molly-guard = "$(readlink $cmd_orig)" && continue #if we already symlinked it (reinstall/force)
    rm -f $cmd_renamed #we don't want the next line to fail if reinstalled with existing original
    mv $cmd_orig $cmd_renamed
    ln -s ../lib/molly-guard/molly-guard $cmd_orig
done

exit 0

%transfiletriggerin -- /usr/sbin
set -e

for cmd in halt poweroff reboot shutdown coldreboot pm-hibernate pm-suspend pm-suspend-hybrid; do
    cmd_orig=/usr/sbin/$cmd
    cmd_renamed=$cmd_orig.no-molly-guard
    test -e $cmd_orig -o -h $cmd_orig || continue #if $cmd does not even exist in /usr/sbin
    test ../lib/molly-guard/molly-guard = "$(readlink $cmd_orig)" && continue #if we already symlinked it (reinstall/force)
    rm -f $cmd_renamed #we don't want the next line to fail if reinstalled with existing original
    mv $cmd_orig $cmd_renamed
    ln -s ../lib/molly-guard/molly-guard $cmd_orig
done

exit 0

%posttrans
# The initramfs of the running kernel is what dracut-shutdown.service restores
# at shutdown, and it was built without the dracut.conf.d entry above. Rebuild
# it so the next reboot works; later kernels pick the entry up on their own.
if command -v dracut >/dev/null 2>&1 && [ -d /lib/modules/$(uname -r) ]; then
    dracut -f --regenerate-all ||
        echo "molly-guard: dracut failed, the next reboot may hang in dracut's debug shell" >&2
fi

%postun
set -e

test "$1" -eq 1 && exit 0 #don't remove files when removing an old molly-guard package after upgrade

for cmd in halt poweroff reboot shutdown coldreboot pm-hibernate pm-suspend pm-suspend-hybrid; do
    cmd_orig=/usr/sbin/$cmd
    cmd_renamed=$cmd_orig.no-molly-guard
    test -e $cmd_renamed -o -h $cmd_renamed || continue #if no replaced binaries exist
    rm -f $cmd_orig
    mv $cmd_renamed $cmd_orig
done

exit 0


%files
%license debian/copyright
%doc debian/changelog
%dir %{_sysconfdir}/molly-guard
%dir %{_sysconfdir}/molly-guard/messages.d
%dir %{_sysconfdir}/molly-guard/run.d
%config(noreplace) %{_sysconfdir}/molly-guard/rc
%config(noreplace) %{_sysconfdir}/molly-guard/run.d/10-print-message
%config(noreplace) %{_sysconfdir}/molly-guard/run.d/30-query-hostname
%config(noreplace) %{_sysconfdir}/dracut.conf.d/molly-guard.conf
%{_prefix}/lib/molly-guard
%{_mandir}/man8/molly-guard.8*

%changelog
* Tue Oct 27 2026 M Norrby <norrby@lysator.liu.se> - 0.8.6-2
- Build from the source tarball with rpmbuild alone, no Debian tooling
- Keep local edits to the configuration across upgrades
- Warn when the initramfs rebuild fails
- Require run-parts, without which the checks were silently skipped

* Tue Oct 27 2026 M Norrby <norrby@lysator.liu.se> - 0.8.6-1
- Update to molly-guard 0.8.6, packaging changes only

* Tue Oct 27 2026 M Norrby <norrby@lysator.liu.se> - 0.8.5-13
- Bring the real reboot commands into dracut's shutdown initramfs, so a
  reboot no longer hangs in dracut's debug shell (Hampus Rosenquist)
