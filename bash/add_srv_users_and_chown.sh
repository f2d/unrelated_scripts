#!/bin/bash

add_group_and_user_if_not_yet()
{
	local group_name="${1?need a string}"
	local user_name="${2?need a string}"

	# https://superuser.com/a/336708
	if [ ! -z "$(getent group "${group_name}")" ]
	then
		echo "Group exists: ${group_name}"
	else
		echo "Group does not exist, adding now: ${group_name}"

		addgroup "${group_name}"
	fi

	if [ ! -z "$(getent passwd "${user_name}")" ]
	then
		echo "User exists: ${user_name}"
	else
		echo "User does not exist, adding now: ${user_name}"

		adduser --system --no-create-home --disabled-login --ingroup "${group_name}" "${user_name}"
	fi
}

add_group_and_user_if_not_yet www-data www-data
add_group_and_user_if_not_yet drawpile drawpile
add_group_and_user_if_not_yet discord-bot taga
add_group_and_user_if_not_yet twitter nitter

chown -R drawpile:drawpile /srv/drawpile
chown -R taga:discord-bot  /srv/discord/taga
chown -R nitter:twitter    /srv/nitter
chown -R www-data:www-data /srv/www
