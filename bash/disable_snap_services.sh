#! /bin/bash
# https://landofnightandday.blogspot.com/2018/06/disable-snap-core-service-on-ubuntu-1804.html?showComment=1571187598966#c4668522615045489287

snap_services=$(systemctl list-unit-files | grep snap|grep enabled|cut -d ' ' -f 1)
echo $snap_services

for snap_service in $snap_services
do
	cmd="sudo systemctl disable $snap_service"
	echo $cmd
	$cmd
done
