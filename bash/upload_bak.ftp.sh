#!/bin/bash

if [ "${ftp_protocol}" == "ftps" ]
then
	ftp_config_cmd="source ${script_dir}/common_lftp_ftps_config.sh"
else
	ftp_config_cmd=
fi

if [ -z "${ftp_port}" ]
then
	ftp_addr=${ftp_hostname}
else
	ftp_addr=${ftp_hostname}:${ftp_port}
fi

echo -e "
${ftp_config_cmd}
connect ${ftp_protocol}://${ftp_username}:${ftp_password}@${ftp_addr}/
ls
${ftp_upload_cmd}
ls
bye
"
