#!/bin/bash

source "/root/scripts/common_script_variables.sh"

if [ -z "${start_date}"          ]; then start_date=`date '+%F_%H-%M-%S.%N'` ; fi
if [ -z "${cert_file_path}"      ]; then cert_file_path="/etc/letsencrypt/live/${HOSTNAME}/fullchain.pem" ; fi
if [ -z "${ocsp_conf_file_path}" ]; then ocsp_conf_file_path="/etc/nginx/snippets/proxy-ocsp.conf" ; fi

echo "- ${start_date} - Started OCSP URL update script."

# Get OCSP responder:
# https://raymii.org/s/articles/OpenSSL_Manually_Verify_a_certificate_against_an_OCSP.html

ocsp_responder_url=`openssl x509 -noout -ocsp_uri -in "${cert_file_path}"`

if [ -z "${ocsp_responder_url}" ]
then
	echo "OCSP responder not found."
	echo "Aborted."

	exit 1
fi

# Split 1 argument into 2:
# https://stackoverflow.com/a/11416230

ocsp_responder_protocol="${ocsp_responder_url%:\/\/*}"
ocsp_responder_hostname="${ocsp_responder_url#*:\/\/}"

# Overwrite conf part file using new values:

new_conf_content="
# Autoupdated by shell script at $(date '+%F_%H-%M-%S.%N')

set \$backend_protocol ${ocsp_responder_protocol};
set \$backend_hostname ${ocsp_responder_hostname};

# proxy_pass ${ocsp_responder_url};
# Use nginx variables in proxy_pass to resolve at runtime to avoid ipv6 errors:
# https://trac.nginx.org/nginx/ticket/723
proxy_pass \$backend_protocol://\$backend_hostname;
"

echo "- New content for ${ocsp_conf_file_path}:"
echo -e "${new_conf_content}"
echo -e "${new_conf_content}" > "${ocsp_conf_file_path}" && echo "- Written to ${ocsp_conf_file_path}."

echo "- $(date '+%F_%H-%M-%S.%N') - Finished OCSP URL update script."
