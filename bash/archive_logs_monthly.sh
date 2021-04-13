#!/bin/bash

echo "- $(date '+%F_%H-%M-%S.%N') - Started log archiving script."

source "/root/scripts/common_script_variables.sh"

if [ -z "${start_date}"   ]; then start_date=`date '+%F_%H-%M-%S.%N'` ; fi
if [ -z "${ftp_hostname}" ]; then ftp_hostname=ftp.example.com ; fi
if [ -z "${script_dir}"   ]; then script_dir="/root/scripts" ; fi
if [ -z "${log_dir}"      ]; then log_dir="/var/log" ; fi

# Only in this directory:
# tar cf ${log_dir}/logs_${start_date}.gz.tar --remove-files ${log_dir}/*.gz

# Recursively:
# https://stackoverflow.com/a/18731818

cmd_sort=(
	sort -V
)

if [ -d "${log_dir}" ]
then
	cd "${log_dir}"

	cmd_list=(
		find
		-name "*.gz"
	)

	cmd_arch=(
		tar cf
		"${log_dir}/var_logs_${start_date}.gz.tar"
		--remove-files -T -
	)

	"${cmd_list[@]}" | "${cmd_sort[@]}" | "${cmd_arch[@]}"
fi

sub_dirs=(
	"chatbot"
	"drawpile"
	"drawpile-srv"
	"duplicity"
	"nginx"
)

for i in "${sub_dirs[@]}"
do
	sub_dir="${log_dir}/${i}"

	if [ -d "${sub_dir}" ]
	then
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
			"${sub_dir}_logs_${start_date}.tar.xz"
			--remove-files -T -
		)

		"${cmd_list[@]}" | "${cmd_sort[@]}" | "${cmd_arch[@]}"
	fi
done

if [ -d "${log_dir}" ]
then
	cd "${log_dir}"

	source "${script_dir}/update_hostname_ip.sh" ${ftp_hostname}

	# Old way to use a static script file with hardcoded login/password/hostname:
	# lftp -f "${script_dir}/upload_bak_logs.ftp"

	# Feed script output into a FTP client, to avoid writing files or showing password in arguments:
	# https://stackoverflow.com/a/60655361

	source "${script_dir}/upload_bak_logs.ftp.sh" > >(lftp)

	# Wait for all running background jobs and the last-executed process substitution:
	# https://man7.org/linux/man-pages/man1/bash.1.html

	wait

	# Cleanup after upload:

	# sub_dir=${log_dir}/delete_after_upload
	sub_dir="/tmp/delete_after_upload"

	if [ ! -d "${sub_dir}" ]
	then
		mkdir "${sub_dir}"
	fi

	if [   -d "${sub_dir}" ]
	then
		mv "--target-directory=${sub_dir}" *.gz.tar
		mv "--target-directory=${sub_dir}" *.tar.xz
	fi
fi

echo "- $(date '+%F_%H-%M-%S.%N') - Finished log archiving script."
