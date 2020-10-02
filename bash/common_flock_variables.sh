#!/bin/bash

# root_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )/"
# source "${root_dir}common-flock-variables.sh"

if [ -z "${start_date}" ]; then start_date="$(date '+%F_%H-%M-%S.%N')"; fi
if [ -z "${log_dir}"    ]; then log_dir=/var/log; fi
if [ -z "${lock_dir}"   ]; then lock_dir=/run/lock; fi
if [ -z "${script_dir}" ]; then script_dir=/root/scripts; fi

cmd_lock=(
	flock
	${lock_dir}/backup_cron_job.lock
)
