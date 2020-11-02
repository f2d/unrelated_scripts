#!/bin/bash

if [ -z "${update_hosts_file}" ]; then update_hosts_file=true; fi
if [ -z "${hosts_file_path}"   ]; then hosts_file_path=/etc/hosts; fi
if [ -z "${target_hostname}"   ]; then target_hostname=ftp.example.com; fi

ip_pattern='^[0-9\.]+$'

if [ "${update_hosts_file}" == "true" ]
then
	# https://unix.stackexchange.com/a/20793
	# 1) dig queries DNS servers directly, does not look at /etc/hosts/NSS/etc:
	target_ip=`dig +short $target_hostname | awk '/^[0-9]+\./ { print ; exit }'`
else
	# 2) getent, which comes with glibc, resolves using gethostbyaddr/gethostbyname2, and so also will check /etc/hosts/NIS/etc:
	target_ip=`getent ahosts $target_hostname | awk '/^[0-9]+\./ { print $1; exit }'`
fi

if [[ "$target_ip" =~ $ip_pattern ]]
then
	if [ "${update_hosts_file}" == "true" ]
	then
		# https://gist.github.com/Fuxy22/da4b7ca3bcb0bfea2c582964eafeb4ed
		if [ -n "$(grep ${target_hostname} ${hosts_file_path})" ]
		then
			echo "Hostname ${target_hostname} found in ${hosts_file_path}, replacing IP with ${target_ip}"

			cmd_replace=(
				sed
				--in-place=.bak
				--regexp-extended
				"s/(^|[\r\n])[ \t]*\b[0-9\.]+([ \t]+${target_hostname}\b)/\1${target_ip}\2/"
				"${hosts_file_path}"
			)

			"${cmd_replace[@]}"
		else
			echo "Hostname ${target_hostname} not found in ${hosts_file_path}, addind with IP ${target_ip}"

			printf "\n# Autoupdated by shell script:\n%s\t%s\n" "${target_ip}" "${target_hostname}" >> "${hosts_file_path}"
		fi
	else
		echo "Using IP ${target_ip} to connect instead of hostname."

		target_addr=${target_ip}
	fi
else
	echo "Warning: ${target_ip} is not a valid IP address. Using hostname instead."
fi
