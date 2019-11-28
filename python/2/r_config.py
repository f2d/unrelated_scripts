#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import re

default_name_cut_length = 123

ext_web = ['htm', 'html', 'maff', 'mht', 'mhtml']

dest_root = u'd:/_bak/_www/'
dest_root_yt = u'd:/1_Video/other/_xz/YouTube/'
dest_root_by_ext = {
	'hathdl':	dest_root+'_img/_manga/e-hentai.org/_dl/_hath/' # 'd:/programs/!_net/HatH/hathdl'
,	'torrent':	'd:/_bak/4torrent/_tfiles/'
}

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

subscrape = {'sub_threads': '_scrape'}
unscrape = '!_unscrape,roots,etc'

sub_a = [
	[unscrape+'/_src'	,re.compile(r'^[^/?#]+(/+arch)?/+src/+[^/]+', re.I)]
,	[unscrape+'/_arch'	,re.compile(r'^[^/?#]+/+arch/+res/+([?#]|$)', re.I)]
,	[unscrape+'/_catalog'	,re.compile(r'^[^/?#]+/+catalog', re.I)]
,	[unscrape+'/_rules'	,re.compile(r'^([^/?#]+/+)?rules', re.I)]
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
				[None				,re.compile(r'^/+(cgi-bin|d|err)/|^/+[^/?#]+/arch/res/+([?#]|$)', re.I)]
			,	[re.compile(r'^[^#]*#(.*[^/.])[/.]*$'), r'!_tar,thread_archives/\1']
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
