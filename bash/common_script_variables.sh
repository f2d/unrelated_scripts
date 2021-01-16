#!/bin/bash

# root_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )/"
# source "${root_dir}common-flock-variables.sh"

if [ -z "${custom_var_file_path}" ]
then
	# Use the following file to set your own hostnames, logins, etc.
	# And make sure it does not have read permission for everyone.

	custom_var_file_path=/root/scripts/custom_script_variables.sh

	if [ -f "${custom_var_file_path}" ]
	then
		source "${custom_var_file_path}"
	fi
fi

# Example defaults for any common vars not defined above:

if [ -z "${start_date}" ]; then start_date="$(date '+%F_%H-%M-%S.%N')"; fi

if [ -z "${log_dir}"    ]; then log_dir=/var/log; fi
if [ -z "${lock_dir}"   ]; then lock_dir=/run/lock; fi
if [ -z "${script_dir}" ]; then script_dir=/root/scripts; fi

if [ -z "${ftp_protocol}" ]; then ftp_protocol=ftps ; fi
if [ -z "${ftp_hostname}" ]; then ftp_hostname=ftp.example.com ; fi
if [ -z "${ftp_username}" ]; then ftp_username=LOGIN ; fi
if [ -z "${ftp_password}" ]; then ftp_password=PASSWORD ; fi

if [ -z "${cert_hostname}"       ]; then cert_hostname=${HOSTNAME} ; fi
if [ -z "${cert_dir}"            ]; then cert_dir=/etc/letsencrypt/live/${cert_hostname}/; fi
if [ -z "${cert_file_path}"      ]; then cert_file_path=${cert_dir}/fullchain.pem; fi
if [ -z "${ocsp_conf_file_path}" ]; then ocsp_conf_file_path=/etc/nginx/snippets/proxy-ocsp.conf; fi

if [ -z "${lock_file_name}"    ]; then lock_file_name=backup_cron_job; fi
if [ -z "${hosts_file_path}"   ]; then hosts_file_path=/etc/hosts; fi
if [ -z "${update_hosts_file}" ]; then update_hosts_file=true; fi
