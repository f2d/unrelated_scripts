
/*
	Usage:
Copypaste this script into web-browser console,
It will expand all visible collapsed branches of comment tree, one by one with delays to allow loading.
If needed, repeat by pressing [Up] in the console and then [Enter] key again, until the total shows "0".

Target CSS classes and text content parts are written for specific sites.
Change these lists as needed for other sites.

Enter the following line to stop it:
	window.stopOpeningExpanders = 0;
*/

(function () {

	var targetTextParts = [
		/\d+\s+repl(y|ies)/i,	//* youtube.com/watch
		'read more',		//* youtube.com/watch
		'more replies',		//* youtube.com/watch
		'show more',		//* vk.com
		'see more',		//* vk.com
		'load more comment',	//* reddit
		'[+]',			//* reddit
		'loading...',		//* reddit
		'показать',		//* pikabu.ru, ru.wiktionary.org
		'раскрыть ветку',	//* pikabu.ru
		'комментари',		//* pikabu.ru, dtf.ru, naked-science.ru
		/Ещё\s+\d+\s+комментари/i,	//* dzen.ru
		/Показать\s+\d+\s+ответ/i,	//* dzen.ru
		'ещё',				//* dzen.ru
		' ответ',			//* dzen.ru
		'▼',
		'[show replies]',
		'more>>',
		'spoiler',
		'expand',
	];

	var targetCssClasses = [
		'comment__more',
		'comment__load-more',	//* dtf.ru
		'button',		//* reddit
		'expand',		//* reddit
		'PostTextMore',		//* vk.com
		'wall_post_more',	//* vk.com
		'wall_reply_more',	//* vk.com
		'mw-collapsible-text',	//* wiktionary.org
		'NavToggle',		//* wiktionary.org
		'HQToggle',		//* wiktionary.org
		'comment-toggle-children_collapse',	//* pikabu.ru
		'comment-hidden-group__toggle',		//* pikabu.ru
		'community-info-block__read-more-label',//* pikabu.ru
		'story__read-more-label',		//* pikabu.ru
		'shesht-comments-block-form-readmore',	//* naked-science.ru
		'toggle-comment',			//* naked-science.ru
		'ytd-continuation-item-renderer',	//* youtube.com/watch
		'more-button',				//* youtube.com/watch
		'comment-more-button_child',			//* dzen.ru
		'comments2--more-comments-button__block-3P',	//* dzen.ru
		'comments2--root-comment__textBtn-1S',		//* dzen.ru
		'comments2--rich-text__expandWord-2_',		//* dzen.ru
		'showreplies',
		'ml-px',
		'morelink',
		'sp-head',
		/styles_lia-g-loader-btn__\S/i,
	];

	var skipCssClasses = ['unfolded'];
	var clickableTagNames = ['a', 'button'];
	var clickedElements = [];

	function openAllVisibleExpanders() {
		var linksTotalCount = 0;

		function getClickCallback(e, i) { return (function() {
			if (window.stopOpeningExpanders) {
				console.log(
					i
				+	' / '
				+	linksTotalCount
				+	' skipped'
				);
			} else if (e) {
				console.log(
					i
				+	' / '
				+	linksTotalCount
				+	' = '
				+	e.textContent
					.replace(/^\s+|\s+$/g, '')
					.replace(/\s+/g, ' ')
				);

				(getClickableChild(e) || e).click();
			}

			if (
				!window.stopOpeningExpanders
			&&	i === linksTotalCount
			) {
				console.log('Retrying...');

				setTimeout(openAllVisibleExpanders, 1234);
			}
		}); }

		function getClickableChild(e, a) {
			for (var eachTagName of clickableTagNames) {
				if (e.tagName.toLowerCase() === eachTagName) return e;
				if (a = e.getElementsByTagName(eachTagName)[0]) return a;
			}
		}

		function checkLinkElement(eachLinkElement) {
			for (var eachSkipName of skipCssClasses)
			if (
				eachSkipName.test
				? eachSkipName.test(eachLinkElement.className)
				: eachLinkElement.classList.contains(eachSkipName)
			) return;

			var style, testElement = eachLinkElement;

			while (testElement)
			if (
				testElement.hidden
			||	clickedElements.includes(testElement)
			||	(
					(style = testElement.style)
				&&	(
						style.opacity === 0
					||	style.display === 'none'
					||	style.visibility === 'hidden'
					)
				)
			) {
				return;
			} else {
				testElement = testElement.parentNode;
			}

			if (linkTextContent = eachLinkElement.textContent) {
				var linkTextLowerCase = linkTextContent.toLowerCase();

				for (var eachLinkText of targetTextParts)
				if (
					typeof eachLinkText === 'string'
					? (
						linkTextContent.includes(eachLinkText)
					||	linkTextLowerCase.includes(eachLinkText)
					)
					: eachLinkText.test(linkTextContent)
				) {
					++linksOfClassCount;
					++linksTotalCount;

					clickedElements.push(eachLinkElement);

					setTimeout(
						getClickCallback(eachLinkElement, linksTotalCount)
					,	linksTotalCount * 900 + Math.random() * 900
					);

					break;
				}
			}
		}

		for (var eachCssClass of targetCssClasses) {
			var linksOfClassCount = 0;

			if (eachCssClass.test) {
				for (var eachTagName of clickableTagNames)
				for (var eachLinkElement of document.getElementsByTagName(eachTagName))
				if (eachCssClass.test(eachLinkElement.className)) {
					checkLinkElement(eachLinkElement);
				}
			} else {
				for (var eachLinkElement of document.getElementsByClassName(eachCssClass)) {
					checkLinkElement(eachLinkElement);
				}
			}

			if (linksOfClassCount > 0) console.log(
				'Found '
			+	linksOfClassCount
			+	' targets of class "'
			+	eachCssClass
			+	'" '
			);
		}

		console.log(
			'Total visible targets: '
		+	linksTotalCount
		);

		if (!window.stopOpeningExpanders && !linksTotalCount) {
			setTimeout(openAllVisibleExpanders, 12345);
			clickedElements = [];
		}
	}

	openAllVisibleExpanders();
})(window.stopOpeningExpanders = 0)
