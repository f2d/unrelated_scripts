#!/bin/bash

source "/root/scripts/common_script_variables.sh"

if [ -z "${start_date}" ]; then start_date=`date '+%F_%H-%M-%S.%N'` ; fi
if [ -z "${script_dir}" ]; then script_dir="/root/scripts" ; fi
if [ -z "${log_dir}"    ]; then log_dir="/var/log" ; fi

if [ "$1" == "full" ]
then
	cmd_scope="full"
else
	cmd_scope="incremental"
fi

cmd_name="duplicity"

cmd_args=(
	"${script_dir}/${cmd_name}.sh"
	"${cmd_scope}"
	"${start_date}"
)

if [ ! -d "${log_dir}/${cmd_name}" ]
then
	mkdir "${log_dir}/${cmd_name}"
fi

"${cmd_args[@]}" > "${log_dir}/${cmd_name}/${cmd_name}_${start_date}.log" 2>&1
