#!/bin/bash

source "/root/scripts/common_script_variables.sh"

if [ -z "${start_date}"        ]; then start_date="$(date '+%F_%H-%M-%S.%N')"; fi
if [ -z "${update_hosts_file}" ]; then update_hosts_file=true; fi
if [ -z "${hosts_file_path}"   ]; then hosts_file_path=/etc/hosts; fi
if [ -z "${resolv_file_path}"  ]; then resolv_file_path=/etc/resolv.conf; fi

echo "- ${start_date} - Started hostname IP update script."

target_hostname=$1

if [ -z "${target_hostname}" ]
then
	echo "No target hostname argument given."
	echo "Aborted."

	exit 1
fi

ip_pattern="[0-9]+([.][0-9]+)*"

if [[ "${target_hostname}" =~ ^${ip_pattern}$ ]]
then
	echo "Given hostname is an IP address."
	echo "Aborted."

	exit 2
fi

if [ "${update_hosts_file}" == "true" ]
then
	# https://unix.stackexchange.com/a/20793
	# 1) dig queries DNS servers directly, does not look at /etc/hosts/NSS/etc (unless dummy localhost DNS server does it):

	resolver_pattern="(^|[\r\n])nameserver[[:space:]]+(localhost|127([.]0+)*[.](1|53))($|[\r\n]|[[:space:]])"
	resolver_is_localhost=`grep -P "${resolver_pattern}" "${resolv_file_path}"`

	if [ -n "${resolver_is_localhost}" ]
	then
		dns_resolver="@1.1.1.1"

		echo "Localhost resolver ${resolver_is_localhost} found in ${resolv_file_path}, using ${dns_resolver} instead."
	else
		dns_resolver=""
	fi

	target_ip=`dig ${dns_resolver} +short ${target_hostname} | awk '/^[0-9]+[.]/ { print ; exit }'`
else
	# 2) getent, which comes with glibc, resolves using gethostbyaddr/gethostbyname2, and so also will check /etc/hosts/NIS/etc:
	target_ip=`getent ahosts ${target_hostname} | awk '/^[0-9]+[.]/ { print $1; exit }'`
fi

if [[ "${target_ip}" =~ ^${ip_pattern}$ ]]
then
	if [ "${update_hosts_file}" == "true" ]
	then
		hostname_pattern_in_hosts="[[:blank:]]+${target_hostname//[.]/[.]}($|[[:space:]])"
		hostname_found_in_hosts=`grep -P "${hostname_pattern_in_hosts}" "${hosts_file_path}"`

		if [ -n "${hostname_found_in_hosts}" ]
		then
			echo "Hostname ${target_hostname} found in ${hosts_file_path}, replacing IP with ${target_ip}"

			cmd_replace=(
				sed
				--in-place=.bak
				--regexp-extended
				"s/(^|[\r\n])[[:blank:]]*${ip_pattern}(${hostname_pattern_in_hosts})/\1${target_ip}\3/"
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

echo "- $(date '+%F_%H-%M-%S.%N') - Finished hostname IP update script."
