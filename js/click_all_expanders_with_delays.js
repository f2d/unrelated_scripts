
/*
	Usage:
Copypaste this script into web-browser console,
It will expand all visible collapsed branches of comment tree, one by one with delays to allow loading.
If needed, repeat by pressing [Up] in the console and then [Enter] key again, until the total shows "0".

Target CSS classes and text content parts are written for specific sites.
Change these lists as needed for other sites.

Enter the following line to stop it:
	window.stopOpeningExpanders = 1;
*/

(function () {

	var targetTextParts = [
		/\d+\s+repl(y|ies)/i,	//* youtube.com/watch
		'read more',		//* youtube.com/watch
		'more replies',		//* youtube.com/watch, fandom.com
		'show more',		//* vk.com
		'see more',		//* vk.com
		'load more comment',	//* reddit, fandom.com
		'[+]',			//* reddit
		'loading...',		//* reddit
		'note',			//* tvtropes.org
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
		'expand',		//* reddit
		'button',		//* reddit
		'PostTextMore',		//* vk.com
		'wall_post_more',	//* vk.com
		'wall_reply_more',	//* vk.com
		'mw-collapsible-text',	//* wiktionary.org
		'NavToggle',		//* wiktionary.org
		'HQToggle',		//* wiktionary.org
		'notelabel',		//* tvtropes.org
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
		'load-more-button',			//* fandom.com
		/LoadMoreButton_load-more__\S/i,	//* fandom.com
		/ReplyList_view-all-replies__\S/i,	//* fandom.com
		/styles_lia-g-loader-btn__\S/i,
	];

	var skipCssClasses = ['unfolded'];
	var unskipTextParts = ['load more comments','loading...'];
	var clickableTagNames = ['a', 'button'];
	var doneElements = [];

	function openAllVisibleExpanders() {
		var pendingTotalCount = 0;
		var pendingIndex = 0;
		var pendingElements = [];

		function checkPendingElement(e) {
			if (window.stopOpeningExpanders) {
				console.log('Stopped.');
			} else {
				if (e = pendingElements[pendingIndex++]) {
					console.log(
						pendingIndex
					+	' / '
					+	pendingTotalCount
					+	' = '
					+	e.textContent
						.replace(/^\s+|\s+$/g, '')
						.replace(/\s+/g, ' ')
					);

					(getClickableChild(e) || e).click();

					setTimeout(checkPendingElement, (Math.ceil(pendingIndex / 50) + Math.random()) * 900);
				} else {
					console.log('Retrying...');

					setTimeout(openAllVisibleExpanders, 1234);
				}
			}
		}

		function getClickableChild(e, a) {
			for (var eachTagName of clickableTagNames) {
				if (e.tagName.toLowerCase() === eachTagName) return e;
				if (a = e.getElementsByTagName(eachTagName)[0]) return a;
			}
		}

		function isTextMatch(matchRules, text, textLowerCase) {
			for (var eachRule of matchRules)
			if (
				eachRule.test
				? eachRule.test(text)
				: (
					text.includes(eachRule)
				||	textLowerCase.includes(eachRule)
				)
			) return true;
		}

		function checkLinkElement(eachLinkElement) {
			for (var eachSkipName of skipCssClasses)
			if (
				eachSkipName.test
				? eachSkipName.test(eachLinkElement.className)
				: eachLinkElement.classList.contains(eachSkipName)
			) return;

			var style, testElement = eachLinkElement;

			while (testElement) {
				if (
					testElement.hidden
				||	doneElements.includes(testElement)
				||	(
						(style = testElement.style)
					&&	(
							style.opacity === 0
						||	style.display === 'none'
						||	style.visibility === 'hidden'
						)
					)
				) return;

				testElement = testElement.parentNode;
			}

			if (linkTextContent = eachLinkElement.textContent) {
				var linkTextLowerCase = linkTextContent.toLowerCase();

				if (isTextMatch(targetTextParts, linkTextContent, linkTextLowerCase)) {
					++pendingClassCount;
					++pendingTotalCount;

					pendingElements.push(eachLinkElement);

					if (!isTextMatch(unskipTextParts, linkTextContent, linkTextLowerCase)) {
						doneElements.push(eachLinkElement);
					}
				}
			}
		}

		for (var eachCssClass of targetCssClasses) {
			var pendingClassCount = 0;

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

			if (pendingClassCount > 0) console.log(
				'Found '
			+	pendingClassCount
			+	' targets of class "'
			+	eachCssClass
			+	'" '
			);
		}

		console.log(
			'Total visible targets: '
		+	pendingTotalCount
		);

		if (!window.stopOpeningExpanders) {
			if (pendingTotalCount) {
				setTimeout(checkPendingElement, 1234);
			} else {
				setTimeout(openAllVisibleExpanders, 12345);
			}
		}
	}

	openAllVisibleExpanders();
})(window.stopOpeningExpanders = 0)
