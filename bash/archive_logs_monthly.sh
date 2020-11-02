#!/bin/bash

echo "- $(date '+%F_%H-%M-%S.%N') - Started log archiving script."

if [ -z "${start_date}" ]; then start_date="$(date '+%F_%H-%M-%S.%N')"; fi
if [ -z "${log_dir}"    ]; then log_dir=/var/log; fi
if [ -z "${script_dir}" ]; then script_dir=/root/scripts; fi

# only in this directory:
# tar cf ${log_dir}/logs_${start_date}.gz.tar --remove-files ${log_dir}/*.gz

# recursively:
# https://stackoverflow.com/a/18731818

cmd_sort=(
	sort -V
)

if [ -d "${log_dir}" ]; then
	cd "${log_dir}"

	cmd_list=(
		find
		-name "*.gz"
	)

	cmd_arch=(
		tar cf
		${log_dir}/var_logs_${start_date}.gz.tar
		--remove-files -T -
	)

	"${cmd_list[@]}" | "${cmd_sort[@]}" | "${cmd_arch[@]}"
fi

sub_dirs=(
	chatbot
	drawpile
	drawpile-srv
	duplicity
	nginx
)

for i in "${sub_dirs[@]}"
do
	sub_dir=${log_dir}/${i}

	if [ -d "${sub_dir}" ]; then
		cd "${sub_dir}"

		cmd_list=(
			find
			-daystart
			-not -mtime 0
			-not -empty
			-name "*.log*"
		)

		cmd_arch=(
			tar cfJ
			${sub_dir}_logs_${start_date}.tar.xz
			--remove-files -T -
		)

		"${cmd_list[@]}" | "${cmd_sort[@]}" | "${cmd_arch[@]}"
	fi
done

if [ -d "${log_dir}" ]; then
	cd "${log_dir}"

	source "${script_dir}/update_hostname_ip.sh"

	lftp -f "${script_dir}/upload_bak_logs.ftp"

	# sub_dir=${log_dir}/delete_after_upload
	sub_dir=/tmp/delete_after_upload

	if [ ! -d "${sub_dir}" ]; then mkdir "${sub_dir}"; fi
	if [   -d "${sub_dir}" ]; then
		mv "--target-directory=${sub_dir}" *.gz.tar
		mv "--target-directory=${sub_dir}" *.tar.xz
	fi
fi

echo "- $(date '+%F_%H-%M-%S.%N') - Finished log archiving script."
