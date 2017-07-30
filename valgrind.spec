%{?scl:%scl_package valgrind}

Summary: Tool for finding memory management bugs in programs
Name: %{?scl_prefix}valgrind
Version: 3.13.0
Release: 1%{?dist}
Epoch: 1
License: GPLv2+
URL: http://www.valgrind.org/
Group: Development/Debuggers

# Only necessary for RHEL, will be ignored on Fedora
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

# Are we building for a Software Collection?
%{?scl:%global is_scl 1}
%{!?scl:%global is_scl 0}

# Only arches that are supported upstream as multilib and that the distro
# has multilib builds for should set build_multilib 1. In practice that
# is only x86_64 and ppc64 (but not in fedora 21 and later, and never
# for ppc64le or when building for scl).
%global build_multilib 0

%ifarch x86_64
 %global build_multilib 1
%endif

%ifarch ppc64
  %if %{is_scl}
    %global build_multilib 0
  %else
    %if 0%{?rhel}
      %global build_multilib 1
    %endif
    %if 0%{?fedora}
      %global build_multilib (%fedora < 21)
    %endif
  %endif
%endif

# Note s390x doesn't have an openmpi port available.
# We never want the openmpi subpackage when building a software collecton
%if %{is_scl}
  %global build_openmpi 0
%else
  %ifarch %{ix86} x86_64 ppc ppc64 ppc64le %{arm} aarch64
    %global build_openmpi 1
  %else
    %global build_openmpi 0
  %endif
%endif

# Whether to run the full regtest or only a limited set
# The full regtest includes gdb_server integration tests.
# On arm the gdb integration tests hang for unknown reasons.
# On rhel6 the gdb_server tests hang.
# On rhel7 they hang on ppc64 and ppc64le.
%ifarch %{arm}
  %global run_full_regtest 0
%else
  %if 0%{?rhel} == 6
    %global run_full_regtest 0
  %else
    %if 0%{?rhel} == 7
      %ifarch ppc64 ppc64le
        %global run_full_regtest 0
      %else
        %global run_full_regtest 1
      %endif
    %else
      %global run_full_regtest 1
    %endif
  %endif
%endif

# Generating minisymtabs doesn't really work for the staticly linked
# tools. Note (below) that we don't strip the vgpreload libraries at all
# because valgrind might read and need the debuginfo in those (client)
# libraries for better error reporting and sometimes correctly unwinding.
# So those will already have their full symbol table.
%undefine _include_minidebuginfo

Source0: ftp://sourceware.org/pub/valgrind/valgrind-%{version}.tar.bz2

# Needs investigation and pushing upstream
Patch1: valgrind-3.9.0-cachegrind-improvements.patch

# KDE#211352 - helgrind races in helgrind's own mythread_wrapper
Patch2: valgrind-3.9.0-helgrind-race-supp.patch

# Make ld.so supressions slightly less specific.
Patch3: valgrind-3.9.0-ldso-supp.patch

# KDE#381272  ppc64 doesn't compile test_isa_2_06_partx.c without VSX support
Patch4: valgrind-3.13.0-ppc64-check-no-vsx.patch

%if %{build_multilib}
# Ensure glibc{,-devel} is installed for both multilib arches
BuildRequires: /lib/libc.so.6 /usr/lib/libc.so /lib64/libc.so.6 /usr/lib64/libc.so
%endif

%if 0%{?fedora} >= 15
BuildRequires: glibc-devel >= 2.14
%else
%if 0%{?rhel} >= 6
BuildRequires: glibc-devel >= 2.12
%else
BuildRequires: glibc-devel >= 2.5
%endif
%endif

%if %{build_openmpi}
BuildRequires: openmpi-devel >= 1.3.3
%endif

# For %%build and %%check.
# In case of a software collection, pick the matching gdb and binutils.
%if %{run_full_regtest}
BuildRequires: %{?scl_prefix}gdb
%endif
BuildRequires: %{?scl_prefix}binutils

# gdbserver_tests/filter_make_empty uses ps in test
BuildRequires: procps

# Some testcases require g++ to build
BuildRequires: gcc-c++

# check_headers_and_includes uses Getopt::Long
%if 0%{?fedora}
BuildRequires: perl-generators
%endif
BuildRequires: perl(Getopt::Long)

%{?scl:Requires:%scl_runtime}

# We need to fixup selinux file context when doing a scl build.
# In RHEL6 we might need to fix up the labels even though the
# meta package sets up a fs equivalence. See post.
%if 0%{?rhel} == 6
%{?scl:Requires(post): /sbin/restorecon}
%endif

ExclusiveArch: %{ix86} x86_64 ppc ppc64 ppc64le s390x armv7hl aarch64
%ifarch %{ix86}
%define valarch x86
%define valsecarch %{nil}
%endif
%ifarch x86_64
%define valarch amd64
%define valsecarch x86
%endif
%ifarch ppc
%define valarch ppc32
%define valsecarch %{nil}
%endif
%ifarch ppc64
  %define valarch ppc64be
  %if %{build_multilib}
    %define valsecarch ppc32
  %else
    %define valsecarch %{nil}
  %endif
%endif
%ifarch ppc64le
%define valarch ppc64le
%define valsecarch %{nil}
%endif
%ifarch s390x
%define valarch s390x
%define valsecarch %{nil}
%endif
%ifarch armv7hl
%define valarch arm
%define valsecarch %{nil}
%endif
%ifarch aarch64
%define valarch arm64
%define valsecarch %{nil}
%endif

%description
Valgrind is an instrumentation framework for building dynamic analysis
tools. There are Valgrind tools that can automatically detect many
memory management and threading bugs, and profile your programs in
detail. You can also use Valgrind to build new tools. The Valgrind
distribution currently includes six production-quality tools: a memory
error detector (memcheck, the default tool), two thread error
detectors (helgrind and drd), a cache and branch-prediction profiler
(cachegrind), a call-graph generating cache and branch-prediction
profiler (callgrind), and a heap profiler (massif).

%package devel
Summary: Development files for valgrind
Group: Development/Debuggers
Requires: %{?scl_prefix}valgrind = %{epoch}:%{version}-%{release}

%description devel
Header files and libraries for development of valgrind aware programs
or valgrind plugins.

%if %{build_openmpi}
%package openmpi
Summary: OpenMPI support for valgrind
Group: Development/Debuggers
Requires: %{?scl_prefix}valgrind = %{epoch}:%{version}-%{release}

%description openmpi
A wrapper library for debugging OpenMPI parallel programs with valgrind.
See the section on Debugging MPI Parallel Programs with Valgrind in the
Valgrind User Manual for details.
%endif

%prep
%setup -q -n %{?scl:%{pkg_name}}%{!?scl:%{name}}-%{version}

%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1

%build
# We need to use the software collection compiler and binutils if available.
# The configure checks might otherwise miss support for various newer
# assembler instructions.
%{?scl:PATH=%{_bindir}${PATH:+:${PATH}}}

CC=gcc
%if %{build_multilib}
# Ugly hack - libgcc 32-bit package might not be installed
mkdir -p shared/libgcc/32
ar r shared/libgcc/32/libgcc_s.a
ar r shared/libgcc/libgcc_s_32.a
CC="gcc -B `pwd`/shared/libgcc/"
%endif

# Old openmpi-devel has version depended paths for mpicc.
%if %{build_openmpi}
%if 0%{?fedora} >= 13 || 0%{?rhel} >= 6
%define mpiccpath %{!?scl:%{_libdir}}%{?scl:%{_root_libdir}}/openmpi/bin/mpicc
%else
%define mpiccpath %{!?scl:%{_libdir}}%{?scl:%{_root_libdir}}/openmpi/*/bin/mpicc
%endif
%endif

# Filter out some flags that cause lots of valgrind test failures.
# Also filter away -O2, valgrind adds it wherever suitable, but
# not for tests which should be -O0, as they aren't meant to be
# compiled with -O2 unless explicitely requested. Same for any -mcpu flag.
# Ideally we will change this to only be done for the non-primary build
# and the test suite.
%undefine _hardened_build
OPTFLAGS="`echo " %{optflags} " | sed 's/ -m\(64\|3[21]\) / /g;s/ -fexceptions / /g;s/ -fstack-protector\([-a-z]*\) / / g;s/ -Wp,-D_FORTIFY_SOURCE=2 / /g;s/ -O2 / /g;s/ -mcpu=\([a-z0-9]\+\) / /g;s/^ //;s/ $//'`"
%configure CC="$CC" CFLAGS="$OPTFLAGS" CXXFLAGS="$OPTFLAGS" \
%if %{build_openmpi}
  --with-mpicc=%{mpiccpath} \
%endif
  GDB=%{_bindir}/gdb

make %{?_smp_mflags}

# Ensure there are no unexpected file descriptors open,
# the testsuite otherwise fails.
cat > close_fds.c <<EOF
#include <stdlib.h>
#include <unistd.h>
int main (int argc, char *const argv[])
{
  int i, j = sysconf (_SC_OPEN_MAX);
  if (j < 0)
    exit (1);
  for (i = 3; i < j; ++i)
    close (i);
  execvp (argv[1], argv + 1);
  exit (1);
}
EOF
gcc $RPM_OPT_FLAGS -o close_fds close_fds.c

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install
mkdir docs/installed
mv $RPM_BUILD_ROOT%{_datadir}/doc/valgrind/* docs/installed/
rm -f docs/installed/*.ps

# We want the MPI wrapper installed under the openmpi libdir so the script
# generating the MPI library requires picks them up and sets up the right
# openmpi libmpi.so requires. Install symlinks in the original/upstream
# location for backwards compatibility.
%if %{build_openmpi}
pushd $RPM_BUILD_ROOT%{_libdir}
mkdir -p openmpi/valgrind
cd valgrind
mv libmpiwrap-%{valarch}-linux.so ../openmpi/valgrind/
ln -s ../openmpi/valgrind/libmpiwrap-%{valarch}-linux.so
popd
%endif

%if "%{valsecarch}" != ""
pushd $RPM_BUILD_ROOT%{_libdir}/valgrind/
rm -f *-%{valsecarch}-* || :
for i in *-%{valarch}-*; do
  j=`echo $i | sed 's/-%{valarch}-/-%{valsecarch}-/'`
  ln -sf ../../lib/valgrind/$j $j
done
popd
%endif

rm -f $RPM_BUILD_ROOT%{_libdir}/valgrind/*.supp.in

%ifarch %{ix86} x86_64
# To avoid multilib clashes in between i?86 and x86_64,
# tweak installed <valgrind/config.h> a little bit.
for i in HAVE_PTHREAD_CREATE_GLIBC_2_0 HAVE_PTRACE_GETREGS HAVE_AS_AMD64_FXSAVE64 \
%if 0%{?rhel} == 5
         HAVE_BUILTIN_ATOMIC HAVE_BUILTIN_ATOMIC_CXX \
%endif
         ; do
  sed -i -e 's,^\(#define '$i' 1\|/\* #undef '$i' \*/\)$,#ifdef __x86_64__\n# define '$i' 1\n#endif,' \
    $RPM_BUILD_ROOT%{_includedir}/valgrind/config.h
done
%endif

# We don't want debuginfo generated for the vgpreload libraries.
# Turn off execute bit so they aren't included in the debuginfo.list.
# We'll turn the execute bit on again in %%files.
chmod 644 $RPM_BUILD_ROOT%{_libdir}/valgrind/vgpreload*-%{valarch}-*so

%check
# Make sure some info about the system is in the build.log
uname -a
rpm -q glibc gcc %{?scl_prefix}binutils
%if %{run_full_regtest}
rpm -q %{?scl_prefix}gdb
%endif

LD_SHOW_AUXV=1 /bin/true
cat /proc/cpuinfo

# Make sure a basic binary runs.
./vg-in-place /bin/true

# Build the test files with the software collection compiler if available.
%{?scl:PATH=%{_bindir}${PATH:+:${PATH}}}
# Make sure no extra CFLAGS, CXXFLAGS or LDFLAGS leak through,
# the testsuite sets all flags necessary. See also configure above.
make %{?_smp_mflags} CFLAGS="" CXXFLAGS="" LDFLAGS="" check

# Workaround https://bugzilla.redhat.com/show_bug.cgi?id=1434601
# for gdbserver tests.
export PYTHONCOERCECLOCALE=0

echo ===============TESTING===================
%if %{run_full_regtest}
  ./close_fds make regtest || :
%else
  ./close_fds make nonexp-regtest || :
%endif

# Make sure test failures show up in build.log
# Gather up the diffs (at most the first 20 lines for each one)
MAX_LINES=20
diff_files=`find . -name '*.diff' | sort`
if [ z"$diff_files" = z ] ; then
   echo "Congratulations, all tests passed!" >> diffs
else
   for i in $diff_files ; do
      echo "=================================================" >> diffs
      echo $i                                                  >> diffs
      echo "=================================================" >> diffs
      if [ `wc -l < $i` -le $MAX_LINES ] ; then
         cat $i                                                >> diffs
      else
         head -n $MAX_LINES $i                                 >> diffs
         echo "<truncated beyond $MAX_LINES lines>"            >> diffs
      fi
   done
fi
cat diffs
echo ===============END TESTING===============

%files
%defattr(-,root,root)
%doc COPYING NEWS README_*
%doc docs/installed/html docs/installed/*.pdf
%{_bindir}/*
%dir %{_libdir}/valgrind
# Install everything in the libdir except the .so and .a files.
# The vgpreload so files might file mode adjustment (see below).
# The libmpiwrap so files go in the valgrind-openmpi package.
# The .a archives go into the valgrind-devel package.
%{_libdir}/valgrind/*[^ao]
# Turn on executable bit again for vgpreload libraries.
# Was disabled in %%install to prevent debuginfo stripping.
%attr(0755,root,root) %{_libdir}/valgrind/vgpreload*-%{valarch}-*so
# And install the symlinks to the secarch files if the exist.
# These are separate from the above because %%attr doesn't work
# on symlinks.
%if "%{valsecarch}" != ""
%{_libdir}/valgrind/vgpreload*-%{valsecarch}-*so
%endif
%{_mandir}/man1/*

%files devel
%defattr(-,root,root)
%{_includedir}/valgrind
%dir %{_libdir}/valgrind
%{_libdir}/valgrind/*.a
%{_libdir}/pkgconfig/*

%if %{build_openmpi}
%files openmpi
%defattr(-,root,root)
%dir %{_libdir}/valgrind
%{_libdir}/openmpi/valgrind/libmpiwrap*.so
%{_libdir}/valgrind/libmpiwrap*.so
%endif

%if 0%{?rhel} == 6
%post
# There is a bug in rpm (rhbz#214737) that might cause post to be run
# even thought the binary isn't installed when installing two multilib
# versions at the same time.
if [ -x %{_bindir}/valgrind ]; then
# On RHEL6 the fs equivalency should be setup by the devtoolset meta
# package, but because of a rpm bug (rhbz#924044) it might not work.
%{?scl:/sbin/restorecon %{_bindir}/valgrind}%{!?scl:true}
fi
%endif

%changelog
* Thu Jun 15 2017 Mark Wielaard <mjw@fedoraproject.org> - 3.13.0-1
- valgrind 3.13.0 final.
- Drop all upstreamed patches.
- Add valgrind-3.13.0-ppc64-check-no-vsx.patch

* Tue Jun  6  2017 Mark Wielaard <mjw@fedoraproject.org> - 3.13.0-0.1.RC1
- Update description as suggested by Ivo Raisr.
- Workaround gdb/python bug in testsuite (#1434601)
- Update to upstream 3.13.0-RC1.
- Drop all upstreamed patches.
- Add valgrind-3.13.0-arm-dcache.patch
- Add valgrind-3.13.0-g++-4.4.patch
- Add valgrind-3.13.0-s390x-GI-strcspn.patch
- Add valgrind-3.13.0-xtree-callgrind.patch

* Tue Mar 28 2017 Mark Wielaard <mjw@redhat.com> - 3.12.0-8
- Add valgrind-3.12.0-powerpc-register-pair.patch
- Add valgrind-3.12.0-ppc64-isa-3_00.patch

* Sat Feb 18 2017 Mark Wielaard <mjw@redhat.com> - 3.12.0-7
- Add valgrind-3.12.0-aarch64-syscalls.patch

* Sat Feb 18 2017 Mark Wielaard <mjw@redhat.com> - 3.12.0-6
- Add valgrind-3.12.0-arm64-ppc64-prlimit64.patch
- Add valgrind-3.12.0-arm64-hint.patch
- Add valgrind-3.12.0-clone-spawn.patch
- Add valgrind-3.12.0-quick-fatal-sigs.patch
- Add valgrind-3.12.0-exit_group.patch
- Add valgrind-3.12.0-deregister-stack.patch
- Add valgrind-3.12.0-x86-gdt-and-ss.patch
- Add valgrind-3.12.0-cd-dvd-ioctl.patch
- Add valgrind-3.12.0-tests-cxx11_abi_0.patch
- Add valgrind-3.12.0-helgrind-dl_allocate_tls-supp.patch
- Add valgrind-3.12.0-ppc-xxsel.patch

* Fri Feb 17 2017 Mark Wielaard <mjw@redhat.com> - 3.12.0-5
- Add valgrind-3.12.0-ppc64-r2.patch (#1424367)

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:3.12.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Sat Nov 12 2016 Mark Wielaard <mjw@redhat.com> - 3.12.0-3
- Add valgrind-3.12.0-nocwd-cleanup.patch (#1390282)

* Fri Oct 21 2016 Orion Poplawski <orion@cora.nwra.com> - 1:3.12.0-2
- Rebuild for openmpi 2.0

* Fri Oct 21 2016 Mark Wielaard <mjw@redhat.com> - 3.12.0-1
- Update to valgrind 3.12.0 release.

* Thu Oct 20 2016 Mark Wielaard <mjw@redhat.com> - 3.12.0-0.4-RC2
- Update to 3.12.0-RC1. Drop integrated patches.
- Add valgrind-3.12.0-skip-cond-var.patch

* Fri Sep 30 2016 Mark Wielaard <mjw@redhat.com> - 3.12.0-0.3-BETA1
- Clear CFLAGS, CXXFLAGS and LDFLAGS during make check.

* Thu Sep 29 2016 Mark Wielaard <mjw@redhat.com> - 3.12.0-0.2-BETA1
- Add valgrind-3.12-beta1-ppc64be.patch. (#1378963)
- Enable gdb_server tests again. (#1378143)
- And disable it again on rhel6 (both i686 and x86_64)
  and rhel7 (ppc64 and ppc64le only) (#1380513)

* Tue Sep 20 2016 Mark Wielaard <mjw@redhat.com> - 3.12.0-0.1-BETA1
- Update to valgrind 3.12.0 pre-release.
  - Drop upstreamed patches.
  - Disable exp-tests in %%check. GDB crashes on gdb_server tests.

* Fri Jul 22 2016 Mark Wielaard <mjw@redhat.com> - 3.11.0-26
- Rebase against fedora package:
  - Only build valgrind-openmpi when not creating a software collection.
  - No support for multilib on secondary arches when creating scl.
  - Mandatory Perl build-requires added
  - Add valgrind-3.11.0-shr.patch
  - Add valgrind-3.11.0-pcmpxstrx-0x70-0x19.patch
  - Update valgrind-3.11.0-wrapmalloc.patch
  - Add valgrind-3.11.0-sighandler-stack.patch
  - Update valgrind-3.11.0-ppoll-mask.patch (#1344082)
  - Add valgrind-3.11.0-arm64-handle_at.patch
  - Add valgrind-3.11.0-ppc64-syscalls.patch
  - Add valgrind-3.11.0-deduppoolalloc.patch
  - Add valgrind-3.11.0-ppc-bcd-addsub.patch
  - Add valgrind-3.11.0-ppc64-vgdb-vr-regs.patch
  - Update valgrind-3.11.0-cxx-freeres.patch (x86 final_tidyup fix)
  - Add valgrind-3.11.0-s390x-risbgn.patch
  - Add valgrind-3.11.0-cxx-freeres.patch (#1312647)
  - Add valgrind-3.11.0-ppc64-separate-socketcalls.patch
  - Add valgrind-3.11.0-isZeroU.patch
  - Replace valgrind-3.11.0-arm64-ldpsw.patch with upstream version

* Fri Apr 01 2016 Mark Wielaard <mjw@redhat.com> - 3.11.0-19
- Touch up empty .exp files. (#1323160)

* Fri Apr 01 2016 Mark Wielaard <mjw@redhat.com> - 3.11.0-18
- Refresh valgrind from fedora. (#1323160)

* Wed Feb 24 2016 Mark Wielaard <mjw@redhat.com> - 3.11.0-11
- Rebuilt against new buildroot.

* Fri Jan 22 2016 Mark Wielaard <mjw@redhat.com> - 3.11.0-9
- Fix valgrind-3.11.0-pthread_barrier.patch to apply with older patch.
- Fix multilib issue in config.h with HAVE_AS_AMD64_FXSAVE64.

* Thu Jan 21 2016 Mark Wielaard <mjw@redhat.com> - 3.11.0-8
- Remerge with fedora to rebase to valgrind 3.11.0+ (#1290471)

* Thu Jan 14 2016 Mark Wielaard <mjw@redhat.com> - 3.11.0-5
- Merge with fedora to rebase to valgrind 3.11.0 (#1290471)

* Tue Oct 13 2015 Mark Wielaard <mjw@redhat.com> - 3.10.1-15
- Add valgrind-3.11.0-rexw-cvtps2pd.patch (#1268438)

* Tue Sep 01 2015 Mark Wielaard <mjw@redhat.com> - 3.10.1-14
- Add valgrind-3.10.1-helgrind-supp-io-mempcpy.patch (#1248891)

* Tue Jul 07 2015 Mark Wielaard <mjw@redhat.com> - 3.10.1-13
- 3.10.1 Refresh.
  - Add valgrind-3.10.1-di_notify_mmap.patch
  - Add valgrind-3.10.1-memmove-ld_so-ppc64.patch
  - Add valgrind-3.10.1-kernel-4.0.patch.
  - Add valgrind-3.10.1-cfi-redzone.patch.
  - Add valgrind-3.10.1-memfd_create.patch.
  - Add valgrind-3.10.1-syncfs.patch.
  - Add valgrind-3.10.1-arm-process_vm_readv_writev.patch.
  - Add valgrind-3.10.1-fno-ipa-icf.patch.
  - Add valgrind-3.10.1-demangle-q.patch
  - Add valgrind-3.10-1-ppc64-sigpending.patch
  - Filter out -fstack-protector-strong and disable _hardened_build.
  - Add valgrind-3.10.1-send-recv-mmsg.patch
  - Add mount and umount2 to valgrind-3.10.1-aarch64-syscalls.patch.
  - Add valgrind-3.10.1-glibc-version-check.patch
  - Add accept4 to valgrind-3.10.1-aarch64-syscalls.patch.
  - Add valgrind-3.10.1-ppc64-accept4.patch.
  - Add valgrind-3.10.1-aarch64-syscalls.patch.
  - Add valgrind-3.10-s390-spechelper.patch.
  - Add valgrind-3.10.1-mempcpy.patch.

* Thu Dec 18 2014 Mark Wielaard <mjw@redhat.com> - 3.10.1-1
- Upgrade to 3.10.1.

* Wed May 28 2014 Mark Wielaard <mjw@redhat.com> - 3.9.0-8.3
- Fix %%post to be rhel6 only (#1101849)

* Mon May 19 2014 Mark Wielaard <mjw@redhat.com> - 3.9.0-8.2
- Fix colon typo in make nonexp-regtest.

* Mon May 12 2014 Mark Wielaard <mjw@redhat.com> - 3.9.0-8.1
- Rebase to 3.9.0-8.
- Don't cleanup fake 32-bit libgcc created in %%build. make regtest
  might depend on it to build -m32 binaries.
- Use nonexp-regtest in check so gdbserver_tests are not run.
  They might hang the build.

* Wed Dec 11 2013 Mark Wielaard <mjw@redhat.com> - 3.8.1-30.8
- Remove nonexp-regtest check hack. (#1019750)

* Mon Nov  4 2013 Mark Wielaard <mjw@redhat.com> - 3.8.1-30.7
- Add valgrind-3.8.1-amd64-sigstack.patch (#1026230)

* Mon Oct 14 2013 Mark Wielaard <mjw@redhat.com> - 3.8.1-30.6
- Fix colon typo in make nonexp-regtest.

* Mon Oct 14 2013 Mark Wielaard <mjw@redhat.com> - 3.8.1-30.5
- Use nonexp-regtest in check so gdbserver_tests are not run.
  They might hang the build.

* Mon Oct 14 2013 Mark Wielaard <mjw@redhat.com> - 3.8.1-30.4
- Fix multilib issue with HAVE_PTRACE_GETREGS in config.h.

* Fri Oct 04 2013 Mark Wielaard <mjw@redhat.com> - 3.8.1-30.3
- Rebuilt for i386 and x86_64.

* Thu Oct 03 2013 Mark Wielaard <mjw@redhat.com> - 3.8.1-30.2
- Fixup selinux labels even on RHEL6 in post. (#1014726).

* Tue Oct 01 2013 Mark Wielaard <mjw@redhat.com> - 3.8.1-30.1
- Resync with 3.8.1-30
- Filter out -mcpu= so tests are compiled with the right flags. (#996927).
- Implement SSE4 MOVNTDQA insn (valgrind-3.8.1-movntdqa.patch)
- Don't BuildRequire /bin/ps, just BuildRequire procps
  (procps-ng provides procps).
- Fix power_ISA2_05 testcase (valgrind-3.8.1-power-isa-205-deprecation.patch)
- Fix ppc32 make check build (valgrind-3.8.1-initial-power-isa-207.patch)
- Add valgrind-3.8.1-mmxext.patch
- Allow building against glibc 2.18. (#999169)
- Add valgrind-3.8.1-s390-STFLE.patch
  s390 message-security assist (MSA) instruction extension not implemented.
- Add valgrind-3.8.1-power-isa-205-deprecation.patch
  Deprecation of some ISA 2.05 POWER6 instructions.
- Fixup auto-foo generation of new manpage doc patch.
- tests/check_isa-2_07_cap should be executable.
- Add valgrind-3.8.1-initial-power-isa-207.patch
  Initial ISA 2.07 support for POWER8-tuned libc.
- Don't depend on docdir location and version in openmpi subpackage
  description (#993938).
- Enable openmpi subpackage also on arm.
- Add valgrind-3.8.1-ptrace-include-configure.patch (#992847)
- Add valgrind-3.8.1-dwarf-anon-enum.patch
- Cleanup valgrind-3.8.1-sigill_diag.patch .orig file changes (#949687).
- Add valgrind-3.8.1-ppc-setxattr.patch
- Add valgrind-3.8.1-new-manpages.patch
- Add valgrind-3.8.1-ptrace-thread-area.patch
- Add valgrind-3.8.1-af-bluetooth.patch
- Add valgrind-3.8.1-zero-size-sections.patch. Resolves issues with zero
  sized .eh_frame sections on ppc64.

* Fri Aug 02 2013 Lubos Kocman <lkocman@redhat.com> - 3.8.1-14.4
- Fixing incorrect dist-tag el5_6 -> el5

* Thu Aug  1 2013 Frank Ch. Eigler <fche@redhat.com> 3.8.1-14.3
- bz988640, selinux context fix

* Fri Jun 28 2013 Mark Wielaard <mjw@redhat.com> 3.8.1-14.2
- selinux context fixup only needed for RHEL5 scl build. (#979412)

* Thu Apr 18 2013 Mark Wielaard <mjw@redhat.com> 3.8.1-14.1
- Resync with fedora 3.8.1-14
  - fixup selinux file context when doing a scl build.
  - Enable regtest suite on ARM.
  - valgrind-3.8.1-abbrev-parsing.patch, drop workaround, enable real fix.
  - Fix -Ttext-segment configure check. Enables s390x again.
  - BuildRequire ps for testsuite.

* Tue Mar 12 2013 Mark Wielaard <mjw@redhat.com> 3.8.1-13.1
- Resync with fedora 3.8.1-13
  - Add valgrind-3.8.1-text-segment.patch
  - Don't undefine _missing_build_ids_terminate_build.
  - Fix quoting in valgrind valgrind-3.8.1-enable-armv5.patch
  - Add valgrind-3.8.1-regtest-fixlets.patch.

* Tue Mar 12 2013 Mark Wielaard <mjw@redhat.com> 3.8.1-11.1
- Resync with fedora 3.8.1-11
  Mark Wielaard <mjw@redhat.com>
  - Add valgrind-3.8.1-manpages.patch
  - Don't disable -debuginfo package generation, but do undefine
    _missing_build_ids_terminate_build.
  - Add valgrind-3.8.1-sendmsg-flags.patch
  - Add valgrind-3.8.1-ptrace-setgetregset.patch
  - Add valgrind-3.8.1-static-variables.patch
  Jon Ciesla <limburgher@gmail.com>
  - Merge review fixes, BZ 226522.

* Wed Jan 16 2013 Mark Wielaard <mjw@redhat.com> 3.8.1-6.1
- Allow building against glibc-2.17.

* Mon Jan 14 2013 Mark Wielaard <mjw@redhat.com> 3.8.1-5.1
- Add valgrind-3.8.1-stpncpy.patch (KDE#309427)
- Add valgrind-3.8.1-ppc-32-mode-64-bit-instr.patch (#810992, KDE#308573)
- Add valgrind-3.8.1-sigill_diag.patch (#810992, KDE#309425)
- Rebase on fedora valgrind 3.8.1-5

* Tue Oct 16 2012 Mark Wielaard <mjw@redhat.com> 3.8.1-3.2
- Add valgrind-3.8.1-xaddb.patch (#866943, KDE#307106)

* Mon Oct 15 2012 Mark Wielaard <mjw@redhat.com> 3.8.1-3.1
- Rebase on fedora valgrind 3.8.1-3

* Fri Sep 14 2012 Mark Wielaard <mjw@redhat.com> 3.8.0-8.2
- Only use DTS binutils and gdb for new asm and test checks, not gcc.

* Wed Sep 12 2012 Mark Wielaard <mjw@redhat.com> 3.8.0-8.1
- Rebase on fedora 3.8.0-8.
  - Add valgrind-3.8.0-avx2-bmi-fma.patch (KDE#305728)
  - Add configure fixup valgrind-3.8.0-bmi-conf-check.patch
- Use scl gcc and binutils also for build to pick up new instruction support.

* Wed Sep 12 2012 Mark Wielaard <mjw@redhat.com> - 3.8.0-6.2
- libmpiwrapper should not require a particular libmpi.so version (#854542)

* Tue Sep 11 2012 Mark Wielaard <mjw@redhat.com> - 3.8.0-6.1
- Rebase on fedora 3.8.0-6.
  - tweak up <valgrind/config.h> to allow simultaneous installation
    of valgrind-devel.{i686,x86_64} (#848146)
  - Add valgrind-3.8.0-find-buildid.patch workaround bug #849435 (KDE#305431).
  - Add valgrind-3.8.0-abbrev-parsing.patch for #849783 (KDE#305513).
  - Add valgrind-3.8.0-lzcnt-tzcnt-bugfix.patch (KDE#295808)
  - Add valgrind-3.8.0-avx-alignment-check.patch (KDE#305926)

* Fri Aug 10 2012 Mark Wielaard <mjw@redhat.com> - 3.8.0-1.1
- update to 3.8.0 release, based on fedora 3.8.0-1.

* Mon Jul 23 2012 Mark Wielaard <mjw@redhat.com> - 3.7.0-4.2
- Enable devtoolset-1.1-gcc build requires again for check.

* Mon Jul 16 2012 Mark Wielaard <mjw@redhat.com> - 3.7.0-4.1
- Add SCL macros
- Temporarily disable gcc requires, devtoolset-1.1-gcc not yet there.

* Mon May  7 2012 Jakub Jelinek <jakub@redhat.com> 3.7.0-4
- adjust suppressions so that it works even with ld-2.15.so (#806854)
- handle DW_TAG_unspecified_type and DW_TAG_rvalue_reference_type
  (#810284, KDE#278313)
- handle .debug_types sections (#810286, KDE#284124)

* Sun Mar  4 2012 Peter Robinson <pbrobinson@fedoraproject.org> 3.7.0-2
- Fix building on ARM platform

* Fri Jan 27 2012 Jakub Jelinek <jakub@redhat.com> 3.7.0-1
- update to 3.7.0 (#769213, #782910, #772343)
- handle some further SCSI ioctls (#783936)
- handle fcntl F_SETOWN_EX and F_GETOWN_EX (#770746)

* Wed Aug 17 2011 Adam Jackson <ajax@redhat.com> 3.6.1-6
- rebuild for rpm 4.9.1 trailing / bug

* Thu Jul 21 2011 Jakub Jelinek <jakub@redhat.com> 3.6.1-5
- handle PLT unwind info (#723790, KDE#277045)

* Mon Jun 13 2011 Jakub Jelinek <jakub@redhat.com> 3.6.1-4
- fix memcpy/memmove redirection on x86_64 (#705790)

* Wed Jun  8 2011 Jakub Jelinek <jakub@redhat.com> 3.6.1-3
- fix testing against glibc 2.14

* Wed Jun  8 2011 Jakub Jelinek <jakub@redhat.com> 3.6.1-2
- fix build on ppc64 (#711608)
- don't fail if s390x support patch hasn't been applied,
  move testing into %%check (#708522)
- rebuilt against glibc 2.14

* Wed Feb 23 2011 Jakub Jelinek <jakub@redhat.com> 3.6.1-1
- update to 3.6.1

* Mon Feb 07 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:3.6.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Fri Jan 28 2011 Jakub Jelinek <jakub@redhat.com> 3.6.0-2
- rebuilt against glibc 2.13 (#673046)
- hook in pwrite64 syscall on ppc64 (#672858)
- fix PIE handling on ppc/ppc64 (#665289)

* Fri Nov 12 2010 Jakub Jelinek <jakub@redhat.com> 3.6.0-1
- update to 3.6.0
- add s390x support (#632354)
- provide a replacement for str{,n}casecmp{,_l} (#626470)

* Tue May 18 2010 Jakub Jelinek <jakub@redhat.com> 3.5.0-18
- rebuilt against glibc 2.12

* Mon Apr 12 2010 Jakub Jelinek <jakub@redhat.com> 3.5.0-16
- change pub_tool_basics.h not to include config.h (#579283)
- add valgrind-openmpi package for OpenMPI support (#565541)
- allow NULL second argument to capget (#450976)

* Wed Apr  7 2010 Jakub Jelinek <jakub@redhat.com> 3.5.0-15
- handle i686 nopw insns with more than one data16 prefix (#574889)
- DWARF4 support
- handle getcpu and splice syscalls

* Wed Jan 20 2010 Jakub Jelinek <jakub@redhat.com> 3.5.0-14
- fix build against latest glibc headers

* Wed Jan 20 2010 Jakub Jelinek <jakub@redhat.com> 3.5.0-13
- DW_OP_mod is unsigned modulus instead of signed
- fix up valgrind.pc (#551277)

* Mon Dec 21 2009 Jakub Jelinek <jakub@redhat.com> 3.5.0-12
- don't require offset field to be set in adjtimex's
  ADJ_OFFSET_SS_READ mode (#545866)

* Wed Dec  2 2009 Jakub Jelinek <jakub@redhat.com> 3.5.0-10
- add handling of a bunch of recent syscalls and fix some
  other syscall wrappers (Dodji Seketeli)
- handle prelink created split of .bss into .dynbss and .bss
  and similarly for .sbss and .sdynbss (#539874)

* Wed Nov  4 2009 Jakub Jelinek <jakub@redhat.com> 3.5.0-9
- rebuilt against glibc 2.11
- use upstream version of the ifunc support

* Wed Oct 28 2009 Jakub Jelinek <jakub@redhat.com> 3.5.0-8
- add preadv/pwritev syscall support

* Tue Oct 27 2009 Jakub Jelinek <jakub@redhat.com> 3.5.0-7
- add perf_counter_open syscall support (#531271)
- add handling of some sbb/adc insn forms on x86_64 (KDE#211410)

* Fri Oct 23 2009 Jakub Jelinek <jakub@redhat.com> 3.5.0-6
- ppc and ppc64 fixes

* Thu Oct 22 2009 Jakub Jelinek <jakub@redhat.com> 3.5.0-5
- add emulation of 0x67 prefixed loop* insns on x86_64 (#530165)

* Wed Oct 21 2009 Jakub Jelinek <jakub@redhat.com> 3.5.0-4
- handle reading of .debug_frame in addition to .eh_frame
- ignore unknown DWARF3 expressions in evaluate_trivial_GX
- suppress helgrind race errors in helgrind's own mythread_wrapper
- fix compilation of x86 tests on x86_64 and ppc tests

* Wed Oct 14 2009 Jakub Jelinek <jakub@redhat.com> 3.5.0-3
- handle many more DW_OP_* ops that GCC now uses
- handle the more compact form of DW_AT_data_member_location
- don't strip .debug_loc etc. from valgrind binaries

* Mon Oct 12 2009 Jakub Jelinek <jakub@redhat.com> 3.5.0-2
- add STT_GNU_IFUNC support (Dodji Seketeli, #518247)
- wrap inotify_init1 syscall (Dodji Seketeli, #527198)
- fix mmap/mprotect handling in memcheck (KDE#210268)

* Fri Aug 21 2009 Jakub Jelinek <jakub@redhat.com> 3.5.0-1
- update to 3.5.0

* Tue Jul 28 2009 Jakub Jelinek <jakub@redhat.com> 3.4.1-7
- handle futex ops newly added during last 4 years (#512121)

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> 3.4.1-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Jul 13 2009 Jakub Jelinek <jakub@redhat.com> 3.4.1-5
- add support for DW_CFA_{remember,restore}_state

* Mon Jul 13 2009 Jakub Jelinek <jakub@redhat.com> 3.4.1-4
- handle version 3 .debug_frame, .eh_frame, .debug_info and
  .debug_line (#509197)

* Mon May 11 2009 Jakub Jelinek <jakub@redhat.com> 3.4.1-3
- rebuilt against glibc 2.10.1

* Wed Apr 22 2009 Jakub Jelinek <jakub@redhat.com> 3.4.1-2
- redirect x86_64 ld.so strlen early (#495645)

* Mon Mar  9 2009 Jakub Jelinek <jakub@redhat.com> 3.4.1-1
- update to 3.4.1

* Mon Feb  9 2009 Jakub Jelinek <jakub@redhat.com> 3.4.0-3
- update to 3.4.0

* Wed Apr 16 2008 Jakub Jelinek <jakub@redhat.com> 3.3.0-3
- add suppressions for glibc 2.8
- add a bunch of syscall wrappers (#441709)

* Mon Mar  3 2008 Jakub Jelinek <jakub@redhat.com> 3.3.0-2
- add _dl_start suppression for ppc/ppc64

* Mon Mar  3 2008 Jakub Jelinek <jakub@redhat.com> 3.3.0-1
- update to 3.3.0
- split off devel bits into valgrind-devel subpackage

* Thu Oct 18 2007 Jakub Jelinek <jakub@redhat.com> 3.2.3-7
- add suppressions for glibc >= 2.7

* Fri Aug 31 2007 Jakub Jelinek <jakub@redhat.com> 3.2.3-6
- handle new x86_64 nops (#256801, KDE#148447)
- add support for private futexes (KDE#146781)
- update License tag

* Fri Aug  3 2007 Jakub Jelinek <jakub@redhat.com> 3.2.3-5
- add ppc64-linux symlink in valgrind ppc.rpm, so that when
  rpm prefers 32-bit binaries over 64-bit ones 32-bit
  /usr/bin/valgrind can find 64-bit valgrind helper binaries
  (#249773)
- power5+ and power6 support (#240762)

* Thu Jun 28 2007 Jakub Jelinek <jakub@redhat.com> 3.2.3-4
- pass GDB=%%{_prefix}/gdb to configure to fix default
  --db-command (#220840)

* Wed Jun 27 2007 Jakub Jelinek <jakub@redhat.com> 3.2.3-3
- add suppressions for glibc >= 2.6
- avoid valgrind internal error if io_destroy syscall is
  passed a bogus argument

* Tue Feb 13 2007 Jakub Jelinek <jakub@redhat.com> 3.2.3-2
- fix valgrind.pc again

* Tue Feb 13 2007 Jakub Jelinek <jakub@redhat.com> 3.2.3-1
- update to 3.2.3

* Wed Nov  8 2006 Jakub Jelinek <jakub@redhat.com> 3.2.1-7
- some cachegrind improvements (Ulrich Drepper)

* Mon Nov  6 2006 Jakub Jelinek <jakub@redhat.com> 3.2.1-6
- fix valgrind.pc (#213149)
- handle Intel Core2 cache sizes in cachegrind (Ulrich Drepper)

* Wed Oct 25 2006 Jakub Jelinek <jakub@redhat.com> 3.2.1-5
- fix valgrind on ppc/ppc64 where PAGESIZE is 64K (#211598)

* Sun Oct  1 2006 Jakub Jelinek <jakub@redhat.com> 3.2.1-4
- adjust for glibc-2.5

* Wed Sep 27 2006 Jakub Jelinek <jakub@redhat.com> 3.2.1-3
- another DW_CFA_set_loc handling fix

* Tue Sep 26 2006 Jakub Jelinek <jakub@redhat.com> 3.2.1-2
- fix openat handling (#208097)
- fix DW_CFA_set_loc handling

* Tue Sep 19 2006 Jakub Jelinek <jakub@redhat.com> 3.2.1-1
- update to 3.2.1 bugfix release
  - SSE3 emulation fixes, reduce memcheck false positive rate,
    4 dozens of bugfixes

* Mon Aug 21 2006 Jakub Jelinek <jakub@redhat.com> 3.2.0-5
- handle the new i686/x86_64 nops (#203273)

* Fri Jul 28 2006 Jeremy Katz <katzj@redhat.com> - 1:3.2.0-4
- rebuild to bring ppc back

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 1:3.2.0-3.1
- rebuild

* Fri Jun 16 2006 Jakub Jelinek <jakub@redhat.com> 3.2.0-3
- handle [sg]et_robust_list syscall on ppc{32,64}

* Fri Jun 16 2006 Jakub Jelinek <jakub@redhat.com> 3.2.0-2
- fix ppc64 symlink to 32-bit valgrind libdir
- handle a few extra ppc64 syscalls

* Thu Jun 15 2006 Jakub Jelinek <jakub@redhat.com> 3.2.0-1
- update to 3.2.0
  - ppc64 support

* Fri May 26 2006 Jakub Jelinek <jakub@redhat.com> 3.1.1-3
- handle [sg]et_robust_list syscalls on i?86/x86_64
- handle *at syscalls on ppc
- ensure on x86_64 both 32-bit and 64-bit glibc{,-devel} are
  installed in the buildroot (#191820)

* Wed Apr 12 2006 Jakub Jelinek <jakub@redhat.com> 3.1.1-2
- handle many syscalls that were unhandled before, especially on ppc

* Mon Apr  3 2006 Jakub Jelinek <jakub@redhat.com> 3.1.1-1
- upgrade to 3.1.1
  - many bugfixes

* Mon Mar 13 2006 Jakub Jelinek <jakub@redhat.com> 3.1.0-2
- add support for DW_CFA_val_offset{,_sf}, DW_CFA_def_cfa_sf
  and skip over DW_CFA_val_expression quietly
- adjust libc/ld.so filenames in glibc-2.4.supp for glibc 2.4
  release

* Mon Jan  9 2006 Jakub Jelinek <jakub@redhat.com> 3.1.0-1
- upgrade to 3.1.0 (#174582)
  - many bugfixes, ppc32 support

* Thu Oct 13 2005 Jakub Jelinek <jakub@redhat.com> 3.0.1-2
- remove Obsoletes for valgrind-callgrind, as it has been
  ported to valgrind 3.0.x already

* Sun Sep 11 2005 Jakub Jelinek <jakub@redhat.com> 3.0.1-1
- upgrade to 3.0.1
  - many bugfixes
- handle xattr syscalls on x86-64 (Ulrich Drepper)

* Fri Aug 12 2005 Jakub Jelinek <jakub@redhat.com> 3.0.0-3
- fix amd64 handling of cwtd instruction
- fix amd64 handling of e.g. sarb $0x4,val(%%rip)
- speedup amd64 insn decoding

* Fri Aug 12 2005 Jakub Jelinek <jakub@redhat.com> 3.0.0-2
- lower x86_64 stage2 base from 112TB down to 450GB, so that
  valgrind works even on 2.4.x kernels.  Still way better than
  1.75GB that stock valgrind allows

* Fri Aug 12 2005 Jakub Jelinek <jakub@redhat.com> 3.0.0-1
- upgrade to 3.0.0
  - x86_64 support
- temporarily obsolete valgrind-callgrind, as it has not been
  ported yet

* Tue Jul 12 2005 Jakub Jelinek <jakub@redhat.com> 2.4.0-3
- build some insn tests with -mmmx, -msse or -msse2 (#161572)
- handle glibc-2.3.90 the same way as 2.3.[0-5]

* Wed Mar 30 2005 Jakub Jelinek <jakub@redhat.com> 2.4.0-2
- resurrect the non-upstreamed part of valgrind_h patch
- remove 2.1.2-4G patch, seems to be upstreamed
- resurrect passing -fno-builtin in memcheck tests

* Sun Mar 27 2005 Colin Walters <walters@redhat.com> 2.4.0-1
- New upstream version 
- Update valgrind-2.2.0-regtest.patch to 2.4.0; required minor
  massaging
- Disable valgrind-2.1.2-4G.patch for now; Not going to touch this,
  and Fedora does not ship 4G kernel by default anymore
- Remove upstreamed valgrind-2.2.0.ioctls.patch
- Remove obsolete valgrind-2.2.0-warnings.patch; Code is no longer
  present
- Remove upstreamed valgrind-2.2.0-valgrind_h.patch
- Remove obsolete valgrind-2.2.0-unnest.patch and
  valgrind-2.0.0-pthread-stacksize.patch; valgrind no longer
  includes its own pthread library

* Thu Mar 17 2005 Jakub Jelinek <jakub@redhat.com> 2.2.0-10
- rebuilt with GCC 4

* Tue Feb  8 2005 Jakub Jelinek <jakub@redhat.com> 2.2.0-8
- avoid unnecessary use of nested functions for pthread_once
  cleanup

* Mon Dec  6 2004 Jakub Jelinek <jakub@redhat.com> 2.2.0-7
- update URL (#141873)

* Tue Nov 16 2004 Jakub Jelinek <jakub@redhat.com> 2.2.0-6
- act as if NVALGRIND is defined when using <valgrind.h>
  in non-m32/i386 programs (#138923)
- remove weak from VALGRIND_PRINTF*, make it static and
  add unused attribute

* Mon Nov  8 2004 Jakub Jelinek <jakub@redhat.com> 2.2.0-4
- fix a printout and possible problem with local variable
  usage around setjmp (#138254)

* Tue Oct  5 2004 Jakub Jelinek <jakub@redhat.com> 2.2.0-3
- remove workaround for buggy old makes (#134563)

* Fri Oct  1 2004 Jakub Jelinek <jakub@redhat.com> 2.2.0-2
- handle some more ioctls (Peter Jones, #131967)

* Thu Sep  2 2004 Jakub Jelinek <jakub@redhat.com> 2.2.0-1
- update to 2.2.0

* Thu Jul 22 2004 Jakub Jelinek <jakub@redhat.com> 2.1.2-3
- fix packaging of documentation

* Tue Jul 20 2004 Jakub Jelinek <jakub@redhat.com> 2.1.2-2
- allow tracing of 32-bit binaries on x86-64

* Tue Jul 20 2004 Jakub Jelinek <jakub@redhat.com> 2.1.2-1
- update to 2.1.2
- run make regtest as part of package build
- use glibc-2.3 suppressions instead of glibc-2.2 suppressions

* Thu Apr 29 2004 Colin Walters <walters@redhat.com> 2.0.0-1
- update to 2.0.0

* Tue Feb 25 2003 Jeff Johnson <jbj@redhat.com> 1.9.4-0.20030228
- update to 1.9.4 from CVS.
- dwarf patch from Graydon Hoare.
- sysinfo patch from Graydon Hoare, take 1.

* Fri Feb 14 2003 Jeff Johnson <jbj@redhat.com> 1.9.3-6.20030207
- add return codes to syscalls.
- fix: set errno after syscalls.

* Tue Feb 11 2003 Graydon Hoare <graydon@redhat.com> 1.9.3-5.20030207
- add handling for separate debug info (+fix).
- handle blocking readv/writev correctly.
- comment out 4 overly zealous pthread checks.

* Tue Feb 11 2003 Jeff Johnson <jbj@redhat.com> 1.9.3-4.20030207
- move _pthread_desc to vg_include.h.
- implement pthread_mutex_timedlock().
- implement pthread_barrier_wait().

* Mon Feb 10 2003 Jeff Johnson <jbj@redhat.com> 1.9.3-3.20030207
- import all(afaik) missing functionality from linuxthreads.

* Sun Feb  9 2003 Jeff Johnson <jbj@redhat.com> 1.9.3-2.20030207
- import more missing functionality from linuxthreads in glibc-2.3.1.

* Sat Feb  8 2003 Jeff Johnson <jbj@redhat.com> 1.9.3-1.20030207
- start fixing nptl test cases.

* Fri Feb  7 2003 Jeff Johnson <jbj@redhat.com> 1.9.3-0.20030207
- build against current 1.9.3 with nptl hacks.

* Tue Oct 15 2002 Alexander Larsson <alexl@redhat.com>
- Update to 1.0.4

* Fri Aug  9 2002 Alexander Larsson <alexl@redhat.com>
- Update to 1.0.0

* Wed Jul  3 2002 Alexander Larsson <alexl@redhat.com>
- Update to pre4.

* Tue Jun 18 2002 Alexander Larsson <alla@lysator.liu.se>
- Add threadkeys and extra suppressions patches. Bump epoch.

* Mon Jun 17 2002 Alexander Larsson <alla@lysator.liu.se>
- Updated to 1.0pre1

* Tue May 28 2002 Alex Larsson <alexl@redhat.com>
- Updated to 20020524. Added GLIBC_PRIVATE patch

* Thu May  9 2002 Jonathan Blandford <jrb@redhat.com>
- add missing symbol __pthread_clock_settime

* Wed May  8 2002 Alex Larsson <alexl@redhat.com>
- Update to 20020508

* Mon May  6 2002 Alex Larsson <alexl@redhat.com>
- Update to 20020503b

* Thu May  2 2002 Alex Larsson <alexl@redhat.com>
- update to new snapshot

* Mon Apr 29 2002 Alex Larsson <alexl@redhat.com> 20020428-1
- update to new snapshot

* Fri Apr 26 2002 Jeremy Katz <katzj@redhat.com> 20020426-1
- update to new snapshot

* Thu Apr 25 2002 Alex Larsson <alexl@redhat.com> 20020424-5
- Added stack patch. Commented out other patches.

* Wed Apr 24 2002 Nalin Dahyabhai <nalin@redhat.com> 20020424-4
- filter out GLIBC_PRIVATE requires, add preload patch

* Wed Apr 24 2002 Alex Larsson <alexl@redhat.com> 20020424-3
- Make glibc 2.2 and XFree86 4 the default supressions

* Wed Apr 24 2002 Alex Larsson <alexl@redhat.com> 20020424-2
- Added patch that includes atomic.h

* Wed Apr 24 2002 Alex Larsson <alexl@redhat.com> 20020424-1
- Initial build
