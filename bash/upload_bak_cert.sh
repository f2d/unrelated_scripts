#!/bin/bash

echo "- $(date '+%F_%H-%M-%S.%N') - Started SSL cert upload script."

cd /etc/letsencrypt/live/${HOSTNAME}

lftp -f /root/scripts/upload_bak_cert.ftp

echo "- $(date '+%F_%H-%M-%S.%N') - Finished SSL cert upload script."
