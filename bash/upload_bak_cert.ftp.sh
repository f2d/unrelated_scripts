#!/bin/bash

echo -e "
connect ${ftp_protocol}://${ftp_username}:${ftp_password}@${ftp_hostname}/
ls
mput *.pem
ls
bye
"
