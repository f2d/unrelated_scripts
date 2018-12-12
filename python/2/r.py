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
part_domain = r'''(?P<All>(?P<AllOver2>(?P<LastOver2>[^/?#\s
]+)(?P<NotLastOver2>(?:\.[^/?#.\s
]+)*))(?P<TopBoth>(?P<Top2nd>\.[^/?#.\s
]+)(?P<Top>\.[^/?#.\s
]+)))(?:/|$)'''

pat_subdomain_inc_www = re.compile(part_protocol + part_domain, re.I)				# <- to treat "www" like a separate subdomain
pat_subdomain_exc_www = re.compile(part_protocol + r'(?:www\.|(?!www\.))' + part_domain, re.I)	# <- to discard "www", if any

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

,	[
		[	'17track.net','aftership.com','box-cargo.ru','cdek.ru','customs.ru','dellin.ru'
		,	'edost.ru','efl.ru','emspost.ru','gdeposylka.ru','jde.ru','mainbox.com'
		,	'nrg-tk.ru','packagetrackr.com','pecom.ru','pochta.ru','pochtoy.com','ponyexpress.ru','qwintry.com'
		,	'shipito.com','shopfans.ru','shopotam.ru','spk-ptg.ru','taker.im','tks.ru','ups.com','vnukovo.ru'
		]
	,	'_business/_delivery/'
	]
,	[['jobs-ups.com','ups-broker.ru'			],'_business/_delivery/ups.com/']
,	[['career.ru','hh.ru','job-mo.ru','upwork.com'		],'_business/_job/']
,	[['patreonhq.com'					],'_business/_money/_crowd-sourcing/patreon.com']
,	[
		[	'bomjstarter.com','boomstarter.ru','crowdrise.com','d.rip','gofundme.com','indiegogo.com'
		,	'kickstarter.com','patreon.com','yasobe.ru'
		]
	,	'_business/_money/_crowd-sourcing/'
	]
,	[['bitcoin.it','coindesk.com','hashcoins.com','polybius.io','wirexapp.com','z.cash'],'_business/_money/_crypto-coins/']
,	[['nigelpickles.com'					],'_business/_money/ko-fi.com/']
,	[['paypal-community.com'				],'_business/_money/paypal.com/']
,	[re.compile(r'(^|\.)paypal\.\w+$', re.I			),'_business/_money/paypal.com']
,	[re.compile(r'(^|\.)qiwi\.\w+$', re.I			),'_business/_money/qiwi.ru']
,	[re.compile(r'(^|\.)visa(\.com)?.\w+$', re.I		),'_business/_money/visa.com']
,	[
		[	'bestchange.ru','commishes.com','donationalerts.ru','gratipay.com','internetdengi.net','ko-fi.com'
		,	'mdmbank.ru','payonline.ru','payonlinesystem.com','sovest.com','tinkoff.ru','visa.com','webmoney.ru','xe.com'
		]
	,	'_business/_money/'
	]
,	[['dpdcart.com','getdpd.com'				],'_business/_shop//',{'sub': [[pat_subdomain_exc_www, r'_subdomain/\3']]}]
,	[re.compile(r'(^|\.)ali(baba|express|promo).\w+$', re.I	),'_business/_shop/aliexpress.com',{'sub': [[pat_subdomain_exc_www, r'_subdomain/\1']]}]
,	[re.compile(r'(^|\.)amazon(\.com?)?.\w+$', re.I		),'_business/_shop/amazon.com']
,	[re.compile(r'(^|\.)ebay\.\w+$', re.I			),'_business/_shop/ebay.com']
,	[re.compile(r'(^|\.)nix(\d*|opt)\.ru$', re.I		),'_business/_shop/nix.ru']
,	[['player.ru'						],'_business/_shop/pleer.ru/']
,	[
		[	'5ka.ru','aliexpress.com','amazon.com','avito.ru','bandb.ru','dpdcart.com'
		,	'ebay.com','etsy.com','myshopify.com','pleer.ru','regard.ru','shopify.com','taobao.com','techbot.ru'
		]
	,	'_business/_shop/'
	]
,	[
		[	'alibaba.com','bcorporation.net','bestchange.ru','businessinsider.com'
		,	'chistieprudi.info','creativecommons.org','croc.ru','dataspace.ru'
		,	'femida.us','fool.com','forbes.com','forentrepreneurs.com','go.jp','gopractice.ru','gs1.org'
		,	'ipwatchdog.com','irr.ru','kit.com','megafon.ru','mts.ru','nalog.ru'
		,	'pavluque.ru','producthunt.com','printerstudio.com','primeliber.com'
		,	'redbend.com','regionsoft.ru','sap.com','seekingalpha.com','sovest.com','stripe.com','subway.ru','sunrisecity.ru'
		,	'ted.com','trello.com','uspto.gov','vc.ru','wisdomgroup.com','zendesk.com'
		]
	,	'_business/'
	]

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

,	[
		[	'amiami.com','amiami.jp','anatomicaldoll.com','dollfiedream.tokyo','dsdoll.ph','e2046.com'
		,	'geekwars.ru','goodsmile.info','ihaztoys.com'
		,	'miniqtoys.com','myfigurecollection.net','ninoma.com','otakumode.com','plamoya.com','realdoll.com','sup-b.ru','trottla.net'
		]
	,	'_fig/'
	]

,	[['nyaarchive.moe','nyaa.pantsu.cat','sukebei.pantsu.cat'],'_torrents/nyaa.se/_db/']
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
		,	'filecloud.me','filedwon.info','filefactory.com','fileplanet.com','filesmelt.com','firedrop.com'
		,	'ge.tt','ichigo-up.com','ipfs.io','littlebyte.net'
		,	'mediafire.com','mixtape.moe','multcloud.com','my-files.ru','nofile.io','nya.is'
		,	'rapidgator.net','sendspace.com','solidfiles.com','storagon.com'
		,	'topshape.me','turbobit.net','upload.cat','uploadable.ch','uploaded.net','vocaroo.com','webfile.ru','zippyshare.com'
		]
	,	'_fileshares/'
	]

,	[['yummi.club'				],'_food/']

#--[ fun ]---------------------------------------------------------------------

,	[['ht-line.ru','marketgid.com','roomguru.ru','sh.st'],'_fun/_ad/']
,	[['nya.sh','nyash.org','nyash.org.ru'	],'_fun//']
,	[['bash.im','bash.org.ru'		],'_fun//']
,	[['ithappens.ru','ithappens.me'		],'_fun/bash.im//']
,	[['zadolba.li'				],'_fun/bash.im/']
,	[['kym-cdn.com'				],'_fun/knowyourmeme.com/pix']
,	[
		[	'2x2tv.ru','4tob.ru','9gag.com','airpano.ru','anekdot.ru','astrosfera.ru'
		,	'bash.org','breakingmad.me','cheezburger.com','cracked.com'
		,	'dagobah.net','det.org.ru','developerslife.ru','diginfo.tv','disemia.com','downloadmoreram.com','downloadmorerem.com'
		,	'fineleatherjackets.net','fishki.net','fucking-great-advice.ru','funimation.com','funnyjunk.com'
		,	'gieskes.nl','gooodnews.ru','govnokod.ru','hiddenlol.com','how-old.net'
		,	'i-mockery.com','illmosis.net','imgrush.com','instantrimshot.com','iwannarofl.com'
		,	'kaimi.ru','kg-portal.ru','killpls.me','knowyourmeme.com'
		,	'linorgoralik.com','live4fun.ru','me.me','medialeaks.ru','meduza.io','memepedia.ru','mrguy.com','myinstants.com','okolnica.ru'
		,	'pikabu.ru','prikol.ru','qdb.us','quickmeme.com','ribalych.ru'
		,	'sabbat.su','shitstream.ru','splasho.com','swfchan.com','top500.org','trinixy.ru'
		,	'waitbutwhy.com','yaplakal.com','yasdelie.ru','zen.ru'
		]
	,	'_fun/'
	]

#--[ games ]-------------------------------------------------------------------

,	[['nesdev.com','parodius.com'			],'_games/_console,emul//']
,	[['forums.pcsx2.net'				],'_games/_console,emul/pcsx2.net/']
,	[
		[	'asfdfdfd.com','coolrom.com','dosbox.com','emu-land.net','emu-russia.net','emuparadise.me','gbatemp.net'
		,	'mameworld.info','pcsx2.net','planetemu.net','psxdev.ru','romhack.net','romhustler.net','tic.computer'
		]
	,	'_games/_console,emul/'
	]
,	[['kongregate.com'								],'_games/_flash/']
,	[['c2community.ru','scirra.com'							],'_games/_making/Construct/']
,	[['gamemakerblog.com','gmapi.gnysek.pl','slw-soft.com','yal.cc','yoyogames.com'	],'_games/_making/Game Maker/']
,	[['gmlscripts.com','gmtoolbox.com'						],'_games/_making/Game Maker']
,	[['rpg-maker.info','rpgmaker.net','rpgmaker.ru','rpgmakerweb.com'		],'_games/_making/RPG Maker/']
,	[re.compile(r'(^|\.)rpg-?maker(web)?\.\w+$', re.I				),'_games/_making/RPG Maker']
,	[['ludumdare.com','ldjam.com'							],'_games/_making//']
,	[
		[	'armory3d.org','bulostudio.com','charas-project.net','dea.su','decarpentier.nl','deconstructoroffun.com','defold.com'
		,	'gamedev.net','gamedev.ru','gamefromscratch.com','gamesdonequick.com','gamesjam.org'
		,	'gdcvault.com','globalgamejam.org','godotengine.org'
		,	'lexaloffle.com','love2d.org','monogame.net','onehourgamejam.com','opengameart.org','procedural-worlds.com','procjam.com'
		,	'radgametools.com','rlgclub.ru','shiningrocksoftware.com','thegamecreators.com','tyranobuilder.com','unity.com','xsion.net'
		]
	,	'_games/_making/'
	]
,	[
		[	'celestia.space','inovaestudios.com','kerbalspaceprogram.com'
		,	'orbit.medphys.ucl.ac.uk','orbiter.dansteph.com','outerra.com','spaceengine.org','stellarium.org'
		]
	,	'_games/_space/'
	]
,	[re.compile(r'(^|\.)dischan\.\w+$', re.I	),'_games/dischan.org']
,	[re.compile(r'(^|\.)gamejolt\.\w+$', re.I	),'_games/gamejolt.com']
,	[re.compile(r'(^|\.)gamin\.\w+$', re.I		),'_games/gamin.ru']
,	[re.compile(r'(^|\.)kolenka\.\w+$', re.I	),'_games/kolenka.net']
,	[re.compile(r'(^|\.)mangagamer\.\w+$', re.I	),'_games/mangagamer.com']
,	[['agar.io','agar-io.ru'			],'_games//']
,	[['caiman.us','dlxcaiman.net'			],'_games//']
,	[['candies.aniwey.net','candybox2.net'		],'_games//']
,	[['nutaku.com','nutaku.net'			],'_games//']
,	[['renai.us','renpy.org'			],'_games//']
,	[['yager.de','specopstheline.com'		],'_games//']
,	[
		['steampowered.com','steamstatic.com']
	,	'_games//'
	,	{
			'sub': [
				['_account'	,['account','login','profiles']]
			,	['_agecheck'	,['agecheck']]
			,	['_app'		,['app']]
			,	['_bundle'	,['bundle']]
			,	['_cart'	,['cart']]
			,	['_checkout'	,['checkout']]
			,	['_search'	,['search']]
			,	['_sharedfiles'	,['sharedfiles']]
			,	['_sub'		,['sub']]
			]
		}
	]
,	[['steamcommunity.com','steamdb.info','steamgames.com','steamgifts.com','steamspy.com','valvesoftware.com'],'_games/steampowered.com/']
,	[['battle.net'							],'_games/Blizzard/']
,	[['playoverwatch.com'						],'_games/Blizzard/Overwatch/']
,	[['openbw.com','sc2mapster.com','starcraft.com'			],'_games/Blizzard/StarCraft/']
,	[['war2.ru'							],'_games/Blizzard/WarCraft/']
,	[['wowcircle.com','wowhead.com','wowwiki.com'			],'_games/Blizzard/WoW/']
,	[['chaosforge.org','doom2d.org','zdoom.org'			],'_games/Doom/']
,	[['eve-ru.com','eveonline.com','eveuniversity.org'		],'_games/EVE Online/']
,	[['shimmie.katawa-shoujo.com'					],'_games/katawa-shoujo.com/']
,	[['danmaku.mysteryparfait.com','flightoftwilight.com'		],'_games/mysteryparfait.com/']
,	[['megaman-world.ru','megamanxcorrupted.com','rockmanpm.com'	],'_games/Rockman (Megaman)/']
,	[['gensokyo.org','shrinemaiden.org','tasofro.net','thpatch.net'	],'_games/Touhou/']
,	[['uoguide.com'							],'_games/Ultima Online/']
,	[['bladefirelight.com','openxcom.org'				],'_games/X-COM (UFO) series/']
,	[['hg101.kontek.net'						],'_games/hardcoregaming101.net/']
,	[
		[	'1morecastle.com','1up.com','8bitevolution.com'
		,	'androidarts.com','anivisual.net','armitagegames.com','arturgames.com','asenheim.org','atarata.ru'
		,	'bit16.info','bngames.net','bungie.org'
		,	'cactusquid.com','cavestory.org','chrono.gg','chushingura46.com','com3d2.jp','compileheart.com','cs.rin.ru'
		,	'dailytelefrag.com','deepnight.net','deepsilver.com','desura.com','digital-synthesis.com','dividebyzer0.com'
		,	'dodistribute.com','doujinstyle.com','drivethrurpg.com','dside.ru','dtf.ru'
		,	'ea.com','empathybox.me','erogegames.com','escapistmagazine.com','eurogamer.net'
		,	'famicase.com','foreverapril.be','fuwanovel.net'
		,	'galyonkin.com','gamasutra.com'
		,	'game-debate.com','game-forest.com','gamebanana.com','gamebook.pw','gamedev.net','gamedev.ru','gamefaqs.com'
		,	'gamemux.com','gamenet.ru','gamepedia.com','gamer.ru','gameranx.com','gamesplanet.com','gametrax.eu'
		,	'gcup.ru','gog.com','granbluefantasy.jp'
		,	'fig.co','foddy.net','fullrest.ru','hardcoregaming101.net','hongfire.com'
		,	'ign.com','igromania.ru','indiedb.com','insani.org','itch.io'
		,	'kanobu.ru','katawa-shoujo.com','killscreendaily.com','kogado.com','konjak.org','kotaku.com'
		,	'legendsworld.net','lewdgamer.com','lionwood-studios.com','lokator-studio.ru','lparchive.org'
		,	'maxplay.io','mclelun.com','mightyno9.com','moddb.com','moregameslike.com','motion-twin.com'
		,	'myabandonware.com','mysteryparfait.com'
		,	'naarassusi-game.ru','namikaze.org','nd.ru','nethack.org','newgrounds.com','nexusmods.com'
		,	'nicalis.com','nisamerica.com','nrvnqsr.com'
		,	'old-games.com','old-games.ru','oneangrygamer.net','onegameamonth.com','onlyhgames.com','osu.ppy.sh','oxygine.org'
		,	'pcgamer.com','phantasy-star.net','pikointeractive.com','pixeljoint.com'
		,	'playstation.com','polygon.com','positech.co.uk','primitive-games.jp','projectwritten.com'
		,	'raphkoster.com','remar.se','renegade-x.com','rockpapershotgun.com','rockstargames.com','roguetemple.com'
		,	'sakevisual.com','sefan.ru','sekaiproject.com','sgn.net','shedevr.org.ru','shmuplations.com'
		,	'sinemoragame.com','skullgirls.com','shmups.com','small-games.info'
		,	'sonicretro.org','sovietgames.su','squares.net','squidi.net','stopgame.ru','summertimesaga.com'
		,	'strategycore.co.uk','strategywiki.org','suki.jp','sunrider-vn.com','superhippo.com','system11.org'
		,	'tasvideos.org','tatrix.org','tcrf.net','tesera.ru','theclassicgamer.net','theguardianlegend.com'
		,	'tigsource.com','tinykeep.com','totaljerkface.com','tozicode.com','tv-games.ru'
		,	'unepicgame.com','unseen64.net','usamin.info','vg247.com','vgmuseum.com','vndb.org','vogons.org'
		,	'warframe.com','warnworld.com','wayforward.com','worldoftanks.ru','xgm.guru','yardteam.org'
		]
	,	'_games/'
	]

#--[ devices ]-----------------------------------------------------------------

,	[['6p3s.ru','cqham.ru','cxem.net','qrz.ru','radiokot.ru','radioscanner.ru','radiostroi.ru'],'_hardware/_DIY/']
,	[['adexelec.com','ameri-rack.com'					],'_hardware/_cables,ports/']
,	[['dahua-spb.ru','dahuasecurity.com','dahuawiki.com','dh-russia.ru'	],'_hardware/_cam/']
,	[['eraworld.ru','svetlix.ru'						],'_hardware/_lamp/']
,	[['alcatelonetouch.com','alcatelonetouch.eu','alcatel-mobile.com'	],'_hardware/_mobile,phone,tablet//']
,	[['irbis-digital.ru','irbis.biz'					],'_hardware/_mobile,phone,tablet//']
,	[
		[	'4pda.ru','allnokia.ru','androidmtk.com','coolstylecase.com','gsmarena.com','gsmforum.ru','icover.ru','j-phone.ru','leagoo.com'
		,	'micromaxinfo.com','micromaxstore.ru','msggsm.com','mzarya.ru','nokia.com','repairmymobile.in','soft112.com','wexler.ru'
		]
	,	'_hardware/_mobile,phone,tablet/'
	]
,	[re.compile(r'(^|\.)netgear\.\w+$', re.I				),'_hardware/_net/netgear.com']
,	[
		[	'advancedtomato.com','arhab.org','asuswrt.lostrealm.ca','broadcom.com','cisco.com'
		,	'dd-wrt.com','granit-radio.ru','lede-project.org'
		,	'routerguide.net','rtl-sdr.com','snbforums.com','trendnet.com','vstarcam.ru'
		]
	,	'_hardware/_net/'
	]
,	[
		[	'americanmusclecar.ru','audi.co.uk','auto.ru','avtodom.ru','comma.ai','electrotransport.ru','euroresgroup.ru'
		,	'fotobus.msk.ru','garagashyan.ru','liaz-677.ru','lilium.com','motochrome.net'
		,	'pelec.ru','porsche.com','segway.cz','sherp.ru','spacex.com','tesla.com','trecol.ru','zapata.com'
		]
	,	'_hardware/_transport,cars/'
	]
,	[['apacer.com','flashboot.ru','mydigit.net','rmprepusb.com','sandisk.com','upan.cc','usbdev.ru'],'_hardware/_storage/_flash,cards,SD,USB/']
,	[
		[	'backblaze.com','hdd-911.com','hddmag.com','hddmasters.by','hddscan.com','hgst.com'
		,	'rlab.ru','seagate.com','wdc.com'
		]
	,	'_hardware/_storage/_HDD/'
	]
,	[['easeus.com','partition-tool.com'					],'_hardware/_storage/_HDD//']
,	[['silicon-power.com','ssd-life.com','ssdboss.com','storagegaga.com'	],'_hardware/_storage/_SSD/']
,	[['ocz.com','ocztechnologyforum.com'					],'_hardware/_storage/_SSD//']
,	[['enmotus.com','storagereview.com','win-raid.com'			],'_hardware/_storage/']
,	[['baikalelectronics.ru','cpuboss.com','mcst.ru'			],'_hardware/_CPU/']
,	[['aopen.com','evga.com','gpuboss.com','guru3d.com'			],'_hardware/_GPU/']
,	[['htcvive.com','oculus.com'						],'_hardware/_VR/']
,	[['jtksoft.net','joytokey.net'									],'_hardware/_controls//']
,	[['banggood.com','keysticks.net','migamepad.com','redragon.ru','rewasd.com','steelseries.com'	],'_hardware/_controls/']
,	[['coolermaster.com','kingpincooling.com','thermaltakeusa.com'					],'_hardware/_cooling/']
,	[['flatpanelshd.com','tftcentral.co.uk'			],'_hardware/_display,monitor/']
,	[['huiontablet.com','ugee.net','yiynova.su'		],'_hardware/_controls/_graphic_tablet/']
,	[['bosto-tablet.com','kingtee.ru'			],'_hardware/_controls/_graphic_tablet//']
,	[['xp-pen.com','xp-pen.ru','storexppen.com'		],'_hardware/_controls/_graphic_tablet//']
,	[re.compile(r'(^|\.)wacom(eng)?(\.com?)?\.\w+$', re.I	),'_hardware/_controls/_graphic_tablet/wacom.com']
,	[re.compile(r'(^|\.)elsa(-jp)?(\.com?)?\.\w+$', re.I	),'_hardware/_GPU/elsa.com']
,	[re.compile(r'(^|\.)dlink(tw)?(\.com?)?\.\w+$', re.I	),'_hardware/_net/dlink.com']
,	[re.compile(r'(^|\.)mikrotik\.\w+$', re.I		),'_hardware/_net/mikrotik.com']
,	[re.compile(r'(^|\.)tp-link(ru)?\.\w+$', re.I		),'_hardware/_net/tp-link.com']
,	[re.compile(r'(^|\.)zyxel\.\w+$', re.I			),'_hardware/_net/zyxel.com']
,	[['batareiki.by','batteries.gr','csb-battery.com','upsbatterycenter.com'],'_hardware/_power/_UPS/_batteries/']
,	[['riello-ups.com'					],'_hardware/_power/_ups/']
,	[re.compile(r'(^|\.)apc+(\.com?)?\.\w+$', re.I		),'_hardware/_power/_ups/apc.com']
,	[re.compile(r'(^|\.)(canon|c-ij)\.\w+$', re.I		),'_hardware/_printer/canon.com']
,	[re.compile(r'(^|\.)fix-free\.\w+$', re.I		),'_hardware/_printer/fix-free.ru']
,	[re.compile(r'(^|\.)(fuji)?xerox(\.com?)?\.\w+$', re.I	),'_hardware/_printer/xerox.com']
,	[['driversprintercanon.com','hi-black.ru','net-product.ru','t2now.ru'],'_hardware/_printer/']
,	[re.compile(r'(^|\.)asus(\.com?)?\.\w+$', re.I		),'_hardware/asus.com']
,	[re.compile(r'(^|\.)asmedia(\.com?)?\.\w+$', re.I	),'_hardware/asmedia.com.tw']
,	[re.compile(r'(^|\.)ecs(\.com?)?\.\w+$', re.I		),'_hardware/ecs.com.tw']
,	[re.compile(r'(^|\.)genius(net?)?\.\w+$', re.I		),'_hardware/genius.com']
,	[re.compile(r'(^|\.)gigabyte(\.com?)?\.\w+$', re.I	),'_hardware/gigabyte.com']
,	[re.compile(r'(^|\.)huawei\.\w+$', re.I			),'_hardware/huawei.com']
,	[re.compile(r'(^|\.)ifixit\.\w+$', re.I			),'_hardware/ifixit.com']
,	[re.compile(r'(^|\.)intel\.\w+$', re.I			),'_hardware/intel.com']
,	[re.compile(r'(^|\.)(nvidia|geforce)\.\w+$', re.I	),'_hardware/nvidia.com']
,	[re.compile(r'(^|\.)panasonic\.\w+$', re.I		),'_hardware/panasonic.com']
,	[re.compile(r'(^|\.)philips\.\w+$', re.I		),'_hardware/philips.com']
,	[re.compile(r'(^|\.)sony(\.com?)?\.\w+$', re.I		),'_hardware/sony.com']
,	[re.compile(r'(^|\.)supermicro(\.com?)?\.\w+$', re.I	),'_hardware/supermicro.com']
,	[re.compile(r'(^|\.)via-?(embedded|labs|tech)?(\.com?)?\.\w+$', re.I),'_hardware/via.com.tw']
,	[re.compile(r'(^|\.)zalman(\.com?)\.\w+$', re.I		),'_hardware/zalman.com']
,	[re.compile(r'(^|\.)amd-?(club|surveys?)\.\w+$', re.I	),'_hardware/amd.com/']
,	[['amd.com'						],'_hardware//',{'sub': [[pat_subdomain_exc_www, r'\1']]}]
,	[['arachnidlabs.com','notdot.net'			],'_hardware//']
,	[['st-lab.com','st-lab.ru','sunrichtech.com.hk'		],'_hardware//']
,	[['tomshardware.com','tomshardware.co.uk'		],'_hardware//']
,	[
		[	'3ders.org','3dmark.com','51cto.com','acer.com','altera.com','amd.by','amperka.ru','atmel.com'
		,	'breaknes.com','computer34.ru','computeruniverse.ru','crown-micro.com'
		,	'dadget.ru','datamath.org','defender.ru','dell.com','deskthority.net'
		,	'dialoginvest.com','digitalchip.ru','digital-razor.ru','dns-shop.ru'
		,	'electronshik.ru','espada-tech.ru','fccid.io','ferra.ru','flextron.ru'
		,	'gamemaxpc.com','garnizon.su','gearbest.com','goal.ru'
		,	'hp.com','htc.com','hwcompare.com','hyperpc.ru','innovatefpga.com','kinesis-ergo.com','kitguru.net'
		,	'lamptest.ru','lenovo.com','lg.com','logicalincrements.com','logitech.com','lucidlogix.com'
		,	'marsohod.org','marvell.com','mew-hpm.ru','micron.com','motherboard.vice.com','msi.com','mvideo.ru'
		,	'newegg.com','notebookcheck.net'
		,	'odroid.com','oldi.ru','outsidethebox.ms','overclock.net','overclockers.com','overclockers.ru'
		,	'pcnews.ru','perfeo.ru','pocketbook-int.com','polycom.com','powercube.ru','quadrone.ru','qumo.ru'
		,	'robo-hunter.com','rocketboards.org','rozetka.com.ua','rusograda.ru'
		,	'samsung.com','sannata.ru','startech.com','station-drivers.com','sven.fi','svyaznoy.ru'
		,	'technopoint.ru','terasic.com.tw','thesycon.de','thg.ru','tripplite.com'
		,	'ulmart.ru','usbkill.com','unitsolutions.ru','userbenchmark.com','yadro.com'
		]
	,	'_hardware/'
	]

#--[ pictures ]----------------------------------------------------------------

,	[re.compile(r'(^|\.)gensokyo.4otaku\.\w+$', re.I	),'_img/4otaku.ru/gensokyo.4otaku.ru']
,	[re.compile(r'(^|\.)4otaku\.\w+$', re.I			),'_img/4otaku.ru']
,	[re.compile(r'(^|\.)ricegnat\.\w+$', re.I		),'_img/ricegnat.moe']
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
,	[['yerkaland.com','yerka.org.ru'			],'_img//']
,	[['booth.pm','chat.pixiv.net','dic.pixiv.net','pixiv.help','pixivision.net','sketch.pixiv.net','spotlight.pics'],'_img/pixiv.net/']
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
,	[['deepdream.pictures','dreamscopeapp.com','zainshah.net'	],'_img//']
,	[re.compile(r'(^|\.)(cook|joy|porn)?reactor\.(cc|com)$', re.I	),'_img/joyreactor.cc']
,	[['waifu2x.udp.jp'		],'_img//',{'sub': [['_result',['api']]]}]
,	[['gramunion.com','studiomoh.com'],'_img/tumblr.com/']
,	[['media.tumblr.com'		],'_img/tumblr.com/_pix']
,	[['txmblr.com','www.tumblr.com'	],'_img/tumblr.com',{'sub': [['_video',['video']],'_mht']}]
,	[['tumblr.com'			],'_img/tumblr.com/_mht/_personal',{'sub': [['_post',['post']],'_subdomain']}]
,	[
		[	'animizer.net','ezgif.com','gfycat.com','gifcreator.me','gifmagic.com','giphy.com'
		]
	,	'_img/_animated/'
	]
,	[re.compile(r'(^|\.)0-?chan\.\w+$', re.I		),'_img/_board/0chan.ru',subscrape]
,	[re.compile(r'(^|\.)2-?chru\.\w+$', re.I		),'_img/_board/2chru.net']
,	[re.compile(r'(^|\.)m?2-?ch\.(cm|ec|hk|pm|ru|so)$', re.I),'_img/_board/2ch.so',subscrape]
,	[['largeb.ru'						],'_img/_board/2ch.so/']
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
				[None		,['d','errors']]
			,	'_scrape'
			]
		,	'sub': sub_a+[
				[unscrape	,re.compile(r'^err(or(s)?)?/|^[^/?#]+/arch/res/+([?#]|$)|^\.[\w-]+(/|$)|^[\w-]+\.\w+([?#]|$)', re.I)]
			]+sub_d
		}
	]
,	[re.compile(r'(^|\.)dobrochan\.\w+$', re.I		),'_img/_board/dobrochan.ru',{'sub_threads': '_scrape', 'sub': sub_a+sub_b}]
,	[re.compile(r'(^|\.)zenchan\.\w+$', re.I		),'_img/_board/zenchan.hk']
,	[['rei-ayanami.com','asuka-langley-sohryu.com','lsa.su'	],'_img/_board//']
,	[['horochan.ru','hanabira.ru','i-bbs.org','mayuri.ru'	],'_img/_board//']
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
,	[re.compile(r'(^|\.)(iichan|official)-eroge(-[\w-]+)?\.blogspot\.\w+$', re.I	),'_img/_board/iichan.ru/eroge']
,	[['everlastingsummer.su'							],'_img/_board/iichan.ru/eroge/']
,	[['iihub.org','iinet.tk'							],'_img/_board/iichan.ru/dev//']
,	[['2chance-projects.ru','iichantra.ru','neon.org','openchannel.tk'		],'_img/_board/iichan.ru/dev/']
,	[['hramopedia.esy.es'								],'_img/_board/iichan.ru/RPG chat/']
,	[['ichan.ru','ii.booru.org','noobtype.ru','coyc.net'				],'_img/_board/iichan.ru/']
,	[['ii-chan.ru','iichan.me','ii.dollchan.org','i.dollchan.org'			],'_img/_board/dollchan.org//',subscrape]
,	[['1chan.ru','1chan.ca'				],'_img/_board//']
,	[['3chan.co','3chan.ml'				],'_img/_board//',subscrape]
,	[['kurisu.ru','kurisa.ch'			],'_img/_board//']
,	[['xynta.ch','nahuya.ch'			],'_img/_board//']
,	[['wakachan.org','secchan.net'			],'_img/_board//',subscrape]
,	[['zerochan.in','snyb.tk','jaggy.site90.net'	],'_img/_board//']
,	[['touhou-project.com','touhouproject.com'	],'_img/_board//']
,	[['arhivach.org','arhivach.cf'			],'_img/_board//']
,	[
		[	'13ch.ru','d3w.org','lampach.net','lolifox.org','n0l.ch','nowere.net','owlchan.ru','rollach.ru','sibirchan.ru','zadraw.ch'
		]
	,	'_img/_board/'
	,	subscrape
	]
,	[
		[	'02ch.in','0m3ga.ga','1-chan.ru','100ch.ru','10ch.ru','12ch.ru','1chan.net'
		,	'2--ch.ru','2-ch.su','2ch.lv','2ch.net','2ch.rip','2chan.net','2channel.net','2channel.ru','2chru.net','2watch.in'
		,	'314n.org','4-ch.net','5channel.net','8chan.co','9ch.in','9ch.ru'
		,	'a2ch.ru','alphachan.org','alterchan.net','animuchan.net','anoma.ch','apachan.net','ascii.geekly.info'
		,	'bakachan.org','brchan.org','bunbunmaru.com','chanon.ro','chanstat.ru','chaos.fm','crychan.ru','cultnet.net','cunnychan.org'
		,	'deachrysalis.cc','depreschan.ovh','desulauta.org','devchach.ru'
		,	'dollchan.org','dollchan.ru','doushio.com','dscript.me','dva-ch.net','dva-ch.ru'
		,	'e3w.ru','ech.su','endchan.net','endchan.xyz','erlach.co','freedollchan.org','freeport7.org','futaba-only.net'
		,	'gaech.org','gamechan.ru','gchan.ru','glauchan.org','green-oval.net','gurochan.ch'
		,	'haibane.ru','hatsune.ru','hexchan.org','hikkachan.us','hivemind.me','honokakawai.com'
		,	'ichan.org','idlechan.net','iichan.net','iiichan.net','inach.org','ivchan.org','jsib.ml'
		,	'kakashi-nenpo.com','kazumi386.org','kohlchan.net','komica.org','krautchan.net','lenta-chan.ru','lucidchan.org','lynxhub.com'
		,	'maruchan.ru','metachan.ru','midorichan.ru','miskatonic.ko.tl','netchan.ru','nichan.net','nowai.ru','nullchan.org','nyamo.org'
		,	'ololoepepe.me','osach.ru','overchan.ru','owlchan.ru','ponyach.ru','post0chan.ru','rakochan.ru','rchan.ru','rfch.rocks'
		,	'samechan.ru','shanachan.org','sich.co','syn-ch.ru'
		,	'tanami.org','tinyboard.org','tripfags.com','trln.hk','twbbs.org'
		,	'u18chan.com','uboachan.net','uchan.to','ukrachan.org','utochan.ru'
		,	'vichan.net','volgach.ru','wizchan.org','xchan.ru','yochan.org','yotsubasociety.org'
		]
	,	'_img/_board/'
	]
,	[re.compile(r'(^|\.)4walled\.\w+$', re.I),'_img/_booru/4walled.cc']
,	[['derpiboo.ru','derpibooru.org'],'_img/_booru//']
,	[['konachan.com','konachan.net'	],'_img/_booru//']
,	[['yande.re','imouto.org'	],'_img/_booru//']
,	[['rule34.xxx','paheal.net'	],'_img/_booru//']
,	[['ecchi.me','animekon.com','ahmygoddesshentai.com','koribi.net','naughtytentaclehentai.com','hentaipornimages.com'],'_img/_booru//']
,	[['blog.desudesudesu.org','suigintou.desudesudesu.org','desudesudesu.org','nik.bot.nu'	],'_img/_booru/4scrape.net/']
,	[['chan.sankakucomplex.com','idol.sankakucomplex.com'					],'_img/_booru/sankakucomplex.com/']
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
,	[
		[	'4scrape.net','4walled.cc','anime-pictures.net','booru.org','cgwall.cn','derpiboo.ru','e-shuushuu.net','e621.net','e926.net'
		,	'fakku.net','gelbooru.com','luscious.net','mangadrawing.net','mspabooru.com','nijie.info','ostan-collections.net'
		,	'pururin.com','rewalls.com','safebooru.org','sakugabooru.com','sankakucomplex.com','shishnet.org','tbib.org','theanimegallery.com'
		,	'wallhaven.cc','wallpaperto.com','wallpaperup.com','xbooru.com','yande.re','yshi.org','zerochan.net','zombooru.com'
		]
	,	'_img/_booru/'
	]
,	[['peppercarrot.com'					],'_img/_comix/davidrevoy.com/']
,	[['blag.xkcd.com','blog.xkcd.com'			],'_img/_comix/xkcd//']
,	[['what-if.xkcd.com','whatif.xkcd.com','chtoes.li'	],'_img/_comix/xkcd//']
,	[['explainxkcd.com','forums.xkcd.com','xkcd.ru'		],'_img/_comix/xkcd/']
,	[
		re.compile(r'(^|\.)xkcd\.\w+$', re.I)
	,	'_img/_comix/xkcd'
	,	{
			'sub': [
				['xkcd.com', re.compile(r'^/*(\d+)([/?#_]|$)', re.I)]
			]
		}
	]
,	[['tapastic.com','tapas.io'				],'_img/_comix//']
,	[
		[	'acomics.ru','bubble.ru','captchacomics.com','comico.jp','comics.aha.ru','davidrevoy.com','dresdencodak.com','explosm.net'
		,	'giantitp.com','legorobotcomics.com','looking-for-group.ru','megatokyo.com','mspaintadventures.com','nerfnow.com','oglaf.com'
		,	'smbc-comics.com','sssscomic.com','talesofvaloran.com','themonsterunderthebed.net','theoatmeal.com'
		,	'visucomics.mechafetus.com','webcomunity.net','wthi.one'
		]
	,	'_img/_comix/'
	]
,	[
		['2draw.me','mekurage.html-5.me']
	,	'_img/_doodle//'
	,	{
			'sub': [
				[re.compile(r'^/+archive/(([^/?#]+/)+)\d+\.html?', re.I), r'archive/\2']
			,	['d'		,['d']]
			,	['i'		,['i']]
			,	['archive'	,['archive']]
			,	['room'		,['room']]
			,	[pat_subdomain_exc_www, r'\1']
			]
		}
	]
,	[['multator.ru','toonator.com'			],'_img/_doodle//',{'sub': [[pat_subdomain_exc_www, r'\1']]}]
,	[
		[	'2draw.net','aggie.io','anondraw.com','awwapp.com','chickensmoothie.com','chibipaint.com','cosketch.com'
		,	'doodleordie.com','drawception.com','drawr.net','drawrun.com'
		,	'flockdraw.com','flockmod.com','frenchgirlsapp.com','garyc.me','groupboard.com'
		,	'imudak.ru','iqqsy.com','iscribble.net','o0o0.jp','oekaki.ru','pica.so','scribblegrid.com','sketchdaily.net'
		]
	,	'_img/_doodle/'
	]
,	[
		['imgur.com']
	,	'_img/_host/'
	,	{
			'sub': [
				['albums'	,re.compile(r'^/+a/(\w+)', re.I), r',a,\1']
			,	['gallery'	,re.compile(r'^/+ga[lery]+/(\w+)', re.I), r',gallery,\1']
			]
		}
	]
,	[re.compile(r'(^|\.)imageshack\.\w+$', re.I		),'_img/_host/imageshack.us']
,	[re.compile(r'(^|\.)pinterest(\.com?)?\.\w+$', re.I	),'_img/_host/pinterest.com']
,	[['postimg.com','postimg.io'				],'_img/_host//']
,	[['prnt.sc','prntscr.com'				],'_img/_host//']
,	[
		[	'captionbot.ai','clip2net.com','diff.pics','doigaro.sdbx.jp','fastpic.ru','framecompare.com','funkyimg.com','gyazo.com'
		,	'hqpix.net','imagebam.com','imgsafe.org','imgup.co','instagram.com','jpegshare.net','jpg.to','nudes.nut.cc'
		,	'pinbrowse.com','photobucket.com','postimg.org'
		,	'savepic.net','screencapture.ru','screencast.com','screenshotcomparison.com','sli.mg','snag.gy'
		]
	,	'_img/_host/'
	]
,	[
	#	[	'37.48.119.23','37.48.119.24','37.48.119.27','37.48.119.40','37.48.119.44'
	#	,	'95.211.212.101','95.211.212.238','95.211.212.239','95.211.212.246'
	#	]
		re.compile(r'^(37\.48\.119\.|95\.211\.212\.)\d+$')
	,	'_img/_manga/e-hentai.org/_dl/_archive'
	]
,	[
		re.compile(r'(^|\.)e[x-]hentai\.org$', re.I)
	,	'_img/_manga/e-hentai.org'
	,	{
			'sub': [
				['_dl/_archive'	,['archive','archiver','archiver.php']]
			,	['_dl/_torrent'	,['torrent','torrents','torrents.php','gallerytorrents','gallerytorrents.php']]
			,	['_hath'	,['hentaiathome','hentaiathome.php']]
			,	['_tag'		,['tag','tag.php','tags','tags.php']]
			,	['_gallery'	,['g','gallery','gallery.php']]
			,	['_pages'	,['s','mpv']]
			,	[pat_subdomain_exc_www, r'\1']
			]
		}
	]
,	[['ehwiki.org','hentaiathome.net'		],'_img/_manga/e-hentai.org/']
,	[re.compile(r'(^|\.)madokami\.\w+$', re.I	),'_img/_manga/madokami.com']
,	[
		[	'a-zmanga.net','adultmanga.ru','bato.to','doujinland.com','doujinshi.org','dynasty-scans.com'
		,	'fanfox.net','gmimanga.com','grouple.co','hentai-chan.me','hentai2read.com','hentai4manga.com','hitomi.la'
		,	'jpmangaraw.com','kissmanga.com','lhtranslation.com'
		,	'manga.life','mangachan.ru','mangachan.me','mangadex.org','mangafox.me','mangahere.co','mangakakalot.com','mangalib.me'
		,	'mangaonlinehere.com','mangareader.net','mangarock.com','mangashare.com','mangaupdates.com'
		,	'mintmanga.com','mydailymanga.com','mymanga.me','nhentai.net','onemanga.com'
		,	'rawlh.com','readmanga.me','readms.com','senmanga.com','simple-scans.com','tonarinoyj.jp','tsumino.com'
		]
	,	'_img/_manga/'
	]
,	[['affinelayer.com','girls.moe','paintschainer.preferred.tech','qosmo.jp','s2p.moe'],'_img/_NN/']
,	[['whatanime.ga','trace.moe'						],'_img/_search//']
,	[['everypixel.com','iqdb.org','saucenao.com','tineye.com'		],'_img/_search/']
,	[['affect3dstore.com'							],'_img/affect3d.com/']
,	[['inktober.com','mrjakeparker.com'					],'_img//']
,	[['artstation.com'							],'_img/',{'sub': [['post',['post','artwork']]]}]
,	[
		[	'500px.com','affect3d.com','agawa.info','aika.ru','anatomynext.com','acomics.ru','alphacoders.com','arqute.com'
		,	'behance.net','cghub.com','cgwall.cn','clone-army.org','conceptart.org','cubebrush.com'
		,	'demiart.ru','drawcrowd.com','drawing.today','drawmanga.ru'
		,	'f-picture.net','flaticon.com','flaticons.net','flickr.com','freepik.com','furaffinity.net','fzdschool.com'
		,	'gas13.ru','girlimg.com','gumroad.com'
		,	'hentai.fyi','hentai-foundry.com','huaban.com','illustrators.ru','jamajurabaev.com','kommissia.ru'
		,	'lenna.org','leoartz.com','lockes-art.com','lofter.com'
		,	'magisterofficial.com','mechafetus.com','medicalwhiskey.com','moeimg.net','moregirls.org','mutimutigazou.com'
		,	'peperaart.com','pexels.com','photofunia.com','photomosh.com','photozou.jp','pixelartus.com','poocg.com','posemaniacs.com'
		,	'render.ru','ruanjia.com'
		,	'schakty.com','shii.org','simply-hentai.com','sketchfab.com','soup.io','studiominiboss.com'
		,	'theta360.com','textures.com','virink.com','wildtextures.com'
		]
	,	'_img/'
	]

#--[ Japan ]-------------------------------------------------------------------

,	[['haruhi.tv','yukichan-anime.com'					],'_jap/_anime,manga/kyotoanimation.co.jp/']
,	[['kami.im','madoka-magica.com','matomagi.com','puella-magi.net'	],'_jap/_anime,manga/Madoka/']
,	[['anime.sc','mal.oko.im'						],'_jap/_anime,manga/myanimelist.net/']
,	[['animenewsnetwork.com','animenewsnetwork.cc'				],'_jap/_anime,manga//']
,	[['findanime.ru','findanime.me'						],'_jap/_anime,manga//']
,	[['mahou-shoujo.moe','loli.coffee'					],'_jap/_anime,manga//']
,	[
		[	'anichart.net','anidb.net','anidub.com','anilist.co','animag.ru'
		,	'anime.mikomi.org','anime-mir.com','anime-now.com','anime-planet.com','anime-sharing.com'
		,	'animea.net','animeforum.ru','animemaga.ru','animemaru.com','animeonline.su'
		,	'animeshare.cf','animespirit.ru','animestyle-shop.ru','animesuki.com','arai-kibou.ru','aurora-raws.com'
		,	'cha-no-yu.ru','crunchyroll.com','cuba77.ru','d-addicts.com','desu.ru','diskomir.ru','fapservice.com','fast-anime.ru'
		,	'hentai-for.me','hungry-bags.ru','intercambiosvirtuales.org','jatshop.ru'
		,	'kageru.moe','kametsu.com','kaze-online.de','kiss-anime.co','kyotoanimation.co.jp','leopard-raws.org'
		,	'manga.tokyo','manga-home.com','mangaz.ru','mangazoneapp.com','manifest-spb.ru','monogatari-series.com','myanimelist.net'
		,	'nakanomangaschool.jp','narutoplanet.ru','nyanpass.com'
		,	'oldcastle.moe','otaku.ru','otakubell.com','over-ti.me','pierrot.jp','pixie-shop.ru'
		,	'raw-zip.net','rawacg.com','rawset.org','reanimedia.ru','russia-in-anime.ru','russian-cards.ru'
		,	'sahadou.com','sayoasa.jp','shikimori.org','sukasuka-anime.com','twist.moe','ushwood.ru','vcb-s.com','yaposha.com'
		]
	,	'_jap/_anime,manga/'
	]
,	[
		[	'anisab-subs.ru','ankokufs.us','asenshi.moe','damedesuyo.com'
		,	'fansubs.ru','fffansubs.org','ggkthx.org','honyaku-subs.ru','horriblesubs.info'
		,	'kitsunekko.net','lazylily.moe','melon-subs.de','mod16.org','pandasubs.zz.mu'
		,	'russian-subs.com','subs.com.ru','utw.me','vivid.moe','whynotsubs.com'
		]
	,	'_jap/_sub/'
	]
,	[['sparky4.net','4ch.mooo.com','yotsubano.me'	],'_jap//']
,	[['t-walker.jp','tw4.jp'			],'_jap//']
,	[['bof6.jp','e-capcom.com','capcom-s.jp'	],'_jap/co.jp/capcom.co.jp/']
,	[['seiga.nicovideo.jp','nicoseiga.jp'		],'_jap/nicovideo.jp//']
,	[['fate-go.jp'					],'_jap/typemoon.com/']
,	[
		re.compile(r'(^|\.)(fc2\.com|iinaa\.net|(co|ne|nobody|or)\.jp)$', re.I)
	,	'_jap/'
	,	{
			'sub': [
				[re.compile(r'^([^/?#]+)/+(~[^/?#]+)', re.I), r'\1,\2']
			,	[pat_subdomain_inc_www			, r'\1']
			]
		}
	]
,	[
		[	'ameblo.jp','animatorexpo.com','circle.ms'
		,	'd-stage.com','dannychoo.com','dlsite.com','dmm.com','enty.jp'
		,	'geocities.jp','goods-seisaku.com','gyutto.com','himado.in','idolwars.jp','ikaros.jp','itchstudios.com'
		,	'jlist.com','kannagi.net','kikyou.info','king-cr.jp','kisskiss.tv','kuku.lu','lifeinjapan.ru','livedoor.jp'
		,	'moe-gameaward.com','moehime.org','nalchemy.com','nicovideo.jp'
		,	'otakumode.com','ototoy.jp','ruranobe.ru'
		,	'saiin.net','seismicxcharge.com','shitaraba.net','silkysplus.jp','squeez-soft.jp','stickam.jp','straightedge.jp'
		,	'tackysroom.com','taptaptaptaptap.net','toranoana.jp','tw5.jp','typemoon.com','ufotable.info','usamimi.info','usen.com'
		]
	,	'_jap/'
	]

#--[ languages ]---------------------------------------------------------------

,	[['myscriptfont.com','calligraphr.com'					],'_lang/_fonts/_handwriting//']
,	[['fontcapture.com'							],'_lang/_fonts/_handwriting/']
,	[
		[	'1001fonts.com','1001freefonts.com'
		,	'allfont.ru','billyargel.com','blambot.com','comicraft.com','fixedsysexcelsior.com'
		,	'font2s.com','fontawesome.io','fontbureau.com','fontlibrary.org','fontke.com','fontmeme.com','fontreviews.com'
		,	'fonts.com','fonts-online.ru','fonts2u.com','fontspace.com','fontsquirrel.com'
		,	'freejapanesefont.com','irmologion.ru','marksimonson.com','myfonts.com','myscriptfont.com','nomail.com.ua'
		,	'paratype.ru','sil.org','tehandeh.com','xfont.ru','yourfonts.com'
		]
	,	'_lang/_fonts/'
	]
,	[['caniemoji.com','emojipedia.org','getemoji.com'			],'_lang/_unicode/_emoji/']
,	[
		[	'carrickfergus.de','codepoints.net','fileformat.info','graphemica.com'
		,	'unicode.org','unicode-table.com','unifoundry.com'
		]
	,	'_lang/_unicode/'
	]
,	[['oxforddictionaries.com','usefulenglish.ru'				],'_lang/en/']
,	[['jgram.org','susi.ru','tanoshiijapanese.com'				],'_lang/jp/']
,	[['academic.ru','gramota.ru','russkiy-na-5.ru','teenslang.su'		],'_lang/ru/']
,	[['endangeredlanguages.com','i2ocr.com','urbandictionary.com','vulgarlang.com','wordreference.com'],'_lang/']

#--[ music ]-------------------------------------------------------------------

,	[['abundant-music.com','auralfractals.net','fakemusicgenerator.com','jukedeck.com'],'_music/_generation/']
,	[['anon.fm','alcxemuct.accountant'				],'_music//']
,	[
		[	'ai-radio.org','animeradio.su','di.fm','dps-fm.com'
		,	'echo.msk.ru','edenofthewest.com','euroradio.fm','internet-radio.com'
		,	'moskva.fm','myradiostream.com','plaza.one','radio-astronomy.net','radiooooo.com','radioportal.ru'
		,	'shiza.fm','shoutcast.com','staroeradio.ru','tunein.com','zigafolk.ru'
		]
	,	'_music/_radio/'
	]
,	[['freesfx.co.uk','freewavesamples.com','philharmonia.co.uk'	],'_music/_samples/']
,	[['tenshi.ru','tenshi.spb.ru'					],'_music//']
,	[re.compile(r'(^|\.)keygenmusic\.\w+$', re.I			),'_music/keygenmusic.net']
,	[
		[	'8bitpeoples.com','a-pesni.org','animelyrics.com','aninx.com','bad-band.net','bandcamp.com','barryvan.com.au','boscaceoil.net'
		,	'cbcmusic.ca','chiptuneswin.com','clyp.it','daimp3.org','defytheocean.com'
		,	'fbits.ru','freemusicarchive.org','freesound.org','gendou.com','karaoke.ru','khinsider.com'
		,	'last.fm','lastfm.ru','lenin.ru','lesser-vibes.com','lilypond.org','littlesounddj.com'
		,	'megalyrics.ru','midi.ru','mp3ller.ru','modarchive.org'
		,	'musescore.com','music.uiowa.edu','musicishere.com','musicxml.com','musixmatch.com','muzlostyle.ru','myzuka.org'
		,	'nashipesni.info','nocopyrightsounds.co.uk','noteserver.org','ocremix.org','patefon.fm','picosong.com','pleer.com','realmusic.ru'
		,	's3m.it','s3m.us','sampleswap.org','sh-whitecrow.com','shemusic.org'
		,	'soundcloud.com','soundprogramming.net','spotify.com','surasshu.com','synthmania.com'
		,	'tekst-pesni-tut.ru','tenshi.ru','tlmc.eu','ubiktune.com','untergrund.net'
		,	'vgmdb.net','vgmpf.com','vgmrips.net','vmuzike.net','zaycev.net'
		]
	,	'_music/'
	]

#--[ society ]-----------------------------------------------------------------

,	[['poll-maker.com','pollcode.com','roi.ru','rupoll.com','simpoll.ru','strawpoll.me'],'_poll/']

,	[['cmu.edu','coursera.org','practicum.org','stanford.edu'	],'_science/_education/']
,	[re.compile(r'(^|\.)boinc(stats)?\.(\w+|berkeley\.edu)$', re.I	),'_science/BOINC/']
,	[re.compile(r'(^|\.)emdrive\.\w+$', re.I			),'_science/emdrive.com']
,	[
		[	'aboutbrain.ru','academia.edu','arbital.com','arxiv.org','astronomy.ru','berkeley.edu','buran.ru','calc.ru','cosmomayak.ru'
		,	'distill.pub','elementy.ru','eso.org','evanmiller.org','factroom.ru'
		,	'ieee.org','intelligence.org','kottke.org','laser.ru','lesswrong.com','linearcollider.org','manyworldstheory.com','membrana.ru'
		,	'naked-science.ru','nanometer.ru','nasa.gov','nature.com','nist.gov','nplus1.ru'
		,	'profmattstrassler.com','psihiatr.info','psychic-vr-lab.com','psylab.info','quantamagazine.org'
		,	'sciencemag.org','sens.org','shatters.net','stevenabbott.co.uk','universesandbox.com','wolframalpha.com','zelenyikot.com'
		]
	,	'_science/'
	]

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
,	[['blogs.mail.ru','cloud.mail.ru','otvet.mail.ru'			],'_soc/mail.ru/']
,	[['stwity.com','twimg.com','twitpic.com','twitrss.me','twpublic.com'	],'_soc/twitter.com/']
,	[['pp.userapi.com','vk.me'				],'_soc/vkontakte.ru/_pix']
,	[['vkfaces.com'						],'_soc/vkontakte.ru/']
,	[['vkontakte.ru','vk.com'				],'_soc//']
,	[['facebook.com','fb.com','internet.org'		],'_soc//']
,	[['mastodon.social','joinmastodon.org'			],'_soc//']
,	[['telegram.org','telegra.ph','t.me'			],'_soc//']
,	[['abdulkadir.net','redronin.de'			],'_soc//']
,	[['narod.ru'						],'_soc//',{'sub': [[pat_subdomain_exc_www, r'_subdomain/\3'],['_disk',['disk']]]}]
,	[['stackexchange.com'					],'_soc//',{'sub': [[pat_subdomain_exc_www, r'_subdomain/\3']]}]
,	[
		[	'animeblogger.net','exblog.jp','forumer.com','forumotion.net','livejournal.com','wordpress.com'
		]
	,	'_soc/'
	,	{'sub': [[pat_subdomain_exc_www, r'_subdomain/\1']]}
	]
,	[re.compile(r'(^|\.)stackoverflow(business)?\.\w+$', re.I		),'_soc/stackexchange.com/']
,	[['moms4mom.com','serverfault.com','stackstatus.net','superuser.com'	],'_soc/stackexchange.com/']
,	[['geektimes.ru','geektimes.com'					],'_soc/tmtm.ru//']
,	[['habrahabr.ru','habr.com'						],'_soc/tmtm.ru//']
,	[
		[	'brainstorage.me','freelansim.ru','habrarchive.info','hsto.org'
		,	'megamozg.ru','sohabr.net','tmfeed.ru','tmtm.ru','toster.ru'
		]
	,	'_soc/tmtm.ru/'
	]
,	[
		[	'about.me','arstechnica.com','askingbox.com','avaaz.org','beon.ru','blogerator.ru','blogger.com','buffer.com'
		,	'change.org','chatovod.ru','codinghorror.com','d3.ru','devroye.org','diary.ru','diasp.de','dirty.ru'
		,	'eev.ee','friendfeed.com','geekcode.com','incels.me','juick.com','kazlauskas.me'
		,	'linkedin.com','liveinternet.ru','lj.rossia.org'
		,	'mail.ru','medium.com','metafilter.com','mneploho.net','moikrug.ru','muddycolors.com'
		,	'nicebrains.com','odnoklassniki.ru','onlinepetition.ru','quora.com','reddit.com','ru-board.com'
		,	'scobleizer.com','shontell.me','slashdot.org','stupidsystem.org'
		,	'tencent.com','theverge.com','tjournal.ru','twitter.com','varlamov.ru','woman.ru','ycombinator.com','zeemaps.com'
		]
	,	'_soc/'
	]

#--[ programs ]----------------------------------------------------------------

,	[['bacula.org','boxbackup.org','duplicati.com','rsnapshot.org','urbackup.org','veridium.net'		],'_software/_backup/']
,	[re.compile(r'(^|\.)mysql(release|serverteam)?.com$', re.I						),'_software/_db/mysql.com']
,	[['arangodb.com','datastax.com','mongodb.org','postgresql.org','sqlite.org'				],'_software/_db/']
,	[['freedesktop.org'											],'_software/_free/']
,	[['datatypes.net','extension.info','file.org','file-extension.org','file-extensions.org','filext.com'	],'_software/_file_types/']
,	[re.compile(r'(^|\.)(ghisler|(t|total|win)-?cmd)\.\w+$', re.I	),'_software/_file_management/Total Commander']
,	[
		[	'avidemux.org','bunkus.org','cccp-project.net','codecguide.com','divx.com','doom9.org'
		,	'encoder.pw','ffmpeg.org','kmplayer.com','mpc-hc.org','multimedia.cx'
		,	'orenvid.com','rowetel.com','svp-team.com','videohelp.com','xiph.org'
		]
	,	'_software/_media/_codecs/'
	]
,	[['info-zip.org'						],'_software/_media/_compression/ZIP/']
,	[['rarlab.com','win-rar.com'					],'_software/_media/_compression//']
,	[
		[	'7-zip.org','compression.ru','compressionratings.com','encode.ru','freearc.org'
		,	'maximumcompression.com','tc4shell.com','tukaani.org'
		]
	,	'_software/_media/_compression/'
	]
,	[
		[	'animizer.net','easygifanimator.net','gif-animator.com','graphicsgale.com','morevnaproject.org','cosmigo.com','synfig.org'
		]
	,	'_software/_media/_grafix/_animation/'
	]
,	[['colorschemer.com','colourconstructor.com','workwithcolor.com'],'_software/_media/_grafix/_color/']
,	[['css-ig.net','imageoptim.com','optimizilla.com','pngmini.com','pngquant.org','x128.ho.ua'],'_software/_media/_grafix/_optimize/']
,	[re.compile(r'(^|\.)clip-?studio\.\w+$', re.I			),'_software/_media/_grafix/clipstudio.net/']
,	[['fluxometer.com','justgetflux.com'				],'_software/_media/_grafix/Flux']
,	[['dotpdn.com','getpaint.net','paint-net.ru'			],'_software/_media/_grafix/Paint.NET/']
,	[['rfractals.net'						],'_software/_media/_grafix/incendia.net/']
,	[['imagemagick.org','imagetragick.com'				],'_software/_media/_grafix//']
,	[
		[	'acdsee.com','apophysis.org','ardfry.com','artrage.com','blender.org','chaoticafractals.com'
		,	'digilinux.ru','drawpile.net','firealpaca.com','flam3.com','flif.info'
		,	'gegl.org','getgreenshot.org','gimp.org','glaretechnologies.com'
		,	'illustration2vec.net','incendia.net','inkscape.org','irfanview.com'
		,	'kestrelmoon.com','krita.org','libregraphicsmeeting.org','live2d.com'
		,	'madewithmischief.com','mapeditor.org','medibangpaint.com','mypaint.org','openraster.org'
		,	'photopea.com','photoscape.org','picascii.com','pixls.us','planetside.co.uk','polycount.com','procreate.si','pureref.com'
		,	'quickmark.com.tw','renderhjs.net','simplefilter.de','systemax.jp'
		,	'terawell.net','ultrafractal.com','vectormagic.com','xcont.com','xnview.com'
		]
	,	'_software/_media/_grafix/'
	]
,	[
		[	'ableton.com','abundant-music.com','aimp.ru','audacityteam.org','image-line.com'
		,	'mpg123.de','mptrim.com','openmpt.org','renoise.com'
		]
	,	'_software/_media/_sound/'
	]
,	[['hydrogenaudio.org','hydrogenaud.io'				],'_software/_media/_sound//']
,	[re.compile(r'(^|\.)foobar2000\.\w+$', re.I			),'_software/_media/_sound/foobar2000.org']
,	[re.compile(r'(^|\.)mpesch3\.de(\d*\.\w+)?$', re.I		),'_software/_media/_sound/mpesch3.de']
,	[['aegisub.org','opensubtitles.org'				],'_software/_media/_subtitles']
,	[['khronos.org'							],'_software/_media/']
,	[['openresty.org'						],'_software/_net/nginx.org/']
,	[re.compile(r'(^|\.)nginx\.\w+$', re.I				),'_software/_net/nginx.org']
,	[re.compile(r'(^|\.)lunascape\.\w+$', re.I			),'_software/_net/lunascape.tv']
,	[re.compile(r'(^|\.)vivaldi\.\w+$', re.I			),'_software/_net/vivaldi.net']
,	[
		[	'ashughes.com','basilisk-browser.org','fasezero.com','firefox.com','geckoworld.ru','kmeleonbrowser.org'
		,	'm64.info','mozdev.org','mozilla-community.org','mozilla-russia.org','mozilla64bit.com','mozillazine.org'
		,	'palemoon.org','servo.org'
		]
	,	'_software/_net/mozilla.org/'
	]
,	[
		re.compile(r'(^|\.)mozilla\.\w+$', re.I)
	,	'_software/_net/mozilla.org'
	,	{
			'sub': [
				[re.compile(r'^(?:\w+:/+)?(?:www\.|(?!www\.))(((?:[^/.]+\.)*([^/.]+))\.[^/.]+\.\w+)/', re.I), r'_subdomain/\3']
			,	['en',['en','en-US']]
			,	['ru',['ru','ru-RU']]
			]
		}
	]
,	[['jabber.at','jabber.org','jabber.ru','jabber.to','securejabber.me','xmpp.net'	],'_software/_net/_XMPP,Jabber/']
,	[['ammyy.com','rvisit.net','teamviewer.com','uvnc.com'				],'_software/_net/_remote_control/']
,	[['flexihub.com','sane-project.org','synology.com'				],'_software/_net/_share/']
,	[['bitvise.com','freesshd.com','kpym.com','syncplify.me'			],'_software/_net/_SSH,SFTP/']
,	[['apache-mirror.rbc.ru','apachehaus.com','apachelounge.com'			],'_software/_net/apache.org/']
,	[['miranda.im','miranda.or.at','miranda-me.ru','miranda-planet.com'		],'_software/_net/miranda-im.org/']
,	[['miranda-im.org','miranda-ng.org'						],'_software/_net/',{'sub': [[pat_subdomain_exc_www, r'\1']]}]
,	[['open-server.ru','ospanel.io'							],'_software/_net//']
,	[['spacedesk.net','spacedesk.ph'						],'_software/_net//']
,	[
		[	'adium.im','altocms.ru','apache.org','bitnami.com','bittorrent.com','caddyserver.com','cys-audiovideodownloader.com'
		,	'drupal.org','editthiscookie.com','filezilla-project.org','flexget.com','fossil-scm.org','ftptest.net'
		,	'htpcguides.com','icq.com','lighttpd.net','litespeedtech.com','namecoin.info'
		,	'obsproject.com','openvpn.net','openwrt.org','opera.com','owasp.org','owncloud.org'
		,	'qip.ru','phpbb.com','preferred-networks.jp','privateinternetaccess.com','skype.com','srware.net'
		,	'theworld.cn','tixati.com','tox.chat'
		,	'unhosted.org','utorrent.com','varnish-cache.org','virtualmin.com'
		,	'w3techs.com','wampserver.com','webmin.com','winmtr.net','winscp.net','zeronet.io'
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
,	[['regexbuddy.com','regular-expressions.info','rexegg.com'	],'_software/_prog/_regex/']
,	[['asm32.info','wasm.ru'					],'_software/_prog/assembly/']
,	[['ioccc.org','llvm.org'					],'_software/_prog/C/']
,	[['cplusplus.com','boost.org'					],'_software/_prog/C++/']
,	[['css-live.ru','css-tricks.com','cssreset.com','purecss.io'	],'_software/_prog/CSS/']
,	[['delphi-treff.de','delphibasics.co.uk','embarcadero.com','freepascal.org','lazarus-ide.org','smartbear.com'],'_software/_prog/Delphi,Pascal/']
,	[['ant-karlov.ru','flashdevelop.org','openfl.org'		],'_software/_prog/Flash/']
,	[['godoc.org','golang.org'					],'_software/_prog/Go/']
,	[['haxe.org','napephys.com'					],'_software/_prog/Haxe/']
,	[['javapoint.ru'						],'_software/_prog/Java/']
,	[re.compile(r'(^|\.)java\.\w+$', re.I				),'_software/_prog/Java/java.com']
,	[re.compile(r'(^|\.)nodejs\.\w+$', re.I				),'_software/_prog/JS/nodejs.org']
,	[['howtonode.org','node-os.com','npmjs.com'			],'_software/_prog/JS/nodejs.org/']
,	[['bsonspec.org','json.org'					],'_software/_prog/JS/JSON/']
,	[['david.li','shadertoy.com','webglfundamentals.org'		],'_software/_prog/JS/_3D,WebGL/']
,	[
		[	'2ality.com','asmjs.org','ecmascript.org'
		,	'javascript.ru','javascriptissexy.com','jquery.com','jsbin.com','jsclasses.org','jsfiddle.net','jsperf.com','jwz.org'
		,	'mathiasbynens.be','phpjs.org','pixi.js','prototypejs.org','unpkg.com','webassembly.org'
		]
	,	'_software/_prog/JS/'
	]
,	[['wiki.libsdl.org','forums.libsdl.org'				],'_software/_prog/libsdl.org/']
,	[re.compile(r'(^|\.)libsdl\.\w+$', re.I				),'_software/_prog/libsdl.org']
,	[['terralang.org'						],'_software/_prog/Lua/']
,	[['cpan.org','metacpan.org','perl.com','perl.org','perlmonks.org'],'_software/_prog/Perl/']
,	[
		['php.net']
	,	'_software/_prog/PHP//'
	,	{
			'sub': [
				['bugs'		,['bug.php','bug','bugs']]
			,	['internals'	,['php.internals','internals']]
		#	,	['rfc'		,['rfc']]
		#	,	['todo'		,['todo']]
			,	[re.compile(r'^/+(changelog)'						, re.I)	, r'\1']
			,	[re.compile(r'^/+(manual(/+\w+)?)/'					, re.I)	, r'\1']
			,	[re.compile(r'^/+(migration)\d+'					, re.I)	, r'manual/\1']
			,	[re.compile(r'^(\w+:/+)?((www|secure|[a-z]{2}\d*)\.)?php\.\w+/+[\w-]+$'	, re.I)	, r'manual/functions']
			,	[re.compile(r'^(\w+:/+)?((www|secure|[a-z]{2}\d*)\.)?php\.\w+(/|$)'	, re.I)	, r'']
			,	[pat_subdomain_exc_www							, r'\3']
			]
		}
	]
,	[re.compile(r'(^|\.)php\.\w+$', re.I)										,'_software/_prog/PHP/']
,	[
		[	'3v4l.org','easyphp.org'
		,	'php-compiler.net','php-fig.org','phpclasses.org','phpixie.com','phpsadness.com','phpwact.org'
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
,	[['diveintopython.net','py-my.ru','pygame.org','pypi.org','python.su','pythonware.com'		],'_software/_prog/Python/']
,	[['qt.io','qtcentre.org'									],'_software/_prog/Qt/']
,	[['ruby-forum.com','ruby-lang.org','rubyinstaller.org'						],'_software/_prog/Ruby/']
,	[['crates.io','docs.rs','redox-os.org','rust-lang.org','rustup.rs','rustycrate.ru','turbo.fish'	],'_software/_prog/Rust/']
,	[['learncodethehardway.org','programming-motherfucker.com','progmofo.com'			],'_software/_prog//']
,	[['whathaveyoutried.com','mattgemmell.com'							],'_software/_prog//']
,	[
		[	'99-bottles-of-beer.net'
		,	'cat-v.org','ccc.de','cleancoder.com','codeblocks.org','codeforces.com','codeincomplete.com','codepen.io','coredump.cx','corte.si'
		,	'daringfireball.net','enigma-dev.org','esolangs.org','exceptionnotfound.net'
		,	'gafferongames.com','garagegames.com','icontem.com','ideone.com','infoq.com'
		,	'jetbrains.com','joelonsoftware.com','johndcook.com','jonskeet.uk','kukuruku.co','lgtm.com','mergely.com','mingw.org'
		,	'nim-lang.org','notepad-plus-plus.org','ocks.org','probablyprogramming.com','programmersforum.ru','rosettacode.org'
		,	'schema.org','schizofreni.co','scratch.mit.edu','semver.org','sfml-dev.org','spinroot.com'
		,	'thecodist.com','thedailywtf.com','tiobe.com','tproger.ru','unity3d.com','unrealengine.com','viva64.com'
		]
	,	'_software/_prog/'
	]
,	[['7-max.com','dataram.com'					],'_software/_ram/']
,	[['cgsecurity.org','recuva.com','rlab.ru'			],'_software/_recovery,undelete/']
,	[['qualys.com'							],'_software/_security/_encryption/']
,	[['eset.com','esetnod32.ru'					],'_software/_security/_malware/ESET NOD32/']
,	[re.compile(r'(^|\.)anvir\.\w+$', re.I				),'_software/_security/_malware/anvir.com']
,	[
		[	'360totalsecurity.com','avg.com','avira.com','bamsoftware.com','drweb.com'
		,	'hybrid-analysis.com','kaspersky.com','kasperskyclub.ru','krebsonsecurity.com'
		,	'securitylab.ru','thatisabot.com','threatpost.ru','vxheaven.org'
		]
	,	'_software/_security/_malware/'
	]
,	[['meltdownattack.com','spectreattack.com'			],'_software/_security//']
,	[['sophos.com','xato.net'					],'_software/_security/']
,	[re.compile(r'(^|\.)0install\.\w+$', re.I			),'_software/0install.de']
,	[['android.com','androidcentral.com','androidpit.com','apkmirror.com','apkreleases.com','lineageosroms.org','opengapps.org'],'_software/Android/']
,	[['freebsd.org','openbsd.org'					],'_software/BSD']
,	[['rsyslog.com'							],'_software/Linux/_syslog/']
,	[['fedoraproject.org','getfedora.org'				],'_software/Linux/Fedora']
,	[re.compile(r'(^|\.)centos\.\w+$', re.I				),'_software/Linux/CentOS']
,	[re.compile(r'(^|\.)openartist(hq)?\.\w+$', re.I		),'_software/Linux/OpenArtist']
,	[re.compile(r'(^|\.)pclinuxos\.\w+$', re.I			),'_software/Linux/PCLinuxOS']
,	[re.compile(r'(^|\.)rosal(ab|inux)\.\w+$', re.I			),'_software/Linux/rosalab.ru']
,	[re.compile(r'(^|\.)slackware\.\w+$', re.I			),'_software/Linux/Slackware']
,	[re.compile(r'(^|\.)[\w-]*ubuntu[\w-]*\.\w+$', re.I		),'_software/Linux/Ubuntu']
,	[['wine-staging.com','winehq.org'				],'_software/Linux/Wine']
,	[['raidix.ru','raidixstorage.com'				],'_software/Linux//']
,	[
		[	'altlinux.org','archlinux.org','catap.ru','debian.net','debian.org','distrowatch.com','dotdeb.org','finnix.org','funtoo.org'
		,	'gentoo.org','gnu.org','installgentoo.com','kernel.org'
		,	'lanana.org','launchpad.net','linux.com','linux.org.ru','linuxfoundation.org','linuxtracker.org','lkml.org','lwn.net','lxde.org'
		,	'nongnu.org','partedmagic.com','pendrivelinux.com','redhat.com','sta.li','suckless.org','syslinux.org','tldp.org'
		]
	,	'_software/Linux/'
	]
,	[['ghtorrent.org','github.io','githubuniverse.com','githubusercontent.com'],'_software/github.com/']
,	[
		re.compile(r'(^|\.)github\.\w+$', re.I)
	,	'_software/github.com'
	,	{
			'sub': [
				[pat_subdomain_exc_www			, r'_subdomain/\3']
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
,	[['lavalys.com'							],'_software/aida64.com/']
,	[re.compile(r'(^|\.)edsd\.\w+$', re.I				),'_software/edsd.com']
,	[re.compile(r'(^|\.)ubi(soft)?\.\w+$', re.I			),'_software/ubisoft.com']
,	[['wine-staging.com','winehq.org'				],'_software/Wine']
,	[['old-dos.ru'							],'_software/microsoft.com/DOS/']
,	[
		[	'bing.com','classicshell.net','glass8.eu','live.com','microsoftstore.com','modern.ie','msdn.com','office.com'
		,	'sevenforums.com','sysinternals.com','technet.microsoft.com'
		,	'winaero.com','winbeta.org','windows.com','windowsphone.com','wsusoffline.net'
		]
	,	'_software/microsoft.com/'
	]
,	[['piriform.com','ccleaner.com'					],'_software//']
,	[['thehighload.com','ruhighload.com'				],'_software//']
,	[
		[	'3appes.com','adobe.com','advancemame.it','advsys.net','aida64.com','akeo.ie','alternativeto.net'
		,	'ansuz.sooke.bc.ca','antipope.org','assembla.com','atlassian.com'
		,	'baremetalsoft.com','bitbucket.org','bytehunter.net'
		,	'c3.cx','chainer.org','chikuyonok.ru','chocolatey.org','classicreload.com','codeplex.com','cr.yp.to','cyberforum.ru'
		,	'deskchan.info','destroyallsoftware.com','docker.com','entropymine.com','evolt.org','eyeleo.com'
		,	'fosshub.com','freedos.org','fsf.org'
		,	'geekly.info','ghacks.net','gitgud.io','gitlab.com','gitlab.io','gitorious.org','gmane.org','grompe.org.ru'
		,	'h-online.com','haali.su','hkcmdr.anymania.com','howtogeek.com','humblebundle.com'
		,	'iwrconsultancy.co.uk','java.com','jonof.id.au','kde.org','kha.tech','libraries.io','linkdata.se','lo4d.com'
		,	'maintainerati.org','manictime.com','mantishub.io','microsoft.com','mitre.org','monkrus.ws','mysku.ru'
		,	'nakka.com','ninite.com','nxlog.co'
		,	'openai.com','openhub.net','opennet.ru','opensource.org','openwall.com','oracle.com','oszone.net','outsidethebox.ms'
		,	'parallels.com','partitionwizard.com','perkele.cc','pooi.moe','portableapps.com','psydk.org'
		,	'raxco.com','reactos.org','readthedocs.io'
		,	'saltstack.com','sanographix.net','sapib.ca','smithmicro.com','softonic.com','softoxi.com','softwareishard.com','superliminal.com'
		,	'techdows.com','ultimateoutsider.com','veg.by','videolan.org','virtualbox.org','virtuallyfun.com','vitanuova.com','voidtools.com'
		,	'wj32.org','wonderunit.com','wzor.net','xakep.ru'
		]
	,	'_software/'
	]

#--[ books + pasta ]-----------------------------------------------------------

,	[
		re.compile(r'(^|\.)(titanpad\.com|piratepad\.net)$', re.I)
	,	''
	,	{
			'sub': [
				[re.compile(r'''^
(\w+:/+)?
([^/?#]+\.)*
([^/?#]+\.\w+)/
(\w+/)*
(
# titanpad.com:
	ID1
|	ID2
|	ID3
# piratepad.net:
|	ID4
|	ID5
)
([/?#.]|$)''', re.X), r'_text/_online_pad/_separated_example']
			,	[re.compile(r'^(\w+:/+)?([^/?#]+\.)*([^/?#]+\.\w+)/', re.I), r'_text/_online_pad/\3']
			]
		}
	]
,	[re.compile(r'(^|\.)flibusta\.\w+$', re.I		),'_text/flibusta.is']
,	[['anatolyburov.ru','artgorbunov.ru','maximilyahov.ru'	],'_text/glvrd.ru/']
,	[
		[	'etherpad.fr','etherpad.org','note-pad.net','piratenpad.de','piratepad.net','sync.in','titanpad.com'
		]
	,	'_text/_online_pad/'
	]
,	[
		[	'anonkun.com','codepad.org','copypast.ru','evernote.com','freetexthost.com'
		,	'hastebin.com','hpaste.org','ivpaste.com','kopipasta.ru','lpaste.net'
		,	'paste.ee','paste.org.ru','paste.sh','paste2.org'
		,	'pastebin.ca','pastebin.com','pastebin.ru'
		,	'pasted.co','pastehtml.com','pastie.org'
		,	'slideshare.net','textsave.org','txtdump.com'
		]
	,	'_text/_pasta/'
	]
,	[re.compile(r'(^|\.)(read|write)thedocs\.\w+$', re.I	),'_text/readthedocs.org']
,	[
		[	'aho-updates.com','aldebaran.ru','alfalib.com','armaell-library.net','author.today'
		,	'baka-tsuki.org','bards.ru','bookz.ru','botnik.org'
		,	'e-reading.club','fabulae.ru','fantlab.ru','ficbook.net','gatter.ru','glvrd.ru','goodreads.com','koob.ru'
		,	'labirint.ru','leanpub.com','lib.ru','lib.rus.ec','librebook.ru','litmir.co','livelib.ru','maxima-library.org','multivax.com'
		,	'novelupdates.com','obd-memorial.ru','porrygatter.zx6.ru','pritchi.ru','proza.ru','royallib.com','rus-bd.com','russianplanet.ru'
		,	's-marshak.ru','sacred-texts.com','samlib.ru','smallweb.ru','springhole.net','srkn.ru','stihi.ru','smartfiction.ru'
		,	'text.ru','yourworldoftext.com'
		]
	,	'_text/'
	]

#--[ more stuff ]--------------------------------------------------------------

,	[
		[	'1337x.to','acgnx.se','anicache.com','animetosho.org'
		,	'booktracker.org','btdigg.org','btmon.com','btstorr.cc','cgpersia.com','gundam.eu'
		,	'iknowwhatyoudownload.com','mega-tor.org','ohys.net','oppaiti.me'
		,	'pornolab.net','pornolabs.org','rutracker.org','shanaproject.com'
		,	'torrentfreak.com','touki.ru','tparser.org','tvu.org.ru','unionpeer.org'
		]
	,	'_torrents/'
	]
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
,	[re.compile(r'(^|\.)cgpeers\.\w+$', re.I		),'_torrents/cgpersia.com/_tracker']
,	[['dostup-rutracker.org','rutracker.news','rutracker.wiki','torrents.ru'],'_torrents/rutracker.org/']
,	[['rutor.org','freedom-tor.org'				],'_torrents//']
,	[['kickass.to','kat.cr'					],'_torrents//']

,	[['coub.com'			],'_video/coub.com/_mht']
,	[['youtube.com'			],'_video/youtube.com/_mht']
,	[['ggpht.com'			],'_video/youtube.com']
,	[
		[	'beam.pro','bilibili.com','cbc.ca','cybergame.tv','dailymotion.com','dsgstng.com'
		,	'goodgame.ru','hentaihaven.org','hitbox.tv','hooli.xyz'
		,	'iwara.tv','ivideon.com','kiwi.kz','liveleak.com','liveninegag.com','livestream.com','manyvids.com','ororo.tv'
		,	'picarto.tv','polsy.org.uk','pornhub.com','smashcast.tv','synchtube.ru'
		,	'tenor.com','twitch.tv','vid.me','video.eientei.org','vimeo.com','vine.co'
		,	'webkams.com','webm.host','webm.red','webmshare.com','webmup.com'
		,	'xvideos.com','youdubber.com','youku.com','ytmnd.com','z0r.de','zanorg.net','zenrus.ru'
		]
	,	'_video/'
	]

#--[ hosting ]-----------------------------------------------------------------

,	[['duiadns.net','duia.in'		],'_web/_DNS,Domains//']
,	[['dyn.com','dyndns.com'		],'_web/_DNS,Domains//']
,	[re.compile(r'(^|\.)dot\.\w+$', re.I	),'_web/_DNS,Domains/']
,	[re.compile(r'(^|\.)easydns\.\w+$', re.I),'_web/_DNS,Domains/easydns.com']
,	[re.compile(r'(^|\.)no-?ip\.\w+$', re.I	),'_web/_DNS,Domains/no-ip.com']
,	[
		[	'afraid.org','bind9.net','buydomains.com'
		,	'ddns.net','dnsleaktest.com','dnsmadeeasy.com','domaindiscount24.com','domainnamesales.com','domaintools.com'
		,	'dtdns.com','duckdns.org','dynadot.com'
		,	'eurodns.com','freenom.com','godaddy.com','hugedomains.com','iana.org','icann.org','icannwiki.com','internic.net'
		,	'name.com','namecheap.com','namegrep.com','nameitman.com','nastroisam.ru','nic.ru'
		,	'onlydomains.com','opendns.com','pairdomains.com','pho.to','publicsuffix.org'
		,	'reg.ru','respectourprivacy.com','rrpproxy.net','ru-tld.ru','safedns.com','urlvoid.com','whatsmydns.net','ydns.eu'
		]
	,	'_web/_DNS,Domains/'
	]
,	[
		[	'badssl.com','certbot.eff.org','certificatedetails.com','certificatemonitor.org'
		,	'freessl.com','gethttpsforfree.com','httpvshttps.com','instantssl.com','letsencrypt.org'
		,	'raymii.org','revocationcheck.com','ssldecoder.org','ssllabs.com','startssl.com'
		]
	,	'_web/_HTTPS/'
	]
,	[['geti2p.net','i2pd.website'		],'_web/_i2p/']
,	[
		[	'2ip.ru','anti-hacker-alliance.com','cymon.io','db-ip.com','dronebl.org','dslreports.com'
		,	'find-ip-address.org','geoiplookup.net','hostingcompass.com','iblocklist.com','ifconfig.me'
		,	'ip.cn','ip-address.cc','ip-analyse.com','ip-tracker.org','ip2location.com','ipaddress-finder.com','ipaddresse.com'
		,	'ipindetail.com','ipinfo.io','ipligence.com','iplocationtools.com'
		,	'myip.ms','myip.ru','ntunhs.net','pdrlabs.net','ripe.net','robtex.com'
		,	'servisator.ru','showmyip.com','spamhaus.org','spys.ru','tcpiputils.com','tracemyip.org'
		,	'whatismyip.com','whatismyipaddress.com','who.is','whoer.net','yoip.ru'
		]
	,	'_web/_ip/'
	]
,	[['1v.to','adf.ly','bitly.com','flark.it','hitagi.ru','href.li','ll.la','welcome.to','v.gd'],'_web/_link/']
,	[['bmetrack.com','list-manage.com'				],'_web/_mail/']
,	[['antizapret.info','prostovpn.org'				],'_web/_proxy//']
,	[re.compile(r'(^|\.)angryfox\.\w+$', re.I			),'_web/_proxy/angryfox.org']
,	[
		[	'6a.nl','browse.ninja','dostup.website','findproxy.org','fri-gate.org','mf6.ru'
		,	'phantompeer.com','pickaproxy.com','privoxy.org','torrentprivacy.com'
		]
	,	'_web/_proxy/'
	]
,	[['openlinkprofiler.org'					],'_web/_site/_dev/_SEO,spam,bots/seoprofiler.com/']
,	[
		[	'ahrefs.com','commoncrawl.org','deusu.de','exensa.com','extlinks.com'
		,	'law.di.unimi.it','moz.com','projecthoneypot.org','quicksprout.com'
		,	'screamingfrog.co.uk','searchengines.guru','seoprofiler.com','turnitin.com','yoast.com'
		]
	,	'_web/_site/_dev/_SEO,spam,bots/'
	]
,	[re.compile(r'(^|\.)htmlhelp\.\w+$', re.I			),'_web/_site/_dev/htmlhelp.com']
,	[
		[	'acidtests.org','caniuse.com','cloudinary.com','denwer.ru','disqus.com','dklab.ru','gohugo.io'
		,	'html5.org','html5blank.com','html5rocks.com','htmlbook.ru','hypercomments.com','jasnapaka.com','kg-design.ru'
		,	'larsjung.de','law.di.unimi.it','line25.com','linickx.com'
		,	'masv.io','microformats.org','modernizr.com','motherfuckingwebsite.com','quirksmode.org','rinigroup.ru','robotstxt.org'
		,	'simplemachines.org','sitemaps.org','sitepoint.com','tafttest.com','timkadlec.com','usefulscript.ru'
		,	'w3.org','w3fools.com','w3schools.com','webdeveloper.com','whatwg.org','wicg.io','wordpress.org','yusukekamiyamane.com'
		]
	,	'_web/_site/_dev/'
	]
,	[
		[	'doj.me','downdetector.com','downforeveryoneorjustme.com','isitblockedinrussia.com','isitdownrightnow.com','isup.me'
		]
	,	'_web/_site/_is_it_up_or_down/'
	]
,	[['vm.','vm'						],'_web/_site/_vps/vm']
,	[['v.','me.','server.','webmin.'			],'_web/_site/_vps/webmin']
,	[
		['u.']
	,	'_web/_site/_vps/'
	,	{
			'sub': [
				[re.compile(r'^[\w-]+:/+[^:/?#]+(:[^:/?#]+)?/+[?]*([\w-]+):*/', re.I), r'\2']
			]
		}
	]
,	[re.compile(r'(^|\.)byethost\d*\.com$', re.I				),'_web/_site/byet.net']
,	[['byet.net','byet.org','byet.host','ifastnet.com','securesignup.net'	],'_web/_site//']
,	[['ua.hosting','ua-hosting.company'			],'_web/_site//']
,	[['bytemark.co.uk','bigv.io'				],'_web/_site//']
,	[['modx.com','modxcloud.com'				],'_web/_site//']
,	[['ogp.me','opengraphprotocol.org'			],'_web/_site//']
,	[['ovh.com','ovh.ie','ovh.net','ovhcloud.com'		],'_web/_site//']
,	[['peredovik-company.ru','promolik.ru'			],'_web/_site//']
,	[['webo.in','webogroup.com'		],'_web/_site//']
,	[['herokuapp.com'			],'_web/_site/heroku.com/']
,	[re.compile(r'(^|\.)hetzner\.\w+$', re.I),'_web/_site/hetzner.de']
,	[re.compile(r'(^|\.)ucoz\.\w+$', re.I	),'_web/_site/ucoz.ru']
,	[['pandora.nu'				],'_web/_site/',{'sub': ['xiin',['xiin']]}]
,	[
		[	'1gb.ru','123systems.net','2dayhost.com','alexa.com','alwaysdata.com','atwebpages.com'
		,	'beget.ru','bitballoon.com','bluehost.com','botje.com'
		,	'canarywatch.org','cloud4y.ru','cloudflare.com','controlstyle.ru','copyscape.com','crimeflare.com','csssr.ru'
		,	'debian.pro','dekel.ru','digitalocean.com','domaincrawler.com'
		,	'eurobyte.ru','fasthosts.co.uk','fastvps.ru','fullspace.ru','germanvps.com'
		,	'hc.ru','heroku.com','ho.ua'
		,	'host.ru','host-food.ru','host-tracker.com','hostduplex.com','hostgator.com'
		,	'hostia.ru','hostigger.com','hosting.ua','hosting90.eu','hostinger.ru','hostingvps.ro','hostink.ru'
		,	'ihc.ru','ihor.ru','iliad-datacenter.com','ispsystem.com','jino.ru'
		,	'king-servers.com','leapswitch.com','leaseweb.com','linode.com','litgenerator.ru'
		,	'mainhost.com.ua','marosnet.ru','mchost.ru','mclouds.ru','mediatemple.net','mycroftproject.com'
		,	'nazuka.net','neocities.org','networksolutions.com','ngz-server.de'
		,	'online.net','opensearch.org','openshift.com','pair.com','peterhost.ru','prohoster.info','prq.se'
		,	'ramnode.com','ready.to','rgh.ru','robtex.com','rt.ru','ruvds.com'
		,	'salesforce.com','sbup.com','scaleway.com','seven.hosting','sib-host.ru','siteground.com','sprinthost.ru','timeweb.com','txti.es'
		,	'uptime.com','vps.house','vps.me','vps.today','vpsnodes.com','vultr.com'
		,	'webguard.pro','webhostingsearch.com','webhostingtalk.com','websitetoolbox.com','wix.com'
		]
	,	'_web/_site/'
	]
,	[re.compile(r'(^|\.)akamai(hd)?\.\w+$', re.I		),'_web/akamai.com']
,	[re.compile(r'(^|\.)www\.\w+$', re.I			),'_web/www']
,	[
		[	'1-9-9-4.ru','battleforthenet.com','eff.org','evolutionoftheweb.com','famfamfam.com','filippo.io','mywot.com'
		,	'rublacklist.net','spam-chaos.com','speedtest.net','troyhunt.com','uptolike.ru'
		]
	,	'_web/'
	]

#--[ wiki ]--------------------------------------------------------------------

,	[['boltwire.com','dokuwiki.org','foswiki.org','ikiwiki.info','pmwiki.org','trac.edgewall.org','wikimatrix.org'],'_wiki/_soft/']
,	[re.compile(r'(^|\.)encyclopediadramatica\.\w+$', re.I	),'_wiki/encyclopediadramatica.com']
,	[['mrakopedia.ru','mrakopedia.org','barelybreathing.ru'	],'_wiki//']
,	[['traditio.ru','traditio-ru.org'			],'_wiki//']
,	[['wikia.nocookie.net'					],'_wiki/wikia.com/_img']
,	[['wikia.com','wikipedia.org'				],'_wiki/',{'sub': [[pat_subdomain_exc_www, r'_subdomain/\1']]}]
,	[
		[	'mediawiki.org','wikimedia.org','wikitravel.org','wikimediafoundation.org','wiktionary.org','wikiquote.org'
		]
	,	'_wiki/wikipedia.org/'
	]
,	[
		[	'boobpedia.com','c2.com','cirnopedia.info','cyclowiki.org','deskthority.net','dokuwiki.org','dramatica.org.ua'
		,	'emoji.wiki','emojipedia.org','eswiki.ru'
		,	'genworld.info','gfwiki.com','koumakan.jp','lukomore.org','lurkmore.com','posmotre.li'
		,	'scp-wiki.net','scpfoundation.ru','shoutwiki.com'
		,	'tlwiki.org','touhouwiki.net','tvtropes.org','ufopaedia.org'
		,	'wikimultia.org','wikinews.org','wikireality.ru','wiktenauer.com','zeldawiki.org'
		]
	,	'_wiki/'
	]
,	[re.compile(r'(^|\.)lurkmo(re|ar|)\.\w+(:\d+)?$', re.I	),'_wiki/lurkmore.ru']

#--[ unsorted, etc ]-----------------------------------------------------------

,	[['icloud.com'						],'apple.com/']
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
		[	'googleapis.com','googleblog.com','googlelabs.com','googlesyndication.com','googleusercontent.com','withgoogle.com'
		]
	,	'google.com/'
	]
,	[['lmgtfy.com','google.gik-team.com','g.zeos.in','justfuckinggoogleit.com'],'google.com//']
,	[['code.google.com','googlecode.com'			],'google.com//']
,	[['drive.google.com','googledrive.com'			],'google.com//']
,	[['picasa.google.com','picasaweb.google.com'		],'google.com//']
,	[['accounts.google.com','profiles.google.com'		],'google.com/_accounts']
,	[['chrome.com','chromium.org','my-chrome.ru'		],'google.com/_chrome/']
,	[re.compile(r'(^|\.)gmail\.\w+$', re.I			),'google.com/_mail']
,	[re.compile(r'(^|\.)9oogle\.\w+$', re.I			),'google.com/9oogle.net']
,	[
		re.compile(r'(^|\.)google(\.com?)?(\.\w+)?$', re.I)
	,	'google.com'
	,	{
			'sub': [
				['_accounts'	,['accounts','profiles','settings']]
			,	['_books'	,['books']]
			,	['_chrome'	,['chrome']]
			,	['_img'		,['images','imgres','imghp']]
			,	['_logos'	,['doodle4google','doodles','logos']]
			,	['_mail'	,['mail','gmail']]
			,	['_maps'	,['maps']]
			,	['_q&a'		,['answers','otvety']]
			,	['_reader'	,['reader']]
			,	['_registry'	,['registry']]
			,	['_search/images',re.compile(r'(^/*|search)\?([^&]*&)*?tbm=im?a?g?e?s+e?a?r?ch'	, re.I), pat_tail_google, r'\1 Images\3']
			,	['_search/news'  ,re.compile(r'(^/*|search)\?([^&]*&)*?tbm=ne?ws'		, re.I), pat_tail_google, r'\1 News\3']
			,	['_search/video' ,re.compile(r'(^/*|search)\?([^&]*&)*?tbm=vid'			, re.I), pat_tail_google, r'\1 Video\3']
			,	['_search'       ,re.compile(r'(^/*|search)\?([^&]*&)*?q='			, re.I)]
			,	['_search'	,['search']]
			,	['_support'	,['support']]
			,	['_trends'	,['trends']]
			,	['_webmasters'	,['webmasters']]
			,	['_webstore'	,['webstore']]
			,	[pat_subdomain_exc_www, r'_subdomain/\1']
			]
		}
	]
,	[re.compile(r'(^|\.)greenpeace\.\w+$', re.I		),'greenpeace.org']
,	[re.compile(r'(^|\.)ixbt\.\w+$', re.I			),'ixbt.com']
,	[
		['world-art.ru']
	,	'//'
	,	{
			'sub': [
				['_animation'	,['animation','animation.php']]
			,	['_company'	,['company','company.php']]
			,	['_people'	,['people','people.php']]
			]
		}
	]
,	[['ya.ru'						],'yandex.ru/']
,	[
		re.compile(r'(^|\.)yandex(\.\w+)?$', re.I)
	,	'yandex.ru'
	,	{
			'sub': [
				['_blog'	,['blog']]
			,	['_company'	,['company']]
			,	['_images'	,['images']]
			,	['_legal'	,['legal']]
			,	['_maps'	,['maps']]
			,	['_search'	,['blogs','search','yandsearch']]
			,	['_soft'	,['soft']]
			,	['_support'	,['support']]
			,	[pat_subdomain_exc_www, r'_subdomain/\3']
			]
		}
	]
,	[re.compile(r'(^|\.)yahoo(\.com?)?\.\w+$', re.I		),'yahoo.com']
,	[['shoelace-knots.com','fieggen.com','professor-shoelace.com','shoe-lacing.com','shoelace-knot.com','shoelace.guru'],'//']
,	[['4my.eu'						],'/',{'sub': [[pat_subdomain_exc_www, r'_subdomain/\1']]}]
,	[
		[	'3dnews.ru','360cities.net','about.com','adme.ru','apparat.cc','apple.com','appspot.com','artlebedev.ru','ask.fm'
		,	'baidu.com','beeline.ru','bnw.im'
		,	'championat.com','computerra.ru','ctrlpaint.com','dahr.ru','disconnect.me','duckduckgo.com'
		,	'elkews.com','empower-yourself-with-color-psychology.com','everypony.ru'
		,	'ftn.su','gearbest.com','getit01.com','hi-news.ru'
		,	'idlewords.com','ietf.org','imdb.com','inspirobot.me','it-actual.ru','it-uroki.ru'
		,	'kinopoisk.ru','lenta.ru','lifehacker.com'
		,	'makeuseof.com','membrana.ru','naked-science.ru','oko.im','poly-graph.co','rambler.ru','reformal.ru','riamo.ru'
		,	'sibset.ru','space.com','sputnik.ru','statcounter.com','tutu.ru','tvoya-rossiya.ru'
		,	'un.org','wikihow.com','wired.com','worldometers.info','xenomorph.ru'
		]
	]

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
						dsub = (
							re
							.search(r[0], met)
							.expand(r[1])
						)
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
