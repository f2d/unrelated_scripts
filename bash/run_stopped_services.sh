#!/bin/bash

run_service_command()
{
	local service_name="${1?need a string}"
	local command_name="${2?need a string}"

	# "/etc/init.d/$service_name" "$command_name"
	service "$service_name" "$command_name"
}



# Nginx:

service_name="nginx"
count=`ps -ef | grep -v grep | grep "$service_name" | wc -l`

if [ $count -lt 1 ]
then
	run_service_command "$service_name" start
elif [ $count -lt 2 ]
then
	run_service_command "$service_name" restart
fi



# PHP:

highest_php_version=`ls -vr1 --group-directories-first "/etc/php" | head -n 1`
service_name="php${highest_php_version}-fpm"
count=`ps -ef | grep -v grep | grep "$service_name" | wc -l`

if [ $count -lt 1 ]
then
	run_service_command "$service_name" start
fi
