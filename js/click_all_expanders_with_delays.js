
/*
	Usage:
Copypaste this script into web-browser console,
It will expand all visible collapsed branches of comment tree, one by one with delays to allow loading.
If needed, repeat by pressing [Up] in the console and then [Enter] key again, until the total shows "0".

Target CSS classes and text content parts are written for specific sites.
Change these lists as needed for other sites.
*/

(function() {

	var targetCssClasses = [
		'comment-toggle-children_collapse',	//* pikabu.ru
		'comment-hidden-group__toggle',		//* pikabu.ru
		'community-info-block__read-more-label',//* pikabu.ru
		'story__read-more-label',		//* pikabu.ru
		'shesht-comments-block-form-readmore',	//* naked-science.ru
		'toggle-comment',			//* naked-science.ru
		'ytd-continuation-item-renderer',	//* youtube.com/watch
		'more-button',				//* youtube.com/watch
		'comment__load-more',	//* dtf.ru
		'button',		//* reddit
		'expand',		//* reddit
		'wall_post_more',	//* vk.com
		'wall_reply_more',	//* vk.com
		'mw-collapsible-text',	//* wiktionary.org
	];

	var targetTextParts = [
		/\d+\s+repl(y|ies)/i,	//* youtube.com/watch
		'Read more',		//* youtube.com/watch
		'show more replies',	//* youtube.com/watch
		'see more',		//* vk.com
		'load more comment',	//* reddit
		'[+]',			//* reddit
		'показать',		//* ru.wiktionary.org, pikabu.ru
		'раскрыть ветку',	//* pikabu.ru
		'комментари',		//* dtf.ru, pikabu.ru, naked-science.ru
	];

	function openAllVisibleExpanders() {
		var linksTotalCount = 0;

		function getClickCallback(e,i) { return (function() {
			if (e) {
				console.log(
					i
				+	' / '
				+	linksTotalCount
				+	' = '
				+	e.textContent
					.replace(/^\s+|\s+$/g, '')
					.replace(/\s+/g, ' ')
				);

				e.click();
			}

			if (i === linksTotalCount) {
				console.log('Retrying...');

				setTimeout(openAllVisibleExpanders, 1234);
			}
		}); }

		for (var className of targetCssClasses) {
			var linksOfClassCount = 0;

			forEachLinkElement:
			for (var linkElement of document.getElementsByClassName(className)) {

				var style, testElement = linkElement;

				while (testElement) if (
					testElement.hidden
				||	(
						(style = testElement.style)
					&&	(
							style.opacity === 0
						||	style.display === 'none'
						||	style.visibility === 'hidden'
						)
					)
				) {
					continue forEachLinkElement;
				} else {
					testElement = testElement.parentNode;
				}

				if (linkTextContent = linkElement.textContent) {
					var linkTextLowerCase = linkTextContent.toLowerCase();

					for (var linkText of targetTextParts)
					if (
						typeof linkText === 'string'
						? (
							linkTextContent.includes(linkText)
						||	linkTextLowerCase.includes(linkText)
						)
						: linkText.test(linkTextContent)
					) {
						++linksOfClassCount;
						++linksTotalCount;

						setTimeout(
							getClickCallback(linkElement, linksTotalCount),
							linksTotalCount * 300 + Math.random() * 200
						);

						break;
					}
				}
			}

			if (linksOfClassCount > 0) console.log(
				'Found '
			+	linksOfClassCount
			+	' targets of class "'
			+	className
			+	'" '
			);
		}

		console.log(
			'Total visible targets: '
		+	linksTotalCount
		);
	}

	openAllVisibleExpanders();
})();
