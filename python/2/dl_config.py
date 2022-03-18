#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import re

re_ix = re.I | re.X
re_iux = re.I | re.U | re.X

def get_rei(pattern, flags=None):
	return re.compile(
		pattern
	,	flags or (
			re_ix if (
				'\n' in pattern
			or	'\r' in pattern
			) else re.I
		)
	)


def get_log_path(name):
	return log_path_pattern.format(name)

# Config --------------------------------------------------------------------

# Versions as of 2022-03-18:
user_agent_firefox = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0'
user_agent_chrome = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.136 Safari/537.36'

wait = interval = recurse = 0
timeout_request = 60

# TODO: timeout_slow_dl = 0

default_web_proxy = 'http://u/raw/'
default_encoding = 'utf_8'
read_encoding = default_encoding+'|utf_16_le|utf_16_be|cp1251'

format_epoch = '%Epoch'	# <- not from python library, but custom str-replaced
format_ymd = '%Y-%m-%d'
format_hms = '%H-%M-%S'
format_print = '%Y-%m-%d %H:%M:%S'
format_path_mtime = ';_%Y-%m-%d,%H-%M-%S.'

web_proxy_replacement_add = {
	'from' : get_rei(r'^(?:(?P<Protocol>\w+)://)?(?P<DomainAndPath>[^/].*?)$')
,	'to' : [
		default_web_proxy + r'\g<Protocol>/\g<DomainAndPath>'
	,	default_web_proxy + r'http/\g<DomainAndPath>'
	]
}

web_proxy_replacement_remove = {
	'from' : get_rei(r'^' + default_web_proxy + r'(?P<Protocol>\w+)/+(?P<DomainAndPath>[^/].*?)$')
,	'to' : [
		r'\g<Protocol>://\g<DomainAndPath>'
	]
}

read_root = '|'.join([	# <- only flat string format available from command line; add trailing "/" for no subfolder recursion
	u'd:/_bak/_graber/py/'
,	u'd:/programs/!_net/Miranda-NG/Profiles/u/Logs/MsgExport'
,	u'd:/programs/!_net/Miranda-NG/Profiles/u/Logs/ChatRooms'
])

dest_root = '|'.join([
	u'd:/_bak/_graber/py/dl'
,	u'd:/_bak/_www/_conf/_private'
,	u'd:/_bak/_www/_conf'
])

ff_esr = [u'd:/programs/!_web/Mozilla Firefox x64 ESR/firefox.exe', '-P', 'ESR' , '-new-tab']
ff_v56 = [u'd:/programs/!_web/Mozilla Firefox x64 v56/firefox.exe', '-P', 'ff56', '-new-tab']
ff_v57 = [u'd:/programs/!_web/Mozilla Firefox x64/firefox.exe'    , '-P', 'ff57', '-new-tab']

dest_app = {	# <- usage: "app_ID>http://url"
	'5': ff_esr, 'e': ff_esr
,	'6': ff_v56, 'f': ff_v56
,	'7': ff_v57, 'q': ff_v57
,	'1': [u'd:/programs/!_web/Opera_v11.10.2092/opera.exe']
,	'2': [u'd:/programs/!_web/Opera_v12.18.1873_x64/opera.exe']
,	'o': [u'd:/programs/!_web/Opera Next/launcher.exe']
,	'v': [u'd:/programs/!_web/Vivaldi/Application/vivaldi.exe']
}

dest_app_sep = '>'
dest_app_default = 'v'

meta_root = u'.'

log_path_pattern = meta_root + '/dl.{}.log'

# log_traceback	= get_log_path('traceback')	# <- info about program exceptions
log_traceback	= None
log_completed	= get_log_path('completed')	# <- "src links -> dest path" logged per line + response headers dump
log_last_pos	= get_log_path('last_pos')	# <- last known src log file sizes per line, rewritten every time
log_no_response	= get_log_path('no_response')	# <- when server not found at all, or some weird exception, like SSL
log_no_file	= get_log_path('no_file')	# <- when file not found, forbidden, or something, like "I'm Teapot"
log_not_saved	= get_log_path('not_saved')	# <- failed saving for some reason
log_blocked	= get_log_path('blocked')	# <- ISP firewall
log_skipped	= get_log_path('skipped')	# <- skipped, according to the list above
log_all_urls	= get_log_path('url_%Y-%m')	# <- all processed URLs, bad or OK, to skip repeated, not redownload every rime

url_to_skip = [				# <- various bad or useless stuff, won't fix now, or forever
	'//localhost/', '//l/', '//a/'					# <- localhost and its aliases
,	get_rei(r'^(blob:|[\d+/]*$)')				# <- useless protocols
,	get_rei(r'^(\w+:/+)?([^/?#]+\.)?captcha\d*\.\w+/+')	# <- useless server load

# ,	'mega.co.nz/#', 'mega.nz/#', 'iqdb.org/?'			# <- other useless examples, uncomment to apply
# ,	get_rei(r'^\w+:/+([^/]+\.)?google\.\w+/+')
# ,	get_rei(r'^\w+:/+([^/]+\.)?google(\.co)?\.\w+/+searchbyimage')
]

file_not_to_save = [

# Notes from https://docs.python.org/3/library/hashlib.html
# Algorithms that are always present:
# sha1(), sha224(), sha256(), sha384(), sha512(), blake2b(), blake2s().
# md5() may be missing in a rare "FIPS compliant" build of Python.

	{
		'url_part': 'imgur'
	# ,	'url_part': 'i.imgur.com/removed.png'
	# ,	'name_part': 'imgur'
	# ,	'header_etag': 'd835884373f4d6c8f24742ceabe74946'
	,	'content_size': 503
	# ,	'content_crc32': 0xada61663
	# ,	'content_md5': 'd835884373f4d6c8f24742ceabe74946'
	,	'content_sha1': '20002faf28adfd94ca98cf6ced46f14334b53684'
	,	'comment': 'same dummy file, when any image is not found.'
	}
]

add_headers_to = [				# <- fake useragent, POST option, etc
	[['.', '/'], {				# <- won't bother listing all the sites who banned python naming like itself
		'User-Agent': user_agent_firefox
# }],	[['www.example.com'], {
#		'Cookie': '; '.join([
#			'language=en_US'
#		,	'key=value'
#		,	'etc=...'
#		])
}],	[['file.qip.ru/file'], '']		# <- send request as POST
]

# end config ----------------------------------------------------------------
