#!/bin/bash

if [ "${ftp_protocol}" == "ftps" ]
then
	ftp_config_cmd="source ${script_dir}/common_lftp_ftps_config.sh"
else
	ftp_config_cmd=
fi

echo -e "
${ftp_config_cmd}
connect ${ftp_protocol}://${ftp_username}:${ftp_password}@${ftp_hostname}/
ls
mput *.gz.tar
mput *.tar.xz
ls
bye
"
