#!/bin/bash

source "/root/scripts/common_script_variables.sh"

if [ -z "${lock_dir}"       ]; then lock_dir="/run/lock" ; fi
if [ -z "${lock_file_name}" ]; then lock_file_name="backup_cron_job" ; fi

cmd_lock=(
	flock
	"${lock_dir}/${lock_file_name}.lock"
)

# Call it like this:
# "${cmd_lock[@]}" "${script_dir}/archive_logs_monthly.sh"
