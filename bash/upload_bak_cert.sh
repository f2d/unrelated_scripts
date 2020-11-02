#!/bin/bash

echo "- $(date '+%F_%H-%M-%S.%N') - Started SSL cert upload script."

cd /etc/letsencrypt/live/${HOSTNAME}

if [ -z "${script_dir}" ]; then script_dir=/root/scripts; fi

source "${script_dir}/update_hostname_ip.sh"

lftp -f "${script_dir}/upload_bak_cert.ftp"

echo "- $(date '+%F_%H-%M-%S.%N') - Finished SSL cert upload script."
