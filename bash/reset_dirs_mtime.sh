#!/bin/bash

if [ -z "${script_dir}" ]; then script_dir=/root/scripts; fi
if [ -z "${log_dir}"    ]; then log_dir=/root; fi

dirs=(
# root@example.com:~# du -sh /*
# 0	/dev
# 0	/proc
# 0	/sys
	"/bin"
	"/boot"
	"/etc"
	"/home"
	"/lib"
	"/lib64"
	"/lost+found"
	"/media"
	"/mnt"
	"/opt"
	"/root"
	"/run"
	"/sbin"
	"/srv"
	"/tmp"
	"/usr"
	"/var"
# 0	/initrd.img
# 0	/vmlinuz
)

for i in "${dirs[@]}"
do
	if [ -d "$i" ]
	then
		echo "$i"
		cd "$i"

		touch "${log_dir}/$i.log"
		echo "$i" >> "${log_dir}/$i.log"

		python "${script_dir}/t.py" adr >> "${log_dir}/$i.log"
	fi
done
