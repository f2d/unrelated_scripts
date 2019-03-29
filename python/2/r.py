#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import datetime, os, re, sys, zipfile

argc = len(sys.argv)

ext_web = ['htm', 'html', 'maff', 'mht', 'mhtml']
k = 'cut'
if argc < 2 or sys.argv[1][0] == '-' or sys.argv[1][0] == '/':
	print '* Usage: r.py [flags] [other] [options] [etc] ...'
	print
	print '* Flags (add in any order without spaces as first argument):'
	print '	t: for test output only (don\'t apply changes)'
	print '	f: full path length check'
	print '	o: full path output'
	print '	r: source working folder recursion'
	print
	print '	w: move web page archive files ('+'/'.join(ext_web)+') by URL in file content'
	print '	d: move booru-grabbed duplicates into subdir by md5 in filename, keep oldest'
	print '	b: move aib-grabbed files into subdir by thread ID in filename'
	print '	p: move pixiv-grabbed files into subdir by work ID in filename'
	print '	y: rename Complete YouTube Saver downloads in sub/same-folder by ID in URL and filenames'
	print
	print '* Other options (separate each with a space):'
	print '	'+k+' or '+k+'<number>: first cut long names to specified length (default = 123)'
	print
	print '* Example 1: r.py rwb'
	print '* Example 2: r.py tfo '+k+'234'
	sys.exit()

dest_root = u'd:/_bak/_www/'

flags = sys.argv[1]

TEST = 't' in flags
DO = not TEST

arg_f = 'f' in flags
arg_o = 'o' in flags
arg_r = 'r' in flags

arg_web = 'w' in flags
arg_dup = 'd' in flags
arg_aib = 'b' in flags
arg_pxv = 'p' in flags
arg_ytb = 'y' in flags

j = len(k)
if k in sys.argv:
	arg_len = 123		# <- pass 'cut' or 'cut123' for longname cutting tool; excludes move to folders
else:
	arg_len = 0
	for a in sys.argv:
		if a[0:j] == k:
			arg_len = int(a[j:])
			break

#--[ reusable rule parts ]-----------------------------------------------------

part_protocol = r'^(?:\w+:/+)?'
part_domain_www = r'(?:www\.|(?!www\.))'
part_domain = r'''
(?P<All>
	(?P<AllOver2>
		(?P<LastOver2>[^/?#\s.]+)
		(?P<DotNotLastOver2>
			[.]+
			(?P<NotLastOver2>
				[^/?#\s.]
				(?:[.]+[^/?#\s.]+)*
			)
		)?
	)
	(?P<TopBoth>
		(?P<Top2nd>[.]+[^/?#\s.]+)
		(?P<Top>[.]+[^/?#\s.]+)
	)
)
(?:[/?#]|$)
'''

pat_subdomain_inc_www = re.compile(part_protocol                   + part_domain, re.I | re.X)	# <- to treat "www" like a separate subdomain
pat_subdomain_exc_www = re.compile(part_protocol + part_domain_www + part_domain, re.I | re.X)	# <- to discard "www", if any

pat_tail_dup_name = re.compile(r'(-\d+|\s*\(\d+\)|;_[\d,_-]+)?(\.[^.]+$)', re.I)
pat_tail_google = re.compile(r'( - [^-]*?Google)([\s,(;-].*?)?(\.[^.]+$)', re.I)

subscrape = {'sub_threads': '_scrape'}
unscrape = '!_unscrape,roots,etc'

sub_a = [
	[unscrape+'/_arch'	,re.compile(r'^[^/?#]+/arch/res/+([?#]|$)', re.I)]
,	[unscrape+'/_catalog'	,re.compile(r'^[^/?#]+/catalog', re.I)]
,	[unscrape+'/_rules'	,re.compile(r'^([^/?#]+/)?rules', re.I)]
]

sub_b = [
	[unscrape+'/_boards']
,	unscrape
]

sub_d = [
	[unscrape+'/_d',['d']]
]+sub_b

sub_nyaa = [
	['_search'	,['?','page=search']]
,	['_torrent_info',['view','page=view','page=torrentinfo']]
,	['_browse'	,['user','page=separate','page=torrents']]
,	[pat_subdomain_inc_www, r'_browse/\3']
,	'_browse'
]

#--[ table of rule cases selected by site ]------------------------------------
# To match exact full name and not subparts (like "*.name") set domain string as "name."

# Note:
# Some parts of this table were cut out in public version.
# Others were left mostly as example.
# Feel free to use them as such and throw away everything unneeded.

sites = [

#--[ local ]-------------------------------------------------------------------

	[re.compile(r'^(192\.168\.(\d+\.)*9|127\.(0\.)*\d+|localhost|l|a)(:\d+)?\.$'		, re.I),'!_LAN,intranet/localhost']
#,	[re.compile(r'^(192\.168\.(\d+\.)*1|r\d*|www\.asusnetwork\.net|router\.asus\.com)\.$'	, re.I),'!_LAN,intranet/router/ASUS_RT-AC58U']
#,	[re.compile(r'^(r|d-?(link)?|dir-?(100|120)|192\.168\.[01]\.(1|100|120))$'		, re.I),'!_LAN,intranet/router/D-Link_DIR-120']
#,	[['192.168.1.99'		],'!_LAN,intranet/printer/MG_3040']

#--[ global ]------------------------------------------------------------------

,	[['archive.today','archive.ec','archive.fo','archive.is','archive.li'			],'_archives//']
,	[['archive.org','archiveteam.org','mementoweb.org','peeep.us','perma.cc','web-arhive.ru'],'_archives/']

#--[ chats ]-------------------------------------------------------------------

,	[['slack.com'						],'_conf/',{'sub': [[pat_subdomain_exc_www, r'_subdomain/\1']]}]
,	[re.compile(r'(^|\.)slack(hq)?\.\w+$', re.I		),'_conf/slack.com/']
,	[['discord.gg','discord.pw'				],'_conf/discordapp.com/']
,	[
		['discordapp.com']
	,	'_conf/'
	,	{
			'sub': [
				[re.compile(r'^/+channels?/+(\d+)([/?#]|$)', re.I), r'_channels/\1']
			]
		}
	]

#--[ stuff ]-------------------------------------------------------------------

,	[re.compile(r'(^|\.)d(eposit)?files\.\w+$', re.I	),'_fileshares/depositfiles.com']
,	[re.compile(r'(^|\.)freakshare\.\w+$', re.I		),'_fileshares/freakshare.com']
,	[re.compile(r'(^|\.)rapidshare\.\w+$', re.I		),'_fileshares/rapidshare.com']
,	[re.compile(r'(^|\.)rgho(st)?\.\w+$', re.I		),'_fileshares/rghost.ru']
,	[['dropbox.com','dropboxusercontent.com','db.tt'	],'_fileshares//']
,	[['ifolder.ru','rusfolder.com','rusfolder.net'		],'_fileshares//']
,	[['pomf.se','uguu.se','pomf.cat','pantsu.cat','1339.cf'	],'_fileshares//']
,	[['safe.moe','catbox.moe'				],'_fileshares//']
,	[['yadi.sk','disk.yandex.ru'				],'_fileshares//']
,	[['zalil.ru','slil.ru','gfile.ru'			],'_fileshares//']
,	[
		['mega','mega:','mega.co.nz','mega.nz','megaupload.com','96d0d4e7-1ed7-4efb-99d0-b1bd780800b3']
	,	'_fileshares//'
	,	{
			'sub': [
				['_file'	,re.compile(r'^([^!#]*#+)?(!.+)$'	, re.I), r',#\2']
			,	['_folder'	,re.compile(r'^([^!#]*#+)?(F!.+)$'	, re.I), r',#\2']
			]
		}
	]
,	[
		[	'2shared.com','4shared.com','anonfiles.com','anonymousdelivers.us','aww.moe'
		,	'bitcasa.com','bitshare.com','bowlroll.net','box.com','doko.moe','dropmefiles.com','embedupload.com'
		,	'fayloobmennik.cloud','filecloud.me','filedwon.info','filefactory.com','fileplanet.com','filesmelt.com','firedrop.com'
		,	'ge.tt','ichigo-up.com','ipfs.io','littlebyte.net'
		,	'mediafire.com','mixtape.moe','multcloud.com','my-files.ru','nofile.io','nya.is'
		,	'rapidgator.net','sendspace.com','solidfiles.com','storagon.com'
		,	'topshape.me','turbobit.net','upload.cat','uploadable.ch','uploaded.net','vocaroo.com','webfile.ru','zippyshare.com'
		]
	,	'_fileshares/'
	]

#--[ pictures ]----------------------------------------------------------------

,	[
		['deviantart.com','sta.sh']
	,	'_img//'
	,	{
			'sub': [
				[pat_subdomain_exc_www, r'_mht/_personal/\3']
			,	'_mht'
			]
		}
	]
,	[['booth.pm','chat.pixiv.net','dic.pixiv.net','pawoo.net','pixiv.help','pixivision.net','sketch.pixiv.net','spotlight.pics'],'_img/pixiv.net/']
,	[
		['pixiv.net','pixiv.com','pixiv.me','p.tl']
	,	'_img//'
	,	{
			'sub': [
				['_mht/member/follow'	,re.compile(r'^/+bookmark\.php\?([^&]*&)*type=user&*([^&]*&)*(id=\d+)'	, re.I), r',u\3']
			,	['_mht/member/bookmark'	,re.compile(r'^/+bookmark\.php\?([^&]*&)*(id=\d+)'		, re.I), r',u\2']
			,	['_mht/bookmark/tag'	,re.compile(r'^/+bookmark\.php\?([^&]*&)*(tag=[^&]*)'		, re.I), r',\2']
			,	['_mht/bookmark/add'	,re.compile(r'^/+bookmark_add\.php\?([^&]*&)*(id=\d+)'		, re.I), r',illust_\2,added']
			,	['_mht/bookmark/add'	,re.compile(r'^/+bookmark_add\.php\?([^&]*&)*(illust_id=\d+)'	, re.I), r',\2,add']
			,	['_mht/illust'		,re.compile(r'^/+member_illust\.php\?([^&]*&)*(illust_id=\d+)'	, re.I), r',\2']
			,	['_mht/member/illust'	,re.compile(r'^/+member_illust\.php\?([^&]*&)*(id=\d+)'		, re.I), r',u\2']
			,	['_mht/member/profile'	,re.compile(r'^/+member\.php\?([^&]*&)*(id=\d+)'		, re.I), r',u\2']
			,	['_mht/mypage'		,re.compile(r'^/+mypage\.php\?([^&]*&)*(id=\d+)'		, re.I), r',u\2']
			,	['_mht/member/novel'	,re.compile(r'^/+novel/member\.php\?([^&]*&)*(id=\d+)'		, re.I), r',u\2']
			,	['_mht/novel'		,re.compile(r'^/+novel/([^?]*\?)+([^&]*&)*(id=\d+)'		, re.I), r',novel_\3']
			,	['_mht/bookmark'	,['bookmark.php','bookmark_add.php','bookmark_detail.php']]
			,	['_mht/member/by_tag'	,['personal_tags.php']]
			,	['_mht/msg'		,['msg_view.php']]
			,	['_mht/search'		,['search.php']]
			,	['_mht/feed'		,['stacc']]
			,	['_mht/ranking'		,['ranking.php']]
			,	['_mht/redirects'	,['jump.php']]
			,	'_mht'
			]
		}
	]
,	[['gramunion.com','studiomoh.com'],'_img/tumblr.com/']
,	[['media.tumblr.com'		],'_img/tumblr.com/_pix']
,	[['txmblr.com','www.tumblr.com'	],'_img/tumblr.com',{'sub': [['_video',['video']],'_mht']}]
,	[['tumblr.com'			],'_img/tumblr.com/_mht/_personal',{'sub': [['_post',['post']],'_subdomain']}]
,	[
		['4chan.org','4channel.org']
	,	'_img/_board//'
	,	{
			'sub_threads': [
				['_e_ - Ecchi',['e','h','u']]
			,	'_etc'
			]
		,	'sub': sub_b
		}
	]
,	[
		[	'4archive.org','4chanarchive.org','4plebs.org','archive.moe','archived.moe'
		,	'desuarchive.org','desustorage.org','fireden.net','foolz.us','loveisover.me','nyafuu.org','plus4chan.org'
		,	'rebeccablacktech.com','thisisnotatrueending.com','warosu.org','yuki.la'
		]
	,	'_img/_board/4chan.org/_etc_archive/'
	]
,	[
		re.compile(r'((^|\.)410chan\.\w+|^95\.211\.122\.44)$', re.I)
	,	'_img/_board/410chan.ru'
	,	{
			'sub_threads': [
			#	[None		,['d','errors']]
				[None		,['errors']]
			,	'_scrape'
			]
		,	'sub': sub_a+[
				[unscrape	,re.compile(r'^err(or(s)?)?/|^[^/?#]+/arch/res/+([?#]|$)|^\.[\w-]+(/|$)|^[\w-]+\.\w+([?#]|$)', re.I)]
			]
			# +sub_d
			+sub_b
		}
	]
,	[re.compile(r'(^|\.)dobrochan\.\w+$', re.I		),'_img/_board/dobrochan.ru',{'sub_threads': '_scrape', 'sub': sub_a+sub_b}]
,	[
		['hiichan.org','hiichan.ru','hii.pm']
	,	'_img/_board/iichan.ru'
	,	{
			'sub_threads': '_h_ - Hentai'
		,	'sub': unscrape+'/_h'
		}
	]
,	[
		[	'2007.iichan.hk','2od.ru','old.iichan.ru','ffggchan.appspot.com'
		,	'ii-search.appspot.com','iichan.moe','unylwm.appspot.com','yakuji.moe'
		]
	,	'_img/_board/iichan.ru/!_undelete,mirrors,etc/'
	]
,	[
		['iichan.ru','iichan.hk','haruhiism.net','95.211.138.158']
	,	'_img/_board//'
	,	{
			'sub_threads': [
				[None				,re.compile(r'^/+(cgi-bin|d|err)/|^/+[^/?#]+/arch/res/+([?#]|$)', re.I)]
			,	[re.compile(r'^[^#]*#(.*[^/.])[/.]*$'), r'!_tar,thread_archives/\1']
			,	['_a_ - Anime'			,['a','aa','abe','azu','c','dn','fi','hau','ls','me','rm','sos']]
			,	['_b_ - Bred'			,['b']]
			,	['_h_ - Hentai'			,['g','h']]
			,	['_hr_ - HiRes & requests'	,['hr','r']]
			,	['_m_ - Macros & mascots'	,['m','misc','tan','tenma']]
			,	['_to_ - Touhou'		,['to']]
			,	['_n_prev'			,['n']]
			,	'_etc'
			]
		,	'sub': sub_a+[
			#	[unscrape+'/_h'			,re.compile(r'(^|\w+\.)hii(chan)?\.\w+/', re.I)]
				[unscrape+'/_n'			,['n','index','index.html','']]
			,	[unscrape			,['cgi-bin','err']]
			,	[unscrape			,re.compile(r'^/+[^/?#]+([?#]|$)', re.I)]
			]+sub_d
		}
	]
,	[
		['donmai.us','idanbooru.com']
	,	'_img/_booru//'
	,	{
			'sub': [
				['posts'		, re.compile(r'^(/+mobile)?/+posts?/(show[/?]+)?(\d+)', re.I)]
			,	['posts/comments'	,['comment','comments']]
			,	['posts/pools'		,['pool','pools']]
			,	['posts/search'		,['post','posts']]
			,	['tags'			,['tag','tags','tag_alias','tag_aliases','tag_implication','tag_implications']]
			,	['tags/artists'		,['artist','artists']]
			,	['static'		,['static']]
			,	['static/help'		,['help']]
			,	['forum'		,['forum','forum_post','forum_posts','forum_topic','forum_topics']]
			,	['users'		,['user','users']]
			,	['users/messages'	,['dmail','dmails','message','messages']]
			,	['users/favorites'	,['favorite','favorites']]
			,	['wiki'			,['wiki','wiki_page','wiki_pages']]
			,	['mobile'		,['mobile']]
			]
		}
	]
,	[['booru.org'			],'_img/_booru/',{'sub': [[pat_subdomain_exc_www, r'_subdomain/\3']]}]

,	[['whatanime.ga','trace.moe'						],'_img/_search//']
,	[['everypixel.com','iqdb.org','saucenao.com','tineye.com'		],'_img/_search/']

#--[ society ]-----------------------------------------------------------------

,	[['poll-maker.com','pollcode.com','roi.ru','rupoll.com','simpoll.ru','strawpoll.me'],'_poll/']

,	[
		re.compile(r'(^|\.)blogspot(\.com?)?\.\w+$', re.I)
	,	'_soc/blogspot.com'
	,	{
			'sub': [
				[re.compile(r'^(?:\w+:/+)?\d+\.bp\.[^/?#]+(?:/|$)'				, re.I), r'_pix']
			,	[re.compile(r'^(?:\w+:/+)?([^/?#]+\.)?([^/.]+)\.blogspot(\.com?)?\.\w+(?:/|$)'	, re.I), r'_personal/\2']
			]
		}
	]
,	[['stwity.com','twimg.com','twitpic.com','twitrss.me','twpublic.com'	],'_soc/twitter.com/']
,	[
		['twitter.com']
	,	'_soc/'
	,	{
			'sub': [
				[re.compile(r'^(?:\w+:/+)?(?:[^/?#]+\.)twitter\.com/', re.I), '_mht']
			,	[re.compile(r'^(?:\w+:/+)?(?:www\.)?twitter\.com/+([^/?#]+)/+status/', re.I), r'_mht/_personal/\1/_posts']
			,	[re.compile(r'^(?:\w+:/+)?(?:www\.)?twitter\.com/+([^/?#]+)([/?#]|$)', re.I), r'_mht/_personal/\1']
			,	'_mht'
			]
		}
	]

#--[ programs ]----------------------------------------------------------------

,	[
		['python.org']
	,	'_software/_prog/Python/'
	,	{
			'sub': [
				['2',['2']]
			,	['3',['3']]
			]
		}
	]
,	[['diveintopython.net','py-my.ru','pygame.org','pypi.org','python.su','pythonware.com'		],'_software/_prog/Python/']
,	[['ghtorrent.org','github.io','githubuniverse.com','githubusercontent.com'			],'_software/github.com/']
,	[
		re.compile(r'(^|\.)github\.\w+$', re.I)
	,	'_software/github.com'
	,	{
			'sub': [
				[pat_subdomain_exc_www			, r'_subdomain/\3']
			,	['_blog'				, ['blog']]
			,	['_settings,etc'			, ['login','settings','signup']]
			,	['_users/_repositories'
				,	re.compile(r'[^?#]*\?([^&]*&)*tab=repos'			, re.I)
				,	re.compile(r'(\s+\S\s+GitHub( - \w+)?([\s,(;-].*)?)?(\.[^.]+$)'	, re.I)
				,	r' - GitHub Repositories\4'
				]
			,	[re.compile(r'^/+[^/?#]+/([^/?#]+)/+(commit|issue|label|pull)s?', re.I), r'_projects/\1/\2']
			,	[re.compile(r'^/+[^/?#]+/([^/?#]+)(/|$)'			, re.I), r'_projects/\1']
			,	[re.compile(r'^/+[^/?#]+/*([?#]|$)'				, re.I), r'_users']
			]
		}
	]
,	[
		re.compile(r'(^|\.)osdn\.\w+$', re.I)
	,	'_software/osdn.net'
	,	{
			'sub': [
				[re.compile(r'^/+projects?/([^/?#]+)', re.I)	, r'_projects/\1']
			,	[pat_subdomain_exc_www				, r'_projects/\3']
			]
		}
	]
,	[
		re.compile(r'(^|\.)(sourceforge\.\w+|sf.net)$', re.I)
	,	'_software/sf.net'
	,	{
			'sub': [
				['_accounts'							, re.compile(r'^/+(auth|u|user)/', re.I)]
			,	[re.compile(r'^/+(p|projects?|apps?/\w+)/([^/?#]+)', re.I)	, r'_projects/\2']
			,	[pat_subdomain_exc_www						, r'_projects/\3']
			]
		}
	]

#--[ more stuff ]--------------------------------------------------------------

,	[re.compile(r'(^|\.)anidex\.\w+$', re.I			),'_torrents/anidex.info']
,	[re.compile(r'(^|\.)bakabt\.\w+$', re.I			),'_torrents/bakabt.me']
,	[re.compile(r'(^|\.)isohunt\.\w+$', re.I		),'_torrents/isohunt.to']
,	[re.compile(r'(^|\.)nnm-club\.\w+$', re.I		),'_torrents/nnm-club.ru']
,	[re.compile(r'sukebei?\.nyaa\.si$', re.I		),'_torrents/nyaa.si/hentai'	,{'sub': sub_nyaa}]
,	[re.compile(r'(^|\.)nyaa\.si$', re.I			),'_torrents/nyaa.si'		,{'sub': sub_nyaa}]
,	[re.compile(r'files?\.nyaa(torrents)?\.\w+$', re.I	),'_torrents/nyaa.se/static_files']
,	[re.compile(r'forums?\.nyaa(torrents)?\.\w+$', re.I	),'_torrents/nyaa.se/forums']
,	[re.compile(r'sukebei?\.nyaa(torrents)?\.\w+$', re.I	),'_torrents/nyaa.se/hentai'	,{'sub': sub_nyaa}]
,	[re.compile(r'(^|\.)nyaa(torrents)?\.\w+$', re.I	),'_torrents/nyaa.se'		,{'sub': sub_nyaa}]
,	[re.compile(r'(^|\.)(the|old)piratebay\.\w+$', re.I	),'_torrents/thepiratebay.org']
,	[re.compile(r'(^|\.)tokyo-?tosho\.\w+$', re.I		),'_torrents/tokyotosho.info']

#--[ wiki ]--------------------------------------------------------------------

,	[['boltwire.com','dokuwiki.org','foswiki.org','ikiwiki.info','pmwiki.org','trac.edgewall.org','wikimatrix.org'],'_wiki/_soft/']
,	[re.compile(r'(^|\.)encyclopediadramatica\.\w+$', re.I	),'_wiki/encyclopediadramatica.com']
,	[['mrakopedia.ru','mrakopedia.org','barelybreathing.ru'	],'_wiki//']
,	[['scpfoundation.net','scpfoundation.ru'		],'_wiki//']
,	[['traditio.ru','traditio-ru.org'			],'_wiki//']
,	[['wikia.nocookie.net'					],'_wiki/wikia.com/_img']
,	[['fandom.com','wikia.com'			],'_wiki/',{'sub': [[pat_subdomain_exc_www, [
		r'_subdomain/\g<NotLastOver2>/\g<LastOver2>'
	,	r'_subdomain/\g<LastOver2>'
	]]]}]
,	[['wikipedia.org'				],'_wiki/',{'sub': [[pat_subdomain_exc_www, r'_subdomain/\g<LastOver2>']]}]
,	[
		[	'mediawiki.org','wikidata.org','wikimedia.org','wikitravel.org','wikimediafoundation.org','wiktionary.org','wikiquote.org'
		]
	,	'_wiki/wikipedia.org/'
	]
,	[re.compile(r'(^|\.)lurkmo(re|ar|)\.\w+(:\d+)?$', re.I	),'_wiki/lurkmore.ru']

#--[ internal ]----------------------------------------------------------------

,	[['about:','chrome:','chrome-error:','chrome-extension:','data:','discord:','moz-extension:','opera:', 'vivaldi:'],'!_browser/']
,	[['file:','resource:'],'!_LAN,intranet']
]

#--[ end of rules table ]------------------------------------------------------

pat_url = re.compile(r'''
(?:^|[\r\n]\s*)
(?P<Meta>
	(
		(?:Snapshot-)?Content-Location:[^\r\n\w]*	# <- [skip quotes, whitespace, any garbage, etc]
	|	<base\s+href=[^<>\w]*
	|	<MAF:originalurl\s+[^<>\s=]+=[^<>\w]*
	)
)
(?P<URL>
	(?P<Protocol>[\w-]+:)/*
	(?P<Proxy>
		u
		(?P<ProxyPort>:[^:/?#]+)?
		/+[?]*
		(?P<ProxyProtocol>ftp|https?)
		:*/+
	)?
	(?P<DomainPath>
		(?P<DomainPort>
			(?P<Domain>[^":/?&=\#\s]+)?
			(?P<Port>:\d+)?
		)
		(?P<Path>/+
			(?P<Query>\??
				(?P<QueryPath>
					(?P<QuerySelector>
						(?P<QueryKey>[^"/?&=\#\s]+)?
						(?P<QueryValue>=[^"/?&\#\s]+)?
					)
					([/?&]+
						(?P<ItemSelector>
							(?P<IsArchived>arch[ive]*/)?
							(?P<ItemContainer>prev|res|thread)/|\w+\.pl[/?]*
						)?
					)?
					(?P<ItemID>[^"\#\s]*)
				)
			)
		)?
		(?P<Fragment>\#[^"\r\n]*)?
	)
)
'''
, re.I | re.X)

pat_idx = re.compile(r'<MAF:indexfilename\s+[^=>\s]+="([^">]+)', re.I)
pat_ren_mht_linebreak = re.compile(r'=\s+')
pat_ren_src_name = re.compile(r'([a-z0-9]*[^a-z0-9.]+)+', re.I)
pat_ren_yt_URL_ID = re.compile(r'[?&](?P<ID>v=[\w-]+)(?:[?&#]|$)', re.I)
pat_ren = [
	{
		'type': 'booru'
	,	'page': re.compile(r'''^
			(?P<Domain>\{[^{}\s]+\})?		# <- added by SavePageWE
			(?P<Prefix>
				(/dan|gel|r34|san|sfb)\s+
				([0-9]+)
			)
			(\s+.*)?
			(?P<Ext>\.[^.]+)
		$''', re.I | re.X)
	,	'child': re.compile(r'^([^_]\S*)?[0-9a-f]{32}\S*\.\w+$', re.I)
	}
,	{
		'type': 'rghost'
	,	'page': re.compile(r'''^
			(?P<Domain>\{[^{}\s]+\})?		# <- added by SavePageWE
			(?P<Prefix>
				(?P<SiteName>[-\w.]+)\s+
				(?P<FileID>[-\w]+)\s+-\s+
				(?P<Date>\d{4}(?:\D\d\d){5})
				(?P<TimeZone>\s+[+-]\d+)?
				\s+-\s+
			)
			(?P<FileName>\S.*?)\s+\S\s+
			(?P<Suffix>
				RGhost(?:\s+\S\s+[^.]+)?
			|	\S+\s+Mail\.Ru			# <- "cloud mail.ru"
			|	\S{6}\.\S{4}			# <- "yandex.disk"
			)
			(?P<PageName>\s+-\s+\S+?)?		# <- added by UnMHT
			(?P<SaveDate>\{\d{4}(?:\D\d\d){5}\})?	# <- added by SavePageWE
			(?P<OpenDate>;?_\d{4}(?:\D\d\d){5})?
			(?P<Ext>\.[^.]+)
		$''', re.I | re.X)
	}
,	{
		'type': 'youtube'
	,	'page': re.compile(r'''^	# page files:
			(?P<Domain>\{[^{}\s]+\})?		# <- added by SavePageWE
			(?P<Prefix>
				YouTube
				(?:\s+-\s+(?P<Author>.+?))
				(?:\s+-\s+(?P<Date>\d{4}(-\d\d){2}))
				(?:\s+-\s+(?P<Title>.+?))
			)
			(?P<PageName>\s+-\s+watch)?		# <- added by UnMHT
			(?P<SaveDate>\{\d{4}(?:\D\d\d){5}\})?	# <- added by SavePageWE
			(?P<OpenDate>;?_\d{4}(?:\D\d\d){5})?
			(?P<Ext>\.[^.]+)
		$''', re.I | re.X)
	,	'child': re.compile(r'''^	# video files/folders:
			(?:Youtube(?:,|\s+-\s+))?
			(?P<ID>v=[\w-]+)(?:,|\s+-\s+)
			(?P<Res>\d+p|\d+x\d+)?
			(?P<FPS>\d+fps)?
			(?P<TimeStamp>;?_\d{4}(?:\D\d\d){5})?
			(?P<Ext>\.[^.]+)?
		$''', re.I | re.X)
	,	'dest': u'd:/1_Video/other/_xz/_yt'
	} if arg_ytb else None
#,	['pixiv', re.compile(r',illust_id=(\d+).*\.\w+$', re.I)]
]

pat_sub = [
# item format:
# [
#	match
#	optional subdirname (default = 1st capture group)
#	optional match if 2nd file existed (for series)
#	optional match for duplicate ID
#	optional match for the smallest value to leave one duplicate at old place (to delete others manually, etc)
# ]
	{
		'match': re.compile(r'^.*?\b(\w+#\d+),\d+(, \d+ *\w+, \d+x\d+([.,].*)?)?\.\w+$', re.I)
	,	'subdir': r'\1'
	} if arg_aib else None
,	{
		'match': re.compile(r'^(pxv\D+(\d+)\D*?_)p\d+(\D.*)$', re.I)
	,	'next': r'\1p1\3'
	,	'subdir': r'\2'
	} if arg_pxv else None
,	{
		'match': re.compile(r'''^
			(?:(?P<Site>\S+)\s-\s)
			(?:(?P<NumID>\S+)\s-\s)
			(?P<ID>\S+)
			(?:\s-\s
				(?P<TimeStamp>\d{4}(?:\D\d\d){2,5})
			)?
			(?:\s-\s
				(?P<Etc>.*?)
			)?
			(?P<Ext>\.[^.]+)
		$''', re.I | re.X)
	,	'ID': r'\g<ID>'
	,	'date': r'\g<TimeStamp>'
	,	'subdir': '1'
	} if arg_dup else None
]

dup_lists_by_ID = {}
not_existed = []
n_i = n_matched = n_moved = n_fail = n_back = n_later = 0		# <- count iterations, etc
ext_path_inside = ext_web if arg_web else []				# <- understandable file format extensions
ext_simple = {
	'hathdl':	dest_root+'_img/_manga/e-hentai.org/_dl/_hath/' # 'd:/programs/!_net/HatH/hathdl'
,	'torrent':	'd:/_bak/4torrent/_tfiles'
}

a_type = type(pat_ren)
d_type = type(subscrape)
r_type = type(pat_url)
s_type = type('')
u_type = type(u'')

info_prfx = '\t'
msg_prfx = '\n-\t'

def is_type_str(s):
	return isinstance(s, s_type) or isinstance(s, u_type)

def dumpclean(obj):
	if type(obj) == dict:
		for k, v in obj.items():
			if hasattr(v, '__iter__'):
				print k
				dumpclean(v)
			else: print k, ':', v
	elif type(obj) == list:
		for v in obj:
			if hasattr(v, '__iter__'):
				dumpclean(v)
			else: print v
	else: print obj

def get_ext(path):
	if path.find('/') >= 0: path = path.rsplit('/', 1)[1]
	if path.find('.') >= 0: path = path.rsplit('.', 1)[1]
	return path.lower()

def rf(name, size=0):
	global n_fail
	ext = get_ext(name)
	r = ''
	try:
		if ext == 'maff':
			z = zipfile.ZipFile(name, 'r')
			for path in z.namelist():
				name = path.rsplit('/', 1)[-1:][0]
				if name == 'index.rdf':
					if TEST:
						print info_prfx, 'MAFF test, meta file:', path, '\n'
					r = z.read(path)			# <- return source URL
					if not size:
						s = re.search(pat_idx, r)
						if s and s.group(1):
							path = path[:-len(name)] + s.group(1)
							if TEST:
								print info_prfx, 'MAFF test, content file:', path, '\n'
							r = z.read(path)	# <- return source HTML
					break
		else:
			f = open(name)
			r = f.read(size) if size else f.read()
			f.close()
	except Exception as e:
		n_fail += 1
		print msg_prfx, 'Path length:', len(name)
		print e
	return r

def uniq(src, d):
	i = 0
	if os.path.exists(d) and os.path.exists(src):
		d = datetime.datetime.fromtimestamp(os.path.getmtime(src)).strftime(';_%Y-%m-%d,%H-%M-%S.').join(d.rsplit('.', 1))
		i += 1
	while os.path.exists(d):
		d = '(2).'.join(d.rsplit('.', 1))
		i += 1
	if i:
		print '+', i, 'duplicate(s)'
	return d

def meet(obj, criteria):
	return True if (
		(obj is criteria) or
		(obj == criteria) or (
			(is_type_str(obj	) or obj	) and
			(is_type_str(criteria	) or criteria	) and (
				criteria.match(obj)		if isinstance(criteria, r_type) else
				(obj in criteria)		if isinstance(criteria, a_type) else
				(obj.find(criteria) >= 0)	if is_type_str(criteria) else
				None
			)
		)
	) else False

def get_sub(subj, rules):
	if not rules:
		return None

	if is_type_str(rules):
		return [rules, '']

	name, meeting, board = subj
	for r in rules:
		if not r:
			continue

		if is_type_str(r):
			return [r, '']

		if isinstance(r, a_type):
			if len(r) > 1:
				r0 = isinstance(r[0], r_type)
				pattern = r[0 if r0 else 1]
				met = None
				for me in meeting:
					if meet(me, pattern):
						met = me
						break
				if met is not None:
					if r[0] is None:
						return None

					dsub = rename = ''

				# grab subfolder from URL parts:
					if r0:
						r1 = r[1]
						r1a = r1 if isinstance(r1, a_type) else [r1]
						for r1 in r1a:
							try:
								if r1 and isinstance(r1, s_type):
									dsub = (
										re
										.search(r[0], met)
										.expand(r1)
									)
									break
							except:
								continue
					else:
				# specific rules:
						dsub = r[0]
				# full filename replacement:
						if len(r) > 3 and isinstance(r[2], r_type):
							rename = re.sub(r[2], r[3], name)
				# only append item ID to filename, if not yet:
						elif len(r) > 2 and isinstance(r[1], r_type):
							suffix = (
								re
								.search(r[1], met)
								.expand(r[2])
							)
							if name.find(suffix) < 0:
								rename = (suffix+'.').join(name.rsplit('.', 1))
						if TEST and rename:
							print rename

					return [dsub, rename]

			elif board:
				return [r[0], '']

	return None

def r(path, later=0):
	global n_i, n_fail, n_matched, n_moved, n_back, n_later, not_existed, dup_lists_by_ID
	names = os.listdir(path)
	for name in names:
		n_i += 1
		src = path+'/'+name
		if os.path.isdir(src):
			if arg_r:
				r(src, later)
			continue

		# optionally cut long names before anything else:

		if arg_len:
			ln = len(src if arg_f else name)
			if ln > arg_len:
				n_matched += 1
				if n_back < ln:
					n_back = ln
				print ln, (src if arg_o else name).encode('utf-8')
				if DO:
					ext = '.'+get_ext(name)
					d = uniq(src, src[:arg_len-len(ext)].rstrip()+ext)
					os.rename(src, d)
					src = d
					name = d[len(path):].lstrip('/')
					n_moved += 1

		ext = get_ext(name)
		d = ''

		if ext in ext_simple:
			if later:
				n_later += 1
			else:
				d = ext_simple[ext]
				print d.encode('utf-8'), '<-', name.encode('utf-8')
				if DO and os.path.exists(src) and os.path.isdir(d):
					os.rename(src, uniq(src, d+'/'+name))
					n_moved += 1

		elif ext in ext_path_inside:
			n_matched += 1
			url = re.search(pat_url, rf(src, 123456))
			if not url:
				continue

			ufull = url.group('URL')
			board = url.group('QuerySelector')
			thread = url.group('ItemSelector') and url.group('ItemID')

			# define rule trying order:
			meeting = [
				ufull
			,	url.group('DomainPath')
			,	url.group('Path')
			,	url.group('QueryKey')
			,	url.group('Query')
			,	url.group('Fragment')
			,	board
			]

			for s in sites:
				if not s or not len(s):
					break

				d = url.group('Protocol')
				domain = ''
				if meet(d, s[0]):
					domain = d
				else:
					d = url.group('Domain')
					if not d:
						continue

					dp = url.group('DomainPort')
					if meet(dp+'.', s[0]):	# <- "name." or "name:port." to match exact full name
						domain = d
					else:
						words = reversed(dp.split('.'))
						d = ''
						for i in words:
							d = (i+'.'+d) if d else i
							if meet(d, s[0]):
								domain = d
								break
				if not domain:
					continue

				dest = (s[1] if (len(s) > 1) else domain)		# <- site bak root
				dest += (
					s[0][0]
					if (not isinstance(s[0], r_type) and dest[-2:] == '//')
					else
					domain.strip(':.')
					if (dest[-1:] == '/')
					else ''
				)+'/'

				if len(s) > 2:
					x = [name, meeting, True if board else False]
					z = s[2]
					dsub, rename = (
				# board threads (to scrape by other scripts):
						(
							get_sub(x, z.get('sub_threads'))
							if board and thread
							else None
						)
				# board roots, text boards, other specifics (not to scrape):
					or	get_sub(x, z.get('sub'))
					or	['', '']
					)
					if dsub:
						dest += dsub+'/'
					if rename:
						name = rename

				if TEST:
					if arg_o:
						print info_prfx, src.encode('utf-8')
					print dest, ufull

				# rename target files downloaded from RGHost/booru/yt/etc:
				for p in pat_ren:
					if not p:
						continue

					pat_page_name = p.get('page')
					if not pat_page_name:
						continue

					page_match = re.search(pat_page_name, name)
					if page_match:
						site_type = p.get('type')
						site_dest = p.get('dest', '').rstrip('/')
						pat_child_name = p.get('child')

						if site_type == 'booru':
							page_content = re.sub(pat_ren_mht_linebreak, '', rf(src))
						if site_type == 'youtube':
							page_ID = re.search(pat_ren_yt_URL_ID, url.group('Query'))
							if page_ID:
								page_ID = page_ID.group('ID')
						for child_name in names:
							if pat_child_name:
								child_match = re.search(pat_child_name, child_name)
								if not child_match:
									continue

							child_path = path+'/'+child_name
							child_ext = get_ext(child_name)
							if (child_ext in ext_path_inside) or (not os.path.exists(child_path)):
								continue

							prfx = ''
							if site_type == 'youtube':
								if pat_child_name:
									if page_ID != child_match.group('ID'):
										continue

								prfx = page_match.group('Prefix')+','
								if os.path.isdir(child_path):
									sub_names = os.listdir(child_path)
									for sub_name in sub_names:
										if pat_child_name:
											sub_match = re.search(pat_child_name, sub_name)
											if (not sub_match) or (page_ID != sub_match.group('ID')):
												continue

										sub_path = child_path+'/'+sub_name
										sub_dest = (site_dest or path)+'/'+prfx+sub_name
										print info_prfx, sub_name.encode('utf-8')
										if DO:
											os.rename(sub_path, uniq(sub_path, sub_dest))
											n_moved += 1
							elif os.path.isdir(child_path):
								continue

							if site_type == 'rghost':
								if (
									child_name == page_match.group('FileName')
								or	child_name.rsplit('.', 1)[0] == page_match.group('FileName')
								):
									prfx = page_match.group('Prefix')
							elif site_type == 'booru':
								f = len(child_ext)+1
								f = re.sub(pat_ren_src_name, '', child_name[:-f])
								if f:
									f = re.search(re.compile(r'''(?:^|[\r\n
	])(?:Content-Location: |<meta name="twitter:image:src" content=")\w+:/+[^\r\n
	]+[^w]/(preview|sample[_-]*)?'''+f+'|/'+f+'.'+child_ext+'">Save', re.I), page_content)	# <- [^w] to workaround /preview/ child post list
									if f:
										prfx = page_match.group('Prefix')+(' full,' if f.group(1) else ',')
							if prfx:
								child_dest = (
									path
									if site_type == 'youtube' and os.path.isdir(child_path)
									else
									(site_dest or path)
								)+'/'+prfx+child_name
								print info_prfx, child_dest.encode('utf-8')
								if DO:
									os.rename(child_path, uniq(child_path, child_dest))
									n_moved += 1
						break

				d = ''
				try:
					d = (dest_root+dest).rstrip('/.')
				except Exception as e:
					print 'Destination path error:', e
				if len(d) < 1:
					d = u'.'
				dq = d

				if DO:
					try:
						if not os.path.exists(d):
							print msg_prfx, 'Path not found, make dirs:', d.encode('utf-8')
							os.makedirs(d)
						d += '/'+(name[:-2] if ext == 'mhtml' else name)
						dq = uniq(src, d)
						os.rename(src, dq)
						if os.path.exists(d):		# <- check that new-moved and possible duplicate both exist
							n_moved += 1
							if arg_o:
								print info_prfx, src.encode('utf-8')
							print dest, ufull
						else:
							n_back += 1		# <- if renamed "path/name" to the same "path/name(2)", revert
							os.rename(dq, d)	# <- this is simpler than checking equality, symlinks and stuff
					except Exception as e:
						n_fail += 1
						d, dq = len(d), len(dq)
						print msg_prfx, 'Destination path length:', d
						if d != dq:
							print msg_prfx, 'Renamed unique length:', dq
						print e
				elif not d in not_existed and not os.path.exists(d):
					print msg_prfx, 'Path not found:', d.encode('utf-8')
					not_existed.append(d)
				break

		# unknown filetypes, group into subfolders by ID, for pixiv multipages and such:

		else:
			for p in pat_sub:
				if not p: continue

				pat_match  = p.get('match')
				pat_next   = p.get('next')
				pat_ID     = p.get('ID')
				pat_date   = p.get('date')
				pat_subdir = p.get('subdir')

				if not pat_match: continue

				s = re.search(pat_match, name)
				if not s: continue

				if pat_next and not (s.expand(pat_next) in names): continue

				if pat_ID:
					dup_ID = s.expand(pat_ID)

					try:
						dup_stamp = s.expand(pat_date)
					except:
						dup_stamp = 'last'

					d = dup_lists_by_ID[dup_ID] if dup_ID in dup_lists_by_ID else None
					if later:
						n_later += 1
						if dup_stamp:
							if d:
								if isinstance(d, a_type) and not dup_stamp in d:
									d.append(dup_stamp)
							else:
								d = dup_lists_by_ID[dup_ID] = {}
							if isinstance(d, d_type):
								d[name] = dup_stamp or name
						else:
							if d:
								d += '1'	# <- to simply check len() the same way
							else:
								d = dup_lists_by_ID[dup_ID] = '1'
						if TEST:
							lend = len(d.keys() if isinstance(d, d_type) else d)
							print dup_ID.encode('utf-8'), '- dup #', lend, dup_stamp.encode('utf-8')
						continue
					elif not (
						d
					and	len(d.keys() if isinstance(d, d_type) else d)
					and	(
							(isinstance(d, a_type) and dup_stamp in d)
						or	(isinstance(d, d_type) and name in d)
						)
					):
						continue

				s = '/' + (s.expand(pat_subdir) if pat_subdir else s.group(1)).strip('/')
				i = len(s)
				d = path.rstrip('/')
				while d[-i:] == s: d = d[0:-i]

				d += s
				if d == path: continue

				print d.encode('utf-8'), '<-', name.encode('utf-8')
				if DO:
					dest = d+'/'+name
					try:
						if not os.path.exists(d):
							os.mkdir(d)
						os.rename(src, dest)
						n_moved += 1
					except Exception as e:
						n_fail += 1
						print msg_prfx, 'Path length:', len(src), 'to', len(dest)
						print e

def run(later=0):
	global n_later, dup_lists_by_ID
	r(u'.', later)
	if later:
		for i in dup_lists_by_ID:
			d = dup_lists_by_ID[i]

			if isinstance(d, a_type):
				lend = len(d)
				if lend > 1:
					if TEST:
						print 'ID:', i
						print lend, 'before sort:', d
				d.sort()
				d.pop(0)		# <- leave alone the earliest at old place
				lend = len(d)
				if lend:
					if TEST:
						print lend, 'after sort:', d
						print
				n_later -= 1

			elif isinstance(d, d_type):
				lend = len(d.keys())
				if lend > 1:
					if TEST:
						print 'ID:', i
						print lend, 'before sort:', str(d).replace('u\'', '\nu\'')
						print
				name_0 = stamp_0 = None
				for name in d:
					stamp = d[name]
					if (
						not name_0
					or	not stamp_0
					or	stamp_0 > stamp
					or	(stamp_0 == stamp and name_0 > name)
					):
						name_0 = name
						stamp_0 = stamp
				d.pop(name_0)		# <- leave alone the first by name of the earliest ones
				lend = len(d.keys())
				if lend:
					if TEST:
						print lend, 'after sort:', str(d).replace('u\'', '\nu\'')
						print
				n_later -= 1

			elif TEST:
				print len(d), ':', d
	a = []
	n = [
		[n_i	,	'checks']
	,	[n_matched,	'matches']
	,	[n_moved,	'moved']
	,	[n_later,	'later']
	,	[n_fail,	'failed']
	,	[n_back,	'max name length' if arg_len else 'back']
	]
	for i in n:
		if i[0] > 0:
			a.append(str(i[0])+' '+i[1])
	print msg_prfx, 'Result:', ', '.join(a) if len(a) > 0 else 'no files matched.'
	return n_later if DO else 0

if run(1):
	run()
