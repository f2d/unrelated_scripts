#!/bin/bash

source "/root/scripts/common_script_variables.sh"
source "/root/scripts/custom_bak_cert_variables.sh"

if [ -z "${start_date}"   ]; then start_date=`date '+%F_%H-%M-%S.%N'` ; fi
if [ -z "${ftp_hostname}" ]; then ftp_hostname=ftp.example.com ; fi
if [ -z "${script_dir}"   ]; then script_dir="/root/scripts" ; fi
if [ -z "${cert_dir}"     ]; then cert_dir="/etc/letsencrypt/live/${HOSTNAME}/" ; fi

echo "- ${start_date} - Started SSL cert upload script."

source "${script_dir}/update_hostname_ip.sh" ${ftp_hostname}

cd "${cert_dir}"

# Old way to use a static script file with hardcoded login/password/hostname:
# lftp -f "${script_dir}/upload_bak_cert.ftp"

# Feed script output into a FTP client, to avoid writing files or showing password in arguments:
# https://stackoverflow.com/a/60655361

source "${script_dir}/upload_bak_cert.ftp.sh" > >(lftp)

# Wait for all running background jobs and the last-executed process substitution:
# https://man7.org/linux/man-pages/man1/bash.1.html

wait

echo "- $(date '+%F_%H-%M-%S.%N') - Finished SSL cert upload script."
