#!/bin/bash

# Separate access logs from worker processes and error logs from manager process:
# if [ ! -d "/var/log/nginx-access" ]; then mkdir "/var/log/nginx-access" --mode=0700 ; fi

chown www-data:www-data	"/var/log/nginx-access" "/var/log/php"
chown root:root		"/var/log/nginx"
chown drawpile:drawpile	"/var/log/drawpile"
chown syslog:root	"/var/log/drawpile-srv" "/var/log/chatbot"
chown redis:adm		"/var/log/redis"
