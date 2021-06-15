#!/bin/bash

run_service_command()
{
	local service_name="${1?need a string}"
	local command_name="${2?need a string}"

	# "/etc/init.d/$service_name" "$command_name"
	service "$service_name" "$command_name"
}

restart_service_by_name()
{
	local service_name="${1?need a service full name to start}"
	# echo "service_name=$service_name"

	local process_text="${2?need a process line part to search, e.g. name, conf path, etc.}"
	# echo "process_text=$process_text"

	# Convert argument to integer or zero, source: https://unix.stackexchange.com/a/232438
	local restart_less=`printf '%d' "$3" 2>/dev/null`
	# echo "restart_less=$restart_less"

	# Count running processes by name:
	local process_count=`ps -ef | grep -v grep | grep "$process_text" | wc -l`
	# echo "process_count=$process_count"

	if [ $process_count -lt 1 ]
	then
		# echo "run_service_command $service_name start"

		run_service_command "$service_name" start
	elif [ $process_count -lt $restart_less ]
	then
		# echo "run_service_command $service_name restart"

		run_service_command "$service_name" restart
	fi
}

highest_php_version=`ls -vr1 --group-directories-first "/etc/php" | head -n 1`

restart_service_by_name "php${highest_php_version}-fpm" "php/${highest_php_version}"
restart_service_by_name "php7.4-fpm" "php/7.4"
restart_service_by_name "nginx" "nginx" 2
