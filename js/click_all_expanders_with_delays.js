
(function() {
	var linksTotalCount = 0;
	var linkTexts = [
		'See more',
		'Показать полностью',
		'еще комментари',
		'ещё комментари',
		'раскрыть ветку',
	];

	function getClickCallback(e,i) { return (function() {
		if (e) {
			console.log(
				i
			+	' / '
			+	linksTotalCount
			+	' - '
			+	e.textContent
				.replace(/^\s+|\s+$/g, '')
				.replace(/\s+/g, ' ')
			);

			e.click();
		}
	}); }

	for (var className of arguments) {
		var linksOfClassCount = 0;
		var linkTextContent;

		forEachLinkElement:
		for (var linkElement of document.getElementsByClassName(className)) {

			var testElement = linkElement;

			while (testElement) if (
				testElement.hidden
			||	(testElement.style && testElement.style.display == 'none')
			) {
				continue forEachLinkElement;
			} else {
				testElement = testElement.parentNode;
			}

			if (linkTextContent = linkElement.textContent) {
				for (var linkText of linkTexts)
				if (linkTextContent.indexOf(linkText) >= 0) {
					++linksOfClassCount;
					++linksTotalCount;

					setTimeout(
						getClickCallback(linkElement, linksTotalCount),
						linksTotalCount * 500 + Math.random() * 200
					);

					break;
				}
			}
		}

		if (linksOfClassCount > 0) console.log(linksOfClassCount+' '+className);
	}

	console.log('total '+linksTotalCount);
})(
	'comment-toggle-children_collapse',
	'comment-hidden-group__toggle',
	'story__read-more-label',
	'shesht-comments-block-form-readmore',
	'toggle-comment',
	'wall_post_more',
	'wall_reply_more'
);
