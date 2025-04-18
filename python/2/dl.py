﻿#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

# TODO: decode URL-encoded via a byte-sequence:
# 1. Find all URL-encoded sequences of max length in the filename.
# 2. Keep unique, sort by length descending.
# 3. Try decoding each, starting from position 0.
# 4. On each failure decrement decoded slice length from max down to 0.
# 5. After success, add decoded text as a replacement value for corresponding URL-encoded subsequence.
# 6. After success or failure, step to decoded length (if any) + 1 and try again from there.
# 7. Replace all subsequences in the sequence.
# 8. Replace all sequences in the source text.

# - Help screen shown on demand or without arguments --------------------------

def print_help():
	self_name = os.path.basename(__file__)

	help_text_lines = [
		''
	,	colored('* Description:', 'yellow')
	,	'	Read text files from disk, get list of links,'
	,	'	try to download the links and save results to disk.'
	,	''
	,	'	It is possible to run in cycle, e.g. on log files,'
	,	'	without rereading same places in text files and'
	,	'	without redownloading same links again (with exceptions).'
	,	''
	,	colored('* Usage:', 'yellow')
	,	'	{0} '
		+	colored('\n\t\t'.join([
				'[-<flags-letters>]'
			,	'[e<cp|' + default_encoding + '>]'
			,	'[w<num|1>]'
			,	'[i<num|60>]'
			,	'[t<num|99>]'
			,	'[r<num|999>]'
			,	'[m<dir|..>]'
			,	'[g<dir|.>|<dir>|...]'
			,	'[d<dir|..>|<dir>|...]'
			,	colored('[<help>]', 'magenta')
			]), 'cyan')
	,	''
	,	colored('* Arguments:', 'yellow')
	,	'w: Wait between downloads, in seconds. Omit = 0'
	,	'i: Interval between txt batch checks, in seconds. Check once if zero. Omit = 0'
	,	't: Timeout for sending request, in seconds. Omit = 60'
#	,	'TODO ->	l: Timeout for long downloads, in seconds. Omit = 0'
	,	'r: Recursively read up to N log folders under roots without trailing slash. Omit = 0'
	,	'e: Log content encoding. Omit = "{}"'.format(colored(read_encoding, 'magenta'))
	,	'm: Path to store meta logs. Omit = "{}"'.format(colored(meta_root, 'magenta'))
	,	''
	,	'g: Paths to get files (where to read links to DL). Omit = "{}"'.format(colored(read_root, 'magenta'))
	,	''
	,	'd: Paths to put files (DL\'d from links), + subfolder per log. Omit = "{}"'.format(colored(dest_root, 'magenta'))
	,	''
	,	colored('-<flag-letters>', 'cyan') + ': string of letters in any order after a dash.'
	,	'	l: normalize preloaded urls from old logs (less redundancy, but slow start)'

	,	'	m: http modtime header -> add timestamp to filename (default = current time)'
	,	'	u: add time in format: ' + format_epoch + ' (default = all u+y+h)'
	,	'	y: add time in format: ' + format_ymd
	,	'	h: add time in format: ' + format_hms
	,	'	c: stamp separator = comma "," (default = underscore "_")'
	,	'	p: prepend time before filename (default)'
	,	'	s: append time before ext'
	,	'	a: append time after ext'

	,	'	d: grab Discord emoji by ID'
	,	''
	,	colored('<help>', 'cyan') + ': show this text.'
	,	'	Any format matching </|-><|h|help>, e.g. ?, /?, -?, --?, -h, --help, etc.'
	,	'	Add anything else except help to run with all defaults.'
	,	''
	,	colored('* Examples:', 'yellow')
	,	'	{0} -mu i600 dt3600 r g d e'
	,	'	{0} w10 "gD:/_logs|E:/_grab" "dD:/_dl|E:/_dl"'
	]

	print('\n'.join(help_text_lines).format(self_name))

# - Dependencies --------------------------------------------------------------

from dl_config import *

from email.utils import parsedate
import datetime, glob, hashlib, json, os, re, ssl, string, StringIO, subprocess, sys, time, traceback, zlib

# Use compressed download if available:
try:
	import brotli
except ImportError:
	brotli = None

try:
	import gzip
except ImportError:
	gzip = None

# TODO: fix this script for python 3, then remove this crutch:
# https://stackoverflow.com/a/4383597
sys.path.insert(1, 'd:/programs/!_dev/Python/scripts/2-3')

# Use automatic trim of extraneous digits at the end of files for deduplication, if available:
try:
	from bin2cut import get_extracted_files, run_batch_extract

except ImportError:
	def get_extracted_files(*list_args, **keyword_args): return
	def run_batch_extract  (*list_args, **keyword_args): return

# Use colored text if available:
try:
	from termcolor import colored, cprint
	import colorama

	colorama.init()

except ImportError:
	def colored(*list_args, **keyword_args): return list_args[0]
	def cprint (*list_args, **keyword_args): print (list_args[0])

# https://stackoverflow.com/a/17510727
try:
	# Python 3.0 and later:
	from urllib.error import URLError, HTTPError
	from urllib.request import urlopen, Request

except ImportError:
	# Python 2.x fallback:
	from urllib2 import URLError, HTTPError, urlopen, Request

# https://stackoverflow.com/a/47625614
if sys.version_info[0] >= 3:
	unicode = str

# - Configuration and defaults ------------------------------------------------

print_enc = default_encoding
local_path_prefix = u'//?/'
tab_separator = '\t'
line_separator = '\n'
empty_line_separator = line_separator * 2
content_type_separators = ['+', '-']
exts_to_add_from_content_type = ['json', 'xml']
exts_to_add_from_url = ['flac', 'jxl', 'jxr']
known_image_exts = ['jxl', 'jxr']

TEST = 0

# - Show help and exit --------------------------------------------------------

if len(sys.argv) > 1:
	help = 0

	for a in sys.argv:
		a = a[-4 : ].lower()
		L = a[-1 : ]
		if (a == L or a.lstrip('-/') == L) and (L == '?' or L == 'h' or a == 'help'):
			help = 1

			break
else:
	help = 1

if help:
	print_help()

	sys.exit(1)

# - Check arguments -----------------------------------------------------------

flags = ''
add_time = None

for argv in sys.argv[1 : ]:
	arg = argv.strip('"')

	if not len(arg):
		continue

	L = arg[0].lower()

	if   L == '-': flags              += arg[1 : ]  if len(arg) > 1 else ''
	elif L == 'w': wait            = int(arg[1 : ]) if len(arg) > 1 else 1
	elif L == 'i': interval        = int(arg[1 : ]) if len(arg) > 1 else 60
	elif L == 't': timeout_request = int(arg[1 : ]) if len(arg) > 1 else 99
#	elif L == 'l': timeout_slow_dl = int(arg[1 : ]) if len(arg) > 1 else 99
	elif L == 'r': recurse         = int(arg[1 : ]) if len(arg) > 1 else 999
	elif L == 'm': meta_root           = arg[1 : ].replace('\\', '/') if len(arg) > 1 else '..'
	elif L == 'g': read_root           = arg[1 : ].replace('\\', '/') if len(arg) > 1 else '.'
	elif L == 'd': dest_root           = arg[1 : ].replace('\\', '/') if len(arg) > 1 else '..'
	elif L == 'e': read_encoding       = arg[1 : ].replace('-' , '_') if len(arg) > 1 else default_encoding

for i in 'achmpsuy':
	if i in flags:
		add_time = []

		if 'u' in flags: add_time.append(format_epoch)
		if 'y' in flags: add_time.append(format_ymd)
		if 'h' in flags: add_time.append(format_hms)
		if not add_time: add_time = [format_epoch, format_ymd, format_hms]

		add_time_j = ',' if 'c' in flags else '_'
		add_time_fmt = add_time_j.join(add_time)

		break

read_encoding = read_encoding.split('|')

#print add_time, add_time_j, add_time_fmt
#sys.exit(0)

# Accept-Encoding: br, gzip, deflate
accept_enc = ', '.join(filter(
	None
,	[
		'br' if brotli else None
	,	'gzip' if gzip else None
	,	'deflate' if zlib else None
	]
))

print colored('Accept-Encoding:', 'yellow'), accept_enc

# Precaution ------------------------------------------------------------------

def get_path_list_from_arg(value):

	if local_path_prefix:
		return [local_path_prefix + x for x in value.split('|')]
	else:
		return value.split('|')

read_paths = zip(
	get_path_list_from_arg(read_root)
,	get_path_list_from_arg(dest_root)
)

f = nf = 0

for p in read_paths:
	for d in p:
		if os.path.exists(d):
			f += 1
		else:
			nf += 1

			print colored('Path not found:', 'red'), d

if not f:
	sys.exit(2)

# Set up ----------------------------------------------------------------------

chars_from_url    = r'":/|\?*<>'
chars_to_filename = r"';,,,&___"

url2name = string.maketrans(
	chars_from_url
,	chars_to_filename
)

url2name_unicode = {}

for i in zip(list(chars_from_url), list(chars_to_filename)):
	t = unicode(i[1])
	url2name_unicode[ord(i[0])] = t
	url2name_unicode[ord(unicode(i[0]))] = t

safe_chars_as_ord = [
	[ord('A'), ord('Z')]
,	[ord('a'), ord('z')]
,	[ord('0'), ord('9')]
] + map(ord, list('\';,.-_=+~` !@#$%^&()[]{}'))

pat_grab = get_rei(
	r'''
		(?<![@<])\b
		(?P<App>\w'''+dest_app_sep+''')?
		(?P<URL>
			[a-z0-9][a-z0-9-]*
			(\.[.a-z0-9-]+|:/)/
			(,?[^\s<>",]*[^\s<>",\'`])+
		)
	'''
	+ (
	r'''
	|	<
			(?P<DiscordType>[^:<>\s\r\n/]*)
		:	(?P<DiscordName>[^:<>\s\r\n/]+)
		:	(?P<DiscordID>\d+)
		>	# in text: <(Type or empty):Name:ID> -> URL: https://cdn.discordapp.com/emojis/ID.png
	''' if 'd' in flags else ''
	)
)

pat_placeholders   = get_rei(r'[%][a-z]')
pat_conseq_slashes = get_rei(r'[\\/]+')
pat_sub_counter    = get_rei(r'\d\b|\g<Counter>')
pat_local_prefix   = get_rei(r'(?P<Prefix>^[\\/]+[?][\\/]+)(?P<Path>.*?)$')

pat_badp = get_rei(r'^(\w+):/*')
pat_cdfn = get_rei(r'filename\*?=(?:UTF-8\'+)?"?([^"\r\n>]+)')
pat_exno = get_rei(r'\W')
pat_host = get_rei(r'^(?P<Protocol>[^:]*:/+)?(?P<Domain>[^/@]+)(?P<Path>/.*)?$')
pat_href = get_rei(r'\s+href=[\'"]?([^\'"\s>]+)')
pat_imgs = get_rei(r'<img[^>]*?\s+src=[\'"]?([^"\s>]+)')
pat_synt = get_rei(r'[\d/.,_-]+')
pat_trim = get_rei(r'([.,]+|[*~]+|[_-]+|[()]+|/+)$')
pat_uenc = get_rei(r'%([0-9a-f]{2})')
pat_ymdt = get_rei(r'[_-]+\d{4}[_-]+\d{2}[_-]+\d{2}(\.\w+)?$')

pat_dest_dir_replace = [
	[get_rei(r'\s'), ' ']
,	[get_rei(ur'''
# any non-safe characters:
		[^A-Za-z0-9а-яА-Я\s\/\\\\,.\[\]{}();:'`\-=~!@#$%^&*()_+]
	'''
	# or
	# r'''
# emoji (not working):
	# |	[\u2702-\u27B0]
	# |	[\u24C2\u00A9\u00AE\u203C\u2049\u20E3\u2122\u2139\u2194\u2195\u2196\u2197\u2198\u2199\u21A9\u21AA]
	# |	[\u231A\u231B\u23E9\u23EA\u23EB\u23EC\u23F0\u23F3]
	# |	[\u25AA\u25AB\u25B6\u25C0\u25FB\u25FC\u25FD\u25FE]
	# |	[\u2600\u2601\u260E\u2611\u2614\u2615\u261D\u263A\u2648\u2649\u264A\u264B\u264C\u264D\u264E\u264F]
	# |	[\u2650\u2651\u2652\u2653\u2660\u2663\u2665\u2666\u2668\u267B\u267F\u2693]
	# |	[\u26A0\u26A1\u26AA\u26AB\u26BD\u26BE\u26C4\u26C5\u26CE\u26D4\u26EA\u26F2\u26F3\u26F5\u26FA\u26FD]
	# |	[\u2934\u2935\u2B05\u2B06\u2B07\u2B1B\u2B1C\u2B50\u2B55\u3030\u303D\u3297\u3299]
	# |	\u0001[\u0000-\uFFFF]
	# |	[\U00010000-\UFFFFFFFF]
	# '''
	), '']
]

# -----------------------------------------------------------------------------

# filename formats -> convert to dest folder name
#	a) r'substitute string'
#	b) first found capture group from [array of given names]
#	c) default: 1, etc:
pat_ln2d = [

# - ImageBoard: (ID_number).timestamp.html/txt --------------------------------
	[
		get_rei(r'^(\d+)\.(\d+\.)*([xshtml]+)$')
	]

# - Skype: (chat_name),(chat_ID)==@p2p.thread.skype_y-m-d.log -------------------
,	[
		get_rei(r'''^
			(?P<ChatName>.+?),
			(?P<ChatID>[A-Za-z0-9+=_-]+)@
			(?P<ChatType>(p2p\.)?(thread\.)?skype)
			(?P<Date>[_-]+\d{4}[_-]+\d{2}[_-]+\d{2})?
			(?P<Ext>\.\w+)?
		$''')
	,	'ChatName'
	,	'ChatID'
	]

# - Jabber: c.s.n_(given_name),(ID_name)@conf.server.name_y-m-d.log -----------
,	[
		get_rei(r'''^
			(?P<Client>
				(?P<ServerAbbr>[^@,_]+_)?
				(?P<GivenName>[^@,]+),
			)?
			(?P<Server>
				(?P<RoomID>[^@,]+)@
				(?P<ServerName>[\w.-]*?)
				(?P<Date>[_-]+\d{4}[_-]+\d{2}[_-]+\d{2})?
			)
			(?P<Ext>\.\w+)?
		$''')
	,	'GivenName'
	,	'RoomID'
	]

# - Discord: (guild_name)#(room_name),(ID_number)_y-m-d.log -------------------
,	[
		get_rei(r'''^
			(
				(?P<GuildName>[^#]+)[#]+
				(?P<RoomName>.+?)[;,]
			)?
			(
				(?P<RoomID>\d+)
				(?P<Date>[_-]+\d{4}[_-]+\d{2}[_-]+\d{2})?
			|	(?P<DateTime>(\D\d+){6})
				(?P<Comment>,.*?)?
			)
			(?P<Ext>\.\w+)?
		$''')
	,	r'\g<GuildName>/\g<RoomName>'
	]
]

# -----------------------------------------------------------------------------

pat2replace_before_checking = [			# <- strings before this can have any of "/path/?query&params#fragment" parts
	[get_rei(r'&(?:nbsp|#8203);'	), ' ']
,	[get_rei(r'&lt;'		), '<']
,	[get_rei(r'&gt;'		), '>']
,	[get_rei(r'&quot;'		), '"']
,	[get_rei(r'&#0*39;'		), "'"]
,	[get_rei(r'&amp;'		), '&']
,	[get_rei(r'(?:\[/img\]|[\|\'\\"\s.,;:%|?*]|%2C|%3B|%3A|%25|%7C|%3F)+$'			), '']	# <- remove tail formatting garbage
,	[get_rei(r'^(?:\w+:/+)?(?:[^:/?#]+\.)?steamcommunity\.com/+linkfilter/+\?url='		), '']	# <- remove redirect
,	[get_rei(r'^(?:\w+:/+)?(?:[^:/?#]+\.)?deviantart\.com/+users/+outgoing\?'		), '']	# <- remove redirect
,	[get_rei(r'^(?P<Site>(?:\w+:/+)?[^:/?#]+)\.prx2\.unblocksit\.es(?P<Path>$|/+)'		), r'\g<Site>\g<Path>']			# <- remove given web-proxy
,	[get_rei(r'^(?P<Protocol>\w+):/+(?P<Domain>[^/?#]+)/+'					), r'\g<Protocol>://\g<Domain>/']	# <- remove redundant slashes
,	[get_rei(r'^https(?P<NoProtocol>:/+(?:[^:/?#]+\.)?(?:i\.imgur)\.)'			), r'http\g<NoProtocol>']		# <- remove https for deduplication
,	[get_rei(r'^(?P<FullVersion>(?:\w+:/+)?(?:[^:/?#]+\.)?(?:i\.imgur)\.\w+/+\w{7})[rh]\.'	), r'\g<FullVersion>.']			# <- skip downscaled copy
# ,	[get_rei(r'^(?P<Path>\w+:/+(?:[^:/?#]+\.)?discord[^?#]+/[^?#]+)(?P<Query>[?#].*)$'	), r'\g<Path>#\g<Query>']		# <- ?query to #anchor

# remove discord web-proxy:

# URL sample without arguments:
# https://images-ext-2.discordapp.net/external/rmIM(...)_7kNZEi-(...)/https/media.discordapp.net/attachments/(...).png

# URL sample with arguments (easier to let it be and fix destination filename later, than URL-decode arguments here?):
# https://images-ext-1.discordapp.net/external/NxJF(...)/%3F_nc_ht%3Dscontent-lga3-1.cdninstagram.com/https/scontent-lga3-1.cdninstagram.com/(...).jpg

,	[get_rei(r'^\w+:/+(?:[^:/?#]+\.)?images-ext-[^:/?#]+\.discord[^/?#]+/+external/+[^/?#]+/+(?P<Protocol>\w+)/+'), r'\g<Protocol>://']
# ,	[get_rei(r'^\w+:/+(?:[^:/?#]+\.)?images-ext-[^:/?#]+\.discord[^/?#]+/+external/+[^/?#]+/+(?:\W[^/?#]+/+)*(?P<Protocol>\w+)/+'), r'\g<Protocol>://']

# ,	[get_rei(r'^(?:\w+:/+)?(?:[^:/?#]+\.)?(?:discordapp\.\w+/+)(?P<Path>attachments/.*?)(?:#\?.*)?$'), r'https://cdn.discordapp.com/\g<Path>']

#,	[get_rei(r'^(?:\w+:/+)?(?:(?:danbo+ru|w+)\.)?(?P<Domain>donmai\.us)/+'), r'http://shima.\g<Domain>/']	# <- this needs changing domains, better rely on auto-trying web-proxy instead

,	[get_rei(r'^(?:\w+:/+)(?:[^:/?#]+\.)?youtu\.be/+(?P<ID>[^/?&#]+)$'			), r'https://www.youtube.com/watch?v=\g<ID>']
,	[get_rei(r'^(?:\w+:/+)(?:[^:/?#]+\.)?youtu\.be/+(?P<ID>[^/?&#]+)(?:[?&/](?P<Arg>.*))?$'	), r'https://www.youtube.com/watch?v=\g<ID>&\g<Arg>']
,	[get_rei(r'^(?P<Site>\w+:/+(?:[^:/?#]+\.)?gelbooru\.com/)index\.\w+(?P<Query>[?#]|$)'	), r'\g<Site>\g<Query>']
,	[get_rei(r'^(?P<NoDL>\w+:/+(?:[^:/?#]+\.)?dropbox\.com/s/[^?#]+)[?#]dl=.*$'		), r'\g<NoDL>']
,	[get_rei(r'(?P<Path>file.qip.ru/(?:file|photo)/[^?#]+)(?:\?.*)?$'			), r'\g<Path>?action=downloads']
,	[get_rei(r'shot\.qip\.ru[^-#]*-(?P<Prefix>.)(?P<File>[^/?#]+)(?P<Sub>/+.*)?$'		), r'f\g<Prefix>.s.qip.ru/\g<File>.png']
# ,	[get_rei(r'^(?:\w+:/+)(?:[^:/?#]+\.)?(?:(?:fixupx(?:\w*x)?|twitter)\.com|nitter(?:\.\w+)*)/+(?P<Path>[^/?#])'), twitter_front_end + r'\g<Path>']
,	[get_rei(r'\b(?P<Path>twimg\.com/+media/+[^.:?&#%]+)(?:%3F|\?)(?:[^&#]*(?:%26|\&))*?format(?:%3D|\=)(?P<Format>[^&#%]+).*?$'		), r'\g<Path>.\g<Format>']
,	[get_rei(r'\b(?P<Path>twimg\.com/+media/+[^:?&#%]+\.[^.:?&#%]+)(?:(?:[:?&#]|%3A|%3F|%26|%23).*)?$'					), r'\g<Path>:orig']
,	[get_rei(r'\b(?P<Path>twimg\.com/+profile_images?/+[^:?&#%]+)(?:_[^/:?&#%]+)(?P<File>\.[^.:?&#%]+)(?:(?:[:?&#]|%3A|%3F|%26|%23).*)?$'	), r'\g<Path>\g<File>']
,	[get_rei(r'^(?:\w+:/+)(?:[^:/?#]+\.)?(?:rgho(?:st)?\.\w+|ad-l\.ink)/(?P<Path>\d\w+|private/\d\w+/\w+)[^?#]*'	), r'https://rghost.net/\g<Path>']
,	[get_rei(r'^(?P<Path>(?:\w+:/+)(?:[^:/?#]+\.)?forum\.spaceengine\.org\/+download/+file\.php\?id=[^&#]+)&[^#]*'	), r'\g<Path>']
,	[get_rei(r'^(?P<Protocol>\w+):/+(?:[^:/?#]+\.)?(?P<Domain>skype\.com)/+login/+sso?go=(?P<File>.*)$'		), r'\g<Protocol>://web.\g<Domain>/\g<File>']	# <- get attachments via web version

# reddit URL samples:
# https://www.reddit.com/r/.../comments/t4aemf/..._.../?utm_medium=android_app&utm_source=share
# https://preview.redd.it/g22rbbmq5kn81.jpg?width=640&crop=smart&auto=webp&s=6443a74739a9d9c882ae7d5fb35e35b2c1caed10
# https://i.redd.it/g22rbbmq5kn81.jpg

,	[get_rei(r'^(?:\w+:/+)?(?:[^:/?#]+\.)?(?:i|preview)\.redd\.it/+(?P<FileName>[^?#]+)(?:[?#].*)?$'), r'https://i.redd.it/\g<FileName>']
,	[get_rei(r'^(?P<NoTitle>(?:\w+:/+)?(?:[^:/?#]+\.)?reddit\.com/+r/+(?P<SubName>[^/?#]+)/+comments/+(?P<ThreadID>[^/?#]+))(?:[/?#].*)?$'), r'\g<NoTitle>']
]

pat2replace_before_dl = [			# <- strings after this are sent to web servers
	[get_rei(r'^(?P<Path>[^#]+)#.*$'					), r'\g<Path>']	# <- remove #anchor
# ,	[get_rei(r'^https(?P<NoProtocol>:/+(?:[^:/?#]+\.)?(?:googleusercontent|h(?:abra)?stor(?:age)?|vk|youtu(?:be)?|danbooru)\.)'), r'http\g<NoProtocol>']	# <- remove https
,	[get_rei(r'(?P<NoDL>dropbox\.com/s/[^?#]+)\?.*$'			), r'\g<NoDL>?dl=1']
,	[get_rei(r'img\.5cm\.ru/view/i5'					), r'i5.5cm.ru/i']
,	[get_rei(r'^(?P<Protocol>\w+):/+(?:www\.)?dobrochan\.(?:ru|org|com)(?:$|/+)'			), r'\g<Protocol>://dobrochan.com/']
,	[get_rei(r'^(?P<Protocol>\w+):/+(?:www\.)?2-?ch\.(?:cm|ec|hk|pm|re|ru|so|tf|wf|yt|life)(?:$|/+)'), r'\g<Protocol>://2ch.hk/']	# <- 2ch.life needs CloudFlare cookies
# ,	[get_rei(r'(?P<Site>vocaroo\.com)/i/s'), r'\g<Site>/media_command.php?command=download_flac&media=s']	# <- FLAC not available anymore
,	[get_rei(r'^(?:\w+:/+(?:[^:/?#]+\.)?(?:vocaroo\.com|voca\.ro)/+)(?P<File>[^/?&#]+)$'), r'https://media.vocaroo.com/mp3/\g<File>']
]

default_red2_name_prefix = [[0, r'\1 - ']]	# <- prepend only first captured sub-group - "(...)"

pat2recursive_dl = [				# <- additional sub-steps to grab

# imgur:

# JSON sample from imgur.com/a/zVhZg: {"hash":"JdFDePz","title":"","description":null,"has_sound":false,"width":863,"height":800,"size":136820,"ext":".jpg","animated":false,"prefer_video":false,"looping":false,"datetime":"2015-09-06 19:54:17"}
# JSON sample from imgur.com/a/xyN6u: {"hash":"wPpFLrE","title":"","description":null,"has_sound":false,"width":710,"height":1002,"size":392671,"ext":".png","animated":false,"prefer_video":false,"looping":false,"datetime":"2019-05-29 16:18:38","edited":"0"},

	{	'page':		# <- parent: where to look, URL partial match
		get_rei(r'''^
			(?P<PageURL>
				\w+:/+
				(?:[^:/?#]+\.)?
				imgur\.com/+
				(?:a/+|ga[lery]+/+|t/+[^/]+/+)?
				\w+
				(?:\.gifv|/+embed)?
			)
			(?:[,&?#]|$)
		''')
	,	'grab':		# <- child: what to grab, concat all subpatterns if none can be expanded from optional 'link' array
		get_rei(r'''
			<(?:
				source(?:\s+[^>]*?)?\s+src
			|	link(?:\s+[^>]*?)?\s+rel="(?:canonical|image_src)"(?:\s+[^>]*?)?\s+href
			|	meta(?:\s+[^>]*?)?\s+property="og:image"(?:\s+[^>]*?)?\s+content
		#	|	img(?:\s+[^>]*?)?\s+data-src	# <- thumbs, not needed
			)
			="?/*
			(?P<LinkMetaSrc>(?:\w+:/+)?[^"/]+/)	# <- 1 = LinkMetaSrc
			(?:
				\w+,
				((?:\w+,)*)			# <- 2
			)?
			([^"?]+)				# <- 3

		|	<a(?:\s+[^>]*?)?\s+href="?/*
			(?P<Href>(?:\w+:/+)?[^"/]+/)		# <- 4 = Href
			([^"?]+)"*\s+				# <- 5
			(?:
				[^>]*\bclass="*[^">]*\bzoom
			|	target="_blank">\s*View\s+full
			)

		|	<img(?:\s+[^>]*?)?\s+src=[\'"]*
			(?:((?:\w+:/+|//)[^"/]+/+)|/*)?		# <- 6
			(?P<ImgSrc>[^\s\'">]+/)			# <- 7 = ImgSrc
			([^\s\'">/]+)				# <- 8
			[\s\'"][^>]*?\bcontentURL

		|	\{
			(?:
				\s*"?
				(?:
					width	"?:"?(?P<Width>	\d+)
				|	height	"?:"?(?P<Height>	\d+)
				|	size	"?:"?(?P<Size>	\d+)
				|	hash	"?:"?(?P<ID>	(?:\\"|[^"])*)
				|	ext	"?:"?(?P<Ext>	(?:\\"|[^"])*)
				|	datetime"?:"?(?P<Date>	(?:\\"|[^"])*)	# <- fields in any order
				|	[\w-]+	"?:"?(?:	(?:\\"|[^"])*)	# <- other unneeded fields
				)
				"?\s*[,}]
			)+
		''')
	,	'link': [
			r'i.imgur.com/\g<ID>\g<Ext>'
		,	r'imgur.com/\g<ID>'
		]
	,	'name': [
			[0, r'\g<PageURL> - ']	# <- 0: expand from parent URL
		,	[-1,r'\g<Counter> - ']	# <- negative: substitute \1 or \g<Counter> with recursive processed count, minus given here
		,	[
				get_rei(r'album_images"?\s*:\s*{"?count"?\s*:\s*(?P<AlbumCount>\d+)')
			,	r'of \g<AlbumCount> - '
			]			# <- regex: expand from parent content
		,	[1, r'\g<Href>']	# <- 1: expand from child URL
		,	[1, r'\g<ImgSrc>']
		,	[1, r'\g<LinkMetaSrc>']
		,	[1, r'\g<Width>x\g<Height> - ']
		,	[1, r'\g<Size> B - ']
		,	[1, r'\g<Date> - ']
		]
	}

# gfycat:

# HTML sample from https://gfycat.com/boguscoldchuckwalla (newlines added for clarity):
# <meta data-react-helmet="true" property="og:video" content="https://thumbs.gfycat.com/BogusColdChuckwalla-mobile.mp4"/>
# <meta data-react-helmet="true" property="og:video:secure_url" content="https://thumbs.gfycat.com/BogusColdChuckwalla-mobile.mp4"/>
# <meta data-react-helmet="true" property="og:video:type" content="video/mp4"/>
# <meta data-react-helmet="true" property="og:video:width" content="640"/>
# <meta data-react-helmet="true" property="og:video:height" content="800"/>
# <meta data-react-helmet="true" property="og:video:duration" content="7.63"/>
# ...
# <video class="video media" id="video-boguscoldchuckwalla" alt="wildcatcentre-20200621-0001 GIF" height="900" width="720" muted="" playsinline="" preload="auto" poster="https://thumbs.gfycat.com/BogusColdChuckwalla-mobile.jpg" style="max-width:640px;margin:0 auto;display:block" tabindex="-1">
# <source src="https://thumbs.gfycat.com/BogusColdChuckwalla-mobile.mp4" type="video/mp4"/>
# <source src="https://giant.gfycat.com/BogusColdChuckwalla.webm" type="video/webm"/>
# <source src="https://giant.gfycat.com/BogusColdChuckwalla.mp4" type="video/mp4"/>
# <source src="https://thumbs.gfycat.com/BogusColdChuckwalla-mobile.mp4" type="video/mp4"/>
# </video>

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?gfycat\.com/+(?:\w{2}/+)?[^/]+)(?:[,&?#]|$)')
	,	'grab': get_rei(r'''
			(?:
				<meta(?:\s+[^>]*?)?\s+property="?og:video:
				(?:
					secure_url	"?(?:\s+[^>]*?)?\s+content="?(?P<MetaURL>	[^"]+)	# <- fields in any order
				|	width		"?(?:\s+[^>]*?)?\s+content="?(?P<Width>		\d+)
				|	height		"?(?:\s+[^>]*?)?\s+content="?(?P<Height>	\d+)
				|	duration	"?(?:\s+[^>]*?)?\s+content="?(?P<Duration>	[^"]+)
				|	[\w-]+		"?(?:\s+[^>]*?)?\s+content="?(?:		[^"]+)	# <- other unneeded fields
				)
				"?(?:\s+[^>]*?)?>\s*
			)+
		|	<source(?:\s+[^>]*?)?\s+src="?(?P<Src>[^">]+)	# <- 1
		''')
	,	'link': [
			r'\g<Src>'
		,	r'\g<MetaURL>'
		]
	,	'name': [
			[0, r'\g<PageURL> - ']	# <- 0: expand from parent URL
		# ,	[1, r'\g<MetaURL>']	# <- 1: expand from child URL
		,	[1, r'\g<Width>x\g<Height> - ']
		,	[1, r'\g<Duration>s - ']
		]
	}

# gyazo:

,	{	'page': get_rei(r'''^
			(?:\w+:/+)?
			(?:[^:/?#]+\.)?
			(?P<Domain>gyazo\.com/+)
			(?:[^?#]*?)?
			(?P<ImageID>/+\w{32})
			(?:\W.*)?
		$''')
	,	'link': r'\g<Domain>\g<ImageID>'	# <- view page instead of direct link to image
	}
,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?gyazo\.com/+[^/]+)$')
	,	'grab': get_rei(r'''
			(?:<meta(?:\s+[^>]*?)?\s+content="?(?P<Width> \d+)"?(?:\s+[^>]*?)?\s+property="?og:image:width ["\s/>][^<]*?)?
			(?:<meta(?:\s+[^>]*?)?\s+content="?(?P<Height>\d+)"?(?:\s+[^>]*?)?\s+property="?og:image:height["\s/>][^<]*?)?
			<link   (?:\s+[^>]*?)?\s+href=   "?(?P<Href>[^">\s]+)"?(?:\s+[^>]*?)?\s+rel="?image[^a-z]?src["\s/>]
		|	<img    (?:\s+[^>]*?)?\s+src=    "?(?P<Src>[^">\s]+)
		''')
	,	'link': [
			r'\g<Src>'
		,	r'\g<Href>'
		]
	,	'name': [
			[0, r'\g<PageURL> - ']
		,	[1, r'\g<Width>x\g<Height> - ']
		#,	[1, r'\g<Src>']
		#,	[1, r'\g<Href>']
		]
	}

# twitpic, vk shared files, etc - indiscriminately grab any links:

,	{	'page': get_rei(r'''^
			(?P<PageURL>
				(?:\w+:/+)?
				(?:[^:/?#]+\.)?
				(?:
					jpg\.to
				|	twitpic\.com
				|	vk\.(?:com|ru)/+doc[\w-]+
				)
			)
			(?:[/?#]|$)
		''')
	,	'grab': get_rei(r'\s+(?:src|href)="?([^">\s]+)')
	}

# skype:

# URL samples:
# https://login.skype.com/login/sso?go=xmmfallback?pic=0-weu-d11-183e0e666f79f30ccbcc39d1acc696ae
# https://web.skype.com/xmmfallback?pic=0-weu-d11-183e0e666f79f30ccbcc39d1acc696ae
# https://api.asm.skype.com/v1/objects/0-weu-d11-183e0e666f79f30ccbcc39d1acc696ae/views/imgpsh_fullsize

,	{	'page': get_rei(r'''^
			(?:\w+:/+)?
			(?:[^:/?#]+\.)?
			(?P<Domain>skype\.com/+)
			[^#]*?xmmfallback
			[^#]*?[?&]pic=
			(?P<ImageID>[^?&#]+)
		''')
	,	'link': r'https://api.asm.skype.com/v1/objects/\g<ImageID>/views/imgpsh_fullsize'	# <- direct link to image instead of page, which contains no links and relies on JS
	}

# exhentai:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)e[x-]*hentai\.org/+g(?:/+\d+)+)')
	,	'grab': get_rei(r'\s+href=[\'"]*([^\s\'">]+?hathdler[^\s\'">]+)')
	}

# ezgif:

,	{	'page': get_rei(r'^(?P<PageURL>(?:\w+:/+(?:[^:/?#]+\.)?ezgif\.\w+)/+\w+(?:/+\w+)\.gif)(?:[/?#]|$)')
	,	'grab': get_rei(r'<img(?:\s+[^>]*?)?\s+src="?/*([^">\s]+)"*(?:\s+[^>]*?)?\s+id="?target')
	}

# fastpic:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?fastpic\.ru/+(?:big|view)/+[^?#]*)')
	,	'grab': pat_imgs
	}

# hqpix:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?hqpix.\w+/+image/+[^/?#]+)(?:[/?#]|$)')
	,	'grab': get_rei(r'<a\b[^<]*?\s+href="?([^">\s]+)[">\s][^<]*?\s+download=')
	}

# ibb / imgbb:

# HTML sample from https://ibb.co/M8cc1my:
# <img src="https://i.ibb.co/YDccdx4/scr00044.jpg" alt="scr00044" width="2560" height="1440" data-load="full">

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?(?:ibb|imgbb).com?/+\w+)(?:[/?#]|$)')
	,	'grab': get_rei(r'<img(?:\s+[^>]*?)?\s+src="?/*([^">\s]+)"*(?:\s+[^>]*?)?\s+data-load="?full')
	}

# imgstun:

,	{	'page': get_rei(r'^(?P<PageURL>(?:\w+:/+(?:[^:/?#]+\.)?imgstun.\w+)(?:/+\w+){3}(?:\.\w+){2})(?:[/?#]|$)')
	,	'grab': get_rei(r'</dd>[^<]*?<dt[^<]*?</dt><dd[^<]*?<input(?:\s+[^>]*?)?\s+value="?([^">\s]+)')
	}

# awesomescreenshot:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?awesomescreenshot\.com/+[^/]+)$')
	,	'grab': get_rei(r'\s+id="screenshotA"\s+href="?([^">\s]+)')
	}

# clip2net:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?(?:c2n\.\w+|clip2net\.\w+/+s)/+[^/]+)$')
	,	'grab': get_rei(r'\s+class="image-down-file"\s+href="?([^">\s]+?)(?:&fd=[^&]*)?[">\s]')
	}

# prntscrn:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?(?:prnt.sc|prntscrn?\.com)/+[^/]+)$')
	,	'grab': get_rei(r'''
			<meta\s+property=[\'"]*og:image[\'"]*\s+content=[\'"]*
			([^\s\'">]+)

		|	\s+src=[\'"]*
			([^\s\'">]+)
			[^>]*?\s+id=[\'"]*screenshot-image

		|	\s+id=[\'"]*screenshot-image[^>]*?\s+src=[\'"]*
			([^\s\'">]+)
		''')
	}

# screencapture:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?screencapture\.ru/+file/+[^/]+)$')
	,	'grab': get_rei(r'\s+href="?([^\s\'">]+?/file/download/[^\s\'">]+)')
	}

# screencast:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?screencast\.com/+t/+[^/]+)$')
	,	'grab': get_rei(r'\s+class="?embeddedObject"?\s+src="?([^">\s]+)')
	}

# rghost:

,	{	'page': get_rei(r'^(?:\w+:/+(?:[^:/?#]+\.)?(?:rgho(?:st)?\.\w+|ad-l\.ink))/+(?:private/+)?(?P<ID>\d\w+)')
	,	'grab': get_rei(r'\s+href="((?:\w+:|/+\w+)/+(?:[^/?#.]+\.)?(?:rgho(?:st)?\.\w+|ad-l\.ink)/download/(?:private/)?\d\w+/[^">\s]+)')
	,	'name': [
			[0, r'rgh \g<ID> - ']
		,	[get_rei(r'''
				<time(?:\s+[^>]*?)?\s+datetime="
				(?P<YMD>    [^":\s]+)\s+
				(?P<Hours>  [^":]+):
				(?P<Minutes>[^":]+):
				(?P<Seconds>[^":]+)
			'''), r'\g<YMD>,\g<Hours>-\g<Minutes>-\g<Seconds> - ']
		]
	}

# nofile.io:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?nofile\.io/+f/+[^/].+)$')
	,	'grab': get_rei(r'\s+downloadButton[^>]*?\s+href="?([^\s\'">]+)')
	}

# sta.sh:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+sta\.sh/+\w+)(?:[/?#]|$)')
	,	'grab': get_rei(r'<meta\s+property=[\'"]*og:image[\'"]*\s+content=[\'"]*(?P<LinkURL>[^\s\'">]+)')
	,	'name': [
			[0, r'\g<PageURL> - ']
		,	[1, r'\g<LinkURL>']
		]
	}

# upload.cat:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+upload\.cat/+\w+)(?:[/?#]|$)')
	,	'grab': get_rei(r'''
			<img\s+alt	(?:\s+[^>]*?)?\s+src=	[\'"]*(?P<Src>[^">\s]+)
		|	<a		(?:\s+[^>]*?)?\s+href=	[\'"]*(?P<Href>[^">\s]+)(?:[\s"]+[^>]*)?>\w*?download
		''')

# HTML sample from https://upload.cat/c9d04f72208d7966
# <img alt="cache_95c50f95-ffdb-4502-c548-fef6618fb774.png" src="https://upload.cat/imageviewer/8e175786cf0929b39570ce75f92e307e_40518" style="max-width: 100%;"/>
# <a onclick="_gaq.push(['_trackPageview', '/download_image']);" href="https://upload.cat/c9d04f72208d7966?download_token=9daebf1bf5552c8d83f8a11960f424d820c0d8eb8883de28ae20b1644d2e9abf" target="_blank">(download)</a>

	,	'name': [
			[0, r'\g<PageURL> - ']
		,	[1, r'\g<Src>']
		,	[1, r'\g<Href>']
		]
	}

# webmshare:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?webm(?:share)?\.\w+/+\w+)(?:[/?#]|$)')
	,	'grab': get_rei(r'<source(?:\s+[^>]*?)?\s+src=[\'"]*/*([^\s\'">]+?)(?:/\d+)?[\s\'">]')
	,	'name': [
			[0, r'\g<PageURL> - ']
		,	[get_rei(r'''
				<[^>]+?\s+class="?page-header"?[^>]*>
				[^>]+>		(?P<UploadFileName>	[^<]*	)	</
				[^:/]+:\s*	(?P<UploadDate>		[^<]*	)	</
			'''), r'\g<UploadFileName> - \g<UploadDate> - ']
		]
	}

# nitter - twitter frontend:

# HTML sample from https://nitter.net/Soveno2/status/1483152138972712962
# <link rel="preload" type="image/png" href="/pic/media%2FFJUwOH1XsAExXQs.jpg%3Fname%3Dsmall" as="image" />
# <meta property="og:image" content="https://nitter.net/pic/media%2FFJUwOH1XsAExXQs.jpg" />
# <meta property="twitter:image:src" content="https://nitter.net/pic/media%2FFJUwOH1XsAExXQs.jpg" />
# <...>
# <div class="attachments">
# <div class="gallery-row" style="">
# <div class="attachment image">
# <a class="still-image" href="/pic/media%2FFJUwOH1XsAExXQs.jpg%3Fname%3Dorig" target="_blank">
# <img src="/pic/media%2FFJUwOH1XsAExXQs.jpg%3Fname%3Dsmall" alt="" />
# <...>
# <div class="attachments media-gif">
# <div class="gallery-gif" style="max-height: unset; ">
# <div class="attachment">
# <video class="gif" poster="/pic/tweet_video_thumb%2FFJVma9TWUBEkwAr.jpg%3Asmall" controls="" autoplay="" muted="" loop="">
# <source src="/pic/video.twimg.com%2Ftweet_video%2FFJVma9TWUBEkwAr.mp4" type="video/mp4" />

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^%:/=\s&?#]+\.)?nitter(?:\.\w+)*/+[^?#]+)([?#]|$)')
	,	'grab': get_rei(r'''
			\s\w+="
		(?:	\w+:/+			(?:[^%:/=\s&?#]+\.)?nitter(?:\.\w+)*				)?
			/pic/
		(?:	(?P<Domain>		(?:[^%:/=\s&?#]+\.)?twimg\.com	)	(?:/|%2F)+	)?
			(?P<DirType>		[^%/.\s">]+			)	(?:/|%2F)+
		(?:	(?P<DirNumber>		\d+				)	(?:/|%2F)+	)?
			(?P<FileName>		[^%/.\s">]+			)
			(?P<FileExt>	\.	[^%/.\s">]+			)
		''')
	,	'link': [
			r'https://\g<Domain>/\g<DirType>/\g<DirNumber>/\g<FileName>\g<FileExt>'
		,	r'https://\g<Domain>/\g<DirType>/\g<FileName>\g<FileExt>'
		,	r'https://pbs.twimg.com/\g<DirType>/\g<DirNumber>/\g<FileName>\g<FileExt>'
		,	r'https://pbs.twimg.com/\g<DirType>/\g<FileName>\g<FileExt>'
		]
	}

# twitter:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?t\.co/+[^/]+)')
	,	'grab': get_rei(r'(?:[\s;]URL="?|<title>)(?P<LinkURL>[^"<>\s]+)')
	,	'link': r'\g<LinkURL>'
	}
,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+(?:[^:/?#]+\.)?twitter\.com/+[^/]+/+status/+[^/]+)')
	,	'grab': get_rei(r'''
		\s+(?:
			data-url="?([^"]*?/status/\d+/photo/[^"?]*)
		|	data-image-url="?([^">\s]+)
		|	src="?([^">\s]+):small
		|	background-image:\s*url\(["']([^"'>\s]+/tweet_video_thumb/[^"'>\s]+)
		)
		''')
	}

# twitter - grab video by thumb:

,	{	'page': get_rei(r'^(?:\w+:/+)?(?:[^:/?#]+\.)?(?P<Domain>twimg\.com/+tweet_video)_thumb(?P<ImageID>/+[^/.?#]+)(?:[.?#]|$)')
	,	'link': r'https://video.\g<Domain>\g<ImageID>.mp4'
	}

# URL samples from https://twitter.com/tukudani01/status/1140647123873964032
# https://pbs.twimg.com/tweet_video_thumb/D9RkbuHVUAA7Ch0.jpg
# https://video.twimg.com/tweet_video/D9RkbuHVUAA7Ch0.mp4

# tumblr:

,	{	'page': get_rei(r'''^
			(?P<Protocol>\w+:/+)
			([^:/?#]+\.)?
			(?P<Domain>tumblr\.com)
			/+video
			(?:_file)?
			(?:/+\w+:\w+)?
			/+
			(?P<UserName>\w+)
			/+
			(?P<PostID>\w+)
			(?:[/?#]|$)
		''')
	,	'grab': get_rei(r'<source(?:\s+[^>]*?)?\s+src=[\'"]*(?P<Src>[^">\s]+)')
	,	'name': [
			[0, r'\g<Protocol>\g<UserName>.\g<Domain>/post/\g<PostID> - ']
		# ,	[1, r'\g<Src>']
		]
	}

# tumblr photoset, check this even after 1st "og:image" step:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+[^/?#]+/+post/+\d+/+photoset)_iframe(?:[/?#]|$)')
	,	'grab': get_rei(r'<(?:a(?:\s+[^>]*?)?\s+href|img(?:\s+[^>]*?)?\s+src)="?/*(?P<Src>[^">\s]+)')
	,	'name': [
			[0, r'\g<PageURL> - ']
		,	[-1,r'\g<Counter> - ']
		]
	}

# tumblr-based blogs, any random domains possible:

,	{	'page': get_rei(r'^(?P<PageURL>\w+:/+[^/?#]+/+(image|post|private|video(_file)?(/+\w+:\w+)?)/+\d+)(?:[/?#]|$)')
	,	'grab': get_rei(r'''
			<(?:
				(?:
					meta\s+property=[\'"]*og:image[\'"]*\s+content
				|	a(?:\s+[^>]*?)?\s+data-highres
				|	a(?:\s+[^>]*?)?\s+href=[\'"]*[^\s\'">]+/image/\d+[^>]*<img(?:\s+[^>]*?)?\s+src
				|	iframe(?:\s+[^>]*?)?\s+id=[\'"]*photoset[^>]*?\s+src
				|	img(?:\s+[^>]*?)?\s+data-src
				)
				=[\'"]*
				(?P<PostPath>
					(?:\w+:(?://[^/?#]+)?)?
					/post/\d+/
				)?
				(?P<PostID>[^\s\'">]+/)?

			|	img(?:\s+[^>]*?)?\s+src=[\'"]*
				([^\s\'">]+/tumblr_inline)

			|	iframe(?:\s+[^>]*?)?\s+src=[\'"]*
				([^\s\'">]+/video(?:_file)?/)
			)
			([^\s\'">]+)
		''')
	,	'name': [
			[0, r'\g<PageURL> - ']
		,	[-1,r'\g<Counter> - ']
		,	[1, r'\g<PostID>']
		# ,	[1, r'\g<Src>']
		]
	}
]

# MEGA URL samples:
# https://mega.nz/#!mkpXDQhJ!9Bi_Mop4x3_rEW9QanFQ8U-2UAH1XUKyIFPL7Mt6RaA
# https://mega.nz/#F!eNVWQJhJ!V2KmcjYK9hEhjwgTKz0F_w
# https://mega.nz/file/mkpXDQhJ#9Bi_Mop4x3_rEW9QanFQ8U-2UAH1XUKyIFPL7Mt6RaA
# https://mega.nz/folder/eNVWQJhJ#V2KmcjYK9hEhjwgTKz0F_w

pat_mega_path = get_rei(r'''
(?:
	(?:^|[/.])
	mega
	(?:(?:\.co)?\.nz)?
	[:/]+
|
	^[\w-]+[:/]+96d0d4e7-1ed7-4efb-99d0-b1bd780800b3[^#!]*?
)
(
	#(F)?!.+
|
	(file|folder)/+
	([^!#/]+)[!#]+
	([^!#/]+)
)
$''')

pat2open_in_browser = [	# <- too complicated to grab, so handle it by a prepared browser (js, etc)
	[pat_mega_path, None]
,	[get_rei(r'^(\w+:/+([^:/?#]+\.)?drive\.(google\.\w+/file|bitcasa\.\w+/send)/.*)$')]
,	[get_rei(r'^(\w+:/+([^:/?#]+\.)?yadi\.sk/\w+/[^/]+)'), r'\1#dl']
]

pat2recheck_next_time = [
	get_rei(r'^\w+:/+([^:/?#]+\.)?imgur\.com/(a|ga[lery]+|t/[^/]+)/\w+')
,	get_rei(r'^\w+:/+([^:/?#]+\.)?dropbox(usercontent)?\.\w+/')
,	get_rei(r'^\w+:/+([^:/?#]+\.)?(t\.co|(fixupx|(fx)?twitter)\.com|nitter(\.\w+)*)/\w+')
]

#pat2etag = [	# <- TODO: request using ETag header from the copy saved before, will get "304: not modified" for unchanged without full dl
#	[get_rei(r'dropbox(usercontent)?\.\w+/(?P<ID>s/[^?]+|u/[^?#]+)'), r'dropbox/\g<ID>']
#]

pat2replace_before_saving_file = [
	[get_rei(r'''^
		(?P<Protocol>
			\w+[;,:/]+
		)
		(?P<Domain>
			([^,&/?#]+\.)?
			images-ext-[^,&/?#]+\.
			discord[^,&/?#]+
		)
		(?P<PathPrefix>
			[,/]+
			external
			[,/]+
			[^,&/?#]+
			[,/]+
		)
		(?P<Target>
			(?P<TargetArguments>[^\w,&/?#][^,&/?#]+)
			[,/]+
			(?P<TargetProtocol>\w+)
			[,/]+
			(?P<TargetPath>.*)
		)
	$'''), r'\g<TargetProtocol>;,,\g<TargetPath>\g<TargetArguments>']
# ,	[get_rei(r'\w+[;,:/]+([^,&/?#]+\.)?images-ext-[^,&/?#]+\.discord[^,&/?#]+[,/]+external[,/]+[^,&/?#]+[,/]+(\W[^,&/?#]+[,/]+)*(\w+)[,/]+'), r'\3;,,']				# <- tested in TCMD
,	[get_rei(r'(?P<Path>(?:\w+;,+)?(?:[^,&]+\.)?(?:joy)?reactor\.\w+,[^%]*)(?:[^%]*?(?P<Percent>[%])[a-z0-9]{2,4})+(?P<Suffix>[^%]*)$'), r'\g<Path>\g<Percent>(...)\g<Suffix>']	# <- tested in TCMD
,	[get_rei(r'^(?P<Path>\w+[;,:/]+(?:[^;,:/?#]+\.)?discord[^?#&]+[,/]+[^?#&]+)(?P<Query>[?#&].*)$'			), r'\g<Path>#\g<Query>']
,	[get_rei(r'^(?:\w+[;,:/]+)?(?:[^;,:/?#]+\.)?(?:discordapp\.\w+[,/]+)(?P<Path>attachments[,/]+[^?#&]+)(?:[#?&].*)?$'),'https;,,cdn.discordapp.com,\g<Path>']
,	[get_rei(r'(?P<Path>file.qip.ru,file,\w+),.*?&action=d\w+'			), r'\g<Path>']
,	[get_rei(r'(?P<Path>\.(?:cdninstagram\.com|fbcdn\.net)[,/]+[^;:&?#]+)[;:&?#].+$'), r'\g<Path>']			# <- remove URL arguments
,	[get_rei(r'(?P<Arg>[&?#]token(-\w+)?)(=|%3D)[^&?#=]+?(?P<Ext>\.\w+)$'		), r'\g<Arg>=(...)\g<Ext>']
,	[get_rei(r'(?P<Tags>[;,][^;,]{32})[^;,]+(?P<By>_drawn_by_[^;,]+)$'		), r'\g<Tags>(...)\g<By>']	# <- overly long booru names, too many tags
,	[get_rei(r'\s+-\s+(?:https?;,+)?(\S+?[,.]\S*)(?P<Part2>\s+-\s+(?:https?;,+)?\1\S+)'	), r'\g<Part2>']	# <- child URL: duplicate parts
,	[get_rei(r'\s*-\s+of\s+(?P<Number>\d+)\s+-\s*'					), r' of \g<Number> - ']	# <- fix imgur album count
,	[get_rei(r'(?P<Suffix>(?P<Ext>\.[a-z0-9]+)[;:_][a-z0-9]+)$'			), r'\g<Suffix>\g<Ext>']	# <- fix twitter img link extention
,	[get_rei(r'(?P<Suffix>(?P<Ext>\.(bmp|gif|jp[eg]+|jxl|png|webp))[^.a-z]\S+)$'	), r'\g<Suffix>\g<Ext>']	# <- fix twitter img repost extention
,	[get_rei(r'(?P<Part1>,(\w+),\S+(\.[^\s.]+))\s+-\s+tumblr_\2\S+?\3$'		), r'\g<Part1>']		# <- remove redundant tumblr filename part
# ,	[get_rei(r'(?P<Ext>\.jp[eg]+){2,}$'	), r'\g<Ext>']	# <- remove duplicate extention
,	[get_rei(r'(?P<Ext>\.mov)\.quicktime$'	), r'\g<Ext>']	# <- remove duplicate extention
,	[get_rei(r'(?P<Ext>\.mp3)\.mpeg$'	), r'\g<Ext>']	# <- remove duplicate extention
,	[get_rei(r'(?P<Ext>\.\w+)\1+$'		), r'\g<Ext>']	# <- remove duplicate extention
,	[get_rei(r'[.,&#]+$'			), '.htm']	# <- remove trailing garbage
]

part_link_html_prefix = r'(^|\]\s*=\>\s*)\w+:/+'
part_blocked_host = r'([^:/?#]+\.)?(blocked\.netbynet\.\w+|rpn\.tmpk\.net)'

pat_blocked_url = [
	get_rei(r'^\w+:/+' + part_blocked_host + r'/')
,	get_rei(r'^\w+:/+[^/?#]+/rkndeny')
]

pat_blocked_content = [
	get_rei(part_link_html_prefix + part_blocked_host + r'/')
,	get_rei(part_link_html_prefix + r'[^/?#]+/rkndeny')
,	get_rei(ur'''
		<title>
	\s*		Доступ
	\s+		к
	\s+		(запрашиваемому|информационному)
	\s+		ресурсу
	\s+		ограничен
	\s*	</title>
	''')
]

a_type = type([])
d_type = type({})
r_type = type(pat_grab)
s_type = type('')
u_type = type(u'')

# ignore some SSL fails:
# http://stackoverflow.com/questions/19268548/python-ignore-certicate-validation-urllib2

false_ctx = ssl.create_default_context()
false_ctx.check_hostname = False
false_ctx.verify_mode = ssl.CERT_NONE

# - Utility functions ---------------------------------------------------------

def is_type_int(v): return isinstance(v, int)
def is_type_arr(v): return isinstance(v, a_type)
def is_type_dic(v): return isinstance(v, d_type)
def is_type_reg(v): return isinstance(v, r_type)
def is_type_str(v): return isinstance(v, s_type) or isinstance(v, u_type)

def meet(obj, criteria):
	return True if (
		obj and criteria and (
			criteria.search(obj)		if is_type_reg(criteria) else
			(obj.find(criteria) >= 0)	if is_type_str(criteria) else
			(obj in criteria)		if is_type_arr(criteria) else
			None
		)
	) else False

def get_as_list(value):
	return value if is_type_arr(value) else [ value ]

def try_decode(text, enc_in=None, enc_out=None):
	if not enc_in:
		enc_in = read_encoding
	elif enc_out and enc_in == enc_out:
		return text

	if is_type_arr(enc_in):
		for i in enc_in:
			d = try_decode(text, i, enc_out)
			if d:
				return d
	else:
		try:
			text = text.decode(enc_in)

		except Exception as e:
			write_exception_traceback()

			# return ''

	if enc_out:
		try:
			return text.encode(enc_out)

		except Exception as e:
			write_exception_traceback()

			# return ''

	return text

# https://stackoverflow.com/a/919684
def try_print(*list_args, **keyword_args):
	lines = []
	count_args = count_keyword_args = 0
	before_task = tell_if_readonly = False

	def try_append(arg):
		try:
			lines.append(unicode(arg))
		except:
			try:
				lines.append(str(arg))
			except:
				try:
					lines.append('%s' % arg)
				except:
					lines.append(arg)

	if list_args:
		for arg in list_args:
			try_append(arg)
			count_args += 1

	if keyword_args:
		for keyword, arg in keyword_args.items():
			if keyword == 'before_task':
				before_task = arg
			elif keyword == 'tell_if_readonly':
				tell_if_readonly = arg
			else:
				try_append(arg)
				count_keyword_args += 1

	if not (count_args or count_keyword_args):
		return

# encode/decode are bad kludges:

	# separator = line_separator
	separator = ' '

	if lines:
		try:
			text = separator.join(lines)
		except:
			try:
				text = separator.join(try_decode(line) for line in lines)
			except:
				try:
					text = separator.join(try_decode(line).encode(print_enc) for line in lines)
				except:
					try:
						text = separator.join(line.encode(print_enc) for line in lines)
					except:
						text = separator.join(line.decode(print_enc) for line in lines)

		try:
			print('%s' % text)
		except:
			try:
				print('%s' % text.encode(print_enc))
			except:
				try:
					print('%s' % text.decode(print_enc))
				except:
					print('Error: unprintable text.')

					write_exception_traceback()

	else:
		print('Warning: nothing to print with %d args and %d keyword args.' % (count_args, count_keyword_args))

def normalize_slashes(path):
	return path.replace('\\', '/')

def fix_slashes(path):
	if os.sep != '/':
		path = path.replace('/', os.sep)

	if os.sep != '\\':
		path = path.replace('\\', os.sep)

	return path

def conflate_slashes(path):

	match = re.search(pat_local_prefix, path)

	return (
		local_path_prefix + re.sub(pat_conseq_slashes, '/', match.group('Path'))
		if match
		else
		re.sub(pat_conseq_slashes, '/', path)
	)

def get_path_with_local_prefix(path):

	match = re.search(pat_local_prefix, path)
	path = re.sub(pat_conseq_slashes, '/', match.group('Path') if match else path)

	return local_path_prefix + path.lstrip('/')

def remove_trailing_dots_in_path_parts(path):
	return '/'.join(
		part if part == '.' or part == '..'
		else trim_path(part.rstrip('.'))
		for part in normalize_slashes(path).split('/')
	)

def get_long_abs_path(path):
	if local_path_prefix:
		path = remove_trailing_dots_in_path_parts(path)

		if path.find(normalize_slashes(local_path_prefix)) == 0:
			return path
		else:
			return local_path_prefix + os.path.abspath(path)

	return fix_slashes(remove_trailing_dots_in_path_parts(path))

def translate_url_to_filename(text):
	try:			return text.translate(url2name)
	except TypeError:	pass
	except Exception:	write_exception_traceback()

	try:			return text.translate(url2name_unicode)
	except TypeError:	pass
	except Exception:	write_exception_traceback()

	try:			return sanitize_filename(text)
	except TypeError:	pass
	except Exception:	write_exception_traceback()

	return text

def sanitize_char(input_char):
	input_ord = ord(input_char)

	for safe_ord in safe_chars_as_ord:
		if (
			(
				input_ord >= safe_ord[0]
			and	input_ord <= safe_ord[1]
			)
			if is_type_arr(safe_ord) else
			input_ord == safe_ord
		):
			return input_char
	return '_'

def sanitize_filename(input_text):
	result_text = ''

	for i in range(len(input_text)):
		result_text += sanitize_char(input_text[i])

	return result_text

def fix_filename_before_saving(filename):
	filename = get_unproxified_url(try_decode(filename))

	for p in pat2replace_before_saving_file:
		filename = re.sub(p[0], p[1], translate_url_to_filename(filename))

	return translate_url_to_filename(filename)

def get_attr_text_if_not_empty(obj, i):
	if hasattr(obj, i):
		v = getattr(obj, i)
		if not callable(v):
			s = str(v)
			if len(s) > 0:
				return 'obj.%s = %s\n' % (i, s)
	return ''

def dump(obj, check_list=[]):

	result_text = ''

	if check_list and is_type_arr(check_list):
		for i in check_list:
			attr_text = ''

			if is_type_arr(i):
				for j in i:
					attr_text = get_attr_text_if_not_empty(obj, j)
					if attr_text:
						break
			else:
				attr_text = get_attr_text_if_not_empty(obj, i)

			if attr_text:
				result_text += attr_text

	else:
		for i in dir(obj):
			result_text += get_attr_text_if_not_empty(obj, i)

	return result_text

# https://stackoverflow.com/a/3314411
def get_obj_pretty_print(obj):
	try:
		d = obj.__dict__ if '__dict__' in obj else obj

		return json.dumps(d, sort_keys=True, indent=4, default=repr)

	except Exception as e:
		write_exception_traceback(e)

		return str(obj)

def timestamp():
	return time.strftime('- '+format_print+' -')

def log_stamp():
	return time.strftime('['+format_print+']	')

def timestamp_now(str_format=format_epoch):
	return time.strftime(str_format.replace(format_epoch, str(int(time.time()))))

# http://code.activestate.com/recipes/577015-parse-http-date-time-string/
# http://stackoverflow.com/questions/11743019/convert-python-datetime-to-epoch-with-strftime

def get_timestamp_from_http_modtime(str_modtime, str_format=format_epoch):
	t = datetime.datetime(*parsedate(str_modtime)[ : 6])
	s = str(int((t - datetime.datetime(1970,1,1)).total_seconds()))
	t = datetime.datetime.fromtimestamp(time.mktime(t.timetuple()))
	f = str_format.replace(format_epoch, s)

	return t.strftime(f)

def read_file(path, mode='r'):
	if not os.path.isfile(path):
		return ''

	f = open(path, mode)
	r = f.read()
	f.close()

	return r

def write_file(path, conts, mode='a+b'):
	for f in ['lower', 'real']:
		if hasattr(conts, f):
			conts = [conts]

			break

	f = open(path, mode)

	for content in conts:
		try:
			f.write(content)

		except Exception:
			write_exception_traceback()

			try:
				k = dump(content, ['__class__', '__doc__', 'args', 'message', ['headers', 'hdrs']])
				f.write(k or dump(content))

			except Exception:
				write_exception_traceback()

				f.write('<Unwritable>')
	f.close()

def write_exception_traceback(text=''):
	if not log_traceback:
		return

	f = open(log_traceback, 'a+b')
	t = line_separator + log_stamp()

	try:
		if text:
			text += line_separator
		f.write(t + text)

	except Exception:
		f.write(t + '<Unwritable pretext>' + line_separator)

	try:
		traceback.print_exc(None, f)

	except Exception:
		f.write('<Unwritable traceback>')

	f.close()

def trim_path(path, path_sep='/', name_sep='.', placeholder='(...)', max_len=250):
	path = conflate_slashes(path)

	if len(path) > max_len:
		path, name = ('', path) if path.find(path_sep) < 0 else path.rsplit(path_sep, 1)
		head, tail = (name, '') if name.find(name_sep) < 0 else name.rsplit(name_sep, 1)

		if path:
			path += path_sep

		tail = (placeholder + name_sep + tail) if tail else placeholder

		len_without_name = len(path) + len(tail)
		left_for_name = max_len - len_without_name

		path += (
			name[0 : max_len - len(path)]
			if left_for_name < 0
			else
			(head[0 : left_for_name] + tail)
		)

	return path

def save_uniq_copy(path, content):
	path = get_long_abs_path(path)
	path = trim_path(path)

	try:
		is_existing_path = os.path.exists(path)

	except TypeError:
		old_path = try_decode(path)

		for enc in read_encoding:
			try:
				path = old_path.encode(enc)
				is_existing_path = os.path.exists(path)

			except Exception:
				write_exception_traceback(enc)

				path = None

			if path:
				break

		# if not path:
			# path = 'bad_file_path' + time.strftime(format_path_mtime) + '.ext'

	if path:
		if is_existing_path:
			if content == read_file(path, 'rb'):
				return False

			path_with_old_file_modtime = (
				datetime.datetime.fromtimestamp(os.path.getmtime(path))
				.strftime(format_path_mtime)
				.join(path.rsplit('.', 1))
			)

			new_path_for_old_file = uniq_path(trim_path(path_with_old_file_modtime, ';'))
			# new_path_for_old_file = uniq_path(path_with_old_file_modtime)

			try:
				os.rename(path, new_path_for_old_file)

			except Exception:
				write_exception_traceback()

				path = uniq_path(path)

		write_file(path, content, 'wb')

	return path

def uniq_path(path):
	if os.path.exists(path):
		n = 1
		i = int(time.time())
		t = str(i)
		base, ext = path.rsplit('.', 1)
		base += '('
		ext += ').'

		while os.path.exists(path):
			n += 1
			if n >= i:
				n = 1
				base += t + '_'

			path = base + n + ext

	return path

def read_log(path, start=0, size=0):
	f = open(path, 'r+b')
	if start:
		f.seek(start)
	r = f.read(size) if size else f.read()
	sz = f.tell()
	f.close()

	bytes_text = colored('%d to %d bytes in' % (start, sz), 'yellow')

	try:
		try_print(bytes_text, path.rsplit('/', 1)[1])

	except Exception:
		write_exception_traceback()

		try_print(bytes_text, colored('<Unprintable>', 'red'))

	return [r, '%d	%d	%s' % (start, sz, path)]

def get_prereplaced_url(url, hostname='', protocol='http://'):
	if url[0 : 1] == '/':
		if url[1 : 2] == '/':
			url = protocol + url.lstrip('/')
		elif hostname:
			url = hostname + url
	elif url.find('://') < 0:
		url = protocol + url.lstrip('/')

	if url.find('(') < 0:
		url = url.strip(')')

	for p in pat2replace_before_checking:
		url = re.sub(p[0], p[1], url)	# <- fix urls to note

	return url

def get_proxified_url(url, prfx=False):
	if prfx:
		# prfx = default_web_proxy
		# prfx = prfx.rstrip('/')+'/'

		return (
			prfx+'http/'+url if url.find('://') < 0 else
			re.sub(pat_badp, prfx+(
				'https/' if url.find('https://') == 0 else
				'http/'
			), url)
		)

	match = re.search(web_proxy_replacement_add['from'], url)

	if match:
		for pat in web_proxy_replacement_add['to']:
			try:
				return match.expand(pat)

			except Exception:
				continue

	return url

def get_unproxified_url(url):

	match = re.search(web_proxy_replacement_remove['from'], url)

	if match:
		for pat in web_proxy_replacement_remove['to']:
			try:
				return match.expand(pat)

			except Exception:
				continue

	return url

def get_dest_dir_from_log_name(name):
	for rule in pat_ln2d:
		a = rule if is_type_arr(rule) else [rule]
		match = re.search(a[0], name)
		if match:
			if len(a) > 1:
				for i in a[1 : ]:
					try:
						if i.find('\\') >= 0:
							g = match.expand(i)
						else:
							g = match.group(i)
						if g and len(g) > 0:
							g_clean = g
							for pat in pat_dest_dir_replace:
								g_clean = re.sub(pat[0], pat[1] or '', g_clean).strip()

							return g_clean if len(g_clean) > 0 else g

					except Exception:
						write_exception_traceback()

						continue
			else:
				for i in match.groups():
					if i and len(i) > 0:
						return i
			return name
	return ''

def get_path_without_local_prefix(path):
	if local_path_prefix and path.find(local_path_prefix) == 0:
		return path[len(local_path_prefix) : ]

	return path

def read_path(path, dest_root, lvl=0):
	global changes, old_meta, new_meta

	urls = []
	if not (os.path.exists(path) and os.path.isdir(path)):
		return urls

	if recurse:
		can_go_deeper = (path == path.rstrip('/.')) and (recurse > lvl)
		if TEST:
			try_print(path, colored('->', 'yellow'), lvl)
		else:
			try_print(path)
	else:
		can_go_deeper = False

		try_print(path)

	for name in os.listdir(path):
		f = path+'/'+name
		if os.path.isdir(f):
			if can_go_deeper:
				urls += read_path(f, dest_root, lvl+1)

			continue

		meta = r = ''
		start = 0
		src_file_path = get_path_without_local_prefix(f)

		for line in old_meta:
			if src_file_path == get_path_without_local_prefix(line[2]):

				start = int(line[1])
				meta = tab_separator.join(line)

				break

		sz = os.path.getsize(f)
		if sz != start:
			try:
				r, meta = read_log(f, start if sz > start else 0)
				changes += 1

			except IOError as e:
				write_exception_traceback()

				try_print(colored('Error reading log:', 'red'), log_stamp(), e)
				r = meta = ''

				# continue

		if r:
			u = 0
			dest = dest_root+'/'+get_dest_dir_from_log_name(name)

			for enc in read_encoding:
				rd = try_decode(r, enc, default_encoding)

				if TEST:
					try_print(name, colored('length in %s = %d' % (enc, len(rd)), 'yellow'))

				for i in re.finditer(pat_grab, rd):
					prfx = dnm = dtp = None
					did = i.group('DiscordID') if 'd' in flags else None
					if did:
						dtp = i.group('DiscordType')
						dnm = i.group('DiscordName')
						url = 'https://cdn.discordapp.com/emojis/' + did + '.png'
					else:
						url = i.group('URL').strip()

					url = get_prereplaced_url(url)

					recheck = 1
					d = i.group('App')
					if not d:
						d = dest
						if url in urls_done:
							recheck = 0
							for p in pat2recheck_next_time:
								if p.search(url):
									recheck = 1

									break
					if recheck:
						if did:
							prfx = (
								'Discord Emoji'
							+	((' - ' + dtp) if dtp else '')
							+	((' - ' + dnm) if dnm else '')
							)
						try:
							ude = url.decode(enc)
							utf = ude.encode(default_encoding)

						except Exception as e:
							write_exception_traceback()

							try:
								ude = url.decode(default_encoding)
								utf = url

							except Exception as e:
								write_exception_traceback()

								ude = utf = url
						try:
							try_print(ude)

						except Exception as e:
							write_exception_traceback()

							try_print(colored('<Unprintable>', 'red'), url.split('//', 1)[-1].split('/', 1)[0])

						urls.append([d, url, utf, prfx])
						u += 1

						if did and dtp:
							urls.append([
								d
							,	url.rsplit('.', 1)[0] + '.gif'
							,	utf.rsplit('.', 1)[0] + '.gif'
							,	prfx
							])
							u += 1

						if TEST and u > 1:
							break
		new_meta += meta + line_separator

	if lvl < 1:
		print('')

	return urls

def get_response(req):
	hostname = re.search(pat_host, req).group('Domain')
	headers = { 'Accept-Encoding' : accept_enc } if accept_enc else {}
	data = []

	for batch in add_headers_to:
		for s in batch[0]:
			if (hostname if s.find('/') < 0 else req).find(s) >= 0:
				h = batch[1]
				if hasattr(h, 'update'):
					headers.update(h)
				else:
					data.append(h)
				break

	if headers:
		try_print(colored('Request headers:', 'yellow'), headers)

	if data:
		try_print(colored('POST:', 'yellow'), data)
	else:
		data = None

	if headers:
		req = Request(req, data, headers)

	return urlopen(req, data, timeout_request, context=false_ctx)

def get_by_caseless_key(dic, k):
	k = k.lower()
	for i in dic:
		if i.lower() == k:
			return dic[i]
	return ''

def redl(url, regex, msg=''):
	if msg:
		try_print(colored(msg, 'yellow'), url)

	response = get_response(url)
	content = response.read()
	headers = response.info()

	print('')
	try_print(colored('Response headers:', 'yellow'), headers)

	match = re.search(regex, content)
	if match:
		return match.group(1)
	else:
		raise URLError(content)

def get_reason_why_file_not_to_save(
	content=None
,	etag=None
,	file_url=None
,	filename=None
,	filesize=None
):
	if (
		content is None
	and	etag is None
	and	file_url is None
	and	filename is None
	and	filesize is None
	):
		return

	if filesize is not None and filesize <= 0:
		return 'filesize = ' + str(filesize)

	for rule_set in file_not_to_save:
		try:
			if filesize is not None:
				t = rule_set.get('content_size')
				if t and t != filesize:
					continue

			if etag is not None:
				t = rule_set.get('header_etag')
				if t and t != etag:
					continue

			if file_url is not None:
				t = rule_set.get('url_part')
				if t and file_url.find(t) < 0:
					continue

			if filename is not None:
				t = rule_set.get('name_part')
				if t and filename.find(t) < 0:
					continue

			if content is not None:

				# Note: To generate the same numeric value across all Python versions and platforms, use crc32(data) & 0xffffffff.
				# https://docs.python.org/3/library/zlib.html#zlib.crc32

				t = rule_set.get('content_crc32')
				if t and t != (zlib.crc32(content) & 0xffffffff):
					continue

				t = rule_set.get('content_md5')
				if t and t != hashlib.md5(content).hexdigest():
					continue

				t = rule_set.get('content_sha1')
				if t and t != hashlib.sha1(content).hexdigest():
					continue

			return get_obj_pretty_print(rule_set)

		except Exception as e:
			write_exception_traceback()


def is_url_blocked(url=None, content=None):
	if url:
		for p in pat_blocked_url:
			if p.search(url):
				return True
	if content:
		for p in pat_blocked_content:
			if p.search(content):
				return True
	return False

def pass_url(app, url):
	global urls_passed

	if url in urls_passed:
		return 0

	urls_passed.add(url)

	k = app.strip(dest_app_sep)
	app_path = dest_app[k if k in dest_app else dest_app_default]

	try:
		try_print('Passing URL (as is) to program,', app, app_path)
		p = subprocess.Popen(
			(app_path + [url]) if isinstance(app_path, a_type) else
			[app_path, url]
		)
		if p:
			print colored('Process ID:', 'magenta'), p.pid

	except Exception as e:
		write_exception_traceback()

		cprint('Unexpected error. See logs.\n', 'red')
		write_file(log_no_response, [log_stamp(), e, empty_line_separator])

	return 1

def process_url(dest_root, url, utf='', unprfx='', prfx=''):
	global urls_done, urls_done_this_time, processed
	processed += 1
	finished = recheck = 0

	if not len(re.sub(pat_synt, '', url)) or (url in urls_done_this_time):
		return 0

	hostname = re.search(pat_host, url)
	if hostname:
		protocol = hostname.group('Protocol')
		if not utf:
			utf = url
		if not protocol:
			protocol = 'http://'
			url = protocol + url
		hostname = hostname.group('Domain')
		for s in url_to_skip:
			if meet(hostname if is_type_str(s) and s.find('/') < 0 else url, s):

				write_file(log_skipped, [log_stamp(), utf, line_separator])
				hostname = 0

				break
	if not hostname:
		return 0

	if dest_root[-1 : ] == dest_app_sep or os.path.isfile(dest_root):
		return pass_url(dest_root, url)

	urls_done_this_time.add(url)				# <- so it won't recursively recheck same link in endless cycle

	if url in urls_done:
		for p in pat2recheck_next_time:
			if p.search(url):
				recheck = 1

				break

		if not recheck:
			return 0
	else:
		urls_done.add(url)				# <- add to skip list

		try:
			log_path = time.strftime(log_all_urls) if '%' in log_all_urls else log_all_urls

		except Exception:
			log_path = log_all_urls

		write_file(log_path, [log_stamp(), get_path_without_local_prefix(dest_root), tab_separator, url, line_separator])

	finished = 1
	udl = url
	for p in pat2replace_before_dl:
		if len(p) > 1:
			udl = re.sub(p[0], p[1], udl)		# <- fix urls to DL
	udn = [utf, line_separator]+([udl, line_separator] if udl != url else [])

	try:
		try_print(colored('Downloading:', 'yellow'), udl)
		req = ('l/?'+udl) if TEST else udl

		if hostname == 'db.tt':
			response = get_response(req)
			req = response.geturl()
			headers = response.info()

			print('')
			try_print(colored('Response headers:', 'yellow'), headers)

			if req == udl:
				req = redl(get_proxified_url(udl), pat_href, 'Expected redirect, got dummy. Trying proxy:')

		response = get_response(req)

	except HTTPError as e:
		print colored('Server could not fulfill the request. Error code:', 'red'), e.code, '\n'

		headers = e.headers or e.hdrs

		if headers:
			try_print(colored('Response headers:', 'red'), headers)

		write_file(log_no_file, [log_stamp(), '%d' % e.code, tab_separator]+udn)

		if (
			e.code > 300
		and	e.code < 400
		):
			write_file(log_no_file, [e, empty_line_separator])

		udl_trim = re.sub(pat_trim, '', udl)

		if udl != udl_trim:
			cprint('Retrying after trim:\n', 'yellow')
			finished += process_url(dest_root, udl_trim)

		elif (
			e.code != 404
		and	e.code > 400
		and	e.code < 500
		and	udl.find(default_web_proxy) != 0
		):
			cprint('Retrying with proxy:\n', 'yellow')
			finished += process_url(dest_root, get_proxified_url(udl))

	except Exception as e:
		write_exception_traceback()

		cprint('Unexpected error. See logs.\n', 'red')
		write_file(log_no_response, [log_stamp()]+udn+[e, empty_line_separator])

		if udl.find('http://') != 0:
			cprint('Retrying with plain http:\n', 'yellow')
			finished += process_url(dest_root, re.sub(pat_badp, 'http://', udl), unprfx=udl)

		elif udl.find(default_web_proxy) != 0:
			cprint('Retrying with proxy:\n', 'yellow')
			finished += process_url(dest_root, get_proxified_url(unprfx or udl))
	else:
		try:
			urldest = response.geturl()
			headers = response.info()
			content = response.read()

		except Exception as e:
			write_exception_traceback()

			cprint('Unexpected error. See logs.\n', 'red')
			write_file(log_no_response, [log_stamp()]+udn+[e, empty_line_separator])
		else:
			filesize = len(content)

			# uncompress file content:

			decoded_content = None

			encoding_type = get_by_caseless_key(headers, 'Content-Encoding').lower()
			try:
				if brotli is not None and encoding_type == 'br':
					decoded_content = brotli.decompress(content)

				elif zlib is not None and encoding_type == 'deflate':
					decoded_content = zlib.decompress(content)

				elif gzip is not None and encoding_type == 'gzip':
					i = StringIO.StringIO(content)
					o = gzip.GzipFile(fileobj=i)
					decoded_content = o.read()

			# except Exception as e:
			except (IOError, ValueError) as e:
				write_exception_traceback()

				write_file(log_no_file, [log_stamp()]+udn+[e, empty_line_separator])

			if decoded_content is not None:
				decoded_size = len(decoded_content)
				compression_ratio = 100.0 * filesize / decoded_size

				try_print(
					colored('Decompressed:', 'yellow')
				,	'{enc_type} from {enc_size} to {dec_size} bytes, compression ratio {ratio:.2f}%'.format(
						enc_type=encoding_type
					,	enc_size=filesize
					,	dec_size=decoded_size
					,	ratio=compression_ratio
					)
				)

				headers['X-Downloaded-Content-Length'] = str(filesize)
				headers['X-Decoded-Content-Length'] = str(decoded_size)

				content = decoded_content
				filesize = decoded_size

			# check result:

			if urldest != url:
				try_print(colored('Request URL:', 'yellow'), urldest)

				if is_url_blocked(urldest, content):
					write_file(log_blocked, [log_stamp(), 'blocked	']+udn)

					cprint('Blocked page, retrying with proxy:\n', 'yellow')
					finished += process_url(dest_root, get_proxified_url(udl))
			else:
				urldest = ''

			print('')
			try_print(colored('Response code:', 'yellow'), response.code)
			try_print(colored('Response headers:', 'yellow'), headers)

			urls_to_log = [url]

			if utf and utf != url and utf.find('/') >= 0:
				urls_to_log.append('Text URL: ' + utf)

			if urldest and urldest != url:
				urls_to_log.append('Dest URL: ' + urldest)

			write_file(
				log_completed
			,	line_separator.join([
					'{time}{urls}'
				,	''
				,	'Response code: {code}'
				,	'Response headers:'
				,	'{headers}'
				,	''
				]).format(
					time=log_stamp()
				,	urls=line_separator.join(urls_to_log)
				,	code=response.code
				,	headers=headers
				)
			)

			dest = url.rstrip('/')

			if prfx:
				dest = prfx + (
					dest.rsplit('/', 1)[1]
					if prfx[-3 : ] == ' - ' else
					' - ' + dest
				)

			dest = dest.split('#', 1)[0]
			dest = fix_filename_before_saving(dest)

			filename_in_header = get_by_caseless_key(headers, 'Content-Disposition')
			if filename_in_header:
				match = re.search(pat_cdfn, filename_in_header)
				if match:
					filename_in_header = match.group(1)
					d = fix_filename_before_saving(filename_in_header)

					try:
						if d and dest.find(d) < 0:
							if udl.find(default_web_proxy) == 0:
								dest = d
							else:
								dest += ' - '+d

					except Exception:
						write_exception_traceback()

						cprint('<filename appending error>', 'red')

			ext = '' if dest.find('.') < 0 else dest.rsplit('.', 1)[1].lower()
			d = dest_root+'/'

			content_type = get_by_caseless_key(headers, 'Content-Type').split(';', 1)[0].lower()
			if content_type:
				media, format = (content_type, '') if content_type.find('/') < 0 else content_type.split('/', 1)
				is_ext_not_in_format = not any((ext in format.split(s)) for s in content_type_separators)
				is_amp_in_ext = bool(re.search(pat_exno, ext))
				subd = 'etc'
				add_ext = ''

				if media == 'text':
					if format == 'plain':
						add_ext = 'txt'

					elif (
						ext != 'txt'
					and	ext.find('htm') < 0
					):
						add_ext = 'htm'

				elif (
					media == 'video'
				or	media == 'audio'
				or	media == 'application'
				):
					if format == 'x-javascript':
						add_ext = 'js'

					elif (
						is_ext_not_in_format
					and	format[0 : 2] != 'x-'
					and	format != 'octet-stream'
					):
						add_ext = format

				elif media == 'image':
					subd = 'pix'

					if (
						format == 'jpg'
					or	format == 'jpeg'
					):
						if (
							ext != 'jpg'
						and	ext != 'jpeg'
						):
							add_ext = 'jpg'

					elif is_ext_not_in_format:
						add_ext = format

				elif is_ext_not_in_format:
					for x in exts_to_add_from_content_type:
						if x in format:
							add_ext = x

							break

				else:
					for x in exts_to_add_from_url:
						if udl.find('.' + x) > 0:
							add_ext = x

							if x in known_image_exts:
								subd = 'pix'

							break

				if add_ext and (
					is_amp_in_ext
				or	ext.find(add_ext) < 0
				):
					dest += '.'+add_ext

				if subd:
					d += subd+'/'

			dest = fix_filename_before_saving(dest)

			if add_time:
				time_text = None
				if 'm' in flags:
					time_text = get_by_caseless_key(headers, 'Last-Modified').lower()

					if time_text:
						time_text = get_timestamp_from_http_modtime(time_text, add_time_fmt)
				else:
					time_text = timestamp_now(add_time_fmt)

				if time_text:
					a = -1
					if 's' in flags:
						if dest.find('.') < 0:
							a = 1
						else:
							a = 0
							dest = (add_time_j + time_text + '.').join(dest.rsplit('.', 1))
					if 'a' in flags or a > 0:
						a = 0
						dest += add_time_j + time_text
					if 'p' in flags or a < 0:
						dest = time_text + add_time_j + dest

			if not os.path.exists(d):
				os.makedirs(d)

			f = d

			try:
				f += fix_filename_before_saving(dest)

			except Exception as e:
				write_exception_traceback()

				try:
					f += dest.replace('/', ',')

				except Exception:
					write_exception_traceback()

					f += sanitize_filename(dest)

			# got destination path and content.
			# check if result is needed to save:

			filename = f.rsplit('/', 1)[-1 : ][0]
			file_url = urldest or udl
			etag = get_by_caseless_key(headers, 'ETag')
			saved = extracted_file = extracted_files = None

			why_not_save = get_reason_why_file_not_to_save(
				content=content
			,	etag=etag
			,	file_url=file_url
			,	filename=filename
			,	filesize=filesize
			)

			if not why_not_save:
				cprint('Cutting extraneous data:', 'yellow')

				try:
					extracted_files = get_extracted_files([
						content
					,	filename
					# ,	'--in-folder'
					,	'--truncate'
					,	'--truncate-num'
					,	'--truncate-hex'
					,	'--picture'
					])

				except Exception as e:
					write_exception_traceback()

					cprint('Failed cutting extraneous data.', 'red')

				print('')

				if (
					not extracted_files
				# or	not is_type_arr(extracted_files)
				or	is_type_int(extracted_files)
				):
					extracted_file = False

				elif len(extracted_files) > 0:

					extracted_file = extracted_files[0]

					if is_type_dic(extracted_file) and (
						filename != extracted_file['name']
					or	filesize != extracted_file['size']
					):
						old_filename_length = len(filename)
						content = extracted_file['content']
						filename = extracted_file['name']
						filesize = extracted_file['size']

						why_not_save = get_reason_why_file_not_to_save(
							content=content
						,	filename=filename
						,	filesize=filesize
						)

						if not why_not_save:
							f = (
								(
									f[ : -old_filename_length]
									# .rstrip('/.')
									+ '/'
									+ filename
								) if len(f) > old_filename_length
								else filename
							)
					else:
						extracted_file = True

			# save this file:

			if why_not_save:
				try_print(colored('Not saved, reason:', 'red'), why_not_save)

				write_file(log_not_saved, [log_stamp()]+udn+[why_not_save, empty_line_separator])
			else:
				try:
					saved = save_uniq_copy(f, content)

					if saved == False:
						saved = f
						try_print(colored('Same as existing copy:', 'yellow'), saved)
					elif saved:
						try_print(colored('Saved to:', 'yellow'), saved)
					else:
						try:
							try_print(colored('Tried to', 'red'), f)
						except Exception as e:
							cprint('Tried to <Unprintable>', 'red')

						write_file(log_not_saved, [log_stamp()]+udn+[
							'Tried path: ', f, line_separator
						,	'Saved path: ', saved, empty_line_separator
						])

				except Exception as e:
					write_exception_traceback()

					try:
						try_print(colored('Save to', 'yellow'), f)
					except Exception as e:
						cprint('Save to <Unprintable>', 'red')

					try_print(colored('failed with error:', 'red'), e)

					write_file(log_not_saved, [log_stamp()]+udn+[e, empty_line_separator])

			if saved and extracted_file is None:
				cprint('Cutting extraneous data:', 'yellow')

				try:
					run_batch_extract([
						saved
					# ,	'-defmpnx'
					,	'--in-folder'
					,	'--truncate'
					,	'--truncate-num'
					,	'--truncate-hex'
					,	'--picture'
					,	'--keep-time'
					,	'--remove-old'
					])

				except Exception as e:
					write_exception_traceback()

					cprint('Failed cutting extraneous data.', 'red')

				print('')

			# check new links found on the way:

			for p in pat2recursive_dl:
				r2 = re.search(p['page'], file_url)
				if r2:
					pat_grab = p.get('grab')
					pat_link = p.get('link')
					pat_name = p.get('name', default_red2_name_prefix)

					if pat_link and not pat_grab:
						for x in get_as_list(pat_link):
							try:
								url2 = r2.expand(x)
								if url2 and not url2 == x:
									url2 = get_prereplaced_url(url2, hostname, protocol)

									try_print(colored('Sub-URL from URL:', 'yellow'), dest_root, url2)

									finished += process_url(dest_root, url2)

									break

							except Exception:
								write_exception_traceback()

								cprint('<re: skipped unmatched group in source link>', 'red')
						break

					try:
						p2 = (
							pat_grab					if is_type_reg(pat_grab) else
							get_rei(r2.expand(pat_grab))			if is_type_str(pat_grab) else
							get_rei(r2.expand(pat_grab[0]), pat_grab[1])	if is_type_arr(pat_grab) else
							pat_href
						)

					except Exception:
						write_exception_traceback()

						cprint('<re: skipped unmatched group in source link>', 'red')
						p2 = pat_href

					try_print(colored('Recurse target pattern:', 'yellow'), type(pat_grab), p2.pattern)

					for d2 in re.finditer(p2, content):
						prfx = ''
						if pat_name:
							for x in pat_name:
								try:
									z = x[0]

									prfx += re.sub(
										pat_sub_counter
									,	str(processed+z)
									,	x[1]
									) if z < 0 else (
										r2 if z == 0 else
										d2 if z == 1 else
										re.search(z, content)
									).expand(x[1])

								except Exception:
									write_exception_traceback()

									if TEST: cprint('<re: skipped unmatched group in dest.link>', 'red')
						url2 = ''
						if pat_link:
							for x in get_as_list(pat_link):
								try:
									url2 = d2.expand(x)

								except Exception:
									write_exception_traceback()

									if TEST: cprint('<re: skipped unfulfilled link pattern>', 'red')

								if url2:
									break
						if not url2:
							url2 = ''.join(d2.groups(''))

						url2 = get_prereplaced_url(url2, hostname, protocol)

						try_print(colored('Sub-URL from grab:', 'yellow'), dest_root, prfx, url2)

						finished += process_url(dest_root, url2, prfx=prfx)

					break

			for p in pat2open_in_browser:
				url2 = file_url
				p2 = None
				if len(p) > 1:
					p2 = p[1]
					if not is_type_str(p2):
						url2 = url
				r2 = re.search(p[0], url2)
				if r2:
					if is_type_str(p2):
						url2 = r2.expand(p2)
					pass_url(dest_app_default, url2)

					break
	if wait:
		cprint('%s Waiting for %d sec. after each download attempt.\n' % (timestamp(), wait), 'cyan')
		time.sleep(wait)

	return finished

# Prepare to run --------------------------------------------------------------

urls_passed = set()
urls_done = set()

url_log_files = (
	glob.glob(
		re.sub(pat_placeholders, '*', log_all_urls)
		if '%' in log_all_urls
		else log_all_urls
	) if (
		'*' in log_all_urls
	or	'?' in log_all_urls
	or	'%' in log_all_urls
	) else
	[ log_all_urls ]
)

cprint('Reading already done URLs:', 'yellow')

count_urls_done_in_all_old_files = 0

for log_file_path in url_log_files:
	count_urls_done_in_old_file = 0

	for line in read_file(log_file_path).split(line_separator):
		if tab_separator in line:
			url = line.rsplit(tab_separator, 1)[-1 : ][0]
			urls_done.add(url)

			count_urls_done_in_old_file += 1
			count_urls_done_in_all_old_files += 1

	print log_file_path, count_urls_done_in_old_file

print colored('Preloaded total URLs:', 'yellow'), count_urls_done_in_all_old_files
print colored('Preloaded unique URLs:', 'yellow'), len(urls_done)

if 'l' in flags:
	for url in urls_done:
		url = get_prereplaced_url(url)
		urls_passed.add(url)

	urls_done = urls_passed
	urls_passed = set()

	print colored('Normalized unique URLs:', 'yellow'), len(urls_done)

count_urls_done_this_run = new_meta = old_meta = i = 0

# Run in endless cycle until interrupted --------------------------------------

while 1:
	i += 1
	cprint('%s Reading logs # %d #, URLs found: %d, done: %d' % (timestamp(), i, len(urls_done), count_urls_done_this_run), 'yellow')

	new_meta = ''
	old_meta = []

	for line in read_file(log_last_pos).decode(default_encoding).split(line_separator):
		if tab_separator in line:
			old_meta.append(line.split(tab_separator))

	if TEST:
		cprint(default_encoding, 'magenta')
		cprint(log_last_pos, 'cyan')
		print(old_meta)

		break

	changes = count_urls_done_this_round = count_urls_to_do = 0
	urls_done_this_time = set()

	for p in read_paths:
		lines = read_path(p[0], p[1])
		count_urls_to_do += len(lines)

		for line in lines:
			processed = 0
			finished = process_url(*line)

			if finished:
				if finished > 1:
					count_urls_to_do += finished - 1

				count_urls_done_this_round += finished

				cprint('(done in this round: %d / %d)\n' % (count_urls_done_this_round, count_urls_to_do), 'green')

			if TEST and count_urls_done_this_round > 1:
				break

	count_urls_done_this_run += count_urls_done_this_round

	if changes and new_meta:
		write_file(log_last_pos, new_meta.encode(default_encoding), 'w')

	if interval:
		cprint('%s Sleeping for %d sec. Press Ctrl+C to break.' % (timestamp(), interval), 'cyan')

		try:
			time.sleep(interval)

		except KeyboardInterrupt:
			sys.exit(0)

		except Exception:
			write_exception_traceback()
	else:
		cprint('Done.', 'green')

		break

# - End -----------------------------------------------------------------------
