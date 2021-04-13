#!/bin/bash

# Separate access logs from worker processes and error logs from manager process:

# if [ ! -d "/var/log/nginx/access" ]; then mkdir "/var/log/nginx/access" --mode=0755 ; fi
# chown www-data:www-data "/var/log/nginx/access"
# chown root:root "/var/log/nginx"

chown www-data:www-data "/var/log/nginx" "/var/log/php"
chown drawpile:drawpile "/var/log/drawpile"
