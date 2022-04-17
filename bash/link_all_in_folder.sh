#!/bin/bash

echo "- $(date '+%F_%H-%M-%S.%N') - Started link script."

link_dir=/usr/local/bin
dest_dir=/usr/local/bin/nim-versions/nim-1.6.4/bin

# find "${dest_dir}" -type f -execdir echo 'ln -s ${dest_dir}/{} ${link_dir}/{}' \;
# fd -g '${dest_dir}/*' -X 'ln -s'

# https://stackoverflow.com/a/58429077
while IFS= read -rd '' file; do

	filename=$(basename "${file}")

	cmd_link=(
		ln
		-sfv
		"${dest_dir}/${filename}"
		"${link_dir}/${filename}"
	)

	echo "${cmd_link[@]}"
	"${cmd_link[@]}"

done < <(find "${dest_dir}" -type f -print0)

echo "- $(date '+%F_%H-%M-%S.%N') - Finished link script."
