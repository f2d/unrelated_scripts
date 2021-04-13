#!/bin/bash

source "/root/scripts/common_script_variables.sh"

if [ -z "${start_date}" ]; then start_date=`date '+%F_%H-%M-%S.%N'` ; fi
if [ -z "${script_dir}" ]; then script_dir="/root/scripts" ; fi
if [ -z "${log_dir}"    ]; then log_dir="/root" ; fi

echo "- ${start_date} - Started time reset script."

cmd_name="python"
cmd_script_name="t.py"

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

		"${cmd_name}" "${script_dir}/${cmd_script_name}" adr >> "${log_dir}/$i.log"
	fi
done

echo "- $(date '+%F_%H-%M-%S.%N') - Finished time reset script."
