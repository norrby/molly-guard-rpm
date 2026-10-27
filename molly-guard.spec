Name: molly-guard
Version: 0.8.5
Release: 13
Summary: protects machines from accidental shutdowns/reboots
License: see /usr/share/doc/molly-guard/copyright
Distribution: Debian
Group: Converted/admin
Requires: /usr/sbin/reboot
BuildArch: noarch

%define _rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm
%define _unpackaged_files_terminate_build 0

%prep
# Fetched from Debian's pool rather than with apt-get source, so the build
# host's distribution does not decide which version ends up in the RPM.
# molly-guard is a native Debian package: no -<revision> in the file name.
dget -u https://deb.debian.org/debian/pool/main/m/molly-guard/%{name}_%{version}.dsc

%build
cd %{NAME}-%{VERSION}
debuild -b -uc -us
mkdir -p %buildroot
mv debian/molly-guard/* %buildroot

# dracut copies /usr/sbin/reboot (and friends) into the shutdown initramfs
# (/run/initramfs) and runs it from there to finish a reboot. It follows the
# molly-guard symlink but has no reason to bring the renamed original along,
# so without this the wrapper finds no reboot.no-molly-guard, exits with
# "E: not a regular file:" and dracut drops into its debug shell instead of
# rebooting.
mkdir -p %buildroot/etc/dracut.conf.d
cat > %buildroot/etc/dracut.conf.d/molly-guard.conf <<'EOC'
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
    dracut -f --regenerate-all || :
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

%files
%defattr(0755,root,root)
%dir "/etc/molly-guard/"
%dir "/etc/molly-guard/messages.d/"
%config "/etc/molly-guard/rc"
%dir "/etc/molly-guard/run.d/"
%config "/etc/molly-guard/run.d/10-print-message"
%config "/etc/molly-guard/run.d/30-query-hostname"
%attr(0644,root,root) %config(noreplace) "/etc/dracut.conf.d/molly-guard.conf"
%dir "/usr/lib/molly-guard/"
"/usr/lib/molly-guard/molly-guard"
%dir "/usr/share/doc/molly-guard/"
"/usr/share/doc/molly-guard/changelog.gz"
"/usr/share/doc/molly-guard/copyright"
%dir "/usr/share/lintian/"
%dir "/usr/share/lintian/overrides/"
"/usr/share/lintian/overrides/molly-guard"
"/usr/share/man/man8/molly-guard.8.gz"
