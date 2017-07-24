%global debug_package %{nil}
%define name smartmgr
%define version
%define rel
%define commit

Name:           %{name}
Version:        %{version}
Release:        %{rel}%{?pbdata_dist}
Summary:	    Phegda smartmgr
Vendor:		    Phegda Technologies
Packager:	    Ma Ming <ming_ma@pbdata.com.cn>
Group:		    Storage
License:        ASL 2.0
URL:            http://www.phegda.com/
Source:         %name-%{version}-%{rel}.tgz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      %{_arch}
Provides:	    %name

Requires:       fio pal >= 1.3.1 pyodbc python-psutil isdct perccli hpssacli uuid protobuf-python python-twisted-core pyparted python-pyudev >= 0.19 python-six >= 1.9.0
Requires:       phegdalic >= 2.2 python-babel shannon-utils shannon-module2 python-flask python-itsdangerous python-jinja2 python-markupsafe python-werkzeug python-netifaces

%define __os_install_post %{nil}

%description
Phegda smartmgr
%{commit}

%prep
echo %{buildroot}
rm -rf $RPM_BUILD_ROOT
%setup -q -n %name-%{version}-%{rel}

%build

%install 
FILE_LIST_MAIN=%{_tmppath}/%name-file-list-main
echo -n > $FILE_LIST_MAIN

# Delete the dir where the userspace programs were built
if [ "${RPM_BUILD_ROOT}" != "/" -a -d ${RPM_BUILD_ROOT} ] ; then rm -rf ${RPM_BUILD_ROOT} ; fi
mkdir -p ${RPM_BUILD_ROOT}

function copy_n_add_file()
{
        orig_file=$1
        dest_path=$2
        distro=$3
        directive=$4

        if [ $5 ]; then
                file_name=$5
        else
                file_name=$(basename $orig_file)
        fi

        cp $orig_file ${RPM_BUILD_ROOT}$dest_path/$file_name

        add_file $orig_file $dest_path $distro $directive $file_name
}

function add_file()
{
        file_orig_path=$1
        file_dest_path=$2
        distro=$3
        directive=$4

        if [ $5 ]; then
                file_name=$5
        else
                file_name=$(basename $file_orig_path)
        fi

        echo "$directive $file_dest_path/$file_name" >> %{_tmppath}/%name-file-list-$distro
}

function add_dirs()
{
    basedir=$1
    subdir=$2
    distro=$3

    split=${subdir//\// }
    local i
    for i in $split ; do
	basedir="$basedir/$i"
	if [ ! -d "$RPM_BUILD_ROOT/$basedir" ]; then
	    mkdir -p "$RPM_BUILD_ROOT/$basedir"
	    echo "%dir $basedir" >> %{_tmppath}/%name-file-list-$distro
	fi
    done
}

# compile and optimize python src
function compile_py() {
    local fn=$1
    local e
    # there is a trick here to check for error since in python 2.4 py_compile
    # always returns 0
    e=$(python -c "import py_compile ; py_compile.main([\"$fn\"])" 2>&1)
    test -z "$e" || return 1
}

cd message && make && cd -

# add compiled python
OPT_SMARTMGR_SOURCES_LIST=$(find ./pdsframe -type f -name "*.py")
for i in $OPT_SMARTMGR_SOURCES_LIST ; do
    d=${i}
	d=$(dirname $d)
	add_dirs "/opt/smartmgr" $d main
	dest="/opt/smartmgr/$d"
    compile_py $i || exit 1
	copy_n_add_file ${i}c $dest main "%attr(0644,root,root)"
done

# add compiled python
OPT_SMARTMGR_SOURCES_LIST=$(find ./clients -type f -name "*.py")
for i in $OPT_SMARTMGR_SOURCES_LIST ; do
    d=${i}
	d=$(dirname $d)
	add_dirs "/opt/smartmgr" $d main
	dest="/opt/smartmgr/$d"
    compile_py $i || exit 1
	copy_n_add_file ${i}c $dest main "%attr(0644,root,root)"
    # copy_n_add_file ${i}o $dest main "%attr(0644,root,root)"
done

# add compiled python
OPT_SMARTMGR_SOURCES_LIST=$(find ./message -type f -name "*.py")
for i in $OPT_SMARTMGR_SOURCES_LIST ; do
    d=${i}
	d=$(dirname $d)
	add_dirs "/opt/smartmgr" $d main
	dest="/opt/smartmgr/$d"
    compile_py $i || exit 1
	copy_n_add_file ${i}c $dest main "%attr(0644,root,root)"
    # copy_n_add_file ${i}o $dest main "%attr(0644,root,root)"
done

# add compiled python
OPT_SMARTMGR_SOURCES_LIST=$(find ./service_ios -type f -name "*.py")
for i in $OPT_SMARTMGR_SOURCES_LIST ; do
    d=${i}
	d=$(dirname $d)
    if [ $d == "./service_ios/utest" ];then
        continue
    fi
	add_dirs "/opt/smartmgr" $d main
	dest="/opt/smartmgr/$d"
    compile_py $i || exit 1
	copy_n_add_file ${i}c $dest main "%attr(0644,root,root)"
done

# add compiled python
OPT_SMARTMGR_SOURCES_LIST=$(find ./service_mds -type f -name "*.py")
for i in $OPT_SMARTMGR_SOURCES_LIST ; do
    d=${i}
	d=$(dirname $d)
    if [ $d == "./service_ios/utest" ];then
        continue
    fi
	add_dirs "/opt/smartmgr" $d main
	dest="/opt/smartmgr/$d"
    compile_py $i || exit 1
	copy_n_add_file ${i}c $dest main "%attr(0644,root,root)"
done

# build api help
make -C clients/api/

%{__install} -d %{buildroot}/opt/smartmgr/clients/api/static
%{__install} -d %{buildroot}/opt/smartmgr/clients/api/templates
%{__install} -p -m 0755 clients/api/static/main.css %{buildroot}/opt/smartmgr/clients/api/static
%{__install} -p -m 0755 clients/api/templates/help.html %{buildroot}/opt/smartmgr/clients/api/templates/help.html

%{__install} -d %{buildroot}/usr/local/bin
%{__install} -p -m 0755 bin/smartmgrcli %{buildroot}/usr/local/bin

%{__install} -d %{buildroot}/var/log/smartmgr
%{__install} -d %{buildroot}/opt/smartmgr/bin
%{__install} -p -m 0755 pdsframe/pdsframe %{buildroot}/opt/smartmgr/pdsframe/
%{__install} -p -m 0755 pdsframe/pdsapi %{buildroot}/opt/smartmgr/pdsframe/

%{__install} -d %{buildroot}/opt/smartmgr/conf
%{__install} -p -m 0644 conf/service.mds.ini %{buildroot}/opt/smartmgr/conf
%{__install} -p -m 0644 conf/service.ios.ini %{buildroot}/opt/smartmgr/conf

# 根据操作系统平台,添加对应的服务启动脚本
%if 0%{?rhel} >= 7
    %{__install} -d %{buildroot}/lib/systemd/system
    %{__install} -p -m 0755 bin/smartmgr.el7 %{buildroot}/usr/local/bin/smartmgr
    %{__install} -p -m 0644 service/el7/smartmgr-mds.service %{buildroot}/lib/systemd/system
    %{__install} -p -m 0644 service/el7/smartmgr-ios.service %{buildroot}/lib/systemd/system
    %{__install} -p -m 0644 service/el7/smartmgr-api.service %{buildroot}/lib/systemd/system
    %{__install} -p -m 0644 service/el7/smartmgr-watchdog.service %{buildroot}/lib/systemd/system
    %{__install} -p -m 0755 bin/smartmgrwatchdog.el7 %{buildroot}/opt/smartmgr/bin/smartmgrwatchdog
    echo "%attr(0644,root,root) /lib/systemd/system/smartmgr-mds.service" >> %{_tmppath}/%name-file-list-main
    echo "%attr(0644,root,root) /lib/systemd/system/smartmgr-api.service" >> %{_tmppath}/%name-file-list-main
    echo "%attr(0644,root,root) /lib/systemd/system/smartmgr-ios.service" >> %{_tmppath}/%name-file-list-main
    echo "%attr(0644,root,root) /lib/systemd/system/smartmgr-watchdog.service" >> %{_tmppath}/%name-file-list-main
    echo "%config(noreplace) /lib/systemd/system/smartmgr-mds.service" >> %{_tmppath}/%name-file-list-main
    echo "%config(noreplace) /lib/systemd/system/smartmgr-api.service" >> %{_tmppath}/%name-file-list-main
    echo "%config(noreplace) /lib/systemd/system/smartmgr-ios.service" >> %{_tmppath}/%name-file-list-main
    echo "%config(noreplace) /lib/systemd/system/smartmgr-watchdog.service" >> %{_tmppath}/%name-file-list-main
    echo "%attr(0755,root,root) /opt/smartmgr/bin/smartmgrwatchdog" >> %{_tmppath}/%name-file-list-main
%else 
    %{__install} -d %{buildroot}/etc/init.d
    %{__install} -p -m 0755 bin/smartmgr.el6 %{buildroot}/usr/local/bin/smartmgr
    %{__install} -p -m 0755 service/el6/smartmgr-mds %{buildroot}/etc/init.d/
    %{__install} -p -m 0755 service/el6/smartmgr-ios %{buildroot}/etc/init.d/
    %{__install} -p -m 0755 service/el6/smartmgr-api %{buildroot}/etc/init.d/
    %{__install} -p -m 0755 service/el6/smartmgr-watchdog %{buildroot}/etc/init.d/
    %{__install} -p -m 0755 bin/smartmgrwatchdog.el6 %{buildroot}/opt/smartmgr/bin/smartmgrwatchdog
    echo "%attr(0755,root,root) /etc/init.d/smartmgr-mds" >> %{_tmppath}/%name-file-list-main
    echo "%attr(0755,root,root) /etc/init.d/smartmgr-ios" >> %{_tmppath}/%name-file-list-main
    echo "%attr(0755,root,root) /etc/init.d/smartmgr-api" >> %{_tmppath}/%name-file-list-main
    echo "%attr(0755,root,root) /etc/init.d/smartmgr-watchdog" >> %{_tmppath}/%name-file-list-main
    echo "%attr(0755,root,root) /opt/smartmgr/bin/smartmgrwatchdog" >> %{_tmppath}/%name-file-list-main
%endif


%{__install} -d %{buildroot}/etc/init.d/
%{__install} -p -m 0755 service/el7/smartmgr_ctl %{buildroot}/etc/init.d

%{__install} -d %{buildroot}/opt/smartmgr/scripts
%{__install} -p -m 0755 scripts/fiotest.py %{buildroot}/opt/smartmgr/scripts
%{__install} -p -m 0755 scripts/storcli64 %{buildroot}/opt/smartmgr/scripts
%{__install} -p -m 0755 scripts/msecli %{buildroot}/opt/smartmgr/scripts
%{__install} -p -m 0755 scripts/sas2ircu %{buildroot}/opt/smartmgr/scripts
%{__install} -p -m 0755 scripts/hioadm %{buildroot}/opt/smartmgr/scripts
%{__install} -p -m 0755 scripts/smartcache_load %{buildroot}/opt/smartmgr/scripts
%{__install} -p -m 0755 scripts/init_srbd.sh %{buildroot}/opt/smartmgr/scripts
%{__install} -p -m 0755 scripts/set_conf.sh %{buildroot}/opt/smartmgr/scripts

# firstboot
%{__install} -d %{buildroot}/opt/firstboot
%{__install} -p -m 0755 firstboot/install.sh %{buildroot}/opt/firstboot

# firstboot/common
%{__install} -d %{buildroot}/opt/firstboot/common
%{__install} -p -m 0755 firstboot/common/*.sh %{buildroot}/opt/firstboot/common

# firstboot/common/configure
%{__install} -d %{buildroot}/opt/firstboot/common/configure
%{__install} -d %{buildroot}/opt/firstboot/common/configure/smartstore2
%{__install} -d %{buildroot}/opt/firstboot/common/configure/smartstore3
%{__install} -p -m 0755 firstboot/common/configure/smartstore2/* %{buildroot}/opt/firstboot/common/configure/smartstore2/
%{__install} -p -m 0755 firstboot/common/configure/smartstore3/* %{buildroot}/opt/firstboot/common/configure/smartstore3/
%{__install} -p -m 0644 firstboot/common/configure/bonding.conf %{buildroot}/opt/firstboot/common/configure
%{__install} -p -m 0644 firstboot/common/configure/hangcheck-timer.conf %{buildroot}/opt/firstboot/common/configure
%{__install} -p -m 0644 firstboot/common/configure/hangcheck-timer.modules %{buildroot}/opt/firstboot/common/configure
%{__install} -p -m 0644 firstboot/common/configure/ifcfg-bondib0 %{buildroot}/opt/firstboot/common/configure
%{__install} -p -m 0644 firstboot/common/configure/ifcfg-ib0 %{buildroot}/opt/firstboot/common/configure
%{__install} -p -m 0644 firstboot/common/configure/ifcfg-ib1 %{buildroot}/opt/firstboot/common/configure
%{__install} -p -m 0644 firstboot/common/configure/multipath.conf %{buildroot}/opt/firstboot/common/configure
%{__install} -p -m 0644 firstboot/common/configure/srp_daemon.conf %{buildroot}/opt/firstboot/common/configure
%{__install} -p -m 0644 firstboot/common/configure/sysctl.conf %{buildroot}/opt/firstboot/common/configure
%{__install} -p -m 0644 firstboot/common/configure/global_common.conf %{buildroot}/opt/firstboot/common/configure

# firstboot/conf
%{__install} -d %{buildroot}/opt/firstboot/conf
%{__install} -p -m 0755 firstboot/conf/* %{buildroot}/opt/firstboot/conf

# firstboot/task
%{__install} -d %{buildroot}/opt/firstboot/task
%{__install} -d %{buildroot}/opt/firstboot/task/task1.d
%{__install} -d %{buildroot}/opt/firstboot/task/task2.d
%{__install} -d %{buildroot}/opt/firstboot/task/task3.d
%{__install} -d %{buildroot}/opt/firstboot/task/task4.d
%{__install} -d %{buildroot}/opt/firstboot/task/task.d
%{__cp} -a firstboot/task/task1.d/* %{buildroot}/opt/firstboot/task/task1.d
%{__cp} -a firstboot/task/task2.d/* %{buildroot}/opt/firstboot/task/task2.d
%{__cp} -a firstboot/task/task3.d/* %{buildroot}/opt/firstboot/task/task3.d
%{__cp} -a firstboot/task/task4.d/* %{buildroot}/opt/firstboot/task/task4.d
%{__cp} -a firstboot/task/task.d/*  %{buildroot}/opt/firstboot/task/task.d

%post
if [ "$1" = "1" ] ; then
    sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config
    %if 0%{?rhel} >= 7 
        systemctl enable smartmgr-watchdog.service >/dev/null 2>&1
        systemctl enable smartmgr-mds.service >/dev/null 2>&1
        systemctl enable smartmgr-ios.service >/dev/null 2>&1
        systemctl enable smartmgr-api.service >/dev/null 2>&1
        systemctl enable smartmgr_ctl >/dev/null 2>&1
    %else 
        /sbin/chkconfig smartmgr-mds on
        /sbin/chkconfig smartmgr-api on
        /sbin/chkconfig smartmgr-ios on
        /sbin/chkconfig smartmgr-watchdog on
        /sbin/chkconfig smartmgr_ctl on
    %endif
fi

if [ "$1" = "1" ] ; then
    sed -i s/00000000-0000-0000-0000-000000000000/`/usr/bin/uuid`/g /opt/smartmgr/conf/service.mds.ini
fi

if [ "$1" = "2" -a -d /etc/asm_dev_map/ ] ; then
    %if 0%{?rhel} >= 7 
        install /opt/firstboot/common/configure/smartstore3/smartscsi-disk-map.sh /etc/asm_dev_map/
    %else 
        install /opt/firstboot/common/configure/smartstore2/smartscsi-disk-map.sh /etc/asm_dev_map/
    %endif
fi

%preun
if [ "$1" = "0" ] ; then
    %if 0%{?rhel} >= 7 
        systemctl disable smartmgr-watchdog.service >/dev/null 2>&1
        systemctl disable smartmgr-mds.service >/dev/null 2>&1
        systemctl disable smartmgr-ios.service >/dev/null 2>&1
        systemctl disable smartmgr-api.service >/dev/null 2>&1
        systemctl disable smartmgr_ctl >/dev/null 2>&1
    %else 
        /sbin/chkconfig smartmgr-mds off
        /sbin/chkconfig smartmgr-api off
        /sbin/chkconfig smartmgr-ios off
        /sbin/chkconfig smartmgr-watchdog off
        /sbin/chkconfig smartmgr_ctl off

    %endif
fi

%postun

%files -f %{_tmppath}/%name-file-list-main
%config(noreplace) /opt/smartmgr/conf/service.mds.ini
%config(noreplace) /opt/smartmgr/conf/service.ios.ini
%dir /var/log/smartmgr
/etc/init.d/smartmgr_ctl
/usr/local/bin/smartmgr
/usr/local/bin/smartmgrcli
/opt/smartmgr/pdsframe/pdsframe
/opt/smartmgr/pdsframe/pdsapi
/opt/smartmgr/bin/smartmgrwatchdog
/opt/smartmgr/scripts/fiotest.py
/opt/smartmgr/scripts/storcli64
/opt/smartmgr/scripts/msecli
/opt/smartmgr/scripts/sas2ircu
/opt/smartmgr/scripts/hioadm
/opt/smartmgr/scripts/smartcache_load
/opt/smartmgr/scripts/init_srbd.sh
/opt/smartmgr/scripts/set_conf.sh
/opt/smartmgr/clients/api/static
/opt/smartmgr/clients/api/templates/help.html
/opt/firstboot

%clean
#[ "${RPM_BUILD_ROOT}" != "/" -a -d ${RPM_BUILD_ROOT} ] && rm -rf ${RPM_BUILD_ROOT}
