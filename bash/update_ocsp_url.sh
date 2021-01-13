#!/bin/bash

if [ -z "${start_date}" ]; then start_date="$(date '+%F_%H-%M-%S.%N')"; fi
if [ -z "${cert_hostname}" ]; then cert_hostname=example.com ; fi
if [ -z "${cert_file_path}" ]; then cert_file_path=/etc/letsencrypt/live/${cert_hostname}/fullchain.pem; fi
if [ -z "${conf_file_path}" ]; then conf_file_path=/etc/nginx/snippets/common-proxy-ocsp.conf; fi

# Get OCSP responder:
# https://raymii.org/s/articles/OpenSSL_Manually_Verify_a_certificate_against_an_OCSP.html

ocsp_responder_url=`openssl x509 -noout -ocsp_uri -in "${cert_file_path}"`

# Split 1 argument into 2:
# https://stackoverflow.com/a/11416230

ocsp_responder_protocol=${ocsp_responder_url%:\/\/*}
ocsp_responder_hostname=${ocsp_responder_url#*:\/\/}

# Overwrite conf part file using new values:

new_conf_content="\n# Autosaved at ${start_date}\n\nset \$backend_hostname ${ocsp_responder_hostname};\nset \$backend_protocol ${ocsp_responder_protocol};\n"

echo "- New conf content:"
echo -e "${new_conf_content}"
echo -e "${new_conf_content}" > "${conf_file_path}" && echo "- Written to ${conf_file_path}"
