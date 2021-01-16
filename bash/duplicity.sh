#!/bin/bash

source "/root/scripts/common_script_variables.sh"

if [ -z "${start_date}" ]; then start_date="$(date '+%F_%H-%M-%S.%N')"; fi
if [ -z "${script_dir}" ]; then script_dir=/root/scripts; fi
if [ -z "${log_dir}"    ]; then log_dir=/var/log; fi

if [ -z "${ftp_protocol}" ]; then ftp_protocol=ftps ; fi
if [ -z "${ftp_hostname}" ]; then ftp_hostname=ftp.example.com ; fi
if [ -z "${ftp_username}" ]; then ftp_username=LOGIN ; fi
if [ -z "${ftp_password}" ]; then ftp_password=PASSWORD ; fi

echo "- ${start_date} - Started backup script."

cmd_name=duplicity

# https://stackoverflow.com/a/44811468
sanitize()
{
	local s="${1?need a string}"	# receive input in first argument
	s="${s//[^[:alnum:]]/-}"	# replace all non-alnum characters to -
	s="${s//+(-)/-}"		# convert multiple - to single -
	s="${s/#-}"			# remove - from start
	s="${s/%-}"			# remove - from end
	echo "${s,,}"			# convert to lowercase
}

if [ "$1" == "test" ]
then
	cmd_test_or_run=test
else
	cmd_test_or_run=run
fi

if [ "$1" == "all" ]
then
	cmd_scope=all_${start_date}

	cmd_args=(
		"${cmd_name}"
		full
		'--exclude-device-files'
		'--exclude=**.lock'
	)

	src_dirs_arr=(
		"/"
	)
else
	if [ "$1" == "full" ]
	then
		cmd_scope=full
	else
		cmd_scope=incremental
	fi

	cmd_args=(
		"${cmd_name}"
		"${cmd_scope}"
		'--exclude-device-files'
		'--exclude=**.lock'
		'--exclude=**/var/cache'
		'--exclude=**/var/run'
		'--exclude=**/root/.cache/duplicity'
		'--full-if-older-than=1Y'	# <- s, m, h, D, W, M, Y = seconds, minutes, hours, days, weeks, months, years
		'--no-encryption'
		'--ssl-no-check-certificate'	# <- workaround for using IP address in FTP
		# '--time-separator=.'		# <- option deprecated, dashes forbidden
	)

	src_dirs_arr=(
		"/srv"
		"/home"
		"/root"
		"/var"
		"/etc"
	)
fi

target_addr=${ftp_hostname}

source "${script_dir}/update_hostname_ip.sh" ${ftp_hostname}

ftp_path=${ftp_protocol}://${ftp_username}@${target_addr}/${HOSTNAME}_${cmd_scope}/

FTP_PASSWORD=${ftp_password}
export FTP_PASSWORD

for src_dir in "${src_dirs_arr[@]}"
do
	# https://stackoverflow.com/a/17902999
	src_dir_contents=$(shopt -s nullglob dotglob; echo $src_dir/*)

	echo "- $(date '+%F_%H-%M-%S.%N') - Checking $src_dir: ${#src_dir_contents}"

	#if [ -d "$src_dir" ]
	if (( ${#src_dir_contents} ))
	then
		name="$(sanitize $src_dir)"

		if [ "${name//-/}" == "" ]
		then
			name=all
		fi

		src_dir_start_date="$(date '+%F_%H-%M-%S.%N')"
		cmd_vars=(
			"--log-file=${log_dir}/${cmd_name}/${cmd_name}_${start_date}_${name}_${src_dir_start_date}.log"
			"--name=${name}"
			"$src_dir"
			"${ftp_path}${name}"
		)

		if [ "$1" == "test" ]
		then
			echo "- ${src_dir_start_date} - Command for $src_dir as ${name}:"
			echo "${cmd_args[@]}" "${cmd_vars[@]}"
		else
			echo "- ${src_dir_start_date} - Backing up $src_dir as ${name}:"

			"${cmd_args[@]}" "${cmd_vars[@]}"
		fi
	else
		echo "- $(date '+%F_%H-%M-%S.%N') - Skipped, directory is empty or is not a directory: $src_dir"
	fi
done

unset FTP_PASSWORD

echo "- $(date '+%F_%H-%M-%S.%N') - Finished ${cmd_scope} backup script ${cmd_test_or_run}."
