#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import re, sys

re_ix = re.I | re.X
re_iu = re.I | re.U
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
default_read_bytes = 65535

ext_web = [
	'htm'
,	'html'
,	'maff'
,	'mht'
,	'mhtml'
]

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

part_emoji = (

# https://stackoverflow.com/questions/39108298/a-python-regex-that-matches-the-regional-indicator-character-class#comment125313486_39108298

	ur'([\u10000-\u1FFFF])' if sys.maxunicode > 0xFFFF else
	ur'([\uD800-\uDBFF][\uDC00-\uDFFF])'
)

part_protocol = r'^(?P<Scheme>(?P<Protocol>\w+):/+)?'
part_domain_www = r'(?P<OptionalSubDomain>www[.]|(?!www[.]))'
part_domain = r'''
(?P<All>
	(?P<AllOverTop2>
		(?P<LastOverTop2>		[^:/?=#\s.<>]+)
		(?:
					[.]+
			(?P<NotLastOverTop2>
						[^:/?=#\s.<>]+
				(?:	[.]+	[^:/?=#\s.<>]+)*
			)
		)?
	)
	(?P<Top2>
		(?P<Top2nd>		[.]+	[^:/?=#\s.<>]+)
		(?P<Top>		[.]+	[^:/?=#\s.<>]+)
	)
)
(?:[:](?P<Port>\d+))?
(?=$|[\r\n/?#])
'''

pat_subdomain_inc_www = get_rei(part_protocol                   + part_domain)	# <- to treat "www" like a separate subdomain
pat_subdomain_exc_www = get_rei(part_protocol + part_domain_www + part_domain)	# <- to discard "www", if any
pat_subdomain_forum   = get_rei(part_protocol + part_domain_www + part_domain + r'/+(?P<Folder>forum)/+')
pat_subdomain_top_meta  = get_rei(part_protocol + part_domain_www + r'(?P<MetaSubDomain>meta[.])' + part_domain)
pat_subdomain_over_meta = get_rei(part_protocol + part_domain_www + r'''
(?P<AllOverMeta>
	(	[^:/?=#\s.<>]+	[.])*?
		[^:/?=#\s.<>]+
)				[.]
(?P<MetaSubDomain>meta		[.])
''')

part_ext_etc = r'(?P<ExtEtc>(?P<Date>\{[^.\{\}]+\})?(?P<Ext>\.[^.]+))$'

pat_title_tail_dup = get_rei(r'(?P<Remove>-\d+|\s*\(\d+\)|;_[\d,_-]+)?' + part_ext_etc)
pat_title_tail_g = get_rei(r'(?P<SiteName> - [^-]*?Google)(?P<Remove>[\s,(;-].*?)?' + part_ext_etc)

part_g_search = r'^[/#]*?(search)?[?#]([^&#]*[&#])*?'
part_q_search = part_g_search + r'q=[^&#]'

part_lang = r'(?P<FullLang>(?P<Lang>\w{2}(?P<LangSubTag>-\w{2})?))'
part_url_tail_ID = r'/+[^!#]*?[/.]+(?P<ID>[a-z]?\d+)(?=$|[#?])'

subscrape = {'sub_threads': '_scrape'}
unscrape = '!_unscrape,roots,etc'

sub_domain_exc_www_directly = [
	[pat_subdomain_exc_www, r'\g<All>']
]

sub_domain_exc_www = [
	[pat_subdomain_exc_www, r'_subdomain/\g<All>']
]

sub_domain_over_top2_exc_www = [
	[pat_subdomain_exc_www, r'_subdomain/\g<AllOverTop2>']
]

sub_domain_over_top2_exc_www_directly = [
	[pat_subdomain_exc_www, r'\g<AllOverTop2>']
]

sub_domain_last_over_top2_exc_www = [
	[pat_subdomain_exc_www, r'_subdomain/\g<LastOverTop2>']
]

sub_domain_last_over_top2_forum = [
	[pat_subdomain_forum, r'_subdomain/\g<LastOverTop2>/\g<Folder>']
]

sub_lang = [
	[get_rei(r'^/*' + part_lang + r'/+'), r'\g<Lang>']
]

sub_lang_in_sub_dir = [
	[get_rei(r'^/*' + part_lang + r'/+(?P<Dir>\w+)/+'), r'_\g<Dir>/\g<Lang>']
]

sub_a = [
	[unscrape+'/_src'	, get_rei(r'^[^/?#]+(/+arch)?/+src/+[^/]+')]
,	[unscrape+'/_arch'	, get_rei(r'^[^/?#]+/+arch/+(res|\d+)/+([?#]|$)')]
,	[unscrape+'/_catalog'	, get_rei(r'^[^/?#]+/+catalog')]
,	[unscrape+'/_rules'	, get_rei(r'^([^/?#]+/+)?rules')]
]

sub_b = [
	[unscrape+'/_boards']
,	unscrape
]

sub_d = [
	[unscrape+'/_d',['d']]
] + sub_b

sub_localhost = [
	['4',['4']]
,	['a',['a','event']]
,	['b',['b']]
,	['doodle',['doodle']]
,	['server',['server-info','server-status']]
,	['stats',['stats']]
,	['t',['t']]
]

sub_q_search = [
	[get_rei(part_q_search), r'_search']
]

sub_nyaa = sub_q_search + [
	['_search'		, ['?','page=search']]
,	['_torrent_info'	, ['view','page=view','page=torrentinfo']]
,	['_browse'		, ['user','page=separate','page=torrents','page=rss']]
,	['_site_info'		, ['help','login','profile','register','rules','upload']]
,	[pat_subdomain_inc_www	, r'_browse/\g<LastOverTop2>']
,	'_browse'
]

sub_wikia = [
	[pat_subdomain_exc_www	, [r'_subdomain/\g<NotLastOverTop2>/\g<LastOverTop2>', r'_subdomain/\g<LastOverTop2>']]
]

sub_git = [
	['_blog'		, ['blog','readme']]
,	['_settings,etc'	, ['login','settings','signup']]
] + sub_domain_last_over_top2_exc_www

sub_git_projects = [
	[get_rei(r'^/+[^/?#]+/([^/?#]+)/+(commit|issue|label|pull)s?'	), r'_projects/\1/\2']
,	[get_rei(r'^/+[^/?#]+/([^/?#]+)(/|$)'				), r'_projects/\1']
,	[get_rei(r'^/+[^/?#]+/*([?#]|$)'				), r'_users']
]

sub_gitlab = sub_git + sub_git_projects

pat_by_ext_twMediaDownloader = get_rei(r'^\w+-\d+-\d+_\d+-(img|gif\d+)\.\w+$')
pat_by_ext_coub_DL_button = get_rei(r'^\d+_(ifunny|looped)_\d+\.\w+$')

pat_pixai_art = get_rei(r'^/*artwork/+(\d+)(?:$|[/?#])')

replace_title_pixai_username = [
	get_rei(r'((?:^|[\\/])[^\\/]+?\S by @(?P<Name>[^\\/]+?) _ PixAI(?: - \d+|;_\d{4}(?:\D\d\d){5})*\.\w+$)', re_iu)
,	r'_art_by_user/\g<Name>/\1'
,	r'_art_hidden'
]

replace_title_emoji_cluster = [get_rei(part_emoji + r'{3,}', re_iu), r'_']
replace_title_html_entities = [get_rei(r'&(#(x[0-9A-F]+|\d+)|\w+);'), r'_']
replace_title_underscores = [get_rei(r'_+(\s+_+)*'), r'_']
replace_title_tail_unmht = [get_rei(r'\s+-\s+[\w-]*(?P<Ext>\.\w+)$'), r'\g<Ext>']
replace_title_tail_yt_video = [get_rei(r'(?:\s+-\s+(?:watch|v=[\w-]+)|;?_\d{4}(?:\D\d\d){5})+(?:\(\d+\))?(?P<Ext>\.\w+)$'), r'\g<Ext>']




#--[ table of rule cases selected by filename ]--------------------------------

dest_root_by_ext = {
	'eml':		dest_root + '_web/_mail/'
,	'hathdl':	dest_root + '_img/_manga/e-hentai.org/_dl/_hath/'	# 'd:/programs/!_net/HatH/hathdl'
,	'torrent':	'd:/_bak/4torrent/_torrent_files/not_active/'
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

,	[['status.d420.de'				],'_soc/twitter.com/nitter/']
,	[get_rei(r'^nitter(?:\.\w+)*$'			),'_soc/twitter.com/nitter']
,	[
		['web.archive.org']
	,	'_archives/archive.org/'
	,	{
			'sub': [
				[get_rei(r'''
					(?P<ArchivePrefix>
						(?:^|/)
						(?P<ArchivePrefixFolder>web)/+
						(?P<ArchivePrefixDate>[\d*]+)/+
					)
					(?P<Scheme>
						(?P<Protocol>\w+)
						(?:%3A|:)(?:%2F|/)*
					)?
					(?P<Domain>
						(?P<OptionalSubDomain>www\.)?
						(?P<DomainWithoutWWW>[^:/?&#%]+)
					)
				'''), r'_website/\g<DomainWithoutWWW>']
			]
		}
	]
,	[['archive.today','archive.ec','archive.fo','archive.is','archive.li'	],'_archives//']
,	[
		[	'archive.md','archive.ph','archive.org','archiveofourown.org','archiveteam.org','mementoweb.org'
		,	'peeep.us','perma.cc','usenet-crawler.com','web-arhive.ru'
		]
	,	'_archives/'
	]

,	[
		[	'choosealicense.com','copyright.gov','ethicalsource.dev','freepatentsonline.com','linfo.org','questioncopyright.org'
		,	'removeyourmedia.com','sfconservancy.org','tldrlegal.com','unlicense.org','wtfpl.net'
		]
	,	'_business/_copyright/'
	]
,	[
		[	'17track.net','aftership.com','box-cargo.ru','cdek.ru','customs.ru','dellin.ru'
		,	'edost.ru','efl.ru','emspost.ru','gdeposylka.ru','jde.ru','mainbox.com'
		,	'nrg-tk.ru','packagetrackr.com','pecom.ru','pochta.ru','pochtoy.com','ponyexpress.ru','qwintry.com'
		,	'shipito.com','shopfans.ru','shopotam.ru','spk-ptg.ru','taker.im','tks.ru','ups.com','vnukovo.ru'
		]
	,	'_business/_delivery/'
	]
,	[['cdek.shopping'									],'_business/_delivery/cdek.ru/']
,	[['jobs-ups.com','ups-broker.ru'							],'_business/_delivery/ups.com/']
,	[[u'цифровыепрофессии.рф','xn--b1agajda1bcigeoa6ahw4g.xn--p1ai'				],'_business/_job//']
,	[['career.ru','fiverr.com','hh.ru','job-mo.ru','jooble.org','kwork.ru','upwork.com'	],'_business/_job/']
,	[['graphtreon.com','patrecon.com','patreonhq.com','subscribestar.adult'			],'_business/_money/_crowd-sourcing/patreon.com']
,	[
		[	'bomjstarter.com','boomstarter.ru','boosty.to','buymeacoffee.com','camp-fire.jp','cofi.ru','crowdrise.com','d.rip'
		,	'fundrazr.com','givesendgo.com','gofundme.com','gogetfunding.com','indiegogo.com'
		,	'kickstarter.com','liberapay.com','opencollective.com'
		,	'patreon.com','sponsr.ru','subscribestar.com','tipeee.com','utip.io','yasobe.ru'
		]
	,	'_business/_money/_crowd-sourcing/'
	]
,	[
		[	'binance.com','bitcoin.it','bitcoin.org','coindesk.com','hashcoins.com'
		,	'lightning.network','polybius.io','trustwallet.com','vexel.com','wirexapp.com','xmrig.com','z.cash'
		]
	,	'_business/_money/_crypto,NFT/'
	]
,	[['ownrwallet.com','ownr.wallet'		],'_business/_money/_crypto,NFT//']
,	[get_rei(r'^cloudpayments\.\w+$'		),'_business/_money/cloudpayments.ru']
,	[['nigelpickles.com'				],'_business/_money/ko-fi.com/']
,	[['paypal.me','paypal-communication.com','paypal-community.com','paypalobjects.com'	],'_business/_money/paypal.com/']
,	[get_rei(r'^paypal\.\w+$'			),'_business/_money/paypal.com',{'sub': [['paypal.me',['paypalme']]]}]
,	[['sovest.ru'					],'_business/_money/qiwi.ru/']
,	[get_rei(r'^qiwi\.\w+$'				),'_business/_money/qiwi.ru']
,	[get_rei(r'^visa(\.com)?.\w+$'			),'_business/_money/visa.com']
,	[['wmtransfer.com'				],'_business/_money/webmoney.ru/']
,	[['freekassa.ru','fkwallet.com'			],'_business/_money//']
,	[['tinkoff.ru','tinkoff-debitcard.com'		],'_business/_money//']
,	[['donationalerts.ru','donationalerts.com'	],'_business/_money//']
,	[
		[	'alfabank.ru','alipay.com','alpari.com','americanexpress.com','anypay.io','anypayx.com','assist.ru'
		,	'banki.ru','bankinform.ru','bestchange.ru','brobank.ru'
		,	'cbr.ru','commishes.com','contact-sys.com','donatepay.ru','donorbox.org'
		,	'gazprombank.ru','gratipay.com','internetdengi.net','ko-fi.com','mdmbank.ru','moonpay.com','nalog.ru'
		,	'paykeeper.ru','payonline.ru','payonlinesystem.com','payssion.com','pochtabank.ru'
		,	'robinhood.com','rocketbank.ru','sberbank.ru','sovest.com','swift.com'
		,	'unionpayintl.com','unistream.ru','visa.com','webmoney.ru','xe.com','yoomoney.ru'
		]
	,	'_business/_money/'
	]
,	[['x5.ru'					],'_business/_shop/5ka.ru/']
,	[['dpdcart.com','getdpd.com'			],'_business/_shop//',{'sub': sub_domain_last_over_top2_exc_www}]
,	[['tmall.ru'					],'_business/_shop/aliexpress.com/']
,	[get_rei(r'^ali(baba|express|promo).\w+$'	),'_business/_shop/aliexpress.com',{'sub': sub_domain_exc_www}]
,	[get_rei(r'^amazon(\.com?)?\.\w+$'		),'_business/_shop/amazon.com']
,	[get_rei(r'^ebay(\.com?)?\.\w+$'		),'_business/_shop/ebay.com']
,	[get_rei(r'^nix(\d*|opt|-market)\.ru$'		),'_business/_shop/nix.ru']
,	[['player.ru'					],'_business/_shop/pleer.ru/']
,	[['magnit.ru','magnit.com'			],'_business/_shop//']
,	[['xcom-shop.ru','xcomspb.ru'			],'_business/_shop//']
,	[
		[	'5ka.ru','aliexpress.com','amazon.com','avito.ru','awkwardeverything.com'
		,	'bandb.ru','bookvoed.ru','brandcamp25.ru'
		,	'cafepress.com','caseguru.ru','cian.ru','citilink.ru','dakimarket.ru','dns-shop.ru'
		,	'ebay.com','etsy.com','fast-anime.ru','fastspring.com','geekmagazin.ru','globaldrive.ru','gresso.ru','guash.ru'
		,	'imaxai.ru','initialsite.com','joom.com','lecoshop.ru'
		,	'madrobots.ru','metta.ru','moyo.ua','mydozimetr.ru','myshopify.com'
		,	'ohmygeek.ru','okeyshop4.space','ozon.ru','pleer.ru','price.ru','regard.ru'
		,	'shopify.com','spreadshirt.com','startkid.ru','taobao.com','techbot.ru'
		]
	,	'_business/_shop/'
	]
,	[
		['russkii-print.online']
	,	'_business/_shop//'
	,	{
			'sub': [
				['_categories'		,['designers','tovari']]
			,	[get_rei(r'^/+(sale/+)?[^/?#]+/+[^/?#]+-\d+/+($|[?#])'	), r'_items']
			]
		}
	]
,	[[u'дакимакура.рф','xn--80aaanvlco2b3a.xn--p1ai'				],'_business/_shop//']
,	[[u'игрушки-дёшево.рф',u'игрушки-дешево.рф','xn----dtbbffobp5bn7a1de9j.xn--p1ai'],'_business/_toys//']
,	[[u'катушка-тесла.рф','xn----7sbaby0abl7cfdi9d.xn--p1ai'			],'_business/_toys//']
,	[
		[	'globen-shop.ru','globusy.ru','go-brick.ru','hottoys.com.hk','hydrotank.ru','kids-price.ru'
		,	'lego.com','lori-toys.ru','mosigra.ru','nashaigrushka.ru','nebosvod.ru','nordplast.ru'
		,	'sima-land.ru','tedico.ru','totomosaic.ru','tzar-elka.ru'
		]
	,	'_business/_toys/'
	]
,	[[u'моидокументы.рф','xn--d1achjhdicc8bh4h.xn--p1ai'		],'_business//']
,	[[u'мойбизнес.рф','xn--90aifddrld7a.xn--p1ai'			],'_business//']
,	[[u'объясняем.рф','xn--90aivcdt6dxbc.xn--p1ai'			],'_business//']
,	[[u'онлайнинспекция.рф','xn--80akibcicpdbetz7e2g.xn--p1ai'	],'_business//']
,	[[u'редкийметалл.рф','xn--80ahcbogfmag2b5a.xn--p1ai'		],'_business//']
,	[['forbes.com','forbes.ru','forbes.ua'			],'_business//']
,	[['government.ru','gov.ru'				],'_business//']
,	[['smazka.ru','smazka.ru.com'				],'_business//']
,	[
		[	'akademik-stroy.ru','alibaba.com','arctic-russia.ru','artishup.com','artistsnclients.com'
		,	'b-soc.ru','bcorporation.net','bestchange.ru','boycottrussia.info','businessinsider.com'
		,	'chistieprudi.info','cntd.ru','consultant.ru','creativecommons.org','croc.ru','crunchbase.com','dataspace.ru'
		,	'femida.us','fool.com','forentrepreneurs.com','freepassport.org'
		,	'go.jp','gopractice.ru','gosuslugi.ru','gov.kp','gs1.org'
		,	'indiehackers.com','ipwatchdog.com','irr.ru','kemitchell.com','kit.com','kse.ua'
		,	'licensezero.com','megafon.ru','mid.ru','mts.ru','nalog.ru'
		,	'pavluque.ru','pfrf.ru','polyformproject.org','producthunt.com','printerstudio.com','primeliber.com'
		,	'redbend.com','regionsoft.ru','roscontrol.com'
		,	'sap.com','seekingalpha.com','sovest.com','state.gov','statisfy.io','stripe.com','subway.ru','sunrisecity.ru'
		,	'ted.com','thebell.io','timetoplayfair.com','trello.com','uspto.gov'
		,	'vbr.ru','vc.ru','vc-petition.com','visualcapitalist.com'
		,	'wisdomgroup.com','worldconstitutions.ru','zemlya.store','zendesk.com'
		]
	,	'_business/'
	]

,	[
		[	'baidu.com','chinaru.info','cctv.com','cntechpost.com','ekd.me','gamer.com.tw','getit01.com','guancha.cn'
		,	'iichanchi.com','ixigua.com','lovemeinv2.com','news.cn','people.com.cn','perfare.net'
		,	'sbrnm.com','sina.com.cn','sinodefenceforum.com','sparatali.xyz','taipeitimes.com','tsutsu.cc','weibo.com'
		]
	,	'_China/'
	]

#--[ chats ]-------------------------------------------------------------------

,	[['0chat.top','matrix.org'				],'_conf/']
,	[['element.io','hello-matrix.net','rumatrix.org'	],'_conf/matrix.org/']
,	[['slack.com'						],'_conf/',{'sub': sub_domain_exc_www}]
,	[get_rei(r'^slack(hq)?\.\w+$'				),'_conf/slack.com/']
,	[['cascade.icu','elerium.org','orangecapybara.space'	],'_conf/shinkai_project/dev/Katod (Sabatur)/']
,	[['h903521b.beget.tech'					],u'_conf/shinkai_project/dev/moka (Шмока)/']
,	[['buldozerrepairs.tk','buldozerrepairs.appspot.com'	],'_conf/shinkai_project/dev/reivan.me//']
,	[['reivan.me','reivan.ru','reivan.github.io'		],'_conf/shinkai_project/dev//']
,	[['yarvanok.com'					],'_conf/shinkai_project/dev/']
,	[['ignis-sanat.org','ignis-sanat.com'			],'_conf/vndev/dev//']
,	[['discord.gg','discord.pw','discord.red','discordemoji.com','discordstatus.com','support.discord.com'],'_conf/discord.com/']
,	[
		['discord.com','discordapp.com']
	,	'_conf//'
	,	{
			'sub': [
				[get_rei(r'^/+channels?/+(\d+)([/?#]|$)'), r'_channels/\1']
			]
		}
	]

#--[ stuff ]-------------------------------------------------------------------

,	[
		[	'4woodsusa.com','amiami.com','amiami.jp','anatomicaldoll.com','babiki.ru','bululusexdoll.com','cutesexdoll.com'
		,	'dollfiedream.tokyo','dolk.jp','dolkus.com','dsdoll.ph','e2046.com','exdoll.com'
		,	'geekwars.ru','goodsmile.info','goodsmileshop.com','gunjap.net','ihaztoys.com'
		,	'miniqtoys.com','myfigurecollection.net','ninoma.com','onahole.com','otakumode.com','plamoya.com','realdoll.com'
		,	'sensualdolls.com','sexangelbaby.com','sexdollcenter.vip','sexdollsoff.com','sexydollies.com','sexysexdoll.com'
		,	'sup-b.ru','trottla.net','uusexdoll.com','vsdoll.net','yourdoll.com'
		]
	,	'_fig/'
	]

,	[get_rei(r'^d(eposit)?files\.\w+$'	),'_fileshares/depositfiles.com']
,	[get_rei(r'^freakshare\.\w+$'		),'_fileshares/freakshare.com']
,	[get_rei(r'^rapidshare\.\w+$'		),'_fileshares/rapidshare.com']
,	[get_rei(r'^rgho(st)?\.\w+$'		),'_fileshares/rghost.ru']
,	[['anonfile.com','anonfiles.com'			],'_fileshares//']
,	[['dropbox.com','dropboxusercontent.com','db.tt'	],'_fileshares//']
,	[['ifolder.ru','rusfolder.com','rusfolder.net'		],'_fileshares//']
,	[['pomf.se','uguu.se','pomf.cat','pantsu.cat','1339.cf'	],'_fileshares//']
,	[['safe.moe','catbox.moe'				],'_fileshares//']
,	[['uploadfiles.io','ufile.io'				],'_fileshares//']
,	[['yadi.sk','disk.yandex.ru'				],'_fileshares//']
,	[['zalil.ru','slil.ru','gfile.ru'			],'_fileshares//']
,	[
		['mega','mega:','mega.co.nz','mega.nz','megaupload.com','96d0d4e7-1ed7-4efb-99d0-b1bd780800b3']
	,	'_fileshares/MEGA'
	,	{
			'sub': [
				['_file'	,get_rei(r'^([^!#]*#+?)?(![\w-]+)$'	), r',#\2']
			,	['_folder'	,get_rei(r'^([^!#]*#+)?(F![\w-]+)$'	), r',#\2']
			,	['_file'	,get_rei(r'^(?:[^!#]*?)/+?file/+?([\w-]+)[!#]+([\w-]+)($|[^\w-])'	), r',#!\1!\2']
			,	['_folder'	,get_rei(r'^(?:[^!#]*?)/+folder/+([\w-]+)[!#]+([\w-]+)($|[^\w-])'	), r',#F!\1!\2']
			]
		}
	]
,	[
		[	'0x0.st','1fichier.com','2shared.com','4shared.com','axfc.net','anonymousdelivers.us','aww.moe'
		,	'bitcasa.com','bitshare.com','bowlroll.net','box.com','box.net'
		,	'doko.moe','dropmefiles.com','easyupload.io','embedupload.com'
		,	'fayloobmennik.cloud'
		,	'file.karelia.ru','file-up.org','file-upload.net'
		,	'filebin.net','filecloud.me','filedropper.com','filedwon.info','filefactory.com'
		,	'fileplanet.com','fileserve.com','filesmelt.com'
		,	'firedrop.com','funct.app'
		,	'ge.tt','getuploader.com','gofile.io','ichigo-up.com','ipfs.io','littlebyte.net','krakenfiles.com'
		,	'mediafire.com','mixtape.moe','multcloud.com','multiup.org','my-files.ru','nofile.io','nya.is'
		,	'odrive.com','rapidgator.net','sendspace.com','solidfiles.com','storagon.com','sync.com'
		,	'tinyupload.com','tmp.ninja','topshape.me','transfiles.ru','tstorage.info','turbobit.net'
		,	'ulozto.net','upload.cat','uploadable.ch','uploaded.net','uptobox.com'
		,	'vocaroo.com','webfile.ru','wikisend.com','workupload.com','zippyshare.com'
		]
	,	'_fileshares/'
	]

,	[['airesdejaen.com','kdv-group.com','moya-belarus.ru','yummi.club'			],'_food/']

#--[ fun ]---------------------------------------------------------------------

,	[['007b.com','brazzersnetwork.com','dosugfaq.pro','motherless.com','theporndude.com'	],'_fun/_18+/']
,	[['crafthought.com','ht-line.ru','marketgid.com','roomguru.ru','sh.st'			],'_fun/_ad/']
,	[['aika.ru','cdrr.ru','cdrrhq.ru','gadget-cdrr.ru','konorama.ru','theacorncafe.org','toonster.ru'],'_fun/Chip and Dale Rescue Rangers/']
,	[
		['world-art.ru']
	,	'_fun//'
	,	{
			'sub': [
				['_img/_mht'	,get_rei(r'^([^?#]*?[/_])?((galery_)?endcard|(animation_)?(poster|photos))(\.php)?($|[/?#])')]
			,	['_discussion'	,get_rei(r'^([^?#]*?[/_])?(comment(_all|_answer)?|discussion)(\.php)?($|[/?#])')]
			,	['_people'	,get_rei(r'^([^?#]*?[/_])?(people(_galery(_new)?)?)(\.php)?($|[/?#])')]
			,	['_staff'	,get_rei(r'^([^?#]*?[/_])?(((animation_)?full_)?cast)(\.php)?($|[/?#])')]
			,	['_manga'	,get_rei(r'^([^?#]*?[/_])?(manga)(\.php)?($|[/?#])')]
			,	['_animation'	,['animation','animation.php']]
			,	['_character'	,['character','character.php']]
			,	['_cinema'	,['cinema','cinema.php']]
			,	['_company'	,['company','company.php']]
			,	['_games'	,['games','games.php']]
			,	['_search'	,['search','search.php']]
			,	['_user'	,['account','account.php']]
			]
		}
	]
,	[get_rei(r'^(cook|joy|porn|safe)?reactor\.(cc|com)$'		),'_fun/joyreactor.cc']
,	[['aminoapps.com','golunapark.com','narvii.com'			],'_fun//']
,	[['ebanoe.it','ebanoe-it.ru'					],'_fun//']
,	[['nya.sh','nyash.org','nyash.org.ru','nyash.su','nya.re'	],'_fun//']
,	[['bash.im','bash.org.ru'					],'_fun//']
,	[['ithappens.ru','ithappens.me'					],'_fun/bash.im//']
,	[['zadolba.li'							],'_fun/bash.im/']
,	[['kym-cdn.com'							],'_fun/knowyourmeme.com/pix']
,	[[u'модные-слова.рф','xn----8sbfgf1bdjhf5a1j.xn--p1ai'		],'_fun//']
,	[
		[	'2x2tv.ru','4tob.ru','9gag.com','airpano.ru','anekdot.ru','aniworld.ru','astrosfera.ru'
		,	'bash.org','bobbypills.com','breakingmad.me','brrr.money','cheezburger.com','clientsfromhell.net','cracked.com'
		,	'dagobah.net','det.org.ru','developerslife.ru','dhmo.org','diginfo.tv','disemia.com','disney.com'
		,	'downloadmoreram.com','downloadmorerem.com'
		,	'fineleatherjackets.net','fishki.net','fucking-great-advice.ru','funimation.com','funnyjunk.com'
		,	'gieskes.nl','gooodnews.ru','govnokod.ru','guinnessworldrecords.com','hiddenlol.com','hiero.ru','how-old.net'
		,	'i-mockery.com','idaprikol.ru','illmosis.net','imgflip.com','imgrush.com'
		,	'instantrimshot.com','iwannarofl.com','izismile.com'
		,	'kaimi.ru','kg-portal.ru','killpls.me','knowyourmeme.com'
		,	'linorgoralik.com','live4fun.ru','lovelain.net'
		,	'me.me','medialeaks.ru','meme.institute','memepedia.ru','meming.world','movieforums.com','mrguy.com','myinstants.com'
		,	'neal.fun','netfunny.com','ninjaturtles.ru','okolnica.ru'
		,	'panorama.pub','pikabu.ru','pizudet.su','prikol.ru','qdb.us','quickmeme.com'
		,	'ribalych.ru','rinkworks.com','rottentomatoes.com'
		,	'sabbat.su','shitstream.ru','slanglang.net','snopes.com','splasho.com','swfchan.com'
		,	'thetvdb.com','dtop500.org','trinixy.ru'
		,	'thetvdb.com','top500.org','trinixy.ru'
		,	'unews.pro','visual-memory.co.uk','waitbutwhy.com','whatmeanings.com','whattolaugh.com'
		,	'yaplakal.com','yasdelie.ru','zen.ru'
		]
	,	'_fun/'
	]

#--[ games ]-------------------------------------------------------------------

,	[['chessprogramming.org','chesstactics.org','chessvariants.com','lichess.org'	],'_games/_chess/']
,	[['nesdev.com','parodius.com'							],'_games/_console,emul//']
,	[['nintendo.com','nintendo.ru'							],'_games/_console,emul//']
,	[['forums.pcsx2.net'								],'_games/_console,emul/pcsx2.net/']
,	[
		[	'asfdfdfd.com','coolrom.com','dosbox.com','dosbox-x.com'
		,	'emu-land.net','emu-russia.net','emuhq.com','emulation-evolved.net','emulatorgames.net','emuparadise.me'
		,	'gbatemp.net','kuribo64.net','mamedev.org','mametesters.org','mameworld.info','mgba.io','ngemu.com'
		,	'pcsx2.net','planetemu.net','problemkaputt.de','pspx.ru','psxdev.ru'
		,	'redump.net','romhack.net','romhacking.net','romhustler.net','romsgames.net','ryujinx.org','tic.computer','vba-m.com'
		]
	,	'_games/_console,emul/'
	]
,	[['csdb.dk','hitmen.c02.at','hitmen.eu'					],'_games/_cracking/']
,	[['kongregate.com'							],'_games/_flash/']
,	[['c2community.ru','construct.net','scirra.com'				],'_games/_making/Construct/']
,	[
		[	'gamemaker.io','gamemakerblog.com','gamemakerhub.net'
		,	'gmapi.gnysek.pl','gmlscripts.com','gmshaders.com','gmtoolbox.comslw-soft.com'
		,	'yal.cc','yoyogames.com'
		]
	,	'_games/_making/Game Maker/'
	]
,	[['godotdevelopers.org','godotengine.org','godotforums.org'		],'_games/_making/Godot/']
,	[['kha.tech','kode.tech','kodegarden.org'				],'_games/_making/Kode/']
,	[['rpg-maker.info','rpgmaker.net','rpgmaker.ru','rpgmakerweb.com'	],'_games/_making/RPG Maker/']
,	[get_rei(r'^rpg-?maker(web)?\.\w+$'					),'_games/_making/RPG Maker']
,	[['arongranberg.com','unity.cn','unity.com','unitydeveloperhub.com'	],'_games/_making/Unity/']
,	[['ludumdare.com','ldjam.com'						],'_games/_making//']
,	[
		[	'ancient-ritual.com','aggydaggy.com','anki3d.org','armory3d.org'
		,	'bcrc.site','buildnewgames.com','bulostudio.com'
		,	'castle-engine.io','charas-project.net','cocos2d-x.org'
		,	'danmaq.com','dea.su','decarpentier.nl','deconstructoroffun.com','defold.com'
		,	'gamedev.net','gamedev.ru','gamedeveloper.com','gamefromscratch.com','gamesdonequick.com','gamesjam.org'
		,	'gdconf.com','gdcvault.com','giderosmobile.com','globalgamejam.org'
		,	'heaps.io','impactjs.com'
		,	'ldtk.io','legion-engine.com','lexaloffle.com','love2d.org','ludiq.io','luxeengine.com','luxion.jp'
		,	'magnum.graphics','mod.io','monogame.net','moonworks.ru','neoaxis.com'
		,	'onehourgamejam.com','opengameart.org','orx-project.org','ourmachinery.com'
		,	'phatcode.net','pixelvision8.com','procedural-worlds.com','procjam.com','puzzlescript.net'
		,	'radgametools.com','redblobgames.com','rlgclub.ru','seventeencups.net','shiningrocksoftware.com','suvitruf.ru'
		,	'thegamecreators.com','tyranobuilder.com','unity.com','xsion.net'
		]
	,	'_games/_making/'
	]
,	[['forum.spaceengine.org','old.spaceengine.org','se-archive-project.net'],'_games/_space/spaceengine.org/']
,	[['stellarium-web.org'							],'_games/_space/stellarium.org/']
,	[
		[	'celestia.space','inovaestudios.com','kerbalspaceprogram.com'
		,	'orbit.medphys.ucl.ac.uk','orbiter.dansteph.com','orbithangar.com','orionsarm.com','outerra.com'
		,	'spaceengine.org','stellarium.org'
		]
	,	'_games/_space/'
	]
,	[get_rei(r'^dischan\.\w+$'	),'_games/dischan.org']
,	[get_rei(r'^gamejolt\.\w+$'	),'_games/gamejolt.com']
,	[get_rei(r'^mangagamer\.\w+$'	),'_games/mangagamer.com']
,	[['agar.io','agar-io.ru'			],'_games//']
,	[['caiman.us','dlxcaiman.net'			],'_games//']
,	[['candies.aniwey.net','candybox2.net'		],'_games//']
,	[['digital-synthesis.com','half-face.games'	],'_games//']
,	[['gamin.ru','gamin.me'				],'_games//']
,	[['kolenka.net','kolenka.su','turkey.kreguzda.ru'],'_games//']
,	[['feel-like-going-home.net','no-place-for-old-robots.net','noplace.me','yeo-no-blues.net'],'_games/kolenka.su/_personal/yeo']
,	[['gameved.ru'					],'_games/kolenka.su/_personal/nodoxi']
,	[['examples.url.ph'				],'_games/kolenka.su/_personal/Oxnard']
,	[['pxlpnd.do.am'				],'_games/kolenka.su/_personal/PixelPanda']
,	[['kozinaka.com','rubel.pw','veloc1.me'		],'_games/kolenka.su/_personal/']
,	[['faisu.net','kreguzda.ru'			],'_games/kolenka.su/']
,	[['nicoblog.org','nblog.org'			],'_games//']
,	[['nutaku.com','nutaku.net'			],'_games//']
,	[['playstation.com','playstation.net'		],'_games//']
,	[['renai.us','renpy.org'			],'_games//']
,	[['yager.de','specopstheline.com'		],'_games//']
,	[['cdprojektred.com','cdprojekt.com'		],'_games//']
,	[['gogalaxy.com'				],'_games/gog.com/']
,	[
		['gog.com']
	,	'_games//'
	,	{
			'sub': [
				[get_rei(r'^/*(?:' + part_lang + r'/+)?(?P<SubDir>game|checkout|order)(?=$|/+)'), '_shop/_\g<SubDir>']
			,	[get_rei(r'^/*(?:' + part_lang + r'/+)?(?P<SubDir>forum|wishlist)(?=$|/+)'), '_community/_\g<SubDir>']
			,	['_community/_user'	,get_rei(r'^/*(?:' + part_lang + r'/+)?(?P<SubDir>account|u|users?)(?=$|/+)')]
			,	['_shop/_game_list'	,get_rei(r'^/*(?:' + part_lang + r'/+)?(?P<SubDir>games|mix)(?=$|/+)')]
			,	['_shop'		,get_rei(r'^/*(?:' + part_lang + r'/+)?(?P<SubDir>redeem)(?=$|/+)')]
			# ,	['_shop/_game'		,['game']]
			# ,	['_shop/_game_list'	,['games','mix']]
			# ,	['_shop/_checkout'	,['checkout']]
			# ,	['_shop/_order'		,['order']]
			# ,	['_shop'		,['redeem']]
			# ,	['_community/_forum'	,['forum']]
			# ,	['_community/_wishlist'	,['wishlist']]
			# ,	['_community/_user'	,['u','user','users']]
			]
		}
	]
,	[
		['steamah.com','steamcommunity.com','steampowered.com','steamstatic.com']
	,	'_games/Steam/'
	,	{
			'sub': [
				[get_rei(r'^/*(?:' + part_lang + r'/+)?app/+(?P<AppID>\d+)/+(?P<SubDir>screenshots|images)/+'), r'_\g<SubDir>/\g<AppID>']
			,	['_account'	,['account','login','id','profiles']]
			,	['_agecheck'	,['agecheck']]
			,	['_app'		,['app','games','stats']]
			,	['_bundle'	,['bundle']]
			,	['_cart'	,['cart']]
			,	['_checkout'	,['checkout']]
			,	['_groups'	,['groups']]
			,	['_points'	,['points']]
			,	['_search'	,['search']]
			,	['_sharedfiles'	,['sharedfiles']]
			,	['_sub'		,['sub']]
			,	['_workshop'	,['workshop']]
			]
		}
	]
,	[
		[	'steamcardexchange.net','steamdb.info','steamgames.com','steamgifts.com','steamspy.com'
		,	'valvesoftware.com','valvetime.net'
		]
	,	'_games/Steam/'
	]
,	[['battle.net'							],'_games/Blizzard/']
,	[['playoverwatch.com'						],'_games/Blizzard/Overwatch/']
,	[['openbw.com','sc2mapster.com','starcraft.com'			],'_games/Blizzard/StarCraft/']
,	[['war2.ru'							],'_games/Blizzard/WarCraft/']
,	[['wowcircle.com','wowhead.com','wowwiki.com'			],'_games/Blizzard/WoW/']
,	[['chronocompendium.com','radical.or.tv'			],'_games/Chrono series/']
,	[['mentalomega.com','openra.net','renegade-x.com'		],'_games/C&C/']
,	[['d20pfsrd.com','dandwiki.com','dnd.su','dndbeyond.com','missingdice.com','wizards.com'],'_games/D&D/']
,	[['chaosforge.org','doom2d.org','doomwiki.org','doomworld.com','zdoom.org'	],'_games/DOOM/']
,	[['eve-ru.com','eveonline.com','eveuniversity.org','zkillboard.com'		],'_games/EVE Online/']
,	[['opencarnage.net','reclaimers.net'						],'_games/Halo/']
,	[['heroesofmightandmagic.com','homm.fun','homm3sod.ru','vcmi.eu'		],'_games/HoMM/']
,	[['elecbyte.com','mugenarchive.com'						],'_games/M.U.G.E.N/']
,	[['mariowiki.com'								],'_games/Mario/']
,	[['metroidwiki.org','supermetroid.run'						],'_games/Metroid/']
,	[['bulbagarden.net','serebii.net'						],'_games/Pokemon/']
,	[
		[	'king-soukutu.com','megaman-world.ru','megamanxcorrupted.com','mmhp.net','rockman-corner.com','rockmanpm.com'
		]
	,	'_games/Rockman (Megaman)/'
	]
,	[
		[	'gensokyo.org','gensoukyou.1000.tv','moriyashrine.org','shrinemaiden.org','tasofro.net'
		,	'toho-vote.info','touhou-project.news','touhoulostword.com','touhoumegane.blog.shinobi.jp','touhoureplays.com'
		,	'thpatch.net','walfas.org'
		]
	,	'_games/Touhou/'
	]
,	[['runescape.wiki'						],'_games/Runescape/']
,	[['imperial-library.info'					],'_games/TES,The Elder Scrolls/']
,	[['uoguide.com'							],'_games/Ultima Online/']
,	[['bladefirelight.com','openxcom.org'				],'_games/X-COM (UFO) series/']
,	[['yume-nikki.com','yumeboo.ru'					],'_games/Yume Nikki/']
,	[['doujinstyle.com','theguardianlegend.com'			],'_games/',{'sub': [['_forum',['forum','forums']]]}]
,	[['doujinstyle.info','wuala.com'				],'_games/doujinstyle.com/']
,	[['hg101.kontek.net'						],'_games/hardcoregaming101.net/']
,	[['blastermaster-zero.com'					],'_games/inticreates.com/']
,	[['shimmie.katawa-shoujo.com'					],'_games/katawa-shoujo.com/']
,	[['danmaku.mysteryparfait.com','flightoftwilight.com'		],'_games/mysteryparfait.com/']
,	[['neverball.org','neverforum.com'				],'_games//']
,	[
		[	'1morecastle.com','1up.com','4gamer.net','80.lv','8bitevolution.com'
		,	'abobosbigadventure.com','aidungeon.io','androidarts.com','anivisual.net'
		,	'arcsystemworks.jp','armitagegames.com','arrowheadgamestudios.com','arturgames.com','asenheim.org','atarata.ru'
		,	'battlerealms.cc','bit16.info','bngames.net','boxcar2d.com','bungie.org','buried-treasure.org'
		,	'cactusquid.com','caravelgames.com','cavestory.org','celestegame.com','chrono.gg','chushingura46.com'
		,	'ci-en.jp','cityofmist.co','com3d2.jp','compileheart.com','computeremuzone.com'
		,	'cross-code.com','cs.rin.ru','cybersport.ru'
		,	'dadgum.com','dailytelefrag.com','deepnight.net','deepsilver.com','denpasoft.com','desura.com','develz.org'
		,	'distractionware.com','dividebyzer0.com'
		,	'dodistribute.com','dogbytegames.com','drivethrurpg.com','dside.ru','dtf.ru','dxx-rebirth.com'
		,	'ea.com','empathybox.me','enderlilies.com','eneba.com','enthusiasts-ts.ru','epicgames.com'
		,	'erogames.com','erogegames.com','eroges.com'
		,	'escapistmagazine.com','espritgames.ru','esterior.net','eurogamer.net'
		,	'f95zone.to','famicase.com','fig.co','flyingomelette.com'
		,	'foddy.net','foreverapril.be','fortressofdoors.com','forzamotorsport.net'
		,	'frogatto.com','fullrest.ru','fuwanovel.net'
		,	'g123.jp','galyonkin.com','gamasutra.com'
		,	'game-debate.com','game-forest.com','gamebanana.com','gamebook.pw','gamecolon.com','gamefaqs.com'
		,	'gamemux.com','gamenet.ru','gamepedia.com','gamer.ru','gameranx.com'
		,	'gameseijininspirata.com','gamesp.net','gamesplanet.com','gamespot.com','gametrax.eu'
		,	'gcup.ru','glitchkitty.com','gonintendo.com','gotm.io','granbluefantasy.jp','gravediggerslocal.com'
		,	'hangsim.com','hardcoregaming101.net','hiddenpalace.org','hongfire.com','howlongtobeat.com','hpgames.jp'
		,	'ice-pick.com','idyllicpixel.com','ign.com','igromania.ru','igryflesh.ru'
		,	'indiedb.com','insani.org','inticreates.com','itch.io'
		,	'jellymar.io','jetpacksquad.com','jmpdrv.com','jrouwe.nl','js13kgames.com','jugglingsoot.com'
		,	'kanobu.ru','katawa-shoujo.com','killscreendaily.com'
		,	'kogado.com','koromosoft.com','konjak.org','kotaku.com','krasfs.ru','kyrieru.com'
		,	'laingame.net','latitude.io','legendsoflocalization.com','legendsworld.net','lewdgamer.com','lf2.net'
		,	'libregamewiki.org','lionwood-studios.com','lokator-studio.ru','loverslab.com','lparchive.org','ludomancy.com','lutris.net'
		,	'massiveassault.com','masterunitlist.info','maxplay.io','mclelun.com'
		,	'meetandfuckgames.com','megainformatic.ru','mehen-games.com'
		,	'mightyno9.com','moai.games','mobygames.com','moddb.com','moregameslike.com','motion-twin.com'
		,	'myabandonware.com','mysteryparfait.com'
		,	'naarassusi-game.ru','namikaze.org','nd.ru','nexon.com','ndemiccreations.com'
		,	'neatcorporation.com','neoseeker.com','nethack.org','newgrounds.com','nexusmods.com'
		,	'nicalis.com','nintendolife.com','nisamerica.com','noelberry.ca','nrvnqsr.com'
		,	'old-games.com','old-games.ru','oneangrygamer.net','onegameamonth.com','onlyhgames.com'
		,	'osu.ppy.sh','outfit7.com','oxygine.org'
		,	'pcgamer.com','pcgamingwiki.com','phantasy-star.net','pikointeractive.com','pixeljoint.com'
		,	'playism.com','polygon.com','positech.co.uk','primitive-games.jp','projectwritten.com'
		,	'raphkoster.com','ratalaikagames.com','rawg.io'
		,	'rednuht.org','remar.se','renegadeware.com','resetera.com','revora.net'
		,	'roblox.com','rockpapershotgun.com','rockstargames.com','roguetemple.com','rpg.net','rpgcodex.net','ruinergame.com'
		,	'sakevisual.com','scmapdb.com','sefan.ru','sekaiproject.com','sgn.net','shedevr.org.ru','shmuplations.com','shmups.com'
		,	'siliconera.com','sinemoragame.com','skullgirls.com','smaghetti.com','small-games.info','smwstuff.net','snk-games.net'
		,	'socksmakepeoplesexy.net','softhouse-seal.com','sonicretro.org','sovietgames.su'
		,	'speedrun.com','spriters-resource.com','spritesmind.net'
		,	'square-enix-games.com','squarefaction.ru','squares.net','squidi.net'
		,	'stabyourself.net','stopgame.ru','summertimesaga.com'
		,	'strategycore.co.uk','strategywiki.org','suki.jp','sunrider-vn.com','superhippo.com','sureai.net','system11.org'
		,	'tasvideos.org','tatrix.org','tcrf.net','ternoxgames.com','tesera.ru'
		,	'the-tale.org','theclassicgamer.net','thegamer.com','themissingquests.com','three-eyed-games.com'
		,	'tigsource.com','tinykeep.com','totaljerkface.com','tozicode.com','trinitymugen.net','tv-games.ru','twoweeks.ru'
		,	'ultimatehistoryvideogames.jimdofree.com','unepicgame.com','unseen64.net','usamin.info','uvlist.net'
		,	'vg247.com','vgmuseum.com','vkplay.ru','vlambeer.com','vn-russian.ru','vndb.org','vogons.org','vogonswiki.com'
		,	'warframe.com','warnworld.com','wayforward.com','wesnoth.org','wieringsoftware.nl','worldoftanks.ru','worldofwarships.ru'
		,	'xgm.guru','xitilonic.art','xseedgames.com','xsolla.com','yardteam.org','zoom-platform.com'
		]
	,	'_games/'
	]

#--[ devices ]-----------------------------------------------------------------

,	[['6p3s.ru','cqham.ru','cxem.net','digitalina.ru','qrz.ru','radiokot.ru','radioscanner.ru','radiostroi.ru'],'_hardware/_DIY/']
,	[[u'всепули.рф','xn--b1agjltkq.xn--p1ai'				],'_hardware/_weapons//']
,	[['kalashnikov.com','kalashnikovgroup.ru'				],'_hardware/_weapons//']
,	[['kalashnikov.ru','lobaevarms.ru','sandboxx.us'			],'_hardware/_weapons/']
,	[['cosonic.net.cn','doctorhead.ru'					],'_hardware/_audio/']
,	[['adexelec.com','ameri-rack.com'					],'_hardware/_cables,ports/']
,	[['dahua-spb.ru','dahuasecurity.com','dahuawiki.com','dh-russia.ru'	],'_hardware/_cam/']
,	[['eraworld.ru','svetlix.ru'						],'_hardware/_lamp/']
,	[['4pda.ru','4pda.to'							],'_hardware/_mobile,phone,tablet//']
,	[['alcatelonetouch.com','alcatelonetouch.eu','alcatel-mobile.com'	],'_hardware/_mobile,phone,tablet//']
,	[['irbis-digital.ru','irbis.biz'					],'_hardware/_mobile,phone,tablet//']
,	[
		[	'allnokia.ru','androidmtk.com','aq.ru','auroraos.ru','butouch.ru','coolstylecase.com','cubot.net'
		,	'gsmarena.com','gsmforum.ru','icover.ru','j-phone.ru','leagoo.com'
		,	'micromaxinfo.com','micromaxstore.ru','mobile-review.com','msggsm.com','mzarya.ru','nokia.com'
		,	'repairmymobile.in','soft112.com','wexler.ru'
		]
	,	'_hardware/_mobile,phone,tablet/'
	]
,	[get_rei(r'^netgear\.\w+$'),'_hardware/_net/netgear.com']
,	[
		[	'advancedtomato.com','arhab.org','asuswrt.lostrealm.ca','broadcom.com','cisco.com'
		,	'dd-wrt.com','granit-radio.ru','lede-project.org','openswitch.net'
		,	'routerguide.net','rtl-sdr.com','snbforums.com','tomato.groov.pl','trendnet.com','vstarcam.ru'
		]
	,	'_hardware/_net/'
	]
,	[
		['airliners.net']
	,	'_hardware/_transport,vehicles/'
	,	{
			'sub': [
				['_forum'	,['forum','forums']]
			,	['_photo'	,['photo']]
			,	['_albums'	,['photo-albums','photo-album','album','albums']]
			,	['_search'	,['search']]
			,	['_users'	,['user','users']]
			]
		}
	]
,	[
		[	'aerolodka38.ru','airboat.ru','airwar.ru'
		,	'americanmusclecar.ru','audi.co.uk','auto.ru','autoreview.ru','avtodom.ru','atvrusak.ru'
		,	'bibimot.ru','bikepost.ru','bikerwiki.ru','burancar.com'
		,	'camper4x4.ru','comma.ai','drive2.ru','drom.ru','electrotransport.ru','euroresgroup.ru'
		,	'f-16.net','flyingship.co','forumavia.ru','fotobus.msk.ru','garagashyan.ru','gvtm.ru'
		,	'liaz-677.ru','lilium.com','motochrome.net','motoforum.ru','motor.ru','northhunter.com'
		,	'pelec.ru','polestar.com','porsche.com','rhc.aero','rutrike.ru','segway.cz','sherp.ru','somanyhorses.ru','spacex.com'
		,	'taifun.tech','tanks-encyclopedia.com','tesla.com','tinger.ru','trecol.ru','uazbuka.ru','uralaz.ru','zapata.com'
		]
	,	'_hardware/_transport,vehicles/'
	]
,	[get_rei(r'^avtoros\.\w+$'						),'_hardware/_transport,vehicles/Avtoros']
,	[['fireman.ru','fireman.club'						],'_hardware/_transport,vehicles//']
,	[['paralay.ru','paralay.iboards.ru'					],'_hardware/_transport,vehicles//']
,	[[u'аэровездеходы.рус','xn--80aegadbm7cfn5d0dp.xn--p1acf'		],'_hardware/_transport,vehicles//']
,	[[u'китайские-автомобили.рф','xn----7sbbeeptbfadjdvm5ab9bqj.xn--p1ai'	],'_hardware/_transport,vehicles//']
,	[['apacer.com','flashboot.ru','mydigit.net','rmprepusb.com','sandisk.com','upan.cc','usbdev.ru'],'_hardware/_storage/_flash,cards,SD,USB/']
,	[['cdfreaks.com','cdrinfo.com','domesday86.com','dvdfab.cn'		],'_hardware/_storage/_CD,DVD,BD,optical_drives/']
,	[
		[	'backblaze.com','datarc.ru','hdd-911.com','hddmag.com','hddmasters.by','hddscan.com'
		,	'rlab.ru','seagate.com'
		]
	,	'_hardware/_storage/_HDD/'
	]
,	[['easeus.com','partition-tool.com'					],'_hardware/_storage/_HDD//']
,	[['hgst.com','hitachigst.com'						],'_hardware/_storage/_HDD//']
,	[['wd.com','wdc.com','wdc.custhelp.com','westerndigital.com'		],'_hardware/_storage/_HDD//']
,	[['ocz.com','ocztechnologyforum.com'					],'_hardware/_storage/_SSD//']
,	[['silicon-power.com','ssd-life.com','ssdboss.com','storagegaga.com'	],'_hardware/_storage/_SSD/']
,	[['ddrdrive.com','hybridmemorycube.org','jedec.org','memtest.org','radeonramdisk.com'],'_hardware/_storage/_RAM,memory/']
,	[['enmotus.com','kingston.com','storagereview.com','win-raid.com'	],'_hardware/_storage/']
,	[['angstrem.ru','baikalelectronics.ru','cpuboss.com','mcst.ru'		],'_hardware/_CPU/']
,	[['htcvive.com','oculus.com','uploadvr.com'		],'_hardware/_VR/']
,	[['coolermaster.com','kingpincooling.com'		],'_hardware/_cooling/']
,	[['thermaltake.com','thermaltakeusa.com'		],'_hardware/_cooling/']
,	[['flatpanelshd.com','lagom.nl','tftcentral.co.uk'	],'_hardware/_display,monitor/']
,	[['azeron.eu','banggood.com','keysticks.net','migamepad.com','redragon.ru','rewasd.com','steelseries.com'],'_hardware/_controls/']
,	[['jtksoft.net','joytokey.net'				],'_hardware/_controls//']
,	[['trust.com','ugee.net','yiynova.su'			],'_hardware/_controls/_graphic_tablet/']
,	[['bosto-tablet.com','kingtee.ru'			],'_hardware/_controls/_graphic_tablet//']
,	[['xp-pen.com','xp-pen.ru','storexppen.com'		],'_hardware/_controls/_graphic_tablet//']
,	[get_rei(r'^huion-?(tab(let)?)?(\.com?)?\.\w+$'		),'_hardware/_controls/_graphic_tablet/huion.com']
,	[get_rei(r'^wacom(eng)?(\.com?)?\.\w+$'			),'_hardware/_controls/_graphic_tablet/wacom.com']
,	[['aopen.com','evga.com','gpuboss.com','gpucheck.com','gpuinfo.org','gpuopen.com','guru3d.com'],'_hardware/_GPU/']
,	[get_rei(r'^elsa(-jp)?(\.com?)?\.\w+$'			),'_hardware/_GPU/elsa.com']
,	[get_rei(r'^dlink(tw)?(\.com?)?\.\w+$'			),'_hardware/_net/dlink.com']
,	[get_rei(r'^mikrotik\.\w+$'				),'_hardware/_net/mikrotik.com']
,	[get_rei(r'^tp-?link-?(ru|repeater|extender)?\.\w+$'	),'_hardware/_net/tp-link.com']
,	[get_rei(r'^zyxel\.\w+$'				),'_hardware/_net/zyxel.com']
,	[['batareiki.by','batteries.gr','csb-battery.com','upsbatterycenter.com'],'_hardware/_power/_UPS/_batteries/']
,	[['hiden-eps.ru','power-software-download.com','riello-ups.com'		],'_hardware/_power/_UPS/']
,	[get_rei(r'^apc+(\.com?)?\.\w+$'					),'_hardware/_power/_UPS/apc.com']
,	[get_rei(r'^eaton+(\.com?)?\.\w+$'					),'_hardware/_power/_UPS/eaton.com']
,	[get_rei(r'^gpbatteries(\.com?)?\.\w+$'					),'_hardware/_power/gpbatteries.com']
,	[['power-m.ru','robiton.ru'						],'_hardware/_power/']
,	[get_rei(r'^(canon|c-ij)(\.\w+)?$'			),'_hardware/_printer/canon.com']
,	[get_rei(r'^epson(\.com?)?\.\w+$'			),'_hardware/_printer/epson.com']
,	[get_rei(r'^fix-free\.\w+$'				),'_hardware/_printer/fix-free.ru']
,	[get_rei(r'^(fuji)?xerox(\.com?)?\.\w+$'		),'_hardware/_printer/xerox.com']
,	[['brother.ru','driversprintercanon.com','hi-black.ru','net-product.ru','t2now.ru'],'_hardware/_printer/']
,	[get_rei(r'^(eu-|\.eu|\.com?)?aiwa(-rus|\.eu|\.com?)?\.\w+$'),'_hardware/aiwa.com']
,	[get_rei(r'^asus(\.com?)?\.\w+$'			),'_hardware/asus.com']
,	[get_rei(r'^asmedia(\.com?)?\.\w+$'			),'_hardware/asmedia.com.tw']
,	[get_rei(r'^ecs(\.com?)?\.\w+$'				),'_hardware/ecs.com.tw']
,	[get_rei(r'^genius(net?)?\.\w+$'			),'_hardware/genius.com']
,	[['gigabyte.ru'						],'_hardware/gigabyte.com/']
,	[get_rei(r'^gigabyte(\.com?)?\.\w+$'			),'_hardware/gigabyte.com']
,	[get_rei(r'^hikvision\.\w+$'				),'_hardware/hikvision.com']
,	[get_rei(r'^huawei\.\w+$'				),'_hardware/huawei.com']
,	[get_rei(r'^ifixit\.\w+$'				),'_hardware/ifixit.com']
,	[get_rei(r'^intel\.\w+$'				),'_hardware/intel.com']
,	[get_rei(r'^nikon(\.com?)?\.\w+$'			),'_hardware/nikon.com']
,	[get_rei(r'^(nvidia|geforce)\.\w+$'			),'_hardware/nvidia.com']
,	[get_rei(r'^panasonic\.\w+$'				),'_hardware/panasonic.com']
,	[get_rei(r'^philips\.\w+$'				),'_hardware/philips.com']
,	[get_rei(r'^sony(\.com?)?\.\w+$'			),'_hardware/sony.com']
,	[get_rei(r'^supermicro(\.com?)?\.\w+$'			),'_hardware/supermicro.com']
,	[get_rei(r'^via(-*(embedded|labs|tech))*(\.com?)?\.\w+$'),'_hardware/via.com.tw']
,	[get_rei(r'^zalman(\.com?)?\.\w+$'			),'_hardware/zalman.com']
,	[get_rei(r'^amd(-*(club|surveys?)+)\.\w+$'		),'_hardware/amd.com/']
,	[get_rei(r'^samsung(-*(mobile|press))+(\.com?)?\.\w+$'	),'_hardware/samsung.com/']
,	[['amd.com'						],'_hardware//',{'sub': sub_domain_exc_www_directly}]
,	[['arachnidlabs.com','notdot.net'			],'_hardware//']
,	[['hackaday.com','hackaday.io'				],'_hardware//']
,	[['logitech.com','logitechg.com','logi.com'		],'_hardware//']
,	[['passmark.com','videocardbenchmark.net'		],'_hardware//']
,	[['st-lab.com','st-lab.ru','sunrichtech.com.hk'		],'_hardware//']
,	[['tomshardware.com','tomshardware.co.uk'		],'_hardware//']
,	[['valid.x86.fr','valid.canardpc.com'			],'_hardware//']
,	[[u'проектдуюнова.рф','xn--80adfdztdedkzn7l.xn--p1ai'		],'_hardware/Duyunov motors//']
,	[[u'мотор-колесо.рус','xn----jtboecmaccoqe.xn--p1acf'		],'_hardware/Duyunov motors//']
,	[['duyunovmotors.ru','motor-koleso-duyunova.ru','solargroup.pro'],'_hardware/Duyunov motors/']
,	[
		['nedopc.com','speccy.info','spectrum4ever.org','spectrumcomputing.co.uk','worldofspectrum.org','zxart.ee','zxpress.ru']
	,	'_hardware/ZX Spectrum/'
	]
,	[
		get_rei(r'^ixbt\.\w+$')
	,	'_hardware/ixbt.com'
	,	{
			'sub': [
				[get_rei(r'^(?:\w+:/+)?(?:(?:www|mobile)\.)forums?\.ixbt\.\w+(?:$|/)'	),'_forum']
			,	['_forum'	,['forum','forums']]
			,	['_news'	,['news','live']]
			]
		}
	]
,	[
		[	'3ders.org','3dmark.com','5kwt.ru','51cto.com'
		,	'acer.com','afox-corp.com','altera.com','amd.by','amperka.ru','analogmuseum.org','anandtech.com'
		,	'arm.com','asrock.com','asrockrack.com','atb-e.ru','atmel.com'
		,	'bitblaze.ru','breaknes.com','chipsandcheese.com','computer34.ru','computeruniverse.ru','crown-micro.com'
		,	'dadget.ru','datamath.org','defender.ru','dell.com','deskthority.net'
		,	'dialoginvest.com','digitalfaq.com','digitalchip.ru','digital-razor.ru','dkc.ru','deltacomputers.ru','dorfa.ru'
		,	'electronshik.ru','elerus.ru','espada-tech.ru','exegate.ru','fccid.io','ferra.ru','flextron.ru','fplustech.ru'
		,	'gamemaxpc.com','garnizon.su','gearbest.com','goal.ru','gooxi.us','hp.com','htc.com','hwcompare.com','hyperpc.ru'
		,	'ibm.com','innovatefpga.com','iot.ru','irecommend.ru','kfa2.com','kinesis-ergo.com','kitguru.net'
		,	'lamptest.ru','legolini.com','lenovo.com','lg.com','libre.computer'
		,	'logicalincrements.com','lostarmour.info','lowrisc.org','lowtechmagazine.com','lucidlogix.com'
		,	'marsohod.org','marvell.com','mcgrp.ru','mew-hpm.ru','micron.com','mikron.ru','mini-itx.com'
		,	'motherboard.vice.com','msi.com','mvideo.ru'
		,	'nefteresurs.ru','netac.com','newegg.com','notebookcheck.net','npo-at.com','nwht.ru'
		,	'odroid.com','old-computers.com','oldi.ru','openbenchmarking.org','opentitan.org'
		,	'outsidethebox.ms','overclock.net','overclockers.com','overclockers.ru'
		,	'patriotmemory.com','pcnews.ru','perfeo.ru','pjrc.com','pocketbook-int.com','polycom.com','powercube.ru'
		,	'quadrone.ru','qualcomm.com','qumo.ru'
		,	'raspberrypi.org','rbs-computers.ru','robo-hunter.com','rocketboards.org','rozetka.com.ua','rusograda.ru'
		,	'samsung.com','sannata.ru','scanofthemonth.com','sotel.su','sparkfun.com'
		,	'startech.com','station-drivers.com','sunrise.ru','sven.fi','svyaznoy.ru'
		,	'technopoint.ru','techpowerup.com','tehnologys.ru','terasic.com.tw'
		,	'thesycon.de','thg.ru','thingiverse.com','thinkwiki.org','thirdpin.io','tonk.ru','tripplite.com','ts.ru'
		,	'ulmart.ru','usbkill.com','unitsolutions.ru','userbenchmark.com','wccftech.com','westcomp.ru','yadro.com','zenitco.ru'
		]
	,	'_hardware/'
	]

#--[ pictures ]----------------------------------------------------------------

,	[get_rei(r'^gensokyo.4otaku\.\w+$'	),'_img/4otaku.ru/gensokyo.4otaku.ru']
,	[get_rei(r'^4otaku\.\w+$'		),'_img/4otaku.ru']
,	[get_rei(r'^ricegnat\.\w+$'		),'_img/ricegnat.moe']
,	[
		['deviantart.com','sta.sh']
	,	'_img//'
	,	{
			'sub': [
				[pat_subdomain_exc_www, r'_mht/_personal/\g<LastOverTop2>']
			,	'_mht'
			]
		}
	]
,	[['yerkaland.com','yerka.org.ru'	],'_img//']
,	[
		[	'booth.pm','chat.pixiv.net','dic.pixiv.net','fanbox.cc','pawoo.net'
		,	'pixiv.dev','pixiv.help','pixivision.net','sketch.pixiv.net','spotlight.pics'
		]
	,	'_img/pixiv.net/'
	]
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
			,	['_mht/illust'		,get_rei(r'^/+\w+/+artworks/+(\d+)'				), r',illust_id=\1']
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
,	[['gramunion.com','studiomoh.com','tumgir.com'	],'_img/tumblr.com/']
,	[['media.tumblr.com'				],'_img/tumblr.com/_pix']
,	[['txmblr.com','www.tumblr.com'			],'_img/tumblr.com',{'sub': [['_video',['video']],'_mht']}]
,	[['tumblr.com'					],'_img/tumblr.com/_mht/_personal',{'sub': [['_post',['post']],'_subdomain']}]
,	[
		[	'animizer.net','ezgif.com','gfycat.com','gifcreator.me','gifmagic.com','giphy.com'
		]
	,	'_img/_animated/'
	]
,	[get_rei(r'^0-?chan\.\w+$'			),'_img/_board/0chan.ru',subscrape]
,	[get_rei(r'^2-?chru\.\w+$'			),'_img/_board/2chru.net']
,	[get_rei(r'^m?2-?ch\.(cm|ec|hk|life|pm|ru|so)$'	),'_img/_board/2ch.so',subscrape]
,	[['largeb.ru'					],'_img/_board/2ch.so/']
,	[
		['4chan.org','4channel.org']
	,	'_img/_board//'
	,	{
			'sub_threads': [
				['_scrape/_e_ - Ecchi',['d','e','h','u']]
			,	'_scrape/_etc'
			]
		,	'sub': sub_b
		}
	]
,	[
		[	'4archive.org','4chanarchive.org','4plebs.org'
		,	'archive.moe','archived.moe','archiveofsins.com'
		,	'desuarchive.org','desustorage.org','fireden.net','foolz.us'
		,	'illegal.pics','loveisover.me','nyafuu.org','plus4chan.org'
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
		,	'sub': sub_a + [
				[unscrape, get_rei(r'''
					^err(or(s)?)?/
				|	^[^/?#]+/+arch/+(res|\d+)/+([?#]|$)
				|	^\.[\w-]+(/|$)
				|	^[\w-]+\.\w+([?#]|$)
				''')]
			]
			# + sub_d
			+ sub_b
		}
	]
,	[get_rei(r'^(8ch|8chnl|8chan|8channel)(\.neocities)?\.\w+$'),'_img/_board/8channel.org']
,	[get_rei(r'^dobrochan\.\w+$'				),'_img/_board/dobrochan.ru',{'sub_threads': '_scrape', 'sub': sub_a + sub_b}]
,	[get_rei(r'^zenchan\.\w+$'				),'_img/_board/zenchan.hk']
,	[['rei-ayanami.com','asuka-langley-sohryu.com','lsa.su'	],'_img/_board//']
,	[['horochan.ru','hanabira.ru','i-bbs.org','mayuri.ru'	],'_img/_board//']
,	[['survey.ii.yakuji.moe'				],'_img/_board/iichan.ru/yakuji.moe/']
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
		,	'ii.yakuji.moe','ii-search.appspot.com','iichan.moe','unylwm.appspot.com'
		]
	,	'_img/_board/iichan.ru/!_undelete,mirrors,etc/'
	]
,	[
		['iichan.ru','iichan.hk','haruhiism.net','95.211.138.158']
	,	'_img/_board//'
	,	{
			'sub_threads': [
				[None, get_rei(r'^/+(cgi-bin|d|err)/|^/+[^/?#]+/+arch/+(res|\d+)/+([?#]|$)')]
			,	[get_rei(r'^[^#]*#(.*?\D.*[^/.]|.*[^\d/.])[/.]*$'), r'!_tar,thread_archives/\1']
			,	['_scrape/_a_ - Anime'			,['a','aa','abe','azu','c','dn','fi','hau','ls','me','rm','sos']]
			,	['_scrape/_b_ - Bred'			,['b']]
			,	['_scrape/_h_ - Hentai'			,['g','h']]
			,	['_scrape/_hr_ - HiRes & requests'	,['hr','r']]
			,	['_scrape/_m_ - Macros & mascots'	,['m','misc','tan','tenma']]
			,	['_scrape/_to_ - Touhou'		,['to']]
			,	['_scrape/_n_prev'			,['n']]
			,	'_scrape/_etc'
			]
		,	'sub': sub_a + [
			#	[unscrape+'/_h'	,get_rei(r'(^|\w+\.)hii(chan)?\.\w+/')]
				[unscrape+'/_n'	,['n','index','index.html','']]
			,	[unscrape	,['cgi-bin','err']]
			,	[unscrape	,get_rei(r'^/+[^/?#]+([?#]|$)')]
			] + sub_d
		}
	]
,	[get_rei(r'^(iichan|official)-eroge(-[\w-]+)?\.blogspot\.\w+$'			),'_img/_board/iichan.ru/eroge']
,	[['esonline.tk','everlastingsummer.su'						],'_img/_board/iichan.ru/eroge/']
,	[['iihub.org','iinet.tk'							],'_img/_board/iichan.ru/dev//']
,	[['2chance-projects.ru','iichantra.ru','neon.org','openchannel.tk'		],'_img/_board/iichan.ru/dev/']
,	[['hramopedia.esy.es'								],'_img/_board/iichan.ru/RPG chat/']
,	[['coyc.net','eientei.org','ichan.ru','iibooru.org','noobtype.ru','yakuji.moe'	],'_img/_board/iichan.ru/']
,	[['ii-chan.ru','iichan.me','ii.dollchan.org','i.dollchan.org'			],'_img/_board/dollchan.org//',subscrape]
,	[['1chan.ru','1chan.ca'				],'_img/_board//']
,	[['2cat.org','2cat.club','2nyan.org'		],'_img/_board//']
,	[['3chan.co','3chan.ml'				],'_img/_board//',subscrape]
,	[['dollchan.org','dollchan.ru'			],'_img/_board//']
,	[['endchan.net','endchan.org','endchan.xyz'	],'_img/_board//']
,	[['freedollchan.org','dollchan.net'		],'_img/_board//']
,	[['gurochan.ch','gurochan.cx'			],'_img/_board//']
,	[['kurisu.ru','kurisa.ch'			],'_img/_board//']
,	[['miskatonic.ml','miskatonic.ko.tl','m-ch.ml'	],'_img/_board//']
,	[['tbpchan.net','tbpchan.cz'			],'_img/_board//']
,	[['xynta.ch','nahuya.ch'			],'_img/_board//']
,	[['wakachan.org','secchan.net'			],'_img/_board//',subscrape]
,	[['zerochan.in','snyb.tk','jaggy.site90.net'	],'_img/_board//']
,	[['touhou-project.com','touhouproject.com'	],'_img/_board//']
,	[['arhivach.org','arhivach.cf','arhivach.net','arhivach.ng','arhivach.top'],'_img/_board//']
,	[
		[	'13ch.ru','2chan.net','4-ch.net','d3w.org','lampach.net','lolifox.org','n0l.ch','nowere.net'
		,	'owlchan.ru','rollach.ru','sibirchan.ru','zadraw.ch'
		]
	,	'_img/_board/'
	,	subscrape
	]
,	[
		[	'014chan.org','02ch.in','0m3ga.ga','1-chan.ru','100ch.ru','10ch.ru','12ch.ru','1chan.net'
		,	'2--ch.ru','2-ch.su','2ch.lv','2ch.net','2ch.rip','2channel.net','2channel.ru','2chru.net'
		,	'2watch.in','24random.fun','28chan.org'
		,	'314n.org','5channel.net','600chan.ga','9ch.in','9ch.ru','9chan.tw'
		,	'a2ch.ru','alphachan.org','alterchan.net','animuchan.net','anoma.ch','anonib.ru'
		,	'apachan.net','ascii.geekly.info','atomchan.net'
		,	'baka.tk','bakachan.org','bibanon.org','bluethree.us','boatchan.ml','brchan.org','bunbunmaru.com','bvffalo.land'
		,	'c-board.org','chanon.ro','chanpangur.ru','chanstat.ru','chanverse.uwu.mx'
		,	'chaos.fm','crychan.ru','cultnet.net','cunnychan.org'
		,	'deachrysalis.cc','depreschan.ovh','desulauta.org','devchach.ru'
		,	'doushio.com','dscript.me','dva-ch.net','dva-ch.ru'
		,	'e3w.ru','ech.su','erlach.co','ernstchan.xyz'
		,	'fchan.us','freeport7.org','futaba-only.net','futatsu.org'
		,	'gaech.org','gaika.ch','gamechan.ru','gchan.ru','gemchan.net','glauchan.org','green-oval.net'
		,	'haibane.ru','hatsune.ru','hexchan.org','hikkachan.us','hispachan.org','hivemind.me','honokakawai.com'
		,	'ib.wtf','ibaka.ru','ichan.org','idlechan.net','iichan.net','iiichan.net','inach.org','ivchan.org','jsib.ml'
		,	'kakashi-nenpo.com','kazumi386.org','kissu.moe','kohlchan.net','komica.org','krautchan.net','kyber.io'
		,	'lapchan.moe','lenta-chan.ru','lolcow.farm','loopchan.top','lotusbbs.org','lucidchan.org','lulz.net','lynxhub.com'
		,	'maruchan.ru','metachan.ru','microchan.net','midorichan.ru'
		,	'neboard.me','neonchan.vip','nest.rf.gd','netchan.ru','nichan.net','nowai.ru','nullchan.org','nyamo.org'
		,	'ololoepepe.me','osach.ru','outchan.cf','overchan.ru','owlchan.ru'
		,	'pinkchan.top','ponyach.ru','post0chan.ru','pregchan.com','rakochan.ru','rchan.ru','retrochan.org','rfch.rocks'
		,	'samechan.ru','shanachan.org','sich.co','slothchan.net','smuglo.li','so-slow.com','spamchan.xyz','spirech.org','syn-ch.ru'
		,	'tanami.org','tchan.fun','tinyboard.org','tripfags.com','trln.hk','twbbs.org'
		,	'u18chan.com','uboachan.net','uchan.to','ukrachan.org','utochan.ru'
		,	'vichan.net','void.rest','volgach.ru','voxpopuli.to','wizchan.org'
		,	'xchan.ru','yakui.moe','yochan.org','yotsubasociety.org','zchan.cc','zenchan.xyz','zloiodm.in'
		]
	,	'_img/_board/'
	]
,	[['booru.org'			],'_img/_booru/',{'sub': sub_domain_last_over_top2_exc_www}]
,	[['derpiboo.ru','derpibooru.org'],'_img/_booru//']
,	[['konachan.com','konachan.net'	],'_img/_booru//']
,	[['yande.re','imouto.org'	],'_img/_booru//']
,	[['rule34.xxx','paheal.net'	],'_img/_booru//']
,	[['ecchi.me','animekon.com','ahmygoddesshentai.com','koribi.net','naughtytentaclehentai.com','hentaipornimages.com'],'_img/_booru//']
,	[['chan.sankakucomplex.com','idol.sankakucomplex.com','sankaku.plus'	],'_img/_booru/sankakucomplex.com/']
,	[
		['donmai.us','idanbooru.com']
	,	'_img/_booru//'
	,	{
			'sub': [
				['posts'		,get_rei(r'^(/+mobile)?/+posts?/(show[/?]+)?(\d+)')]
			,	['posts_comments'	,['comment','comments']]
			,	['posts_pools'		,['pool','pools']]
			,	['posts_search'		,['post','posts']]
			,	['tags'			,['tag','tags','tag_alias','tag_aliases','tag_implication','tag_implications']]
			,	['tags_artists'		,['artist','artists']]
			,	['tags_wiki'		,['wiki','wiki_page','wiki_pages']]
			,	['static'		,['static']]
			,	['help'			,['help']]
			,	['forum'		,['forum','forum_post','forum_posts','forum_topic','forum_topics']]
			,	['users'		,['user','users']]
			,	['users/messages'	,['dmail','dmails','message','messages']]
			,	['users/favorites'	,['favorite','favorites']]
			,	['mobile'		,['mobile']]
			]
		}
	]
,	[
		[	'anime-pictures.net','behoimi.org'
		,	'derpiboo.ru','e-shuushuu.net','e621.net','e926.net','fapix.ru'
		,	'gelbooru.com','luscious.net','mangadrawing.net','nijie.info'
		,	'ostan-collections.net','pururin.com','rule34.lol','rule34.world','rule34hentai.net'
		,	'safebooru.org','sakugabooru.com','sankakucomplex.com','shishnet.org'
		,	'tbib.org','tentaclerape.net','theanimegallery.com'
		,	'xbooru.com','yande.re','yshi.org','zerochan.net','zombooru.com'
		]
	,	'_img/_booru/'
	]
,	[['peppercarrot.com'					],'_img/_comix/davidrevoy.com/']
,	[['mspaforums.com','mspabooru.com'			],'_img/_comix/mspaintadventures.com/']
,	[['mspaintadventures.com','homestuck.com'		],'_img/_comix//']
,	[['blag.xkcd.com','blog.xkcd.com'			],'_img/_comix/xkcd//']
,	[['what-if.xkcd.com','whatif.xkcd.com','chtoes.li'	],'_img/_comix/xkcd//']
,	[['explainxkcd.com','forums.xkcd.com','xkcd.ru'		],'_img/_comix/xkcd/']
,	[
		get_rei(r'^xkcd\.\w+$')
	,	'_img/_comix/xkcd'
	,	{
			'sub': [
				['xkcd.com', get_rei(r'^/*(\d+)([/?#_]|$)')]
			]
		}
	]
,	[['tapastic.com','tapas.io'				],'_img/_comix//']
,	[
		[	'acomics.ru','bubble.ru','captchacomics.com','comico.jp','comics.aha.ru','commitstrip.com'
		,	'davidrevoy.com','dilbert.com','dresdencodak.com','explosm.net','fowllanguagecomics.com'
		,	'galactanet.com','giantitp.com','girlgeniusonline.com','gocomics.com'
		,	'legorobotcomics.com','lezhin.com','looking-for-group.ru'
		,	'megatokyo.com','monkeyuser.com','nerfnow.com'
		,	'oglaf.com','pbfcomics.com','penny-arcade.com','phdcomics.com','smbc-comics.com','sssscomic.com','stonetoss.com'
		,	'talesofvaloran.com','tgsa-comic.com','themonsterunderthebed.net','theoatmeal.com','toomics.com'
		,	'visucomics.mechafetus.com','webcomunity.net','webtoons.com','wthi.one'
		]
	,	'_img/_comix/'
	]
,	[
		['2draw.me','mekurage.html-5.me']
	,	'_img/_doodle//'
	,	{
			'sub': [
				[get_rei(r'^/+archive/(([^/?#]+/)+)\d+\.html?'), r'archive/\2']
			,	['d'		,['d']]
			,	['i'		,['i']]
			,	['archive'	,['archive']]
			,	['room'		,['room']]
			] + sub_domain_exc_www_directly
		}
	]
,	[['gartic.com','garticphone.com'		],'_img/_doodle//']
,	[['multator.ru','toonator.com'			],'_img/_doodle//',{'sub': sub_domain_exc_www_directly}]
,	[
		[	'2draw.net','aggie.io','anondraw.com','artfight.net','awwapp.com','chickensmoothie.com','chibipaint.com','cosketch.com'
		,	'doodleordie.com','drawception.com','drawr.net','drawrun.com'
		,	'flockdraw.com','flockmod.com','frenchgirlsapp.com','garyc.me','groupboard.com'
		,	'imudak.ru','iqqsy.com','iscribble.net','malmal.io','o0o0.jp','oekaki.nl','oekaki.ru'
		,	'pica.so','scribblegrid.com','sketchdaily.net','theivrgroup.org'
		]
	,	'_img/_doodle/'
	]
,	[
		['imgur.com']
	,	'_img/_host/'
	,	{
			'sub': [
				['albums'	,get_rei(r'^/+a/(\w+)'		), r',a,\1']
			,	['gallery'	,get_rei(r'^/+ga[lery]+/(\w+)'	), r',gallery,\1']
			]
		}
	]
,	[get_rei(r'^imageshack\.\w+$'		),'_img/_host/imageshack.us']
,	[get_rei(r'^pinterest(\.com?)?\.\w+$'	),'_img/_host/pinterest.com']
,	[get_rei(r'^postimg\.\w+$'		),'_img/_host/postimg.com']
,	[['fastpic.ru','fastpic.org'		],'_img/_host//']
,	[['imgant.com','imgbar.net'		],'_img/_host//']
,	[['prnt.sc','prntscr.com'		],'_img/_host//']
,	[['slow.pics','slowpics.org'		],'_img/_host//']
,	[
		[	'abload.de','bakashots.me','captionbot.ai','check2pic.ru','clip2net.com','ctrlv.link','diff.pics','doigaro.sdbx.jp'
		,	'extraimage.com','flickr.com','framecompare.com','funkyimg.com','gyazo.com','hqpix.net'
		,	'ibb.co','imagebam.com','imageban.ru','imgsafe.org','imgsli.com','imgup.co','instagram.com'
		,	'joxi.ru','jpegshare.net','jpg.to','nudes.nut.cc'
		,	'pinbrowse.com','photobucket.com','postimages.org','publicdomainpictures.net','pxhere.com','radikal.ru'
		,	'savepic.net','screencapture.ru','screencast.com','screenshotcomparison.com','sli.mg','sm.ms','snag.gy'
		,	'unsplash.com'
		]
	,	'_img/_host/'
	]
,	[
	#	[	'37.48.119.23','37.48.119.24','37.48.119.27','37.48.119.40','37.48.119.44'
	#	,	'95.211.212.101','95.211.212.238','95.211.212.239','95.211.212.246'
	#	]
		get_rei(r'^(([\w.]+\.)?hath\.network|(37\.48\.119\.|95\.211\.212\.)\d+)$')
	,	'_img/_manga/e-hentai.org/_dl/_archive'
	]
,	[
		get_rei(r'^e[x-]hentai\.org$')
	,	'_img/_manga/e-hentai.org'
	,	{
			'sub': [
				['_search/_tag'		,get_rei(r'^([^?#]*?/)?(tags?)(\.php)?($|[/?#])')]
			,	['_search/_uploader'	,get_rei(r'^([^?#]*?/)?(uploader)(\.php)?($|[/?#])')]
			,	['_search'		,get_rei(r'^([^#]*?[/?&])?((f_)?search?)(\.php)?($|[/?#=])')]
			,	['_dl/_archive'	,get_rei(r'^([^?#]*?/)?((gallery)?archiver?)(\.php)?($|[/?#])')]
			,	['_dl/_torrent'	,get_rei(r'^([^?#]*?/)?((gallery)?torrents?)(\.php)?($|[/?#])')]
			,	['_hath'	,get_rei(r'^([^?#]*?/)?(exchange|hath(perks)?|hentaiathome)(\.php)?($|[/?#])')]
			,	['_gallery'	,get_rei(r'^([^?#]*?/)?(g|gallery)(\.php)?($|[/?#])')]
			,	['_pages'	,['s','mpv']]
			] + sub_domain_exc_www
		}
	]
,	[['manga-zip.info'			],'_img/_manga/'
	,	{
			'sub': [
				['author'	,['author']]
			,	['dl'		,['dl']]
			,	['tag'		,['tag']]
			]
		}
	]
,	[['mangaupdates.com'			],'_img/_manga/'
	,	{
			'sub': [
				['authors'	,['authors']]
			,	['series'	,['series']]
			,	['topic'	,['topic']]
			,	[get_rei(r'^([^#]*?[/?&])?(\w+)\.\w+\?id=\d+'), r'\2']
			]
		}
	]
,	[['bato.to','vatoto.com'		],'_img/_manga//']
,	[['dlraw.co','dlraw.net','dl-raw.co'	],'_img/_manga//']
,	[['kissmanga.com','kissmanga.nl'	],'_img/_manga//']
,	[['mangadex.org','mangadex.com'		],'_img/_manga//']
,	[['mangakakalot.com','mangakakalots.com'],'_img/_manga//']
,	[['mintmanga.com','mintmanga.live'	],'_img/_manga//']
,	[['readmanga.me','readmanga.live'	],'_img/_manga//']
,	[['selfmanga.ru','selfmanga.live'	],'_img/_manga//']
,	[['nhentai.net','nhentai.com'		],'_img/_manga//']
,	[['ehwiki.org','hentaiathome.net'	],'_img/_manga/e-hentai.org/']
,	[get_rei(r'^madokami\.\w+$'		),'_img/_manga/madokami.com']
,	[
		[	'9hentai.ru','a-zmanga.net','adultmanga.ru','bokudake-gainaimachi.com'
		,	'cubari.moe','desu.me','doujin-eromanga.com','doujin-freee.com','doujinland.com','doujinshi.org','dynasty-scans.com'
		,	'fakku.net','fanfox.net','gmimanga.com','grouple.co'
		,	'haikeisouko.com','helveticascans.com','hennojin.com'
		,	'hentai.cafe','hentai-chan.me','hentai2read.com','hentai4manga.com','hentaihand.com','hentainexus.com'
		,	'hitomi.asia','hitomi.la'
		,	'jpmangaraw.com','lhtranslation.com','lovehug.net'
		,	'manga.life','manga-chan.me','mangachan.me','mangachan.ru'
		,	'mangafox.me','mangahere.co','mangalib.me'
		,	'manganelo.com','mangaonlinehere.com','mangareader.net','mangarock.com'
		,	'mangashare.com','mangatensei.com','mangawindow.net'
		,	'mydailymanga.com','mymanga.me','onemanga.com','onepiecechapters.com'
		,	'rawlh.com','readms.com','remanga.org','senmanga.com','simple-scans.com'
		,	'tonarinoyj.jp','tsumino.com'
		]
	,	'_img/_manga/'
	]
,	[['deepdream.pictures','dreamscopeapp.com','zainshah.net'	],'_img/_NN//']
,	[['waifu2x.udp.jp'						],'_img/_NN//',{'sub': [['_result',['api']]]}]
,	[
		[
			'affinelayer.com','aiportraits.com','artflow.ai','booru.pics','ganbreeder.app','girls.moe','huggingface.co'
		,	'nvidia-research-mingyuliu.com','openart.ai','paintschainer.preferred.tech','palette.fm'
		,	'qosmo.jp','remove.bg','s2p.moe','thisanimedoesnotexist.ai','waifu.lofiu.com'
		]
	,	'_img/_NN/'
	]
,	[
		['pixai.art']
	,	'_img/_NN/'
	,	{
			'sub': [
				[
					'/'
				,	pat_pixai_art
				,	r' - \1'
				,	replace_title_html_entities
				,	replace_title_emoji_cluster
				,	replace_title_underscores
				,	replace_title_pixai_username
				]
			]
		}
	]
,	[
		['ascii2d.net']
	,	'_img/_search/'
	,	{
			'sub': [
				['_search',get_rei(r'^/*(search)/+([^/?#]+)/+([0-9a-f]{32})\b'), r' - \1 - \2 - \3', replace_title_tail_unmht]
			,	['_search',['search']]
			]
		}
	]
,	[['whatanime.ga','trace.moe'								],'_img/_search//']
,	[['everypixel.com','iqdb.org','saucenao.com','tineye.com'				],'_img/_search/']
,	[['blog.desudesudesu.org','suigintou.desudesudesu.org','desudesudesu.org','nik.bot.nu'	],'_img/_wallpapers/4scrape.net/']
,	[get_rei(r'^(4walled|wallhaven)\.\w+$'							),'_img/_wallpapers/4walled.cc']
,	[
		[	'4scrape.net','animestarwall.com','best-wallpaper.net','cgwall.cn','desktopmania.ru'
		,	'iphoneswallpapers.com','ipicstorage.com','minitokyo.net','rewalls.com','teahub.io'
		,	'wallpaperi.net','wallpapersafari.com','wallpapertip.com','wallpaperto.com','wallpaperup.com'
		]
	,	'_img/_wallpapers/'
	]
,	[['affect3dstore.com'						],'_img/_3D/affect3d.com/']
,	[['affect3d.com','sketchfab.com','smutba.se','theta360.com'	],'_img/_3D/']
,	[['inktober.com','mrjakeparker.com'	],'_img//']
,	[['mastera.art','mastera.art'	],'_img//']
,	[['milena-velba.de','milena-velba.com'	],'_img//']
,	[['artstation.com'			],'_img/',{'sub': [['post',['post','artwork']]]}]
,	[
		[	'500px.com'
		,	'acomics.ru','agawa.info','aika.ru','alphacoders.com','anatomynext.com','atoptics.co.uk','arqute.com'
		,	'beaudu.com','behance.net','bokasitter.net'
		,	'cara.app','cc0textures.com','cfake.com','cghub.com','chounyuu.com','clipartkind.com'
		,	'clone-army.org','closeuphotography.com','complexification.net','conceptart.org','cubebrush.com','cults3d.com'
		,	'demiart.ru','digitalartmuseum.org','drawcrowd.com','drawing.today','drawmanga.ru'
		,	'f-picture.net','flaticon.com','flaticons.net','freepik.com','freepng.es','funart.pro','furaffinity.net','fzdschool.com'
		,	'game-icons.net','gas13.ru','gigapan.com','girlimg.com','graphicker.me','gumroad.com'
		,	'hentai.fyi','hentai-foundry.com','hentai-image.com','hentaihorizon.com','hopfengart.de','huaban.com'
		,	'illustrators.ru','jamajurabaev.com','kommissia.ru','kurocore.com'
		,	'lenna.org','leoartz.com','lockes-art.com','lofter.com'
		,	'macroclub.ru','magisterofficial.com','mechafetus.com','medicalwhiskey.com'
		,	'moeimg.net','moregirls.org','mutimutigazou.com'
		,	'nadine-j.de','openclipart.org'
		,	'peperaart.com','pexels.com','photofunia.com','photomosh.com','photozou.jp'
		,	'pixelartus.com','pixxxels.cc','placekeanu.com','placewaifu.com'
		,	'pngegg.com','poocg.com','posemaniacs.com','prettysimpleimages.com'
		,	'reference.pictures','render.ru','rtenzo.net','ruanjia.com'
		,	'schakty.com','senpy.tk','setteidreams.net','shii.org','shutterstock.com','simply-hentai.com'
		,	'skeb.jp','soup.io','studiominiboss.com'
		,	'textures.com','tytoalba.net','virink.com','weheartit.com','wildtextures.com'
		]
	,	'_img/'
	]

#--[ Japan ]-------------------------------------------------------------------

,	[['forum.anidb.net'							],'_Japan/_anime,manga/anidb.net/_forum']
,	[['wiki.anidb.net'							],'_Japan/_anime,manga/anidb.net/_wiki']
,	[
		['anidb.net']
	,	'_Japan/_anime,manga//'
	,	{
			'sub': [
				['_forum'	,get_rei(r'^[^#]*?[?&]show=threads?')]
			,	['_search'	,get_rei(r'^[^#]*?[?&](adb|do).search=')]
			,	['_relations'	,get_rei(r'^[^#]*?/*relations?($|[/?#])')]
			,	['_anime'	,['anime']]
			,	['_episode'	,['episode']]
			,	['_character'	,['character']]
			,	['_creator'	,['creator']]
			,	['_forum'	,['forum']]
			,	['_user'	,['user','profile']]
			,	['_club'	,['club','group']]
			,	['_tag'		,['tag']]
			,	['_file'	,['file']]
			,	['_song'	,['song']]
			,	['_wiki'	,['wiki']]
			,	[get_rei(r'^[^#]*?[?&]show=(?P<Category>\w+)&(\w+)id='), r'_\g<Category>']
			]
		}
	]
,	[
		['animenewsnetwork.com','animenewsnetwork.cc']
	,	'_Japan/_anime,manga//'
	,	{
			'sub': [
				['', get_rei(r'^/*[^/#?]+/+(\d{4}(?:-\d\d-\d\d)?)(?=$|[/#?])'	), r' - \1', replace_title_tail_unmht]
			,	['', get_rei(r'^[^!#]*?/*\.(\d+)(?=$|[#?])'			), r' - \1', replace_title_tail_unmht]
			]
		}
	]
,	[['evageeks.org'							],'_Japan/_anime,manga/Evangelion/']
,	[['kami.im','madoka-magica.com','matomagi.com','puella-magi.net'	],'_Japan/_anime,manga/Madoka/']
,	[['animeplaza.nl','anime-plaza.nl'					],'_Japan/_anime,manga//']
,	[['findanime.ru','findanime.me'						],'_Japan/_anime,manga//']
,	[['hentaianimedownloads.com','hshare.net'				],'_Japan/_anime,manga//']
,	[['mahou-shoujo.moe','loli.coffee'					],'_Japan/_anime,manga//']
,	[['shikimori.org','shikimori.one','shikimori.me'			],'_Japan/_anime,manga//']
,	[['snow-raws.com','snow-raws.win','skyeysnow.com','skyey2.com'		],'_Japan/_anime,manga//']
,	[['weebs4life.ga','asuna.ga'						],'_Japan/_anime,manga//']
,	[['haruhi.tv','maidragon.jp','yukichan-anime.com'			],'_Japan/_anime,manga/kyotoanimation.co.jp/']
,	[['anime.sc','mal.oko.im'						],'_Japan/_anime,manga/myanimelist.net/']
,	[
		[	'abema.tv','absoluteanime.com','ahegao.online','alpha.cafe'
		,	'ani.tv','ani.gamer.com.tw','anichart.net','anidub.com','anilist.co'
		,	'animacity.ru','animag.ru','animatetimes.com','animatorexpo.com'
		,	'anime.aka.yt','anime.everyeye.it','anime.mikomi.org','anime.my'
		,	'anime-chan.me','anime-mir.com','anime-now.com','anime-planet.com','anime-portal.ru','anime-sharing.com'
		,	'animea.net','animebest.org','animeblog.ru','anibox.org','animecharactersdatabase.com','animecritic.com','animecult.org'
		,	'animeforum.ru','animego.org','animeigo.com'
		,	'animekayo.com','animemaga.ru','animemaru.com','animemotivation.com','animemusicvideos.org'
		,	'animenation.net','animencodes.com','animeonline.su','animeperson.com'
		,	'animesenpai.net','animeshare.cf','animespirit.ru','animestyle-shop.ru','animesuki.com','animeukiyo.com'
		,	'animu.date','anisearch.com','arai-kibou.ru','asnet.pw','aurora-raws.com','aziophrenia.com','beatrice-raws.org','boku.ru'
		,	'cbr.com','cha-no-yu.ru','choukadou-anime.com','crunchyroll.com','cuba77.ru'
		,	'd-addicts.com','demonbane.com','desu.ru','detectiveconanworld.com','discotekmedia.com','diskomir.ru','dkb.si'
		,	'erai-raws.info','exiled-destiny.com','fanboyreview.net','fapservice.com','fast-anime.ru'
		,	'gakken-eizo.com','gokoro.me','gundam-seed.net'
		,	'haruha.ru','haruhichan.com','hentai-for.me','hi10anime.com','hungry-bags.ru'
		,	'idforums.net','intercambiosvirtuales.org','isekaimaou-anime.com'
		,	'jacobswaggedup2.com','japari-library.com','jatshop.ru','judging.it'
		,	'kaleido.kageru.moe','kametsu.com','kanzaki.ru','kaze-online.de','keyfc.net'
		,	'kiss-anime.co','kitsu.io','kodansha.us','kumo-anime.com','kyotoanimation.co.jp'
		,	'leopard-raws.org','loveanim.com'
		,	'maikuando.tv','malsync.moe','manga.tokyo','manga-home.com','mangaz.ru','mangazoneapp.com'
		,	'manifest-spb.ru','moekyun.co','monogatari-series.com','morian.icu','musani.jp','myanimelist.net'
		,	'nakanomangaschool.jp','nandesuka.moe','naruhodo.workers.dev','narutoplanet.ru'
		,	'nausicaa.net','nauti.moe','nibl.co.uk','nyanpass.com'
		,	'onepace.net','openings.ninja','otaku.com','otaku.ru','otakubell.com','otakuusamagazine.com','over-ti.me','ozc-anime.com'
		,	'pierrot.jp','pixie-shop.ru','plastic-pleasures.com','pochi.lix.jp','project-imas.com'
		,	'raw-zip.net','rawacg.com','rawset.org','reanimedia.ru','reasonstoanime.com'
		,	'riczroninfactories.eu','russia-in-anime.ru','russian-cards.ru'
		,	'sahadou.com','saishuu.com','sayoasa.jp','sevenseasentertainment.com','shamanking-project.com'
		,	'slowanime.com','space-dandy.com','sukasuka-anime.com','suzumiya.ru'
		,	'theanimedaily.com','tlnotes.com','translationchicken.com','trashstudio.jp','twist.moe'
		,	'uccuss.com','urusei-yatsura.ru','ushwood.ru','vcb-s.com','vivy-portal.com','viz.com','wakanim.tv'
		,	'xlm.ru','yaposha.com','yousei-raws.org','zimmerit.moe','zohead.moe'
		]
	,	'_Japan/_anime,manga/'
	]
,	[
		[	'animeshinigami.altervista.org','anisab-subs.ru','ankokufs.us','asenshi.moe'
		,	'chihiro-subs.com','coalgirls.wakku.to','damedesuyo.com','dats.us','doki.co'
		,	'fallensoul.es','fansub.co','fansubs.ru','ggkthx.org','goodjobmedia.com'
		,	'hologfx.com','honobono.cc','honyaku-subs.ru','horriblesubs.info','ii-subs.net','inka-subs.net'
		,	'kitsunekko.net','lazylily.moe','live-evil.org','m33w-fansubs.com','mazuisubs.com','melon-subs.de','mod16.org'
		,	'nanda.to','nfp.moe','noobsubs.net','octonionic.org','oldcastle.moe','owlolf-fansub.com','oyatsu-jikan.org'
		,	'pandasubs.zz.mu','pas.moe','poweris.moe','russian-subs.com'
		,	'saizenfansubs.com','sakuracircle.com','sakurasoufs.com','some-stuffs.com','snsbu.mangadex.com'
		,	'subs.com.ru','subsplease.org','subscene.com'
		,	'utw.me','vivid.moe','whynotsubs.com'
		]
	,	'_Japan/_sub/'
	]
,	[['fffansubs.org','fffansubs.com'		],'_Japan/_sub//']
,	[['livebus.info','live-bus.com'			],'_Japan//']
,	[['sparky4.net','4ch.mooo.com','yotsubano.me'	],'_Japan//']
,	[['t-walker.jp','tw4.jp'			],'_Japan//']
,	[['bof6.jp','e-capcom.com','capcom-s.jp'	],'_Japan/co.jp/capcom.co.jp/']
,	[['nicogame.info'				],'_Japan/nicovideo.jp/']
,	[['seiga.nicovideo.jp','nicoseiga.jp'		],'_Japan/nicovideo.jp//']
,	[['fate-go.jp','kira-kira-tech.icu'		],'_Japan/typemoon.com/']
,	[['blog.jp','livedoor.blog','livedoor.com'	],'_Japan/livedoor.jp',{'sub': sub_domain_last_over_top2_exc_www}]
,	[
		['livedoor.jp','blogimg.jp']
	,	'_Japan//'
	,	{
			'sub': [
				[get_rei(part_protocol + part_domain + r'/+~?(?P<Folder>[^/?#]+)/+'), r'_subdomain/\g<Folder>']
			]
		}
	]
,	[
		get_rei(r'^(fc2\.com|iinaa\.net|(co|lolipop|ne|nobody|or)\.jp)$')
	,	'_Japan/'
	,	{
			'sub': [
				# [get_rei(r'^([^/?#]+)/+()')	, r'\1,\2']
				[get_rei(part_protocol + part_domain + r'/+(?P<Folder>~[^/?#]+)/+'), r'\g<All>,\g<Folder>']
			] + sub_domain_exc_www_directly
		}
	]
,	[
		[	'acgateway.com','aidn.jp','ameblo.jp','at-x.com','circle.ms'
		,	'd-stage.com','dannychoo.com','dlsite.com','dmm.com','dolphilia.com','enty.jp','fantia.jp'
		,	'geocities.jp','getchu.com','goods-seisaku.com','gundam-challenge.com','gundam-factory.net','gyutto.com'
		,	'hayakawabooks.com','himado.in','i-love-cool.com','idolwars.jp','ifdef.jp','ikaros.jp','iro-dori.jp','itchstudios.com'
		,	'japantoday.com','jav-hunter.com','javshare.ml','jlist.com'
		,	'kannagi.net','kikyou.info','king-cr.jp','kisskiss.tv','kuku.lu','lifeinjapan.ru','lune-soft.jp'
		,	'moe-gameaward.com','moehime.org','monto.me','moshimoshi-nippon.jp','mydramalist.com'
		,	'nalchemy.com','neojaponisme.com','neriko.net','nicovideo.jp','note.com'
		,	'odaibako.net','otakumode.com','ototoy.jp','questant.jp','ruranobe.ru'
		,	'saiin.net','sega.jp','seismicxcharge.com','seoi.net','shitaraba.net','silkysplus.jp'
		,	'squeez-soft.jp','stickam.jp','straightedge.jp','studio-mizutama.net','suishoshizuku.com'
		,	'tackysroom.com','taptaptaptaptap.net','togetter.com','tokyogirlsupdate.com','toranoana.jp','touchable.jp'
		,	'tsukiyo.me','tw5.jp','typemoon.com'
		,	'ufotable.info','usamimi.info','usen.com','yui-kitamura.eng.pro','yuiktmr.blog'
		]
	,	'_Japan/'
	]

#--[ languages ]---------------------------------------------------------------

,	[['myscriptfont.com','calligraphr.com'					],'_lang/_fonts/_handwriting//']
,	[['fontcapture.com','handwritter.ru','hfont.ru'				],'_lang/_fonts/_handwriting/']
,	[['fontawesome.io','fontawesome.com'					],'_lang/_fonts//']
,	[
		[	'1001fonts.com','1001freefonts.com'
		,	'allfont.ru','billyargel.com','blambot.com','comicraft.com','commercialtype.com','dafont.com','dobroshrift.ru'
		,	'ffonts.net','fixedsysexcelsior.com'
		,	'font2s.com','fontbureau.com','fontlibrary.org','fontke.com','fontmeme.com','fontreviews.com'
		,	'fonts.com','fonts-online.ru','fonts2u.com','fontspace.com','fontsquirrel.com'
		,	'freejapanesefont.com'
		,	'galdinootten.com','irmologion.ru','marksimonson.com','myfonts.com','nomail.com.ua'
		,	'paratype.ru','sil.org','tehandeh.com','typocalypse.com','xfont.ru','yourfonts.com'
		]
	,	'_lang/_fonts/'
	]
,	[['caniemoji.com','emojipedia.org','iemoji.com','getemoji.com'		],'_lang/_unicode/_emoji/']
,	[
		[	'alt-codes.net','carrickfergus.de','codepoints.net','compart.com'
		,	'fileformat.info','graphemica.com','htmlsymbols.xyz','icu-project.org','key-shortcut.com'
		,	'unicode.org','unicode-search.net','unicode-symbol.com','unicode-table.com'
		,	'unifoundry.com','utf8-chartable.de','utf8everywhere.org','utf8icons.com'
		]
	,	'_lang/_unicode/'
	]
,	[
		[	'editorsmanual.com','etymonline.com','grammarly.com','merriam-webster.com','oxforddictionaries.com'
		,	'pronoun.is','usefulenglish.ru','wordreference.com'
		]
	,	'_lang/en/'
	]
,	[['susi.ru','yarxi.ru'											],'_lang/jp//']
,	[['ichi.moe','jgram.org','jisho.org','jref.com','guidetojapanese.org','tanoshiijapanese.com','weblio.jp'],'_lang/jp/']
,	[['academic.ru','gramota.ru','russkiy-na-5.ru','sokr.ru','teenslang.su'					],'_lang/ru/']
,	[['shavian.info'						],'_lang/Shavian/']
,	[['localizor.io','localizor.com'				],'_lang//']
,	[
		[	'behindthename.com','deepl.com','dictionary.com','endangeredlanguages.com'
		,	'hinative.com','i2ocr.com','ithkuil.net','lingvanex.com','lingvoforum.net'
		,	'urbandictionary.com','vocabulary.ugent.be','vulgarlang.com','weblate.org','wordreference.com','zkorean.com'
		]
	,	'_lang/'
	]

#--[ music ]-------------------------------------------------------------------

,	[['abundant-music.com','auralfractals.net','fakemusicgenerator.com','jukedeck.com'],'_music/_generation/']
,	[
		[	'ai-radio.org','animeradio.su','di.fm','dps-fm.com'
		,	'echo.msk.ru','edenofthewest.com','euroradio.fm','internet-radio.com'
		,	'moskva.fm','myradiostream.com','plaza.one','radio-astronomy.net','radiooooo.com','radioportal.ru'
		,	'shiza.fm','shoutcast.com','staroeradio.ru','tunein.com','zigafolk.ru'
		]
	,	'_music/_radio/'
	]
,	[['freesfx.co.uk','freewavesamples.com','philharmonia.co.uk'	],'_music/_samples/']
,	[['anon.fm','alcxemuct.accountant'				],'_music//']
,	[['bandcamp.com','bandcamp.help','isitbandcampfriday.com'	],'_music//']
,	[['tenshi.ru','tenshi.spb.ru'					],'_music//']
,	[get_rei(r'^keygenmusic\.\w+$'					),'_music/keygenmusic.net']
,	[
		[	'1hz-music.fun','8bitpeoples.com'
		,	'a-pesni.org','agargara.com','allthemusic.info','animelyrics.com','aninx.com'
		,	'audiomania.ru','audionautix.com','audioschool.ru'
		,	'bad-band.net','barryvan.com.au','beatles.ru','boscaceoil.net'
		,	'cbcmusic.ca','cctrax.com','chiptuneswin.com','clyp.it','cylinders.library.ucsb.edu'
		,	'daimp3.org','dbpoweramp.com','deezer.com','defytheocean.com','discogs.com','electroshock.ru','eurovision.tv'
		,	'fbits.ru','filmmusic.io','freedb.org','freemusicarchive.org','freepd.com','freesound.org'
		,	'gendou.com','gnudb.org','gracenote.com'
		,	'incompetech.com','indieplant.com','ironmaiden.com','jonnyatma.com'
		,	'karaokes.moe','karaoke.ru','khinsider.com','kosmosky.ru','kuukunen.net'
		,	'larc-en-ciel.com','last.fm','lastfm.ru','lenin.ru','lesser-vibes.com'
		,	'lilypond.org','linear.nu','linkco.re','littlesounddj.com','lyrical-nonsense.com'
		,	'megalyrics.ru','metapop.com','midi.ru','mixcloud.com','mp3ller.ru','mobygratis.com','modarchive.org','mora.jp'
		,	'musescore.com','music.uiowa.edu','musicbrainz.org','musicishere.com','musicxml.com','musixmatch.com'
		,	'mutopiaproject.org','muzlostyle.ru','myzuka.org'
		,	'nashipesni.info','no-fate.net','nocopyrightsounds.co.uk','noteserver.org','ocremix.org'
		,	'patefon.fm','picosong.com','planetronica.ru','pleer.com','pouet.net','rateyourmusic.com','realmusic.ru','recochoku.jp'
		,	's3m.it','s3m.us','sampleswap.org','scottbuckley.com.au','sh-whitecrow.com','shemusic.org','silvermansound.com'
		,	'song-story.ru','soundcloud.com','soundprogramming.net','spinninrecords.com','spotify.com','surasshu.com','synthmania.com'
		,	'teknoaxe.com','tekst-pesni-tut.ru','tenshi.ru','themes.moe','theremin.ru','thes1n.com','tlmc.eu'
		,	'ubiktune.com','untergrund.net','vgmdb.net','vgmpf.com','vgmrips.net','vmuzike.net','webamp.org','zaycev.net'
		]
	,	'_music/'
	]

#--[ society ]-----------------------------------------------------------------

,	[['bbc.com','bbc.co.uk'		],'_news//']
,	[['lenta.ru','moslenta.ru'	],'_news//']
,	[['ng.ru','novayagazeta.ru'	],'_news//']
,	[['ngs.ru','ngs24.ru'		],'_news//']
,	[['tass.ru','tass.com'		],'_news//']
,	[['zona.media','steam-habitat-347616.appspot.com'			],'_news//']
,	[[u'екатеринбург.рф','xn--80acgfbsl1azdqr.xn--p1ai'			],'_news//']
,	[[u'национальныепроекты.рф','xn--80aapampemcchfmo7a3c9ehj.xn--p1ai'	],'_news//']
,	[get_rei(r'^(e|ngs|ufa)?(?!0)1?\d{1,2}\.ru$'),'_news/_regional/']
,	[
		['dzen.ru']
	,	'_news//'
	,	{
			'sub': [
				['_news'	,['news','sport']]
			,	['_help'	,['help']]
			,	['_legal'	,['legal']]
			]
		}
	]
,	[
		[	'24smi.info','3dnews.ru','5-tv.ru'
		,	'akket.com','antimaydan.info','asahi.com','asiafinancial.com'
		,	'baikal-journal.ru','burninghut.ru','c-inform.info','chernovik.net','cnews.ru','cnn.com','csmonitor.com'
		,	'dailymail.co.uk','dnr-live.ru','dou.ua','dw.com'
		,	'eadaily.com','focus.ua','fryazino.info','ft.com','gazeta.ru','gorodperm.ru'
		,	'hi-news.ru','highload.today','inosmi.ru','islam-today.ru','iz.ru'
		,	'kcna.kp','kcpn.info','kgd.ru','kommersant.ru','kp.ru','madeinrussia.ru','marpravda.ru','meduza.io','mk.ru'
		,	'news.ru','newsru.com','nikkei.com','nytimes.com'
		,	'oryxspioenkop.com','ovd.news','passion.ru','proekt.media'
		,	'rbc.ru','readovka.news','ren.tv','reuters.com','rg.ru'
		,	'ria.ru','riamo.ru','roem.ru','rt.com','ruposters.ru','rusvesna.su'
		,	'sdelanounas.ru','servernews.ru','sevastopol.su','simcast.com','sky.com','smi2.ru'
		,	'sobaka.ru','soranews24.com','spichka.media','strana.today','svoboda.org'
		,	'techstory.in','the-liberty.com','thebulletin.org','theguardian.com'
		,	'theregister.com','thetimes.co.uk','thetruestory.news','theverge.com','time.com','topwar.ru','tsargrad.tv'
		,	'ukraina.ru','unian.net','ura.news','verbludvogne.ru','vice.com','vz.ru'
		,	'waronfakes.com','washingtonpost.com','wired.com','ykt.ru'
		]
	,	'_news/'
	]

,	[['poll-maker.com','pollcode.com','roi.ru','rupoll.com','simpoll.ru','strawpoll.com','strawpoll.me'],'_poll/']

,	[['cmu.edu','coursera.org','khanacademy.org','practicum.org','stanford.edu','ugractf.ru','utoronto.ca'],'_science/_education/']
,	[
		[	'3blue1brown.com','artofproblemsolving.com','desmos.com','dynamicmath.xyz','dxdy.ru'
		,	'easings.net','encyclopediaofmath.org','oeis.org','oeisf.org','reflex4you.com'
		]
	,	'_science/_math/'
	]
,	[get_rei(r'^boinc(stats)?\.(\w+|berkeley\.edu)$'),'_science/BOINC/']
,	[get_rei(r'^emdrive\.\w+$'			),'_science/emdrive.com']
,	[['nplus1.ru','nplus1.dev'			],'_science//']
,	[
		[	'aboutbrain.ru','academia.edu','acm.org','algorithmicbotany.org','antarctica.gov.au'
		,	'arbital.com','arxiv.org','astronomy.ru'
		,	'berkeley.edu','biorxiv.org','buran.ru','calc.ru','cosmomayak.ru','cremlinplus.eu'
		,	'datasketch.es','distill.pub','elementy.ru','eso.org','evanmiller.org','factroom.ru','healthdata.org'
		,	'ieee.org','improbable.com','informationisbeautifulawards.com','intelligence.org'
		,	'jstor.org','kottke.org','laser.ru','lesswrong.com','linearcollider.org'
		,	'manyworldstheory.com','matek.hu','membrana.ru'
		,	'naked-science.ru','nanometer.ru','nature.com','nist.gov','nkj.ru','null-hypothesis.co.uk'
		,	'postnauka.ru','profmattstrassler.com','psihiatr.info','psychic-vr-lab.com','psylab.info','quantamagazine.org'
		,	'scienceblogs.com','sciencemag.org','scientaevulgaris.com','sens.org','shatters.net','stevenabbott.co.uk'
		,	'tandfonline.com','universesandbox.com','wolfram.com','wolframalpha.com','zin.ru'
		]
	,	'_science/'
	]

,	[
		[	'amsmeteors.org','astronautix.com','astronomytrek.com'
		,	'epizodyspace.ru','eventhorizontelescope.org','esa.int','esawebb.org'
		,	'galspace.spb.ru','hirise.lpl.arizona.edu','iau.org','imo.net','jasonwang.space','jaxa.jp','lorett.org'
		,	'minorplanetcenter.net','nasa.gov','novosti-kosmonavtiki.ru','nsf.gov','nso.edu'
		,	'openspaceproject.com','planetary.org','planetplanet.net','plasma-universe.com','projectrho.com','roscosmos.ru'
		,	'shubinpavel.ru','skyandtelescope.com','space.com','thehumanitystar.com','theuniversetimes.ru'
		,	'uahirise.org','zelenyikot.com','zooniverse.org'
		]
	,	'_space/'
	]
,	[['edu'			],'_science/_education']

,	[['blogger.com'		],'_soc/blogspot.com/']
,	[
		get_rei(r'^blogspot(\.com?)?\.\w+$')
	,	'_soc/blogspot.com'
	,	{
			'sub': [
				[get_rei(r'^(?:\w+:/+)?\d+\.bp\.[^/?#]+(?:/|$)'					), r'_pix']
			,	[get_rei(r'^(?:\w+:/+)?([^/?#]+\.)?([^/.]+)\.blogspot(\.com?)?\.\w+(?:/|$)'	), r'_personal/\2']
			]
		}
	]
,	[
		[	'buhitter.com','fxtwitter.com','sdlcqz.com','shadowban.eu','ssstwitter.com','stwity.com'
		,	'threader.app','threadreaderapp.com'
		,	'twicomi.com','twimg.com','twitlonger.com','twitpic.com','twitrss.me'
		,	'twittercommunity.com','twitterstat.us','twpublic.com','twtimez.net'
		,	'vxtwitter.com','whotwi.com'
		]
	,	'_soc/twitter.com/'
	]
,	[
		['twitter.com','x.com']
	,	'_soc//'
	,	{
			'sub': [
				['_post',['i']]
			,	['_search',['search']]
			,	['_hashtag',['hashtag']]
			,	[get_rei(r'^(?:\w+:/+)?(?:(?:www|mobile)\.)?\w+\.\w+/+([^/?#]+)/+status/'), r'_personal/\1/_posts']
			,	[get_rei(r'^(?:\w+:/+)?(?:(?:www|mobile)\.)?\w+\.\w+/+([^/?#]+)($|[/?#])'), r'_personal/\1']
			,	[get_rei(r'^(?:\w+:/+)?(?:[^/?#]+\.)(\w+\.\w+)($|[/?#])'), '\1']
			,	'_etc'
			]
		}
	]
,	[['abdulkadir.net','redronin.de'				],'_soc//']
,	[['epal.gg','egirl.gg'						],'_soc//']
,	[['facebook.com','fb.com','internet.org'			],'_soc//']
,	[['medium.com','medium.design','medium.engineering'		],'_soc//']
,	[['narod.ru'							],'_soc//',{'sub': [['_disk',['disk']]]+sub_domain_last_over_top2_exc_www}]
,	[['nifty.com','coocan.jp'					],'_soc//',{'sub': sub_domain_last_over_top2_exc_www}]
,	[['odnoklassniki.ru','ok.ru'					],'_soc//']
,	[['pillowfort.io','pillowfort.social'				],'_soc//']
,	[['slashdot.org','slashdotmedia.com'				],'_soc//']
,	[['strikingly.com','mystrikingly.com'				],'_soc//',{'sub': sub_domain_last_over_top2_exc_www}]
,	[['vbulletin.net','vbulletin.com'				],'_soc//',{'sub': sub_domain_last_over_top2_exc_www}]
,	[['wixsite.com','wix.com'					],'_soc//']
,	[['telegram.org','telegram-store.com','ton.org'			],'_soc//']
,	[['t.me'							],'_soc/telegram.org/',{'sub': [['s',['s']]]}]
,	[['t.me','tgram.link','tlgrm.ru','ttttt.me'			],'_soc/telegram.org//']
,	[['telegra.ph','telemetr.io'					],'_soc/telegram.org/']
,	[['vkontakte.ru','vk.com'					],'_soc//']
,	[['pp.userapi.com','vk.me'					],'_soc/vkontakte.ru/_pix']
,	[['my.com','vkfaces.com'					],'_soc/vkontakte.ru/']
,	[['reddithelp.com','redditinc.com','redditsave.com'		],'_soc/reddit.com/']
,	[
		['stackexchange.com']
	,	'_soc//'
	,	{
			'sub': [
				[pat_subdomain_top_meta,  r'_subdomain/\g<AllOverTop2>/meta']
			,	[pat_subdomain_over_meta, r'_subdomain/\g<AllOverMeta>/meta']
			] + sub_domain_over_top2_exc_www
		}
	]
,	[
		[	'askubuntu.com','dearstackexchange.com','mathoverflow.net','moms4mom.com','nickcraver.com','serverfault.com'
		,	'stackoverflow.com','stackapps.com','stackprinter.com','stackstatus.net','superuser.com'
		]
	,	'_soc/stackexchange.com/'
	,	{'sub': sub_domain_over_top2_exc_www_directly}
	]
,	[get_rei(r'^stackoverflow(business|solutions|(?:\.\w+)*?\.qualtrics)?\.\w+$'),'_soc/stackexchange.com/']
,	[
		get_rei(r'^(habr|habrahabr|geektimes)\.\w+$')
	,	'_soc/tmtm.ru/habr.com'
	,	{
			'sub': [
				[get_rei(r'^/*(?:[^/?#]+/+)*\d+/+(comments?)(?:[/.?#]|$)'			), r'_comments']
			,	[get_rei(r'^/*(?:[^/?#]+/+)*(compan[yies]+)/+([^/?#]+/+)*\d+(?:[/.?#]|$)'	), r'_company']
			,	[get_rei(r'^/*(?:[^/?#]+/+)*(articles?)/+([^/?#]+/+)*\d+(?:[/.?#]|$)'		), r'_article']
			,	[get_rei(r'^/*(?:[^/?#]+/+)*(news)/+([^/?#]+/+)*\d+(?:[/.?#]|$)'		), r'_news']
			,	[get_rei(r'^/*(?:[^/?#]+/+)*(posts?)/+([^/?#]+/+)*\d+(?:[/.?#]|$)'		), r'_post']
			,	[get_rei(r'^/*(?:[^/?#]+/+)*(users?)/+([^/?#]+/+)*(?:[/.?#]|$)'			), r'_user']
			,	[get_rei(r'^/*(?:[^/?#]+/+)*(qn?a?)/+([^/?#]+/+)*\d+(?:[/.?#]|$)'		), r'_qna']
			]
		}
	]
,	[
		[	'brainstorage.me','freelansim.ru','habrarchive.info','hsto.org'
		,	'megamozg.ru','sohabr.net','tmfeed.ru','tmtm.ru','toster.ru'
		]
	,	'_soc/tmtm.ru/'
	]
,	[
		[	'00f.net','0xd34df00d.me','0xj0e.sh','100r.co','1hakr.com','6vcr.com'
		,	'aaronbarker.net','abdulkadir.net','acegikmo.com','adameivy.com','adriancourreges.com','aivanf.com','akkartik.name'
		,	'al3x.net','alexanderell.is','alexandersandberg.com','alexanderwales.com','alexdevs.pw','alexguichet.com'
		,	'anastasiaopara.com','andrea.corbellini.name','andrew.im','andylomas.com','annevankesteren.nl'
		,	'apebox.org','apenwarr.ca','aphyr.com','arjlover.net','arkt.is','arrow2nd.com','asininetech.com','aurynn.com','azuki.dev'
		,	'b4bz.io','balovin.ru','beloved.family','berthub.eu','bfsc.to'
		,	'binarythinker.dev','binfalse.de','bitquabit.com','blackink.cz','blumia.net'
		,	'bnb.im','bolinfest.com','brendaneich.com','bricklin.com','brionv.com','brokenco.de','brouken.com'
		,	'burden.cc','byfat.xxx','byteofdev.com'
		,	'cadence.moe','catb.org','cbloom.com','chadnauseam.com','charity.wtf','chinedufn.com','chris.community'
		,	'coding.blog','codinghorror.com','coraline.codes','coreyhaines.com','cotonoha.io','cringely.com','crockford.com'
		,	'da.vidbuchanan.co.uk','dan.co.jp','daniel.do','danil-pistoletov.org','danluu.com','darkk.net.ru'
		,	'datagubbe.se','daverupert.com','david-colson.com','david-peter.de','davidbau.com'
		,	'dbohdan.com','dechifro.org','desu.systems','deveria.com','devroye.org','dfir.ru'
		,	'dmitry.gr','domenic.me','dotat.at','douady.paris','driven-by-data.net','dustmop.io'
		,	'east-ee.com','eddie4.nl','eev.ee','efcl.info'
		,	'elitedamyth.xyz','elladodelmal.com','elmghari.com','elopezr.com','emersion.fr'
		,	'eoe.codes','ericlippert.com','ethanmarcotte.com','eugeneronin.com','evpopov.com','exler.ru'
		,	'fantastiic.net','farshid.ashouri.org','flibitijibibo.com','florianimdahl.de'
		,	'frankchimero.com','frankforce.com','fredrikj.net','freebsd.dk','frogkun.com','fusik.info'
		,	'garbagecollected.org','genderi.org','giodicanio.com'
		,	'gomakethings.com','gregegan.net','gregoryszorc.com','guido.io'
		,	'haasn.xyz','hashman.ca','hidde.blog','hirob.in','hogg.io','hrishimittal.com','hrt.pw'
		,	'hsivonen.fi','httgp.com','huangxuan.me','humanwhocodes.com'
		,	'iamcal.com','ilikebigbits.com','imperialviolet.org'
		,	'inconvergent.net','independentlyreview.com','infrequently.org','isnot.jp'
		,	'j-paine.org','jeffwidener.com','jellyfish.software','jensscheffler.de','jez.io','jgc.org'
		,	'jhcloos.com','johnresig.com','joyfulbikeshedding.com','jujuadams.com','justi.cz','justin-p.me','jvns.ca','jwz.org'
		,	'k6n.jp','kageru.moe','kasperd.net','kazlauskas.me','kdy.ch','kentcdodds.com','kittygiraudel.com'
		,	'kolivas.org','konaka.com','kotochawan.com','kroah.com','kryogenix.org','ktcoope.com','kuroy.me'
		,	'l-c-n.com','l0cal.com','labalec.fr','lapcatsoftware.com','lerdorf.com'
		,	'lingdong.works','liriansu.com','logological.org','lwsmith.ca'
		,	'marcelschr.me','matt-diamond.com','mattmahoney.net','matthewbutterick.com','matthewflickinger.com','mayeu.me'
		,	'mcfunley.com','meesha.blog','merunno.dev','meyerweb.com','migeel.sk','mihaip.ro','mirovich.media'
		,	'mkweb.bcgsc.ca','mosra.cz','mrkiffie.com','mrpowerscripts.com','mutiny.cz'
		,	'nadyanay.me','nayuki.io','neilgaiman.com','n-e-r-v-o-u-s.com','noqqe.de','nullprogram.com','nullroute.lt','nyam.pe.kr'
		,	'oscarlage.com','oscarmlage.com','ospi.fi','oughta.be','overreacted.io'
		,	'p01.org','parazyd.org','pascoe.pw','paulbourke.net','paulgraham.com','paulirish.com','phoboslab.org','pinealservo.com'
		,	'plasmasturm.org','plausiblydeniable.com','pluralistic.net','praxeology.net','presidentbeef.com'
		,	'qntm.org','quad.moe'
		,	'rachelbythebay.com','randsinrepose.com','randy.gg'
		,	'readingjunkie.com','redsymbol.net','rifatchadirji.com','rinonninqueon.ru'
		,	'robbmob.com','robertxiao.ca','robrhinehart.com','rocketnine.space'
		,	'rodrigofranco.com','romaricpascal.is','ross.net','rsms.me','rudd.fyi'
		,	'saboteur.com.ua','sam.hocevar.net','samaltman.com','samip.fi','samy.pl','sarang.net','saschawillems.de'
		,	'schizofreni.co','schlueters.de','scobleizer.com','scripting.com'
		,	'sean.wtf','sebastiansylvan.com','sebastienlorber.com','sekao.net','seventeenzero.name'
		,	'shadura.me','shakesville.com','shazow.net','shontell.me','shoorick.ru','siipo.la','sirtetris.com','sjm.io'
		,	'slash7.com','slatestarcodex.com','slavfox.space','slbtty.info','smotko.si','snellman.net','sneyers.info','snook.ca'
		,	'stallman.org','starkravingfinkle.org'
		,	'steveklabnik.com','stevelosh.com','stevenhicks.me','stevenklambert.com','stevesouders.com'
		,	'stuartk.com','stuffwithstuff.com','stupidsystem.org'
		,	'superkuh.com','surma.technology','swyx.io'
		,	'taavi.wtf','t3hz0r.com','taoyue.com','techtldr.com','tema.ru'
		,	'thechaperon.ca','thegeekblog.co.uk','thesimplesynthesis.com','thirtythreeforty.net'
		,	'tjll.net','toolness.com','toolness.org','totodile.io','txlyre.website','tylerxhobbs.com','tyrrrz.me','tysontan.com'
		,	'underscorediscovery.com','unhandledexpression.com','urreta.io'
		,	'valdikss.org.ru','varesano.net','varlamov.ru','vas3k.ru','vincent0700.com','voidptr.io'
		,	'weitz.de','whileimautomaton.net','wh0rd.org','while.io','without.boats','woomai.net','writemoretests.com'
		,	'xeneder.com','xvezda.com'
		,	'yehudakatz.com','yiliansource.dev','yoooooooooo.com','yoshuawuyts.com','yoyo-code.com'
		,	'yun.complife.info','yuriy.gr','yusukekamiyamane.com'
		,	'zachholman.com','zegs.site','zpl.fi'
		]
	,	'_soc/_personal/'
	]
,	[['datadatadata.moe','desufags.rocks'		],'_soc/_personal//']
,	[['gavinhoward.com','gavinhoward.org'		],'_soc/_personal//']
,	[['leemeichin.com','mrlee.dev'			],'_soc/_personal//']
,	[['mattgemmell.com','whathaveyoutried.com'	],'_soc/_personal//']
,	[['rezodwel.tk','rezodwel.ml'			],'_soc/_personal//']
,	[['mastodon.social','mastodon.technology','mstdn.io','joinmastodon.org'],'_soc/_fediverse//']
,	[
		[	'baraag.net','fedi.inex.dev','fediverse.party','fosstodon.org'
		,	'instances.social','merveilles.town','pleroma.social','the-federation.info'
		]
	,	'_soc/_fediverse/'
	]
,	[
		[	'animeblogger.net','bearblog.dev','carrd.co','contently.com','dreamwidth.org'
		,	'exblog.jp','f-rpg.ru','forumer.com','forumotion.net'
		,	'hatenablog.com','home.blog','is-a.dev','komkon.org','listbb.ru','livejournal.com'
		,	'mail.ru','over-blog.com','ozlabs.org','simplecast.com','userecho.com','wixsite.com','wordpress.com'
		]
	,	'_soc/'
	,	{'sub': sub_domain_last_over_top2_exc_www}
	]
,	[
		[	'about.me','answers.com','arstechnica.com','askingbox.com','automattic.com','avaaz.org'
		,	'beon.ru','blogerator.ru','buffer.com'
		,	'carrd.co','change.org','chatovod.ru','creativebloq.com','crowdforge.io','curiouscat.me'
		,	'd3.ru','daum.net','diary.ru','diaryland.com','diasp.de','dirty.ru','experts-exchange.com'
		,	'foundation.app','friendfeed.com','friendi.ca','gab.com','geekcode.com','gitter.im','gravatar.com'
		,	'haxx.se','identi.ca','incels.me','juick.com'
		,	'linkedin.com','linktr.ee','liveinternet.ru','lj.rossia.org','ljsear.ch','lobste.rs'
		,	'manzanisimo.net','messenger.com','metafilter.com','mneploho.net','moikrug.ru','muddycolors.com'
		,	'naver.com','nicebrains.com','notion.so','onlinepetition.ru','otzovik.com','paigeeworld.com'
		,	'qiita.com','qntm.org','quora.com'
		,	'reddit.com','rossgram.ru','ru-board.com','signal.org','spacehey.com','svbtle.com'
		,	'tencent.com','thedndsanctuary.eu','tjournal.ru'
		,	'weeaboo.space','wfido.ru','woman.ru','xxiivv.com','ycombinator.com','zeemaps.com','zhihu.com'
		]
	,	'_soc/'
	]

#--[ programs ]----------------------------------------------------------------

,	[['crashplan.com','crashplanpro.com'		],'_software/_backup//']
,	[
		[	'bacula.org','boxbackup.org','duplicati.com'
		,	'rclone.org','rsnapshot.org','rsync.samba.org','urbackup.org','veeam.com','veridium.net'
		]
	,	'_software/_backup/'
	]
,	[get_rei(r'^mongodb\.\w+$'			),'_software/_db/mongodb.org']
,	[get_rei(r'^mysql(release|serverteam)?.com$'	),'_software/_db/mysql.com']
,	[
		[	'antirez.com','arangodb.com','datastax.com','keydb.dev','memcached.org','postgresql.org','sqlite.org','sqlitebrowser.org'
		]
	,	'_software/_db/'
	]
,	[['freedesktop.org'				],'_software/_free/']
,	[
		[	'datatypes.net','dotwhat.net','extension.info'
		,	'file.org','file-extension.org','file-extensions.org','fileinfo.com','filemagic.com','filewikia.com','filext.com'
		]
	,	'_software/_file_types/'
	]
,	[['midnight-commander.org','multicommander.com','quicksfv.org'	],'_software/_file_management/']
,	[get_rei(r'^(ghisler|(t|total|win)-?cmd)\.\w+$'			),'_software/_file_management/Total Commander/']
,	[get_rei(r'^movavi\.\w+$'			),'_software/_media/_codecs/movavi.com']
,	[['gyan.dev'					],'_software/_media/_codecs/ffmpeg.org/']
,	[['any-video-converter.com','avclabs.com'	],'_software/_media/_codecs//']
,	[['avidemux.org','avidemux.berlios.de'		],'_software/_media/_codecs//']
,	[['codecguide.com','codecguide.org'		],'_software/_media/_codecs//']
,	[['doom9.org','doom9.net'			],'_software/_media/_codecs//']
,	[['pavtube.com','pavtube.cn'			],'_software/_media/_codecs//']
,	[
		[	'1f0.de','avsforum.com','bunkus.org','cccp-project.net','deepvideolab.top','divx.com'
		,	'encode.moe','encoder.pw','ffmpeg.org','free-codecs.com','grass.moe','handbrake.fr','kmplayer.com','libav.org'
		,	'madshi.net','mkvtoolnix.download','mpc-hc.org','multimedia.cx'
		,	'orenvid.com','qoaformat.org','rowetel.com','svp-team.com','tipard.com'
		,	'videoconverterfactory.com','videohelp.com','virtualdub.org','vsdb.top','xiph.org','zeranoe.com'
		]
	,	'_software/_media/_codecs/'
	]
,	[['rarlab.com','win-rar.com'			],'_software/_media/_compression/RAR/']
,	[['info-zip.org','libzip.org','winzip.com'	],'_software/_media/_compression/ZIP/']
,	[['encode.pw','compression.pw'			],'_software/_media/_compression//']
,	[['encode.ru','encode.su'			],'_software/_media/_compression//']
,	[
		[	'7-zip.org','7-zip.org.ua','7-zip.de','7-zip.fr'
		,	'7zip.idfoss.org','7zip.rnbastos.com'
		,	'7zip-eo.rnbastos.com','7zip-es.updatestar.com','7zip-thai.inetbridge.net','7zip-vi.updatestar.com'
		]
	,	'_software/_media/_compression//'
	]
,	[
		[	'blosc.org','compression.ca','compression.ru','compression.great-site.net','compressionratings.com'
		,	'freearc.org','gzip.org','imagecompression.info','maximumcompression.com','mcmilk.de'
		,	'peazip.org','squeezechart.com','tc4shell.com','tukaani.org','wimlib.net','zipzip.pro','zlib.net'
		]
	,	'_software/_media/_compression/'
	]
,	[['reshade.me'					],'_software/_media/_grafix/_3D/']
,	[
		[	'animizer.net','cosmigo.com','easygifanimator.net','gif-animator.com','graphicsgale.com'
		,	'morevnaproject.org','pencil2d.org','sketch.metademolab.com','synfig.org'
		]
	,	'_software/_media/_grafix/_animation/'
	]
,	[
		[	'allrgb.com','colorcet.com','colorschemer.com','colourconstructor.com'
		,	'htmlcsscolor.com','wide-gamut.com','workwithcolor.com'
		]
	,	'_software/_media/_grafix/_color/'
	]
,	[
		[	'ijg.org','jpeg.org','jpegclub.org','jpegxl.info','jpegxl.io','libjpeg-turbo.org','openjpeg.org','brunsli.dev'
		]
	,	'_software/_media/_grafix/_formats/JPEG/'
	]
,	[['avif.io'					],'_software/_media/_grafix/_formats/AVIF/']
,	[['openexr.com'					],'_software/_media/_grafix/_formats/EXR, OpenEXR/']
,	[['openraster.org'				],'_software/_media/_grafix/_formats/ORA, OpenRaster/']
,	[['png-pixel.com'				],'_software/_media/_grafix/_formats/PNG/']
,	[['liimatta.org','qoiformat.org'		],'_software/_media/_grafix/_formats/QOI, Quite OK Image/']
,	[['chasemoskal.com'				],'_software/_media/_grafix/_formats/WebP/']
,	[['rfractals.net'				],'_software/_media/_grafix/_fractals/incendia.net/']
,	[
		[	'chaoticafractals.com','fractalarts.com','fractalfoundation.org','hvidtfeldts.net'
		,	'incendia.net','jwildfire.org','mandelbulb.com','ultrafractal.com'
		]
	,	'_software/_media/_grafix/_fractals/'
	]
,	[['css-ig.net','imageoptim.com','optimizilla.com','pngmini.com','pngquant.org','x128.ho.ua'	],'_software/_media/_grafix/_optimize/']
,	[['boltbait.com','dotpdn.com','paint-net.ru','psdplugin.com'					],'_software/_media/_grafix/Paint.NET/']
,	[['getpaint.net'				],'_software/_media/_grafix/Paint.NET/',{'sub': sub_domain_exc_www_directly}]
,	[['bforartists.de','blendernation.com'		],'_software/_media/_grafix/blender.org/']
,	[get_rei(r'^clip-?studio\.\w+$'			),'_software/_media/_grafix/clipstudio.net']
,	[['glimpse-editor.org'				],'_software/_media/_grafix/gimp.org/']
,	[['docs.krita.org','krita-artists.org'		],'_software/_media/_grafix/krita.org/']
,	[['community.mypaint.org'			],'_software/_media/_grafix/mypaint.org/']
,	[['forum.xnview.com','newsgroup.xnview.com'	],'_software/_media/_grafix/xnview.com//']
,	[['fluxometer.com','justgetflux.com'		],'_software/_media/_grafix/Flux']
,	[['cinepaint.org','cinepaint.bigasterisk.com'	],'_software/_media/_grafix//']
,	[['imagemagick.org','imagetragick.com'		],'_software/_media/_grafix//']
,	[['molecular-matters.com','liveplusplus.tech'	],'_software/_media/_grafix//']
,	[['procreate.art','procreate.si'		],'_software/_media/_grafix//']
,	[['pureref.com'					],'_software/_media/_grafix//',{'sub': [['forum',['forum']]]}]
,	[['systemax.jp'					],'_software/_media/_grafix//',{'sub': [['en',['en']],['ja',['ja']]]}]
,	[
		[	'acdsee.com','apophysis.org','ardfry.com','artrage.com','binomial.info','blender.org'
		,	'calligra.org','cdisplayex.com','darktable.org','digilinux.ru','drawpile.net'
		,	'escapemotions.com','exiftool.org','firealpaca.com','flam3.com','flif.info'
		,	'gegl.org','getgreenshot.org','gimp.org','glaretechnologies.com','gmic.eu','graficaobscura.com','graphicsmagick.org'
		,	'heavypoly.com'
		,	'illustration2vec.net','imageflow.io','imageglass.org','imgproxy.net'
		,	'inklab.studio','inkscape.org','irfanview.com','iryoku.com','justsketch.me'
		,	'kestrelmoon.com','krita.org','libregraphicsmeeting.org','libvips.org','live2d.com'
		,	'madewithmischief.com','mapeditor.org','medibangpaint.com','mitsuba-renderer.org','momentsingraphics.de','mypaint.org'
		,	'nathive.org','openboard.ch','opencolorio.org','openlayers.org'
		,	'paintstormstudio.com','photopea.com','photoscape.org','picascii.com','pinta-project.com','pixls.us'
		,	'planetside.co.uk','polycount.com','povray.org'
		,	'quickmark.com.tw','renderhjs.net','riot-optimizer.com','simplefilter.de','spillerrec.dk'
		,	'tachiyomi.org','taron.de','terawell.net','topazlabs.com'
		,	'vectormagic.com','vizref.com','vulkan.org','xcont.com','xnview.com'
		]
	,	'_software/_media/_grafix/'
	]
,	[
		[	'ableton.com','abundant-music.com','aimp.ru','audacityteam.org','audiosciencereview.com','digitalfeed.net'
		,	'head-fi.org','image-line.com','mpg123.de','mptrim.com','openmpt.org','renoise.com','riffusion.com','warmplace.ru'
		]
	,	'_software/_media/_sound/'
	]
,	[['hydrogenaudio.org','hydrogenaud.io'	],'_software/_media/_sound//']
,	[get_rei(r'^foobar2000\.\w+$'		),'_software/_media/_sound/foobar2000.org']
,	[get_rei(r'^mpesch3\.de(\d*\.\w+)?$'	),'_software/_media/_sound/mpesch3.de']
,	[['aegisub.org','opensubtitles.org'	],'_software/_media/_subtitles']
,	[
		[	'aomedia.org','avermedia.com','epubfilereader.com'
		,	'faasoft.com','filestar.com','fraps.com','hdtv.ru','khronos.org','kodi.tv'
		,	'mpv.io','nextpvr.com','sumatrapdfreader.org'
		]
	,	'_software/_media/'
	]
,	[['miranda-im.org','miranda-ng.org','vivaldi.net'				],'_software/_net/',{'sub': sub_domain_exc_www_directly}]
,	[['apache-mirror.rbc.ru','apachefriends.org','apachehaus.com','apachelounge.com'],'_software/_net/apache.org/']
,	[['miranda.im','miranda.or.at','miranda-me.ru','miranda-planet.com'		],'_software/_net/miranda-im.org/']
,	[['basilisk-browser.org','mypal-browser.org','nightlizard.libinfo.science','palemoon.org'],'_software/_net/moonchildproductions.info/']
,	[['angie.software','wbsrv.ru'			],'_software/_net/nginx.org//']
,	[['nginx.com','openresty.org','sysoev.ru'	],'_software/_net/nginx.org/']
,	[
		get_rei(r'^nginx\.\w+$')
	,	'_software/_net/nginx.org'
	,	{
			'sub':	sub_domain_last_over_top2_exc_www
			+	sub_lang_in_sub_dir
			+	sub_lang
		}
	]
,	[get_rei(r'^lunascape\.\w+$'	),'_software/_net/lunascape.tv']
,	[get_rei(r'^vivaldi\.\w+$'	),'_software/_net/vivaldi.net/']
,	[
		[	'amadzone.org','ashughes.com','canvasblocker.kkapsner.de'
		,	'fasezero.com','firefox.com','geckoworld.ru','kmeleonbrowser.org'
		,	'm64.info','mozdev.org','mozilla-community.org','mozilla-russia.org','mozilla64bit.com','mozillazine.org','mozvr.com'
		,	'searchfox.org','servo.org','waterfox.net'
		]
	,	'_software/_net/mozilla.org/'
	]
,	[
		get_rei(r'^mozilla\.\w+$')
	,	'_software/_net/mozilla.org'
	,	{
			'sub': [
				[get_rei(r'^(?:\w+:/+)?(?:www\.|(?!www\.))(((?:[^/.]+\.)*([^/.]+))\.[^/.]+\.\w+)/'), r'_subdomain/\3']
			,	['en',['en','en-US']]
			,	['ru',['ru','ru-RU']]
			] + sub_lang
		}
	]
,	[['jabber.at','jabber.org','jabber.ru','jabber.to','securejabber.me','xmpp.net','xmpp.org'		],'_software/_net/_XMPP,Jabber/']
,	[['handcraftedsoftware.org','ntc.party','shadowsocks.org','spys.one','torguard.net','winpcap.org'	],'_software/_net/_proxy,bypass/']
,	[['dns.net','isc.org','knot-resolver.cz','treewalkdns.com'	],'_software/_net/_DNS/']
,	[['kvirc.net'							],'_software/_net/_IRC/']
,	[['chiark.greenend.org.uk'					],'_software/_net/_SSH,SFTP/PuTTY']
,	[['bitvise.com','freesshd.com','kpym.com','syncplify.me'	],'_software/_net/_SSH,SFTP/']
,	[['postfix.org','sendmail.org','thunderbird.net'		],'_software/_net/_mail/']
,	[['flexihub.com','sane-project.org','synology.com'		],'_software/_net/_share/']
,	[['ammyy.com','rvisit.net','teamviewer.com','uvnc.com'		],'_software/_net/_remote_control/']
,	[['caddy.community'						],'_software/_net/caddyserver.com/']
,	[['bittorrent.com','bittorrent.org'				],'_software/_net//']
,	[['open-server.ru','ospanel.io'					],'_software/_net//']
,	[['owncloud.org','owncloud.com'					],'_software/_net//']
,	[['quic.rocks','quic.rocks:4433'				],'_software/_net//']
,	[['spacedesk.net','spacedesk.ph'				],'_software/_net//']
,	[['ispmanager.com','isplicense.ru','ispmanager.ru','ispsystem.ru'],'_software/_net//']
,	[
		[	'adblockplus.org','adium.im','altocms.ru','amiunique.org','apache.org','aprelium.com','avahi.org'
		,	'beakerbrowser.com','binaryoutcast.com','bitnami.com','browsehappy.com','browserleaks.com','bufferbloat.net'
		,	'caddyserver.com','caminobrowser.org','cancel.fm','curl.se','cys-audiovideodownloader.com'
		,	'darkreader.org','desy.de','dnscrypt.info','drupal.org','editthiscookie.com','envoyproxy.io'
		,	'falkon.org','filebrowser.xyz','filezilla-project.org','flexget.com','floorp.app','fossil-scm.org','ftptest.net'
		,	'hestiacp.com','htpcguides.com','httpie.io','hypercore-protocol.org','icq.com','istio.io'
		,	'jdownloader.org','joedog.org','libtorrent.org','lighttpd.net','litespeedtech.com'
		,	'moonchildproductions.info','mycroftproject.com','myvestacp.com','namecoin.info','netsurf-browser.org'
		,	'obsproject.com','openvpn.net','openwrt.org','opera.com','otter-browser.org','owasp.org'
		,	'phpbb.com','posthog.com','preferred-networks.jp','privateinternetaccess.com','pureftpd.org'
		,	'qbittorrent.org','qip.ru','qutebrowser.org','restoreprivacy.com'
		,	'sabnzbd.org','samba.org','skype.com','slsknet.org','srware.net'
		,	'tabliss.io','theworld.cn','tixati.com','torproject.org','tox.chat'
		,	'unhosted.org','utorrent.com','varnish-cache.org','vestacp.com','virtualmin.com'
		,	'w3techs.com','wampserver.com','webkit.org','webmin.com','wingup.org','winmtr.net','winscp.net'
		,	'yt-dl.org','zeronet.io','zotero.org'
		]
	,	'_software/_net/'
	]
,	[
		[	'ghostery.com','greasespot.net','greasyfork.org'
		,	'monkeyguts.com','noscript.net','online-generators.ru','openuserjs.org','tampermonkey.net'
		,	'unmht.org','userscripts-mirror.org','userscripts.org','userstyles.org'
		]
	,	'_software/_prog/_user_scripts,extensions/'
	]
,	[['isebaro.com','sebaro.pro'					],'_software/_prog/_user_scripts,extensions//']
,	[['pcre.org','regex101.com','regexbuddy.com','regexlib.com','regular-expressions.info','rexegg.com'],'_software/_prog/_regex/']
,	[['emscripten.org','wasmer.io','wasmtime.dev','webassembly.org','webassembly.studio'		],'_software/_prog/WebAssembly/']
,	[['asm32.info','eji.com','godbolt.org','wasm.ru'						],'_software/_prog/assembly/']
,	[['bbcmic.ro'											],'_software/_prog/Basic/']
,	[['arblib.org','ccodearchive.net','ioccc.org','llvm.org'					],'_software/_prog/C/']
,	[['boost.org','cplusplus.com','cppreference.com','cppstories.com'				],'_software/_prog/C++/']
,	[['css-live.ru','css-tricks.com','csslint.net','cssreset.com','csswizardry.com','purecss.io'	],'_software/_prog/CSS/']
,	[['dconf.org','dlang.org'									],'_software/_prog/D/']
,	[
		[	'delphi-treff.de','delphibasics.co.uk','embarcadero.com','freepascal.org','lazarus-ide.org','smartbear.com'
		]
	,	'_software/_prog/Delphi,Pascal/'
	]
,	[['ant-karlov.ru','flashdevelop.org','openfl.org'		],'_software/_prog/Flash/']
,	[['go.dev','godoc.org','golang.org','tinygo.org'		],'_software/_prog/Go/']
,	[['haxe.org','napephys.com'					],'_software/_prog/Haxe/']
,	[['javapoint.ru'						],'_software/_prog/Java/']
,	[get_rei(r'^java\.\w+$'						),'_software/_prog/Java/java.com']
,	[get_rei(r'^nodejs\.\w+$'					),'_software/_prog/JS/nodejs.org']
,	[['howtonode.org','node-os.com','npm-stats.com','npmjs.com'	],'_software/_prog/JS/nodejs.org/']
,	[['jsfuck.com'							],'_software/_prog/JS/JSFuck/']
,	[['bsonspec.org','json.org','json-schema.org'			],'_software/_prog/JS/JSON/']
,	[['deno.com','deno.land'					],'_software/_prog/JS/Deno']
,	[['david.li','shadertoy.com','webglfundamentals.org','webglreport.com','webglstudio.org'],'_software/_prog/JS/_3D,GPU,WebGL/']
,	[
		[	'2ality.com','3d2k.com','asmjs.org','babeljs.io','bestofjs.org','craig.is'
		,	'd3js.org','decaffeinate-project.org','duktape.org','dwitter.net'
		,	'ecma-international.org','ecmascript.org','esdiscuss.org','eslinstructor.net','exploringjs.com','gulpjs.com'
		,	'javascript.ru','javascriptissexy.com','jeasyui.com','joi.dev','jquery.com'
		,	'js.org','jsben.ch','jsbench.me','jsbin.com','jsclasses.org','jsdelivr.com','jsfiddle.net','jsmpeg.com','jsperf.com'
		,	'mathiasbynens.be','measurethat.net','mrale.ph','observablehq.com'
		,	'parceljs.org','phpjs.org','pixi.js','prototypejs.org','purescript.org'
		,	'quasar.dev','runkit.com','stateofjs.com','surma.dev'
		,	'threejs.org','turbo.build','ui.dev','unpkg.com','v8.dev','vanillajstoolkit.com','vitejs.dev','vuejs.org'
		]
	,	'_software/_prog/JS/'
	]
,	[['juliacomputing.com','julialang.org'					],'_software/_prog/Julia/']
,	[['arclanguage.org','plt-scheme.org','racket-lang.org'			],'_software/_prog/Lisp/']
,	[['lua.org','luajit.org','terralang.org'				],'_software/_prog/Lua/']
,	[['odin-lang.org'							],'_software/_prog/Odin/']
,	[['cpan.org','metacpan.org','perl.com','perl.org','perlmonks.org'	],'_software/_prog/Perl/']
,	[['ponylang.io'								],'_software/_prog/Pony/']
,	[
		['php.net']
	,	'_software/_prog/PHP//'
	,	{
			'sub': [
				['bugs'		,['bug.php','bug','bugs']]
			,	['internals'	,['php.internals','internals']]
		#	,	['rfc'		,['rfc']]
		#	,	['todo'		,['todo']]
			,	[get_rei(r'^/+(changelog)'	), r'\1']
			,	[get_rei(r'^/+(manual(/+\w+)?)/'), r'\1']
			,	[get_rei(r'^/+(migration)\d+'	), r'manual/\1']
			,	[get_rei(r'^(\w+:/+)?((www|secure|[a-z]{2}\d*)\.)?php\.\w+/+[\w-]+$'	), r'manual/functions']
			,	[get_rei(r'^(\w+:/+)?((www|secure|[a-z]{2}\d*)\.)?php\.\w+(/|$)'	), r'']
			,	[pat_subdomain_exc_www, r'\g<LastOverTop2>']
			]
		}
	]
,	[get_rei(r'^php\.\w+$'),'_software/_prog/PHP/']
,	[
		[	'3v4l.org','easyphp.org','externals.io','gophp5.org'
		,	'php-compiler.net','php-fig.org','php-myadmin.ru'
		,	'phpclasses.org','phpixie.com','phpsadness.com','phpversions.info','phpwact.org'
		,	'suhosin.org','zend.com'
		]
	,	'_software/_prog/PHP/'
	]
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
,	[
		[	'diveintopython.net','mpmath.org','py-my.ru','pygame.org','pyopenrpa.ru','pypa.io','pypi.org'
		,	'python.su','python-future.org','python3statement.org','pythonanywhere.com','pythonware.com'
		,	'pytorch.org','tensorflow.org'
		]
	,	'_software/_prog/Python/'
	]
,	[['qt.io','qtcentre.org'							],'_software/_prog/Qt/']
,	[['raku.guide','raku.org'							],'_software/_prog/Raku/']
,	[['railsgirls.com','ruby-forum.com','ruby-lang.org','rubyinstaller.org'		],'_software/_prog/Ruby/']
,	[
		[	'amethyst.rs','arewegameyet.rs','crablang.org','crates.io','docs.rs','fasterthanli.me','gamedev.rs','ggez.rs','lib.rs'
		,	'rapier.rs','redox-os.org','ruffle.rs','rust-lang.org','rustrepo.com','rustup.rs','rustycrate.ru','turbo.fish'
		]
	,	'_software/_prog/Rust/'
	]
,	[['scratch.mit.edu','scratch-wiki.info'						],'_software/_prog/Scratch/']
,	[['vlang.io'									],'_software/_prog/V/']
,	[['ziglang.org','ziglearn.org'							],'_software/_prog/Zig/']
,	[['learncodethehardway.org','programming-motherfucker.com','progmofo.com'	],'_software/_prog//']
,	[['numerical.recipes','nrbook.com','nr.com'					],'_software/_prog//']
,	[
		[	'30000000000000004.com','99-bottles-of-beer.net'
		,	'adventofcode.com','antipatterns.com','apiary.io','ariya.io','bikeshed.org','brat-lang.org'
		,	'cat-v.org','ccc.de','cleancoder.com'
		,	'code.golf','codeblocks.org','codeclimate.com','codefactor.io','codeforces.com'
		,	'codeincomplete.com','codepen.io','codetriage.com'
		,	'codr.cc','concurrencykit.org','coredump.cx','corte.si'
		,	'daringfireball.net','db0.company'
		,	'emojicode.org','enigma-dev.org','esolangs.org','example-code.com','exceptionnotfound.net'
		,	'float.exposed','floating-point-gui.de','gafferongames.com','garagegames.com','golancourses.net','golf.shinh.org'
		,	'handmade.network','hardmo.de','icontem.com','ideone.com','idownvotedbecau.se','infoq.com','iolanguage.org'
		,	'jacobdoescode.com','jemalloc.net','jetbrains.com','joelonsoftware.com','johndcook.com','jonskeet.uk','juliobiason.net'
		,	'kukuruku.co','leetcode.com','lgtm.com','lolcode.org','martinfowler.com','mergely.com','merrymage.com','mingw.org'
		,	'nim-lang.org','notepad-plus-plus.org','ocks.org','oneapi.io'
		,	'prettier.io','prideout.net','probablydance.com','probablyprogramming.com','programmersforum.ru'
		,	'realtimerendering.com','rosettacode.org'
		,	'schema.org','scintilla.org','semver.org','sfml-dev.org','spinroot.com','sscce.org'
		,	'thebookofshaders.com','thecodist.com','thedailywtf.com','tiobe.com','tproger.ru','tympanus.net'
		,	'unity3d.com','unrealengine.com','verou.me','visualstudio.com','viva64.com','wren.io','yaml.org'
		]
	,	'_software/_prog/'
	]
,	[['wiki.libsdl.org','forums.libsdl.org'				],'_software/_prog/libsdl.org/']
,	[get_rei(r'^libsdl\.\w+$'					),'_software/_prog/libsdl.org']
,	[['npp-user-manual.org'						],'_software/_prog/notepad-plus-plus.org/']
,	[['7-max.com','dataram.com'					],'_software/_ram/']
,	[
		[	'active-undelete.com','boot-disk.com'
		,	'disk-clone.com','disk-editor.org','disk-image.com','disk-monitor.com','disktools.com'
		,	'file-recovery.com','file-recovery.net','killdisk.com','killdisk-industrial.com','ntfs.com'
		,	'partition-recovery.com','pcdisk.com','smtp-server.com','uneraser.com','unformat.com','zdelete.com'
		]
	,	'_software/_recovery,undelete/lsoft.net'
	]
,	[['cgsecurity.org','lc-tech.com','lsoft.net','recuva.com','rlab.ru'],'_software/_recovery,undelete/']
,	[['cryptolaw.org','cryptopro.ru','openssl.org','qualys.com'	],'_software/_security/_encryption/']
,	[['1password.com','openid.net','password-crackers.ru'		],'_software/_security/_identity,passwords/']
,	[['eset.com','esetnod32.ru'					],'_software/_security/_malware/ESET NOD32/']
,	[get_rei(r'^anvir\.\w+$'					),'_software/_security/_malware/anvir.com']
,	[
		[	'360totalsecurity.com','avg.com','avira.com','bamsoftware.com','drweb.com'
		,	'hybrid-analysis.com','kaspersky.com','kasperskyclub.ru','krebsonsecurity.com','malwarebytes.com','mcafee.com'
		,	'securitylab.ru','thatisabot.com','threatpost.ru','virustotal.com','vxheaven.org'
		]
	,	'_software/_security/_malware/'
	]
,	[['meltdownattack.com','spectreattack.com'			],'_software/_security//']
,	[['shalla.de','shallalist.de'					],'_software/_security//']
,	[
		[	'bleachbit.org','crowdsec.net','cryptome.org','cve.org','cvedetails.com'
		,	'databreaches.net','ddosecrets.com','haveibeenpwned.com','murphysec.com','oss-fuzz.com'
		,	'positive.security','snyk.io','sophos.com','xato.net','xmco.fr','xsshunter.com'
		]
	,	'_software/_security/'
	]
,	[['openvz.org'							],'_software/_VM/']
,	[get_rei(r'^0install\.\w+$'					),'_software/0install.de']
,	[['ruplay.market','ruplaymarket.ru'				],'_software/Android//']
,	[
		[	'android.com','androidcentral.com','androidpit.com','apkmirror.com','apkreleases.com'
		,	'lineageosroms.org','opengapps.org'
		]
	,	'_software/Android/'
	]
,	[['freebsd.org','mirbsd.org','openbsd.org','openbsdfoundation.org'],'_software/BSD']
,	[['rsyslog.com'							],'_software/Linux/_syslog/']
,	[['debian.net','debian.org','devuan.org'			],'_software/Linux/Debian/']
,	[['pagure.io'							],'_software/Linux/Fedora/']
,	[get_rei(r'^[\w-]*fedora[\w-]*\.\w+$'				),'_software/Linux/Fedora']
,	[get_rei(r'^[\w-]*centos[\w-]*\.\w+$'				),'_software/Linux/CentOS']
,	[get_rei(r'^[\w-]*openartist[\w-]*\.\w+$'			),'_software/Linux/OpenArtist']
,	[get_rei(r'^[\w-]*pclinuxos[\w-]*\.\w+$'			),'_software/Linux/PCLinuxOS']
,	[get_rei(r'^[\w-]*(rosalab|rosalinux)[\w-]*\.\w+$'		),'_software/Linux/rosalinux.ru']
,	[get_rei(r'^[\w-]*slackware[\w-]*\.\w+$'			),'_software/Linux/Slackware']
,	[get_rei(r'^[\w-]*ubuntu[\w-]*\.\w+$'				),'_software/Linux/Ubuntu/']
,	[get_rei(r'^deepin\.\w+$'					),'_software/Linux/Deepin']
,	[['protondb.com','wine-staging.com','winehq.org'		],'_software/Linux/Wine']
,	[['fossies.org','fresh-center.net'				],'_software/Linux//']
,	[['raidix.ru','raidixstorage.com'				],'_software/Linux//']
,	[
		[	'alpinelinux.org','altlinux.org','archlinux.org','basealt.ru','catap.ru','chinauos.com'
		,	'dent.dev','distrowatch.com','dotdeb.org','droplinegnome.org'
		,	'finnix.org','funtoo.org'
		,	'gentoo.org','gnu.io','gnu.org','gobolinux.org','hyperbola.info','installgentoo.com','kernel.org','knopper.net'
		,	'lanana.org','launchpad.net','lftp.yar.ru'
		,	'linux.com','linux.die.net','linux.org.ru','linuxfoundation.org'
		,	'linuxhint.com','linuxjournal.com','linuxquestions.org','linuxtracker.org'
		,	'lkml.org','lwn.net','lxde.org'
		,	'manjaro.org','manned.org','nixos.org','nongnu.org','odminblog.ru'
		,	'partedmagic.com','pendrivelinux.com','redhat.com','rpmfind.net'
		,	'snapcraft.io','spdx.org','sta.li','suckless.org','syslinux.org','system-rescue-cd.org'
		,	'tldp.org','turnkeylinux.org','tuxfamily.org'
		,	'voidlinux.org','zorinos.com'
		]
	,	'_software/Linux/'
	]
,	[['github.io'							],'_software/github.com/',{'sub': sub_domain_last_over_top2_exc_www}]
,	[['gitlab.io'							],'_software/gitlab.com/',{'sub': sub_domain_last_over_top2_exc_www}]
,	[
		[	'ghtorrent.org','gitee.com','github.blog'
		,	'githubsatellite.com','githubstatus.com','githubuniverse.com','githubusercontent.com'
		]
	,	'_software/github.com/'
	]
,	[
		get_rei(r'^github\.\w+$')
	,	'_software/github.com'
	,	{
			'sub': sub_git + [
				['_users/_repositories'
				,	get_rei(r'[^?#]*\?([^&]*&)*tab=repos')
				,	[
						get_rei(r'(\s+\S\s+GitHub( - \w+)?([\s,(;-].*)?)?(\.[^.]+$)')
					,	r' - GitHub Repositories\4'
					]
				]
			] + sub_git_projects
		}
	]
,	[get_rei(r'^gitlab\.\w+$'					),'_software/gitlab.com',{'sub': sub_gitlab}]
,	[['hub.mos.ru'							],'_software/',{'sub': sub_gitlab}]
,	[
		get_rei(r'^osdn\.\w+$')
	,	'_software/osdn.net'
	,	{
			'sub': [
				[get_rei(r'^/+projects?/([^/?#]+)')	, r'_projects/\1']
			,	[pat_subdomain_exc_www			, r'_projects/\g<LastOverTop2>']
			]
		}
	]
,	[
		get_rei(r'^(sourceforge\.\w+|sf.net)$')
	,	'_software/sf.net'
	,	{
			'sub': [
				['_accounts'						, get_rei(r'^/+(auth|u|users?)/')]
			,	[get_rei(r'^/+(p|projects?|apps?/\w+)/([^/?#]+)')	, r'_projects/\2']
			,	[pat_subdomain_exc_www					, r'_projects/\g<LastOverTop2>']
			]
		}
	]
,	[get_rei(r'^codeberg\.\w+$'					),'_software/codeberg.org']
,	[get_rei(r'^edsd\.\w+$'						),'_software/edsd.com']
,	[get_rei(r'^ubi(soft)?\.\w+$'					),'_software/ubisoft.com']
,	[get_rei(r'^microsoft\.\w+$'					),'_software/microsoft.com',{'sub': sub_domain_last_over_top2_exc_www}]
,	[['wine-staging.com','winehq.org'				],'_software/Wine']
,	[['ss64.com','ss64.org'						],'_software/microsoft.com/_cmd/']
,	[['old-dos.ru'							],'_software/microsoft.com/DOS/']
,	[
		[	'akamaized.net','bing.com','classicshell.net','glass8.eu','half-open.com','live.com'
		,	'massgrave.dev','microsoftstore.com','modern.ie','msdn.com','msft.social'
		,	'office.com','outsidethebox.ms','sevenforums.com','sysinternals.com','tenforums.com'
		,	'whitekeys.ru','winaero.com','winbeta.org'
		,	'windows.com','windowsphone.com','windowsupdaterestored.com','wsusoffline.net'
		,	'xbox.com'
		]
	,	'_software/microsoft.com/'
	]
,	[['manictime.uservoice.com','support.manictime.com'		],'_software/manictime.com/']
,	[['custhelp.com','rightnow.com'					],'_software/oracle.com/']
,	[['abbyy.com','abbyy.ru'					],'_software//']
,	[['adobe.com','adobe.io','macromedia.com'			],'_software//']
,	[['aida64.com','aida64.co.uk','lavalys.com'			],'_software//']
,	[['atlassian.com','atlassian.net'				],'_software//']
,	[['bitbucket.org','bitbucket.io'				],'_software//']
,	[['makandracards.com','makandracards.de'			],'_software//']
,	[['piriform.com','ccleaner.com'					],'_software//']
,	[['qwoo.eu','qwi-tech.com'					],'_software//']
,	[['sourcehut.org','sr.ht'					],'_software//']
,	[['softline.ru','softline.com','store-softline-ru.turbopages.org'],'_software//']
,	[['thehighload.com','ruhighload.com'				],'_software//']
,	[['travis-ci.org','travis-ci.com'				],'_software//']
,	[['ukyo.dev','hujimi.seesaa.net'				],'_software//']
,	[['akeo.ie','rufus.ie'						],'_software//']
,	[
		[	'1progs.ru','3appes.com','4my.eu'
		,	'abi-laboratory.pro','accusoft.com','acme.com','advancemame.it','advsys.net','alternativeto.net'
		,	'ansuz.sooke.bc.ca','antibody-software.com','antipope.org','appveyor.com','aras-p.info','arbinada.com'
		,	'askwoody.com','assembla.com','astian.org','atom.io','awesomeopensource.com'
		,	'baierouge.fr','baremetalsoft.com','barton.de','bellard.org'
		,	'blicky.net','bountysource.com','bytehunter.net','bytepointer.com'
		,	'c3.cx','chainer.org','chikuyonok.ru','chocolatey.org','circleci.com','classicreload.com','clipsrules.net','cnpmjs.org'
		,	'cockos.com','code.horse','codeclimate.com','codecpack.co','codeplex.com'
		,	'cr.yp.to','crackwatch.com','crystalidea.com','crystalmark.info','cyberforum.ru'
		,	'ddecode.com','dege.freeweb.hu','dependencywalker.com','deskchan.info','desksoft.com','destroyallsoftware.com','dev.to'
		,	'dinaburg.org','diskanalyzer.com','docker.com','donationcoder.com','dunnbypaul.net','dz.rus'
		,	'ekioh.com','endoflife.date','entropymine.com','evolt.org','eyeleo.com'
		,	'filehippo.com','forkhq.com','fosshub.com','freedos.org','fsf.org','fuchsia.dev','fulgan.com'
		,	'geekly.info','ghacks.net'
		,	'git-scm.com','git-tower.com','gitee.io','gitfap.de','gitflic.ru','gitgud.io','githubmemory.com','gitorious.org'
		,	'gmane.org','gnome.org','gplates.org','grompe.org.ru'
		,	'h-online.com','haali.su','hackerone.com','hexagonwebs.com'
		,	'hkcmdr.anymania.com','howtogeek.com','humblebundle.com','hungry.com'
		,	'ifttt.com','implbits.com','informer.com','iwrconsultancy.co.uk','java.com','jonof.id.au'
		,	'kde.org','kmonos.net','kokkonen.net','kolibrios.org','kryo.se'
		,	'lakera.ai','liberamanifesto.com','libhunt.com','libraries.io','linkdata.se','lo4d.com','loyc.net'
		,	'maintainerati.org','manictime.com','mantishub.io','markdowntutorial.com','michelemorrone.eu','mitre.org'
		,	'mnot.net','monkrus.ws','mysku.ru'
		,	'nakka.com','neatnik.net','newos.org','nicobosshard.ch','nih.at','ninite.com','nirsoft.net'
		,	'notabug.org','nushell.sh','nxlog.co'
		,	'oldversion.com','openai.com','opengroup.org','openhub.net','opennet.ru','opensource.org','openwall.com'
		,	'oo-software.com','opensource.jp','oracle.com','oszone.net','outsidethebox.ms'
		,	'paragon-software.com','parallels.com','partitionwizard.com','patchmypc.com'
		,	'perkele.cc','phoronix.com','phrack.org','plex.tv','pooi.moe','portableapps.com'
		,	'producingoss.com','producthunt.com','psydk.org','qoo-app.com'
		,	'radsoft.net','rammichael.com','raxco.com','rawgit.com'
		,	'reactos.org','readthedocs.io','rizonesoft.com','roadkil.net','rocketgit.com'
		,	'saltstack.com','sanographix.net','sapib.ca','scout-soft.com','serenityos.org','shithub.us','skeeve.com','smithmicro.com'
		,	'softonic.com','softoxi.com','softpedia.com','softsea.com','softwareishard.com','sourceware.org'
		,	'sublimetext.com','superliminal.com','sury.org','system76.com'
		,	'tarsnap.com','techdows.com','thereisonlyxul.org','tinytools.directory'
		,	'udse.de','ultimatebootcd.com','ultimateoutsider.com'
		,	'veg.by','videolan.org','virtualbox.org','virtuallyfun.com','vitanuova.com','voidtools.com'
		,	'wearedevelopers.com','winmerge.org','wj32.org','wonderunit.com','wzor.net','xakep.ru','zestedesavoir.com'
		]
	,	'_software/'
	]

#--[ books + pasta ]-----------------------------------------------------------

,	[
		get_rei(r'^(titanpad\.com|piratepad\.net)$')
	,	''
	,	{
			'sub': [
				[get_rei(r'''^
					(\w+:/+)?
					([^/?#]+\.)*
					([^/?#]+\.\w+)/
					(\w+/)*
					(
						PUT_YOUR
					|	PAD_CODES
					|	HERE_ONE_PER_LINE
					)
					([/?#.]|$)
				''', re.X), r'_text/_special_pads'] # <- and change your target folder here
			,	[get_rei(r'^(\w+:/+)?([^/?#]+\.)*([^/?#]+\.\w+)/'), r'_text/_online_pad/\3']
			]
		}
	]
,	[
		[	'etherpad.fr','etherpad.org','note-pad.net','openetherpad.org'
		,	'pad.ouvaton.coop','piratenpad.de','piratepad.net','sync.in','titanpad.com'
		]
	,	'_text/_online_pad/'
	]
,	[
		[	'0bin.net','anonkun.com','bin.disroot.org','codepad.org','controlc.com','copypast.ru'
		,	'diffchecker.com','dropb.in','evernote.com','freetexthost.com'
		,	'ghostbin.co','hasteb.in','hastebin.com','hpaste.org','html.house','htmlpasta.com'
		,	'ivpaste.com','justpaste.it','kopipasta.ru','lpaste.net','meshnotes.com','notproud.ru'
		,	'paste.codenerd.com','paste.ee','paste.gg','paste.org.ru','paste.sh','paste2.org'
		,	'pasteall.org','pastebin.ca','pastebin.com','pastebin.ru'
		,	'pasted.co','pastehtml.com','pastie.org'
		,	'sendprayer.ru','slideshare.net','textsave.org','textuploader.com','txtdump.com'
		,	'webint.io','write.as','wtools.io'
		]
	,	'_text/_pasta/'
	]
,	[['privatebin.at','privatebin.info'			],'_text/_pasta//']
,	[['coollib.com','coollib.net'				],'_text/_books//']
,	[['b-ok.cc','pb1lib.org','zlibcdn.com'			],'_text/_books//']
,	[
		[	'7books.ru','an-ovel.com','baen.com','bhv.ru','blindsight.space','bookmate.com','chitai-gorod.ru'
		,	'dmkpress.com','ekniga.org','gutenberg.org','harry-harrison.ru','isfdb.org','kodges.ru'
		,	'librebook.me','libs.ru','litresp.com','online-knigi.com','paraknig.me'
		,	'ranobehub.org','readli.net','ridero.ru','sfsfss.com','uazdao.ru','unotices.com','vse-knigi.org'
		]
	,	'_text/_books/'
	]
,	[get_rei(r'^(read|write)thedocs\.\w+$'			),'_text/readthedocs.org']
,	[get_rei(r'^flibusta\.\w+$'				),'_text/flibusta.is']
,	[['anatolyburov.ru','artgorbunov.ru','maximilyahov.ru'	],'_text/glvrd.ru/']
,	[
		[	'100bestbooks.info','aho-updates.com','akniga.org','aldebaran.ru','alfalib.com'
		,	'argdown.org','armaell-library.net','author.today'
		,	'baka-tsuki.org','bards.ru','bigenc.ru','bookz.ru','botnik.org'
		,	'e-reading.club','fabulae.ru','fanfiction.net','fantlab.ru','ficbook.net'
		,	'gatter.ru','glvrd.ru','goodreads.com','koob.ru'
		,	'labirint.ru','leanpub.com','lem.pl'
		,	'lib.ru','lib.rus.ec','libgen.io','librebook.ru'
		,	'literotica.com','litmarket.ru','litmir.co','litmir.me','litres.ru','livelib.ru','lleo.me'
		,	'maxima-library.org','mcstories.com','modernlib.net','multivax.com','mybook.ru'
		,	'novel.tl','novelupdates.com','obd-memorial.ru'
		,	'porrygatter.zx6.ru','pritchi.ru','proza.ru','pushshift.io','quoteinvestigator.com'
		,	'readlightnovels.net','royallib.com','rulate.ru','rulibs.com','rulit.me','rus-bd.com','rusf.ru','russianplanet.ru'
		,	's-marshak.ru','sacred-texts.com','samlib.ru','smallweb.ru','springhole.net'
		,	'srkn.ru','stihi.ru','stihi-rus.ru','smartfiction.ru'
		,	'text.ru','textfiles.com','viaf.org','webnovel.com','worldcat.org','yourworldoftext.com'
		]
	,	'_text/'
	]

#--[ more stuff ]--------------------------------------------------------------

,	[
		['animetosho.org']
	,	'_torrents/'
	,	{
			'sub': [
				['_search'	,['search']]
			,	['_series'	,get_rei(r'^/*series'	+ part_url_tail_ID), r' - \g<ID>', replace_title_tail_unmht]
			,	['_series'	,['series']]
			,	['_episode'	,get_rei(r'^/*episode'	+ part_url_tail_ID), r' - \g<ID>', replace_title_tail_unmht]
			,	['_episode'	,['episode']]
			,	['_episodes'	,['episodes']]
			,	['_torrent_info',get_rei(r'^/*view'	+ part_url_tail_ID), r' - \g<ID>', replace_title_tail_unmht]
			,	['_torrent_info',['view']]
			,	['_file'	,get_rei(r'^/*file'	+ part_url_tail_ID), r' - \g<ID>', replace_title_tail_unmht]
			,	['_file'	,['file']]
			,	['_comments/feedback'	,['feedback']]
			,	['_comments'		,['comments']]
			]
		}
	]
,	[
		[	'1337x.to','acgnx.se','acgtracker.com','anicache.com'
		,	'animebytes.tv','animelayer.ru','animereactor.ru','anito.net'
		,	'booktracker.org','btdigg.org','btmon.com','btstorr.cc','catorrent.org','cgpersia.com','dmhy.org'
		,	'fitgirl-repacks.site','frozen-layer.com','gamestracker.org','gundam.eu'
		,	'iknowwhatyoudownload.com','kinozal.tv'
		,	'magnets.moe','mega-tor.org','ohys.net','opentrackers.org','oppaiti.me','orpheus.network'
		,	'pornolab.net','pornolabs.org','rargb.to','rustorka.com','shanaproject.com','stealth.si'
		,	'torrent-paradise.ml','torrenteditor.com','torrentfreak.com','touki.ru','tparser.org','tvu.org.ru'
		,	'unionpeer.org','webtorrent.io'
		]
	,	'_torrents/'
	]
,	[['arenabg.com','arenabg.ch'				],'_torrents//']
,	[['kickass.to','kat.cr'					],'_torrents//']
,	[['nyaa.net','nyaarchive.moe','pantsu.cat'		],'_torrents//']
,	[['openbittorrent.com','opentrackr.org'			],'_torrents//']
,	[['ouo.si'						],'_torrents//']
,	[['rarbg.to','rarbgaccess.org'				],'_torrents//']
,	[['rutor.org','freedom-tor.org'				],'_torrents//']
,	[get_rei(r'^anidex\.\w+$'				),'_torrents/anidex.info']
,	[get_rei(r'^forums?\.bakabt\.\w+$'			),'_torrents/bakabt.me/_forum']
,	[get_rei(r'^wiki\.bakabt\.\w+$'				),'_torrents/bakabt.me/_wiki']
,	[get_rei(r'^bakabt\.\w+$'				),'_torrents/bakabt.me']
,	[get_rei(r'^cgpeers\.\w+$'				),'_torrents/cgpersia.com/_tracker']
,	[get_rei(r'^isohunt\.\w+$'				),'_torrents/isohunt.to']
,	[get_rei(r'^nnm-club\.\w+$'				),'_torrents/nnm-club.ru']
,	[get_rei(r'sukebei?\.(nyaa\.(si|ink|unblockninja\.com)|nya\.iss\.one)$'	),'_torrents/nyaa.si/_hentai'	,{'sub': sub_nyaa}]
,	[get_rei(r'^(nyaa\.(si|ink|unblockninja\.com)|nya\.iss\.one)$'		),'_torrents/nyaa.si'		,{'sub': sub_nyaa}]
,	[get_rei(r'files?\.nyaa(torrents)?\.\w+$'				),'_torrents/nyaa.se/_static_files']
,	[get_rei(r'forums?\.nyaa(torrents)?\.\w+$'				),'_torrents/nyaa.se/_forum']
,	[get_rei(r'sukebei?\.nyaa(torrents)?\.\w+$'				),'_torrents/nyaa.se/_hentai'	,{'sub': sub_nyaa}]
,	[get_rei(r'^nyaa(torrents)?\.\w+$'					),'_torrents/nyaa.se'		,{'sub': sub_nyaa}]
,	[get_rei(r'^popgo\.\w+$'						),'_torrents/popgo.org']
,	[get_rei(r'^(tpb|(the|old)*pirate-?bay)(-?proxy)?\.\w+|$'		),'_torrents/thepiratebay.org']
,	[get_rei(r'^tokyo-?tosho\.\w+$'						),'_torrents/tokyotosho.info']
,	[get_rei(r'^((torrentparadise|internetwarriors)\.\w+|tracker\.cl)$'	),'_torrents/torrentparadise.net']
,	[get_rei(r'^(dostup-)?rutracker\.\w+$'					),'_torrents/rutracker.org/']
,	[
		['rutracker.org','torrents.ru','t-ru.org']
	,	'_torrents//'
	,	{
			'sub': [
				['_search'	,get_rei(r'^/*forum/+tracker\.php($|[?#])')]
			,	['_forum'	,['forum']]
			]
		}
	]

,	[
		['coub.com']
	,	'_video/coub.com/_mht'
	,	{
			'sub': [
				['_help'	,['help']]
			,	['_search'	,['tags']]
			,	['_videos'	,['view']]
			,	['_videos_embed',['embed']]
			]
		}
	]
,	[get_rei(r'^getcoub\.\w+$'				),'_video/coub.com/getcoub.ru']
,	[['coubassistant.com'					],'_video/coub.com/']
,	[['ggpht.com','ytimg.com'				],'_video/youtube.com/_img']
,	[
		[	'astronaut.io','blog.youtube','invidious.io','petittube.com'
		,	'returnyoutubedislike.com','yewtu.be','youtubekids.com'
		]
	,	'_video/youtube.com/_etc/'
	]
,	[
		['youtube.com']
	,	'_video/youtube.com/_mht'
	,	{
			'sub': [
				['_channel'	,['channel','c']]
			,	['_comments'	,['all_comments','comments','comment','comment_servlet']]
			,	['_playlist'	,['playlist','playlists']]
			,	['_search'	,['search','search_query','results','hashtag']]
			,	['_user'	,['user']]
			,	['_user'	,get_rei(r'^@')]
			,	['_videos'	,get_rei(r'^/*watch[^!#]*?[?&](?P<ID>v=[\w-]+)'), r',\g<ID>', replace_title_tail_yt_video]
			,	['_videos'		,['watch']]
			,	['_videos_embed'	,['embed','embeds']]
			,	['_videos_shorts'	,['short','shorts']]
			]
		}
	]
,	[
		[	'beam.pro','bilibili.com','cattube.org','cbc.ca','cybergame.tv','dailymotion.com','dsgstng.com'
		,	'filmy-smotret.online','forfun.com','freehentaistream.com','goodgame.ru'
		,	'hentaihaven.org','hidive.com','hitbox.tv','hooli.xyz'
		,	'iwara.tv','ivideon.com','kavin.rocks','kiwi.kz','liveleak.com','liveninegag.com','livestream.com','lowkey.gg'
		,	'manyvids.com','mat6tube.com','netflix.com','notalone.tv','openings.moe','ororo.tv'
		,	'picarto.tv','piczel.tv','polsy.org.uk','pornhub.com','rutube.ru','rule34video.com'
		,	'smashcast.tv','snep.pw','snotr.com','spankbang.com','streamable.com','synchtube.ru'
		,	'tenor.com','thisishorosho.ru','tiktok.com','twitch.tv'
		,	'vid.me','video.eientei.org','videvo.net','vidivodo.com','vimeo.com','vine.co'
		,	'w0bm.com','wasd.tv','webcams.travel','webkams.com','webm.host','webm.red','webmshare.com','webmup.com'
		,	'xhevc.com','xnxx.com','xvideos.com','youdubber.com','youku.com','youtubemultiplier.com','ytmnd.com'
		,	'z0r.de','zanorg.net','zenrus.ru'
		]
	,	'_video/'
	]

#--[ hosting ]-----------------------------------------------------------------

,	[['1.1.1.1','1.0.0.1','one.one.one.one'	],'_web/_DNS,domains//']
,	[['duiadns.net','duia.in'		],'_web/_DNS,domains//']
,	[['dyn.com','dyndns.com'		],'_web/_DNS,domains//']
,	[['icannwiki.com','icannwiki.org'	],'_web/_DNS,domains//']
,	[['zip'					],'_web/_DNS,domains/_TLD/_zip']
,	[get_rei(r'^(dot|nic)\.\w+$'		),'_web/_DNS,domains/_TLD/']
,	[get_rei(r'^easydns\.\w+$'		),'_web/_DNS,domains/easydns.com']
,	[get_rei(r'^no-?ip\.\w+$'		),'_web/_DNS,domains/no-ip.com']
,	[['opennic.org','opennicproject.org'	],'_web/_DNS,domains/OpenNIC/']
,	[
		['dynadot.com']
	,	'_web/_DNS,domains/'
	,	{
			'sub': [
				['_account'	,['account']]
			,	['_domain'	,['domain']]
			,	['_order'	,['order']]
			,	[get_rei(r'^/+(community)/+([^/]+)/+'), r'_\2']
			]
		}
	]
,	[
		[	'afraid.org','bind9.net','buydomains.com'
		,	'ddns.net','dnsflagday.net','dnsleaktest.com','dnsmadeeasy.com'
		,	'domaindiscount24.com','domainnamesales.com','domaintools.com'
		,	'dtdns.com','duckdns.org'
		,	'ens.domains','eurid.eu','eurodns.com','freenom.com','godaddy.com','host-domen.ru','hugedomains.com'
		,	'iana.org','icann.org','internic.net','ioc2rpz.net','isc.org'
		,	'name.com','namecheap.com','namegrep.com','nameitman.com','nastroisam.ru','nextdns.io','nslookup.io'
		,	'onlydomains.com','opendns.com','pairdomains.com','pho.to','porkbun.com','publicdomainregistry.com','publicsuffix.org'
		,	'reg.ru','respectourprivacy.com','rrpproxy.net','ru-tld.ru','safedns.com'
		,	'unstoppabledomains.com','urlvoid.com','webnames.ru','whatsmydns.net','ydns.eu'
		]
	,	'_web/_DNS,domains/'
	]
,	[
		[	'badssl.com','certbot.eff.org','certificatedetails.com','certificatemonitor.org','crt.sh'
		,	'freessl.com','freessltools.com','gethttpsforfree.com'
		,	'httpvshttps.com','immuniweb.com','instantssl.com','letsencrypt.org'
		,	'raymii.org','revocationcheck.com','ssl.com','ssldecoder.org','ssllabs.com','sslmate.com','startssl.com'
		]
	,	'_web/_HTTPS,SSL/'
	]
,	[['http3check.net','interop.seemann.io','quicwg.org'],'_web/_HTTP3,QUIC/']
,	[['geti2p.net','i2pd.website'		],'_web/_I2P/']
,	[['ipv6-test.com'			],'_web/_IPv6/']
,	[
		[	'2ip.ru','anti-hacker-alliance.com','cymon.io','db-ip.com','dronebl.org','dslreports.com'
		,	'find-ip-address.org','geoiplookup.net','hostingcompass.com','iblocklist.com','ifconfig.me'
		,	'ip.cn','ip-address.cc','ip-analyse.com','ip-tracker.org','ip2location.com','ipaddress-finder.com','ipaddresse.com'
		,	'ipindetail.com','ipinfo.io','ipinfolookup.com','ipip.net','ipligence.com','iplocationtools.com'
		,	'myip.ms','myip.ru','ntunhs.net','pdrlabs.net','ripe.net','robtex.com'
		,	'servisator.ru','showmyip.com','spamhaus.org','spys.ru','tcpiputils.com','tracemyip.org'
		,	'whatismyip.com','whatismyipaddress.com','who.is','whoer.net','yoip.ru'
		]
	,	'_web/_IP/'
	]
,	[
		[	'1v.to','adf.ly','aka.yt','bitly.com','flark.it','hitagi.ru','href.li','ll.la'
		,	'redirect.pizza','welcome.to','uwu.mx','v.gd'
		]
	,	'_web/_link/'
	]
,	[['bmetrack.com','freelists.org','list-manage.com','mail.com','mailchimp.com','tinyletter.com'	],'_web/_mail/']
,	[['antizapret.info','prostovpn.org'	],'_web/_VPN,proxy//']
,	[get_rei(r'^angryfox\.\w+$'		),'_web/_VPN,proxy/angryfox.org']
,	[
		[	'4mirror.workers.dev','6a.nl'
		,	'browse.ninja','dostup.website','findproxy.org','fri-gate.org','hi-l.eu','mf6.ru','onion.ly','onion.ws'
		,	'phantompeer.com','pickaproxy.com','privoxy.org','reqrypt.org','securitykiss.com'
		,	'tor2web.org','torrentprivacy.com','unblockit.dev','vpnpay.io','zaborona.help'
		]
	,	'_web/_VPN,proxy/'
	]
,	[['aboutcookies.org','cookie-consent.app.forthe.top','cookiepro.com','cookiepedia.co.uk'	],'_web/_site/_dev/_cookies/']
,	[['realfavicongenerator.net'		],'_web/_site/_dev/_favicons/']
,	[['openlinkprofiler.org'		],'_web/_site/_dev/_SEO,spam,bots/seoprofiler.com/']
,	[
		[	'ahrefs.com','blackhat.to','bns-advertising.co'
		,	'commoncrawl.org','cleantalk.org','deusu.de','exensa.com','extlinks.com','gdnplus.com'
		,	'law.di.unimi.it','moz.com','negativerseo.co','projecthoneypot.org','quicksprout.com'
		,	'screamingfrog.co.uk','searchengines.guru','seoprofiler.com','sogou.com','turnitin.com','yoast.com'
		]
	,	'_web/_site/_dev/_SEO,spam,bots/'
	]
,	[get_rei(r'^htmlhelp\.\w+$'		),'_web/_site/_dev/htmlhelp.com']
,	[['1c-bitrix.ru','bitrix24.ru'		],'_web/_site/_dev//']
,	[['ozma.io','vabl.io'			],'_web/_site/_dev//']
,	[['spoon.net','turbo.net'		],'_web/_site/_dev//']
,	[['jimdo.com','jimdofree.com'		],'_web/_site/_dev//']
,	[
		[	'acidtests.org','anybrowser.org','arwes.dev','astro.build'
		,	'beautifuljekyll.com','bizcoder.com','browserspy.dk'
		,	'caniuse.com','caprover.com','cloudinary.com','colorlib.com','coollabs.io','crisp.home.xs4all.nl','csvjson.com'
		,	'darkvisitors.com','denwer.ru','discourse.org','dklab.ru','dotapps.io'
		,	'eastmanreference.com','endtimes.dev','evilmartians.com'
		,	'figma.com','frontendmasters.com','getfirebug.com','getnikola.com','gohugo.io'
		,	'hiddedevries.nl','hpbn.co'
		,	'htmhell.dev','html5.org','html5blank.com','html5doctor.com','html5rocks.com','html5test.com','htmlbook.ru'
		,	'humanstxt.org','hypercomments.com'
		,	'ides.ru','iwanttouse.com','jasnapaka.com','javatpoint.com','keithclark.co.uk','kg-design.ru','kinsta.com','kirit.com'
		,	'larsjung.de','law.di.unimi.it','level-level.com','line25.com','linickx.com'
		,	'masv.io','microformats.org','miketaylr.com','mobiforge.com'
		,	'modern-web.dev','modernizr.com','modpagespeed.com','motherfuckingwebsite.com','movethewebforward.org'
		,	'nngroup.com','pingdom.com','quirksmode.org','rinigroup.ru','robotstxt.org','rrweb.io'
		,	'scale.at','scottlogic.com','securityheaders.com','securitytxt.org','simplemachines.org','sitemaps.org','sitepoint.com'
		,	'smashingmagazine.com','stackblitz.com','svelte.dev'
		,	'tafttest.com','themarkup.org','thisthat.dev','tilda.cc','timkadlec.com','tutorialrepublic.com','usefulscript.ru'
		,	'w3.org','w3fools.com','w3schools.com'
		,	'web.dev','webcompat.com','webdeveloper.com','wedal.ru','whatwg.org','wicg.io','wordpress.org','wpt.fyi'
		,	'xclacksoverhead.org','xnode.org'
		]
	,	'_web/_site/_dev/'
	]
,	[
		[	'disqus.com'
		]
	,	'_web/_site/_dev/'
	,	{
			'sub': sub_domain_last_over_top2_exc_www + [
				['by'	,['by']]
			,	['embed',['embed']]
			]
		}
	]
,	[['downdetector.com','downdetector.ru'		],'_web/_site/_is_it_up_or_down//']
,	[['downforeveryoneorjustme.com','downfor.io'	],'_web/_site/_is_it_up_or_down//']
,	[
		[	'doj.me','isitblockedinrussia.com','isitdownrightnow.com','isup.me','uptimestat.ru'
		]
	,	'_web/_site/_is_it_up_or_down/'
	]
,	[['panel.byethost.com','cpanel2.byethost.com','html-5.me','31.22.4.33'	],'_web/_site/byet.net/free']
,	[get_rei(r'^byethost\d*\.com$'						),'_web/_site/byet.net']
,	[['byet.net','byet.org','byet.host','ifastnet.com','securesignup.net'	],'_web/_site//']
,	[['billing.ua-hosting.company','justinstalledpanel.com'	],'_web/_site/ua.hosting/']
,	[['ua.hosting','ua-hosting.company'			],'_web/_site//']
,	[['my.fairyhosting.com','whs.ee'		],'_web/_site/fairyhosting.com/']
,	[['bytemark.co.uk','bigv.io'			],'_web/_site//']
,	[['hostinger.ru','hostinger.com'		],'_web/_site//']
,	[['itsoft.ru','pharm-studio.ru'			],'_web/_site//']
,	[['modx.com','modxcloud.com'			],'_web/_site//']
,	[['ogp.me','opengraphprotocol.org'		],'_web/_site//']
,	[['peredovik-company.ru','promolik.ru'		],'_web/_site//']
,	[['profitserver.ru','pssrv.ru'			],'_web/_site//']
,	[['stormwall.pro','stormwall.network'		],'_web/_site//']
,	[['webo.in','webogroup.com'			],'_web/_site//']
,	[['xanadu.com','xanadu.com.au'			],'_web/_site//']
,	[['cloudflarestatus.com'			],'_web/_site/cloudflare.com/']
,	[['herokuapp.com'				],'_web/_site/heroku.com/']
,	[get_rei(r'^hetzner\.\w+$'			),'_web/_site/hetzner.de']
,	[get_rei(r'^ucoz\.\w+$'				),'_web/_site/ucoz.ru']
,	[['beget.ru','beget.com','beget.email','sprut.io'		],'_web/_site/beget.tech/']
,	[['beget.tech','glitch.me','h1n.ru','netlify.app','tripod.com'	],'_web/_site/',{'sub': sub_domain_last_over_top2_exc_www}]
,	[['pandora.nu'							],'_web/_site/',{'sub': [['xiin',['xiin']]]}]
,	[['nfshost.com'							],'_web/_site/nearlyfreespeech.net/']
,	[['estt.ru','e-style-telecom.clients.site','ssd-vps.ru'			],'_web/_site//']
,	[['ovh.com','ovh.ie','ovh.net','ovhcloud.com','status-ovhcloud.com'	],'_web/_site//']
,	[['sprinthost.ru','sprinthost.online','sprintsite.ru','api.from.sh'	],'_web/_site//']
,	[
		[	'000webhost.com','1gb.ru','123systems.net','2dayhost.com','5apps.com'
		,	'aeza.net','afterburst.com','alexa.com','alwaysdata.com','atlex.ru','atwebpages.com'
		,	'best-hoster.ru','bitballoon.com','bluehost.com','botje.com','bplaced.net','branchable.com','brushd.com'
		,	'canarywatch.org','cloud4y.ru','cloudflare.com'
		,	'controlstyle.ru','copyscape.com','corpsoft24.ru','crimeflare.com','csssr.ru'
		,	'datafort.ru','debian.pro','dekel.ru','depohost.ru','digitalocean.com','dmoztools.net','domaincrawler.com'
		,	'ecatel.co.uk','ega.ee','eurobyte.ru'
		,	'fairyhosting.com','fastdivs.com','fasthosts.co.uk','fastvps.ru','firstvds.ru','fornex.com','fullspace.ru'
		,	'germanvps.com','getpagespeed.com'
		,	'hc.ru','heroku.com','ho.ua'
		,	'host.ru','host-food.ru','host-tracker.com','hostduplex.com','hostgator.com','hostia.ru','hostkey.ru','hostigger.com'
		,	'hosting.ua','hosting90.eu','hostings.info','hostingvps.ro','hostink.ru','hostland.ru'
		,	'ihc.ru','ihead.ru','ihor.ru','iliad-datacenter.com','ispsystem.com','jehost.ru','jino.ru'
		,	'king-servers.com','leapswitch.com','leaseweb.com','linode.com','litgenerator.ru','lowendtalk.com'
		,	'macloud.ru','mainhost.com.ua','majordomo.ru','makecloud.ru','marosnet.ru','mchost.ru','mclouds.ru','mediatemple.net'
		,	'nazuka.net','nearlyfreespeech.net','neocities.org','netangels.ru','netcraft.com','networksolutions.com','ngz-server.de'
		,	'online.net','oocities.org','opensearch.org','openshift.com','ourhost.az','ouvaton.coop'
		,	'pair.com','paper.li','peterhost.ru','prohoster.info','prq.se'
		,	'ramnode.com','ready.to','rgh.ru','robovps.biz','robtex.com','rt.ru','rusonyx.ru','ruvds.com'
		,	'salesforce.com','sbup.com','scaleway.com','selectel.ru','servers.ru','seven.hosting'
		,	'sib-host.ru','siteglobal.ru','siteground.com','siterost.net'
		,	'smartape.ru','sprintbox.ru','statonline.ru','status.io','sweb.ru'
		,	'time4vps.com','timeweb.com','txti.es','uptime.com'
		,	'vdsina.ru','vdska.ru','veesp.com','vps.house','vps.me','vps.today','vpsnodes.com','vpsserver.com','vultr.com'
		,	'w.tools','wappalyzer.com','webfaction.com','webguard.pro','webhostingsearch.com','webhostingtalk.com'
		,	'websiteoutlook.com','websitetoolbox.com','webzilla.com','wellserver.ru'
		,	'wix.com','whatdoesmysitecost.com','whatismybrowser.com','zomro.com'
		]
	,	'_web/_site/'
	]
,	[['fast.com','speedtest.net'			],'_web/_speed/']
,	[get_rei(r'^akamai(hd)?\.\w+$'			),'_web/akamai.com']
,	[get_rei(r'^www\.\w+$'				),'_web/www']
,	[['start.me','startme.com'			],'_web//']
,	[
		[	'1-9-9-4.ru','1mb.club','battleforthenet.com','cispa.saarland','codenerd.com','ctrl.blog','cyberia.is'
		,	'devnull-as-a-service.com','disroot.org','distributed.net','eff.org','evolutionoftheweb.com'
		,	'famfamfam.com','filippo.io','freaknet.org'
		,	'he.net','how-i-experience-web-today.com','howhttps.works','httparchive.org','hubstaff.com'
		,	'indieweb.org','internetgovernance.org'
		,	'miniwebtool.com','mywot.com','netlas.io','netmarketshare.com','netsafe.org.nz','njal.la'
		,	'opte.org','phreedom.club','quitsocialmedia.club'
		,	'rdca.ru','reclaimthenet.org','resetthenet.org','roskomsvoboda.org','rublacklist.net'
		,	'sapphire.moe','siteindices.com','spam-chaos.com','surveymonkey.com','symbolhound.com'
		,	'thehistoryoftheweb.com','troyhunt.com','uptime.is','uptolike.ru','user-agents.net'
		,	'webernetz.net','webhistory.org','webtechsurvey.com','wpt.live'
		]
	,	'_web/'
	]

#--[ wiki ]--------------------------------------------------------------------

,	[['boltwire.com','dokuwiki.org','foswiki.org','ikiwiki.info','pmwiki.org','trac.edgewall.org','twiki.org','wikimatrix.org'],'_wiki/_soft/']
,	[get_rei(r'^encyclopediadramatica\.\w+$'		),'_wiki/encyclopediadramatica.com']
,	[get_rei(r'^(mrakopedia|barelybreathing)\.\w+$'		),'_wiki/mrakopedia.ru']
,	[['absurdopedia.wiki','absurdopedia.net'		],'_wiki//']
,	[['traditio.ru','traditio-ru.org','traditio.wiki'	],'_wiki//']
,	[['urbanculture.lol','urbanculture.link'		],'_wiki//']
,	[[u'руни.рф','xn--h1ajim.xn--p1ai'			],'_wiki//']
,	[['wikia.nocookie.net'				],'_wiki/wikia.com/_img']
,	[['fandom.com','wikia.com','wikia.org'		],'_wiki//',{'sub': sub_wikia}]
,	[['wikifur.com'					],'_wiki/',{'sub': sub_wikia}]
,	[['scpfoundation.ru','scpfoundation.net'	],'_wiki/wikidot.com/_subdomain/scp-ru',{'sub': [['forum',['forum']]]}]
,	[['wdfiles.com'					],'_wiki/wikidot.com/']
,	[['wikidot.com'					],'_wiki/',{'sub': sub_domain_last_over_top2_forum + sub_domain_last_over_top2_exc_www}]
,	[['wikipedia.org'				],'_wiki/',{'sub': sub_domain_last_over_top2_exc_www}]
,	[['wikimedia.org','wikimedia.ru'		],'_wiki/wikipedia.org//']
,	[['wikivoyage.org','wikivoyage.ru'		],'_wiki/wikipedia.org//']
,	[
		[	'mediawiki.org','wikibooks.org','wikidata.org','wikimediafoundation.org'
		,	'wikipediastudy.org','wikiquote.org','wikitravel.org','wikiversity.org','wikiwand.com','wiktionary.org'
		]
	,	'_wiki/wikipedia.org/'
	]
,	[
		[	'1d4chan.org','allll.net','allthetropes.org','asianwiki.com','boobpedia.com'
		,	'c2.com','cirnopedia.info','cyclowiki.org','dramatica.org.ua'
		,	'emoji.wiki','emojipedia.org','eswiki.ru','everything2.com','fanlore.org','fractalwiki.org'
		,	'genworld.info','gfwiki.com','implyingrigged.info','kiwix.org','knowledgr.com','koumakan.jp','krsw-wiki.org'
		,	'liquipedia.net','lostmediawiki.com','lspace.org','lukomore.org','lurklurk.com','lurkmore.com'
		,	'miraheze.org','moegirl.org','neolurk.org','posmotre.li'
		,	'rationalwiki.org','ruwiki.ru','ruxpert.ru','scp-wiki.net','shoutwiki.com','sonichu.com'
		,	'tanasinn.info','tfwiki.net','tlwiki.org','tolkiengateway.net','touhouwiki.net','tvtropes.org','ufopaedia.org'
		,	'wiki2.org','wiki5.ru','wikichip.org','wikimapia.org','wikimultia.org','wikinews.org'
		,	'wikireality.ru','wikisource.org','wikitropes.ru','wikiwarriors.org'
		,	'wiktenauer.com','zeldawiki.org','znanierussia.ru'
		]
	,	'_wiki/'
	]
,	[get_rei(r'^lurkmo(re|ar|)\.\w+(:\d+)?$'),'_wiki/lurkmore.ru']

#--[ unsorted, etc ]-----------------------------------------------------------

,	[['geo.web.ru','jsjgeology.net','labradorit.de','lavrovit.ru','rockref.vsegei.ru','sibmin.ru'],'_materials,minerals/']
,	[['icloud.com'				],'apple.com/']
,	[
		['fcenter.ru','fcshop.ru']
	,	'//'
	,	{
			'sub': [
				['_news'	,['forprint','forprint.shtml','online','online.shtml']]
			,	['_shop'	,['price','product','products','products.shtml','products.shtml?eshop']]
			,	['_compare'	,['compare','compare.shtml']]
			,	['_forum'	,['fcconfa']]
			]
		}
	]
,	[
		[	'9to5google.com','goog','googleapis.com','googleblog.com','googlelabs.com'
		,	'googlesource.com','googlesyndication.com','googleusercontent.com','gstatic.com'
		,	'killedbygoogle.com','thinkwithgoogle.com','withgoogle.com'
		]
	,	'google.com/'
	]
,	[['lmgtfy.com','google.gik-team.com','g.zeos.in','justfuckinggoogleit.com'	],'google.com//']
,	[['code.google.com','googlecode.com'						],'google.com//']
,	[['drive.google.com','googledrive.com'						],'google.com//']
,	[['picasa.google.com','picasaweb.google.com'					],'google.com//']
,	[['accounts.google.com','profiles.google.com'					],'google.com/_accounts']
,	[['chrome.com','chromestatus.com','chromium.org','my-chrome.ru'			],'google.com/_chrome/']
,	[get_rei(r'^gmail\.\w+$'		),'google.com/_mail']
,	[get_rei(r'^9oogle\.\w+$'		),'google.com/9oogle.net']
,	[
		get_rei(r'^google(\.com?)?(\.\w+)?$')
	,	'google.com'
	,	{
			'sub': [
				['_accounts'	,['accounts','profiles','settings']]
			,	['_books'	,['books']]
			,	['_chrome'	,['chrome']]
			,	['_error'	,['error','sorry']]
			,	['_img'		,['images','imgres','imghp']]
			,	['_intl'	,['intl']]
			,	['_logos'	,['doodle4google','doodles','logos']]
			,	['_mail'	,['mail','gmail']]
			,	['_maps'	,['maps']]
			,	['_q&a'		,['answers','otvety']]
			,	['_reader'	,['reader']]
			,	['_registry'	,['registry']]
			,	['_search_images',['webhp']]
			,	['_search_images',get_rei(part_g_search + r'tbm=im?a?g?e?s+e?a?r?ch'	), pat_title_tail_g, r'\1 Images\3']
			,	['_search_news'  ,get_rei(part_g_search + r'tbm=ne?ws'			), pat_title_tail_g, r'\1 News\3']
			,	['_search_video' ,get_rei(part_g_search + r'tbm=vid'			), pat_title_tail_g, r'\1 Video\3']
			,	['_search'       ,get_rei(part_g_search + r'q=')]
			,	['_search'	,['search','custom','cse']]
			,	['_support'	,['support']]
			,	['_trends'	,['trends']]
			,	['_webmasters'	,['webmasters']]
			,	['_webstore'	,['webstore']]
			] + sub_q_search + sub_domain_exc_www
		}
	]
,	[get_rei(r'^greenpeace\.\w+$'		),'greenpeace.org']
,	[get_rei(r'^yahoo(\.com?)?\.\w+$'	),'yahoo.com',{'sub': sub_domain_last_over_top2_exc_www}]
,	[['turbopages.org','ya.ru','yandex-team.ru','yandexwebcache.net'],'yandex.ru/']
,	[
		get_rei(r'^yandex(\.\w+)?$')
	,	'yandex.ru'
	,	{
			'sub': [
				['_blog'	,['blog']]
			,	['_company'	,['company']]
			,	['_legal'	,['legal']]
			,	['_maps'	,['maps']]
			,	['_news'	,['news','sport']]
			,	['_questions'	,['q']]
			,	['_search_images',['images']]
			,	['_search'	,['blogs','search','yandsearch']]
			,	['_soft'	,['soft']]
			,	['_support'	,['support']]
			] + sub_domain_last_over_top2_exc_www
		}
	]
,	[['4my.eu'						],'/',{'sub': sub_domain_exc_www}]
,	[['mbaikal.ru','mybaikal.store'				],'//']
,	[['mil.ru',u'минобороны.рф','xn--90anlfbebar6i.xn--p1ai'],'//']
,	[['mvd.ru',u'мвд.рф','xn--b1aew.xn--p1ai'		],'//']
,	[[u'достижения.рф','xn--d1acchc3adyj9k.xn--p1ai'	],'//']
,	[['shoelace-knots.com','fieggen.com','professor-shoelace.com','shoe-lacing.com','shoelace-knot.com','shoelace.guru'],'//']
,	[
		[	'360cities.net','3dtoday.ru'
		,	'adme.ru','apparat.cc','apple.com','appspot.com','artlebedev.ru','ask.fm'
		,	'back-in-ussr.com','beeline.ru','bnw.im'
		,	'camelotintl.com','catsuka.com','championat.com','computerra.ru','ctrlpaint.com'
		,	'dahr.ru','disconnect.me','duckduckgo.com'
		,	'elkews.com','empower-yourself-with-color-psychology.com','englishrussia.com','etokavkaz.ru','europa.eu','everypony.ru'
		,	'fanres.com','faqs.org','ftn.su'
		,	'gearbest.com','geocaching.su','geraldika.ru','homeless.ru','howstuffworks.com'
		,	'idlewords.com','ietf.org','imdb.com','inspirobot.me','it-actual.ru','it-uroki.ru'
		,	'jewellerymag.ru','kino-teatr.ru','kinopoisk.ru'
		,	'lawsofux.com','lby3.com','lifehacker.com','lukom-a.ru','lumendatabase.org'
		,	'makeuseof.com','maphub.net','mos.ru','nplusonemag.com','npr.org','nuclearwarsurvivalskills.com'
		,	'oko.im','openstreetmap.org','osce.org','pirateparty.gr','poly-graph.co','poorworld.net','pudding.cool'
		,	'rambler.ru','randomwire.com','reformal.ru','remote-tourism.com'
		,	'scribblemaps.com','sibnet.ru','sibset.ru','sonniss.com','space.com','spravedlivo.ru','sputnik.ru'
		,	'stand-with-ukraine.pp.ua','statcounter.com','ststworld.com'
		,	'thebaffler.com','time.is','tutu.ru','tvoya-rossiya.ru','tvojavoda.ru'
		,	'un.org','unesco.org','vole.wtf','wikihow.com','worldometers.info','xenomorph.ru','zorca.ru'
		]
	]

#--[ internal ]----------------------------------------------------------------

,	[['about:','chrome:','chrome-error:','chrome-extension:','data:','discord:','moz-extension:','opera:', 'vivaldi:'],'!_browser/']
,	[['file:','resource:'],'!_LAN,intranet']
]

#--[ end of rules table ]------------------------------------------------------
