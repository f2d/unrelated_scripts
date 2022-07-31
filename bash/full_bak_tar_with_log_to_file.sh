#!/bin/bash

start_date="$(date '+%F_%H-%M-%S.%N')"

log_name=/${hostname}_full_bak_${start_date}.log
archive_name=/${hostname}_full_bak_${start_date}.tar.xz

cmd_args=(
	tar
	--create
	--exclude=/dev
	--exclude=/proc
	--exclude=/sys
	--exclude=/root/.cache/duplicity
	--exclude=/var/cache/nginx
	--exclude=/swap.img
	--exclude=/full_bak.tar.xz
	--exclude=${archive_name}
	--exclude=${log_name}
	--xz
	--file=${archive_name}
	/
)

"${cmd_args[@]}" > "${log_name}" 2>&1
