#!/bin/bash

source "/root/scripts/common_script_variables.sh"

if [ -z "${start_date}" ]; then start_date=`date '+%F_%H-%M-%S.%N'` ; fi
if [ -z "${script_dir}" ]; then script_dir="/root/scripts" ; fi
if [ -z "${log_dir}"    ]; then log_dir="/var/log" ; fi

if [ -z "${ftp_protocol}" ]; then ftp_protocol=ftps ; fi
if [ -z "${ftp_hostname}" ]; then ftp_hostname=ftp.example.com ; fi
if [ -z "${ftp_username}" ]; then ftp_username="LOGIN" ; fi
if [ -z "${ftp_password}" ]; then ftp_password="PASSWORD" ; fi

echo "- ${start_date} - Started backup script."

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

# Check command line arguments: ---------------------------------------------

cmd_name="duplicity"
cmd_scope="incremental"
cmd_test_or_run="run"

# Idiomatic parameter and option handling in sh:
# https://superuser.com/a/186279

# Case pattern matching syntax:
# https://stackoverflow.com/a/4555979

while test $# -gt 0
do
	case "${1//-/}" in
		t|test)	cmd_test_or_run="test";;
		r|run)	cmd_test_or_run="run";;
		a|all)			cmd_scope="all";;
		f|full)			cmd_scope="full";;
		i|inc|incremental)	cmd_scope="incremental";;
	esac
	shift
done 

if [ "${cmd_scope}" == "all" ]
then
	cmd_scope="all_${start_date}"

	cmd_args=(
		"${cmd_name}"
		"full"
	)

	src_dirs_arr=(
		"/"
	)
else
	if ! [ "${cmd_scope}" == "full" ]
	then
		cmd_scope="incremental"
	fi

	cmd_args=(
		"${cmd_name}"
		"${cmd_scope}"
		'--full-if-older-than=9Y'	# <- s, m, h, D, W, M, Y = seconds, minutes, hours, days, weeks, months, years
		'--no-encryption'
		'--ssl-no-check-certificate'	# <- workaround for using IP address in FTP
		# '--time-separator=.'		# <- option deprecated, dashes forbidden
	)

	src_dirs_arr=(
		"/etc"
		"/srv"
		"/home"
		"/root"
		"/var"
	)
fi

# Check IP: -----------------------------------------------------------------

target_addr=${ftp_hostname}

source "${script_dir}/update_hostname_ip.sh" ${ftp_hostname}

ftp_path="${ftp_protocol}://${ftp_username}@${target_addr}/${HOSTNAME}_${cmd_scope}/"

FTP_PASSWORD="${ftp_password}"
export FTP_PASSWORD

# Check paths: --------------------------------------------------------------

for src_dir in "${src_dirs_arr[@]}"
do
	# https://stackoverflow.com/a/17902999
	src_dir_contents=`shopt -s nullglob dotglob; echo $src_dir/*`

	echo "- $(date '+%F_%H-%M-%S.%N') - Checking $src_dir: ${#src_dir_contents}"

	#if [ -d "$src_dir" ]
	if (( ${#src_dir_contents} ))
	then
		name="$(sanitize $src_dir)"

		if [ "${name//-/}" == "" ]
		then
			name="all"
		fi

		cmd_exclude_args=(
			'--exclude-device-files'
			'--exclude=**.lock'
		)

		if [ "${src_dir}" == "/root" ]
		then
			cmd_exclude_args+=(
				'--exclude=**/root/.cache'
				'--exclude=**/root/.cpanm'
				'--exclude=**/root/.choosenim'
				'--exclude=**/root/.nimble'
				'--exclude=**/root/.rustup'
				'--exclude=**/root/.cargo'
			)
		elif [ "${src_dir}" == "/var" ]
		then
			cmd_exclude_args+=(
				'--exclude=**/var/cache/nginx'
				'--exclude=**/var/cache/fontconfig'
				'--exclude=**/var/cache/snapd'
				'--exclude=**/var/cache/man'
				'--exclude=**/var/cache/apparmor'
				'--exclude=**/var/cache/debconf'
				'--exclude=**/var/cache/fwupd'
				'--exclude=**/var/cache/apt'
				'--exclude=**/var/lib/apt'
				'--exclude=**/var/lib/dpkg'
				'--exclude=**/var/lib/snapd/cache'
				'--exclude=**/var/lib/snapd/seed/snaps'
				'--exclude=**/var/lib/snapd/snaps'
				'--exclude=**/var/run'
				'--exclude=**/var/tmp'
			)
		fi

		src_dir_start_date=`date '+%F_%H-%M-%S.%N'`
		cmd_vars=(
			"--log-file=${log_dir}/${cmd_name}/${cmd_name}_${start_date}_${name}_${src_dir_start_date}.log"
			"--name=${name}"
			"$src_dir"
			"${ftp_path}${name}"
		)

		if [ "${cmd_test_or_run}" == "test" ]
		then
			echo "- ${src_dir_start_date} - Command for $src_dir as ${name}:"
			echo "${cmd_args[@]}" "${cmd_exclude_args[@]}" "${cmd_vars[@]}"
		else
			echo "- ${src_dir_start_date} - Backing up $src_dir as ${name}:"

# Run command: --------------------------------------------------------------

			"${cmd_args[@]}" "${cmd_exclude_args[@]}" "${cmd_vars[@]}"
		fi
	else
		echo "- $(date '+%F_%H-%M-%S.%N') - Skipped, directory is empty or is not a directory: $src_dir"
	fi
done

# Cleanup: ------------------------------------------------------------------

unset FTP_PASSWORD

echo "- $(date '+%F_%H-%M-%S.%N') - Finished ${cmd_scope} backup script ${cmd_test_or_run}."
