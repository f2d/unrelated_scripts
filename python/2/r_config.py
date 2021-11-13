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

# default_print_encoding = 'utf-8'
default_print_encoding = 'unicode-escape'

default_name_cut_length = 123
default_read_bytes = 12345

ext_web = ['htm', 'html', 'maff', 'mht', 'mhtml']

ext_web_remap = {
	'htm': 'html'
,	'mhtml': 'mht'
}

ext_web_read_bytes = {
	'html': 0	# <- read whole file
# ,	'mht': 12345
}

ext_web_index_file = {
	'html': 'index.html'
,	'maff': 'index.rdf'
}

dest_root = u'd:/_bak/_www/'
dest_root_yt = u'd:/1_Video/other/_xz/YouTube/'

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

pat_subdomain_inc_www = get_rei(part_protocol                   + part_domain)	# <- to treat "www" like a separate subdomain
pat_subdomain_exc_www = get_rei(part_protocol + part_domain_www + part_domain)	# <- to discard "www", if any

pat_title_tail_dup = get_rei(r'(-\d+|\s*\(\d+\)|;_[\d,_-]+)?(\.[^.]+$)')
pat_title_tail_g = get_rei(r'( - [^-]*?Google)([\s,(;-].*?)?(\.[^.]+$)')

part_g_search = r'(^/*|search)\?([^&]*&)*?'

subscrape = {'sub_threads': '_scrape'}
unscrape = '!_unscrape,roots,etc'

sub_a = [
	[unscrape+'/_src'	,get_rei(r'^[^/?#]+(/+arch)?/+src/+[^/]+')]
,	[unscrape+'/_arch'	,get_rei(r'^[^/?#]+/+arch/+res/+([?#]|$)')]
,	[unscrape+'/_catalog'	,get_rei(r'^[^/?#]+/+catalog')]
,	[unscrape+'/_rules'	,get_rei(r'^([^/?#]+/+)?rules')]
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

pat_by_ext_twMediaDownloader = get_rei(r'^\w+-\d+-\d+_\d+-(img|gif\d+)\.\w+$')
pat_by_ext_coub_DL_button = get_rei(r'^\d+_(ifunny|looped)_\d+\.\w+$')




#--[ table of rule cases selected by filename ]--------------------------------

dest_root_by_ext = {
	'eml':		dest_root + '_web/_mail/'
,	'hathdl':	dest_root + '_img/_manga/e-hentai.org/_dl/_hath/' # 'd:/programs/!_net/HatH/hathdl'
,	'torrent':	'd:/_bak/4torrent/_torrent_files,not_active/'
,	'zip':	[
		{
			'dest_path': dest_root + '_soc/twitter.com/twimg.com/_unsorted_zip/'
		,	'match_name': pat_by_ext_twMediaDownloader
		}
	]
,	'mp4':	[
		{
			'dest_path': dest_root + '_soc/twitter.com/twimg.com/_video/'
		,	'match_name': pat_by_ext_twMediaDownloader
		}
	,	{
			'dest_path': dest_root + '_video/coub.com/_video/'
		,	'match_name': pat_by_ext_coub_DL_button
		}
	]
}




#--[ table of rule cases selected by site ]------------------------------------

# Notes:
# To match exact full name and not subparts (like "*.name") set domain string as "name."
# Some parts of this table were cut out in public version.
# Others were left mostly as example.
# Feel free to use them as such and throw away everything unneeded.

sites = [

#--[ local ]-------------------------------------------------------------------

	[get_rei(r'^(192\.168\.(\d+\.)*9|127\.(0\.)*\d+|localhost|l|a)(:\d+)?\.$'		),'!_LAN,intranet/localhost']
#,	[get_rei(r'^(192\.168\.(\d+\.)*1|r\d*|www\.asusnetwork\.net|router\.asus\.com)\.$'	),'!_LAN,intranet/router/ASUS_RT-AC58U']
#,	[get_rei(r'^(r|d-?(link)?|dir-?(100|120)|192\.168\.[01]\.(1|100|120))$'			),'!_LAN,intranet/router/D-Link_DIR-120']
#,	[['192.168.1.99'									],'!_LAN,intranet/printer/MG_3040']

#--[ global ]------------------------------------------------------------------

,	[['archive.today','archive.ec','archive.fo','archive.is','archive.li'			],'_archives//']
,	[['archive.org','archiveteam.org','mementoweb.org','peeep.us','perma.cc','web-arhive.ru'],'_archives/']

#--[ chats ]-------------------------------------------------------------------

,	[['slack.com'						],'_conf/',{'sub': [[pat_subdomain_exc_www, r'_subdomain/\1']]}]
,	[get_rei(r'(^|\.)slack(hq)?\.\w+$'			),'_conf/slack.com/']
,	[['discord.gg','discord.pw'				],'_conf/discordapp.com/']
,	[
		['discordapp.com']
	,	'_conf/'
	,	{
			'sub': [
				[get_rei(r'^/+channels?/+(\d+)([/?#]|$)'), r'_channels/\1']
			]
		}
	]

#--[ stuff ]-------------------------------------------------------------------

,	[get_rei(r'(^|\.)d(eposit)?files\.\w+$'		),'_fileshares/depositfiles.com']
,	[get_rei(r'(^|\.)freakshare\.\w+$'		),'_fileshares/freakshare.com']
,	[get_rei(r'(^|\.)rapidshare\.\w+$'		),'_fileshares/rapidshare.com']
,	[get_rei(r'(^|\.)rgho(st)?\.\w+$'		),'_fileshares/rghost.ru']
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
				['_file'	,get_rei(r'^([^!#]*#+)?(!.+)$'	), r',#\2']
			,	['_folder'	,get_rei(r'^([^!#]*#+)?(F!.+)$'	), r',#\2']
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
				['_mht/member/follow'	,get_rei(r'^/+bookmark\.php\?([^&]*&)*type=user&*([^&]*&)*(id=\d+)'	), r',u\3']
			,	['_mht/member/bookmark'	,get_rei(r'^/+bookmark\.php\?([^&]*&)*(id=\d+)'				), r',u\2']
			,	['_mht/bookmark/tag'	,get_rei(r'^/+bookmark\.php\?([^&]*&)*(tag=[^&]*)'			), r',\2']
			,	['_mht/bookmark/add'	,get_rei(r'^/+bookmark_add\.php\?([^&]*&)*(id=\d+)'		), r',illust_\2,added']
			,	['_mht/bookmark/add'	,get_rei(r'^/+bookmark_add\.php\?([^&]*&)*(illust_id=\d+)'	), r',\2,add']
			,	['_mht/illust'		,get_rei(r'^/+member_illust\.php\?([^&]*&)*(illust_id=\d+)'	), r',\2']
			,	['_mht/member/illust'	,get_rei(r'^/+member_illust\.php\?([^&]*&)*(id=\d+)'		), r',u\2']
			,	['_mht/member/profile'	,get_rei(r'^/+member\.php\?([^&]*&)*(id=\d+)'			), r',u\2']
			,	['_mht/mypage'		,get_rei(r'^/+mypage\.php\?([^&]*&)*(id=\d+)'			), r',u\2']
			,	['_mht/member/novel'	,get_rei(r'^/+novel/member\.php\?([^&]*&)*(id=\d+)'		), r',u\2']
			,	['_mht/novel'		,get_rei(r'^/+novel/([^?]*\?)+([^&]*&)*(id=\d+)'		), r',novel_\3']
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
				['_scrape/_e_ - Ecchi',['e','h','u']]
			,	'_scrape/_etc'
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
		get_rei(r'((^|\.)410chan\.\w+|^95\.211\.122\.44)$')
	,	'_img/_board/410chan.ru'
	,	{
			'sub_threads': [
			#	[None, ['d','errors']]
				[None, ['errors']]
			,	'_scrape'
			]
		,	'sub': sub_a+[
				[unscrape, get_rei(r'^err(or(s)?)?/|^[^/?#]+/arch/res/+([?#]|$)|^\.[\w-]+(/|$)|^[\w-]+\.\w+([?#]|$)')]
			]
			# +sub_d
			+sub_b
		}
	]
,	[get_rei(r'(^|\.)dobrochan\.\w+$'),'_img/_board/dobrochan.ru',{'sub_threads': '_scrape', 'sub': sub_a+sub_b}]
,	[
		['hiichan.org','hiichan.ru','hii.pm']
	,	'_img/_board/iichan.ru'
	,	{
			'sub_threads': '_scrape/_h_ - Hentai'
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
				[None, get_rei(r'^/+(cgi-bin|d|err)/|^/+[^/?#]+/arch/res/+([?#]|$)')]
			,	[get_rei(r'^[^#]*#(.*[^/.])[/.]*$'), r'!_tar,thread_archives/\1']
			,	['_scrape/_a_ - Anime'			,['a','aa','abe','azu','c','dn','fi','hau','ls','me','rm','sos']]
			,	['_scrape/_b_ - Bred'			,['b']]
			,	['_scrape/_h_ - Hentai'			,['g','h']]
			,	['_scrape/_hr_ - HiRes & requests'	,['hr','r']]
			,	['_scrape/_m_ - Macros & mascots'	,['m','misc','tan','tenma']]
			,	['_scrape/_to_ - Touhou'		,['to']]
			,	['_scrape/_n_prev'			,['n']]
			,	'_scrape/_etc'
			]
		,	'sub': sub_a+[
			#	[unscrape+'/_h'	,get_rei(r'(^|\w+\.)hii(chan)?\.\w+/')]
				[unscrape+'/_n'	,['n','index','index.html','']]
			,	[unscrape	,['cgi-bin','err']]
			,	[unscrape	,get_rei(r'^/+[^/?#]+([?#]|$)')]
			]+sub_d
		}
	]
,	[
		['donmai.us','idanbooru.com']
	,	'_img/_booru//'
	,	{
			'sub': [
				['posts'		,get_rei(r'^(/+mobile)?/+posts?/(show[/?]+)?(\d+)')]
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
		get_rei(r'(^|\.)blogspot(\.com?)?\.\w+$')
	,	'_soc/blogspot.com'
	,	{
			'sub': [
				[get_rei(r'^(?:\w+:/+)?\d+\.bp\.[^/?#]+(?:/|$)'					), r'_pix']
			,	[get_rei(r'^(?:\w+:/+)?([^/?#]+\.)?([^/.]+)\.blogspot(\.com?)?\.\w+(?:/|$)'	), r'_personal/\2']
			]
		}
	]
,	[['stwity.com','twimg.com','twitpic.com','twitrss.me','twpublic.com'	],'_soc/twitter.com/']
,	[
		['twitter.com']
	,	'_soc/'
	,	{
			'sub': [
				[get_rei(r'^(?:\w+:/+)?(?:[^/?#]+\.)twitter\.com/'			), r'_mht']
			,	[get_rei(r'^(?:\w+:/+)?(?:www\.)?twitter\.com/+([^/?#]+)/+status/'	), r'_mht/_personal/\1/_posts']
			,	[get_rei(r'^(?:\w+:/+)?(?:www\.)?twitter\.com/+([^/?#]+)([/?#]|$)'	), r'_mht/_personal/\1']
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
,	[['diveintopython.net','py-my.ru','pygame.org','pypi.org','python.su','pythonware.com'	],'_software/_prog/Python/']
,	[['ghtorrent.org','github.io','githubuniverse.com','githubusercontent.com'		],'_software/github.com/']
,	[
		get_rei(r'(^|\.)github\.\w+$')
	,	'_software/github.com'
	,	{
			'sub': [
				[pat_subdomain_exc_www	, r'_subdomain/\3']
			,	['_blog'		, ['blog']]
			,	['_settings,etc'	, ['login','settings','signup']]
			,	['_users/_repositories'
				,	get_rei(r'[^?#]*\?([^&]*&)*tab=repos')
				,	get_rei(r'(\s+\S\s+GitHub( - \w+)?([\s,(;-].*)?)?(\.[^.]+$)')
				,	r' - GitHub Repositories\4'
				]
			,	[get_rei(r'^/+[^/?#]+/([^/?#]+)/+(commit|issue|label|pull)s?'	), r'_projects/\1/\2']
			,	[get_rei(r'^/+[^/?#]+/([^/?#]+)(/|$)'				), r'_projects/\1']
			,	[get_rei(r'^/+[^/?#]+/*([?#]|$)'				), r'_users']
			]
		}
	]
,	[
		get_rei(r'(^|\.)osdn\.\w+$')
	,	'_software/osdn.net'
	,	{
			'sub': [
				[get_rei(r'^/+projects?/([^/?#]+)')	, r'_projects/\1']
			,	[pat_subdomain_exc_www			, r'_projects/\3']
			]
		}
	]
,	[
		get_rei(r'(^|\.)(sourceforge\.\w+|sf.net)$')
	,	'_software/sf.net'
	,	{
			'sub': [
				['_accounts'						, get_rei(r'^/+(auth|u|user)/')]
			,	[get_rei(r'^/+(p|projects?|apps?/\w+)/([^/?#]+)')	, r'_projects/\2']
			,	[pat_subdomain_exc_www					, r'_projects/\3']
			]
		}
	]

#--[ more stuff ]--------------------------------------------------------------

,	[get_rei(r'(^|\.)anidex\.\w+$'			),'_torrents/anidex.info']
,	[get_rei(r'(^|\.)bakabt\.\w+$'			),'_torrents/bakabt.me']
,	[get_rei(r'(^|\.)isohunt\.\w+$'			),'_torrents/isohunt.to']
,	[get_rei(r'(^|\.)nnm-club\.\w+$'		),'_torrents/nnm-club.ru']
,	[get_rei(r'sukebei?\.nyaa\.si$'			),'_torrents/nyaa.si/hentai'	,{'sub': sub_nyaa}]
,	[get_rei(r'(^|\.)nyaa\.si$'			),'_torrents/nyaa.si'		,{'sub': sub_nyaa}]
,	[get_rei(r'files?\.nyaa(torrents)?\.\w+$'	),'_torrents/nyaa.se/static_files']
,	[get_rei(r'forums?\.nyaa(torrents)?\.\w+$'	),'_torrents/nyaa.se/forums']
,	[get_rei(r'sukebei?\.nyaa(torrents)?\.\w+$'	),'_torrents/nyaa.se/hentai'	,{'sub': sub_nyaa}]
,	[get_rei(r'(^|\.)nyaa(torrents)?\.\w+$'		),'_torrents/nyaa.se'		,{'sub': sub_nyaa}]
,	[get_rei(r'(^|\.)(the|old)piratebay\.\w+$'	),'_torrents/thepiratebay.org']
,	[get_rei(r'(^|\.)tokyo-?tosho\.\w+$'		),'_torrents/tokyotosho.info']

#--[ wiki ]--------------------------------------------------------------------

,	[['boltwire.com','dokuwiki.org','foswiki.org','ikiwiki.info','pmwiki.org','trac.edgewall.org','wikimatrix.org'],'_wiki/_soft/']
,	[get_rei(r'(^|\.)encyclopediadramatica\.\w+$'		),'_wiki/encyclopediadramatica.com']
,	[get_rei(r'(^|\.)lurkmo(re|ar|)\.\w+(:\d+)?$'		),'_wiki/lurkmore.ru']
,	[['mrakopedia.ru','mrakopedia.org','barelybreathing.ru'	],'_wiki//']
,	[['scpfoundation.net','scpfoundation.ru'		],'_wiki//']
,	[['traditio.ru','traditio-ru.org'			],'_wiki//']
,	[['wikia.nocookie.net'					],'_wiki/wikia.com/_img']
,	[['fandom.com','wikia.com'				],'_wiki/',{'sub': [[pat_subdomain_exc_www, [
		r'_subdomain/\g<NotLastOver2>/\g<LastOver2>'
	,	r'_subdomain/\g<LastOver2>'
	]]]}]
,	[['wikipedia.org'					],'_wiki/',{'sub': [[pat_subdomain_exc_www, r'_subdomain/\g<LastOver2>']]}]
,	[
		[	'mediawiki.org','wikidata.org','wikimedia.org','wikitravel.org','wikimediafoundation.org','wiktionary.org','wikiquote.org'
		]
	,	'_wiki/wikipedia.org/'
	]

#--[ unsorted, etc ]-----------------------------------------------------------

,	[['world-art.ru'],'/']

#--[ internal ]----------------------------------------------------------------

,	[['about:','chrome:','chrome-error:','chrome-extension:','data:','discord:','moz-extension:','opera:', 'vivaldi:'],'!_browser/']
,	[['file:','resource:'],'!_LAN,intranet']
]

#--[ end of rules table ]------------------------------------------------------
