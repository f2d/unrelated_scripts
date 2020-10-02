#!/bin/bash

if [ -z "${start_date}" ]; then start_date="$(date '+%F_%H-%M-%S.%N')"; fi
if [ -z "${log_dir}"    ]; then log_dir=/var/log; fi

echo "- ${start_date} - Started backup script."

target_hostname=backup-ftp.example.com
target_username=LOGIN
target_password=PASSWORD

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

target_addr=${target_hostname}

# https://unix.stackexchange.com/a/20793

# 1) dig queries DNS servers directly, does not look at /etc/hosts/NSS/etc:
# target_ip=`dig +short $target_hostname | awk '/^[0-9]+\./ { print ; exit }'`

# 2) getent, which comes with glibc, resolves using gethostbyaddr/gethostbyname2, and so also will check /etc/hosts/NIS/etc:
target_ip=`getent ahosts $target_hostname | awk '/^[0-9]+\./ { print $1; exit }'`
ip_pattern='^[0-9\.]+$'

if [[ "$target_ip" =~ $ip_pattern ]]; then
	echo "Using backup server IP: ${target_ip}"

	target_addr=${target_ip}
else
	echo "Warning: ${target_ip} is not a valid IP address. Using hostname instead."

	# echo "Error: ${target_ip} is not a valid IP address."
	# exit
fi

target_path=ftps://${target_username}@${target_addr}/${HOSTNAME}_${cmd_scope}/

FTP_PASSWORD=${target_password}
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
			"${target_path}${name}"
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
