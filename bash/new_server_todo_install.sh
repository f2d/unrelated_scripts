#!/bin/bash

echo "- $(date '+%F_%H-%M-%S.%N') - Started packages install script."

apt_package_names=(

# not needed to install:

	# bat
	# memcached
	# rsyslog

# utils:

	certbot
	curl
	duplicity
	fd-find
	jdupes
	jpegoptim
	lftp
	optipng
	p7zip
	p7zip-full
	postfix
	rsync
	shadowsocks-libev
	unrar
	unzip
	xz-utils
	zstd

# utils for drawpile:

	imagemagick
	python3
	python3-pip

# libs for drawpile:

	cmake
	g++
	libgif-dev
	libkf5archive-dev
	libkf5dnssd-dev
	libmicrohttpd-dev
	libqt5svg5-dev
	libsodium-dev
	libvpx-dev
	make
	qtbase5-dev
	qtmultimedia5-dev
	wget

# for web server:

	nginx
	nginx-extras

	# php7.4-curl
	# php7.4-fpm
	# php7.4-gd
	# php7.4-intl
	# php7.4-mbstring
	# php7.4-xml

	# php8.0-curl
	# php8.0-fpm
	# php8.0-gd
	# php8.0-intl
	# php8.0-mbstring
	# php8.0-xml
	# php8.0-zip

	php8.2-curl
	php8.2-fpm
	php8.2-gd
	php8.2-intl
	php8.2-mbstring
	php8.2-xml
	php8.2-zip

# for nitter:

	redis-server

# for image board:

	fcgiwrap
	libgd-perl
	perl
	perl-base
	perl-modules-5.30

)

perl_package_names=(

	CGI::Carp
	GD

)

pip_package_names=(

	Pillow
	colorama
	discord.py
	python-dateutil
	sortedcontainers
	termcolor

)

create_folder_paths=(

	"/var/cache/nginx"
	"/var/log/chatbot"
	"/var/log/drawpile"
	"/var/log/drawpile-srv"
	"/var/log/nginx"
	"/var/log/nginx-access"
	"/var/log/php"
	"/var/log/redis"

)

echo " -------- Install Apt packages: -------- "
echo "${apt_package_names[@]}"

sudo apt install "${apt_package_names[@]}"

echo " -------- Install Perl packages: -------- "
echo "${perl_package_names[@]}"

cpanm_version="$(cpanm --version | head -n 1)"

if [ -z "${cpanm_version}" ]
then
	curl -L http://cpanmin.us | perl - App::cpanminus
else
	echo "Existing: ${cpanm_version}"
fi

cpanm "${perl_package_names[@]}"

echo " -------- Install Pip packages: -------- "
echo "${pip_package_names[@]}"

python3 -m pip install --upgrade "${pip_package_names[@]}"

echo " -------- Create folders to write data/logs: -------- "
echo "${create_folder_paths[@]}"

for each_path in "${create_folder_paths[@]}"
do
	if [ ! -d "${each_path}" ]
	then
		mkdir "${each_path}" --mode=0700
	fi
done

echo " -------- Change data/logs folder access rights: -------- "

/root/scripts/add_srv_users_and_chown.sh	&& \
/root/scripts/chown_log_folders.sh		&& \
echo "Done."

echo "- $(date '+%F_%H-%M-%S.%N') - Finished packages install script."
