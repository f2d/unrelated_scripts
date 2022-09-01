
/*
	Usage:
Copypaste this script into web-browser console, press [Enter] key.
It will save visible messages of currently open chat log into UTF-8 HTML file in your download folder on disk.
Saved file will not include linked images and CSS, only links.
The content is saved exactly as it was in HTML of the page in browser, only the part with messages.
Result is mainly usable for searching text history and for grabbing links.

	Sidebar HTML sample, 2022-04-07 21:00:52:
<nav class="container-1NXEtd" aria-label="example server name (server)">

	Chatlog HTML sample, 2022-04-07 20:16:30:
<main class="chatContent-3KubbW" aria-label="example channel name (channel)">
<div class="messagesWrapper-RpOMA3 group-spacing-16">
<div class="scroller-kQBbkU auto-2K3UW5 scrollerBase-_bVAAt disableScrollAnchor-6TwzvM managedReactiveScroller-1lEEh3" dir="ltr" data-jump-section="global" tabindex="-1" role="group">
<div class="scrollerContent-2SW0kQ content-2a4AW9">
<ol class="scrollerInner-2PPAp2" aria-label="Messages in example channel name" role="list" data-list-id="chat-messages" tabindex="0">
<span class="navigationDescription-3xDmE2" id="messagesNavigationDescription" aria-hidden="true">
Use the up and down arrow keys to navigate between messages quickly. New messages will be added to the bottom of the list as they come in.

	Private HTML sample, 2022-04-07 21:39:07:
<section class="title-31SJ6t container-ZMc96U themed-Hp1KC_" aria-label="Channel header">
<div class="children-3xh0VB"><div class="iconWrapper-2awDjA">...</div>
<span class="hiddenVisually-2ydA7k">Direct Message</span>
<h3 role="button" class="cursorPointer-3JF56F title-17SveM base-21yXnu size16-rrJ6ag">example user name</h3>
<div aria-label="Online" class="status-12NUUC disableFlex-3I_kDH">

*/

(function() {

const	textCharSet = 'charset=utf-8';
const	textTime = getTimeStamp();

function getTimeStamp() {
const	d = new Date();
const	t = ['FullYear','Month','Date','Hours','Minutes','Seconds'];

	for (const i in t) if ((t[i] = d['get'+t[i]]()+(i == 1 ? 1 : 0)) < 10) {
		t[i] = '0'+t[i];
	}

	return t[0]+'-'+t[1]+'-'+t[2]+','+t[3]+'-'+t[4]+'-'+t[5];
}

function saveDL(data, type, filename) {

const	dataParts = (
		textCharSet.endsWith('utf-8')
		? [
			new Uint8Array([0xEF, 0xBB, 0xBF]),	//* UTF-8 BOM, https://stackoverflow.com/a/41363077
			new TextEncoder().encode(data)		//* UTF-8 text, https://stackoverflow.com/a/53932873
		]
		: [
			(
				textCharSet.endsWith('utf-16')
				? Uint16Array
				: Uint8Array
			).from(
				Array.prototype.map.call(
					data
				,	(v) => v.charCodeAt(0)
				)
			)
		]
	);

const	blob = new Blob(dataParts, { type });
const	size = blob.size;
const	url = URL.createObjectURL(blob);
const	a = document.createElement('a');
	a.href = url;
	a.download = filename = filename.trim().replace(regWhiteSpace, ' ').replace(regSanitizeFileName, '_');

	console.log({ textTime, filename, size, url, blob });

	a.click();

	setTimeout(function() {
		if (a.parentNode) a.parentNode.removeChild(a);
		if (blob) URL.revokeObjectURL(blob);
	}, 12345);
}

function getChannelId() {
	return location.pathname.split('/').filter(function(v) { return !!v; }).pop();
}

function getElementsByAnyTagName() {
let	elements;

	for (const tagName of arguments) if (
		(elements = document.getElementsByTagName(tagName))
	&&	elements.length > 0
	) {
		break;
	}

	return elements;
}

const	regSanitizeFileName = /[_\/\\:<>?*"]+/g;
const	regWhiteSpace = /\s+/g;

const	privateChannels = 'Private channels';
const	channelPrefix = 'Messages in ';
const	channelSuffix = '(channel)';
const	serverSuffix = '(server)';

const	unknownServerName = '(unknown server)';
const	unknownChannelName = '(unknown channel)';

let	serverName = '';
let	channelName = '';
let	channelNameClean = '';

for (const element of getElementsByAnyTagName('nav')) {
const	name = element.getAttribute('aria-label');

	if (name) {
		if (name === privateChannels) {
			serverName = '_private';
		} else
		if (name.endsWith(serverSuffix)) {
			serverName = name.slice(0, -serverSuffix.length);
		}

		console.log({ textTime, name, serverName });
	}
}

channel_name:
for (const element of getElementsByAnyTagName('section')) {
const	name = element.getAttribute('aria-label');

	if (name && name === 'Channel header') {
		for (const header of element.getElementsByTagName('h3')) {
			channelName = header.textContent;

			console.log({ textTime, name, channelName });

			break channel_name;
		}
	}
}

for (const element of getElementsByAnyTagName('ol', 'main')) {
const	name = element.getAttribute('aria-label');

	if (name && (
		name.endsWith(channelSuffix)
	||	element.getAttribute('data-list-id') === 'chat-messages'
	)) {
		if (name !== channelPrefix) {
			channelName = (
				name.startsWith(channelPrefix)
				? name.slice(channelPrefix.length)
				:
				name.endsWith(channelSuffix)
				? name.slice(0, -channelSuffix.length)
				: name
			);
			channelNameClean = channelName.replace(/\W+$/,'');
		}

		if (channelNameClean === 'art-adult') channelName = 'art-talk-nsfw';
		if (channelNameClean === 'art-lite') channelName = 'art-talk-sfw';

		console.log({ textTime, name, serverName, channelName });

		saveDL(
			element.outerHTML
		,	'text/html'
		,	(
				(serverName || unknownServerName).trim()
			+	'#'
			+	(channelName || getChannelId() || unknownChannelName).trim()
			+	';_'
			+	textTime
			+	','
			+	element.tagName
			+	'.outerHTML,'
			+	textCharSet
			+	'.htm'
			)
		);
	}
}

})();
