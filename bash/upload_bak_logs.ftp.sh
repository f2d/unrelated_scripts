#!/bin/bash

if [ "${ftp_protocol}" == "ftps" ]
then
	ftp_protocol_cmd=set ftps:initial-prot P
else
	ftp_protocol_cmd=
fi

echo -e "
${ftp_protocol_cmd}
connect ${ftp_protocol}://${ftp_username}:${ftp_password}@${ftp_hostname}/
ls
mput *.gz.tar
mput *.tar.xz
ls
bye
"
