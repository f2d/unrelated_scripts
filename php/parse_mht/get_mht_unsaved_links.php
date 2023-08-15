<!doctype html>
<html>
<head>
	<meta charset="utf-8">
	<title>Get unsaved links from dzen.ru/yandex news MHT files with 7z and eDecoder</title>
</head>
<body>
	<pre>Running:</pre>
<?php

$archive_folder_path = 'D:\mht';
$program_arg = '"C:\Program Files\7-Zip\7z.exe"';

ini_set('max_execution_time', 9999);
ini_set('error_reporting', E_ALL);

define('TEST', false);

define('A_HREF_PAT', '~(?:^|\s)href="?([^"]+)~i');
define('A_TEXT_PAT', '~(?:^|>)([^<>]+)(?:$|<)~i');
define('P_HASH_LENGTH', 32);
define('P_HASH_PAT', '~--(\w{32})\b~i');
define('P_ID_PAT', '~[?&]persistent_id=([^&#]+)~i');
define('P_TIME_PAT', '~[?&]t=([^&#]+)~i');
define('RUBRIC_PAT', '~[?&]rubric=([^&#]+)~i');

$return_codes = array(
	0 => 'OK.'
,	1 => 'Warning: non fatal error(s), e.g. files locked by other application.'
,	2 => 'Fatal error.'
,	7 => 'Command line error.'
,	8 => 'Not enough memory.'
,	255 => 'User stopped the process.'
);

$saved_page_hashes = array();
$saved_page_ids = array();
$saved_pages = array();
$linked_pages = array();

function get_substr_by_pat ($text, $pat, $target_length = 0) {
	return (
		$text
	&&	strlen($text)
	&&	preg_match($pat, $text, $match)
	&&	($target_length > 0 ? $target_length === strlen($match[1]) : true)
		? $match[1]
		: false
	);
}

function get_link_text   ($text) { return get_substr_by_pat ($text, A_TEXT_PAT); }
function get_link_url    ($text) { return get_substr_by_pat ($text, A_HREF_PAT); }
function get_page_hash   ($text) { return get_substr_by_pat ($text, P_HASH_PAT, P_HASH_LENGTH); }
function get_page_id     ($text) { return get_substr_by_pat ($text,   P_ID_PAT); }
function get_page_time   ($text) { return get_substr_by_pat ($text, P_TIME_PAT); }
function get_page_rubric ($text) { return get_substr_by_pat ($text, RUBRIC_PAT); }

function get_a_parts ($text) {
	return (
		($page_url = get_link_url($text))
	&&	($page_hash = get_page_hash($page_url))
	&&	($page_title = trim(get_link_text($text)))
		? array(
			'id' => get_page_id($page_url) ?: 'no id'
		,	'url' => $page_url
		,	'hash' => $page_hash
		,	'time' => (intval($t = get_page_time($page_url)) ? date(DATE_ATOM, $t) : 'no time')
		,	'title' => $page_title
		,	'rubric' => get_page_rubric($page_url) ?: 'no rubric'
		) : false
	);
}

function add_saved_page ($page_url) {
	global $saved_page_hashes, $saved_page_ids;

	if (($page_hash = get_page_hash($page_url)) && !in_array($page_hash, $saved_page_hashes)) array_push($saved_page_hashes, $page_hash);
	if (($page_id   = get_page_id  ($page_url)) && !in_array($page_id,   $saved_page_ids))    array_push($saved_page_ids,    $page_id);

	return $page_hash;
}

function add_linked_page ($text) {
	global $saved_page_hashes, $saved_page_ids, $saved_pages, $linked_pages;

	if ($page_entry = get_a_parts(html_entity_decode($text))) {

		$page_id = $page_entry['id'];
		$page_hash = $page_entry['hash'];
		$page_title = $page_entry['title'];

		if (
			in_array($page_hash, $saved_page_hashes)
		||	in_array($page_id, $saved_page_ids)
		) {
			$pages = &$saved_pages;
		} else {
			$pages = &$linked_pages;
		}

		$page_key = $page_id ?: $page_hash;

		if (!array_key_exists($page_key, $pages)) {
			$pages[$page_key] = array();
		}

		foreach ($pages[$page_key] as $found_entry) if ($page_title === $found_entry['title']) {
			return false;
		}

		array_push($pages[$page_key], $page_entry);
	}

	return $page_entry;
}

function is_page_filename ($text) {
	return !!get_page_hash($text);
}

function is_relevant_url ($text) {
	return is_page_filename ($text) && (
		false !== strpos($text, '/instory/')
	||	false !== strpos($text, '/story/')
	);
}

function get_to_print ($var) { return print_r($var, true); }
function print_block ($var) {
	echo '
	<pre>'.htmlspecialchars(get_to_print($var)).'
	</pre>';
}

function run_test ($command_line, $filter_func_name = '', $map_func_name = '', $split_each_line_by = '') {
	global $return_codes;

	flush();

	$output_lines = array();
	$return_code = 0;
	$return_text = exec($command_line, $output_lines, $return_code);

	$return_code = "$return_code: ".(
		array_key_exists($return_code, $return_codes)
		? $return_codes[$return_code]
		: 'Unknown error.'
	);

	if (TEST) {
		if ($split_each_line_by) {
			if (is_array($output_lines)) {

//* https://stackoverflow.com/questions/526556/how-to-flatten-a-multi-dimensional-array-to-simple-one-in-php#comment98422873_14972714
//* array_merge(...): https://stackoverflow.com/a/53891086
//* Note: this can hit memory limit on large enough set of files (e.g. 100-1000 or more). Only do this for testing and debug.

				$output_lines = array_merge(
					...array_map(
						function  ($line) use ($split_each_line_by) {
							return explode($split_each_line_by, $line);
						}, $output_lines
					)
				);
			} else {
				$output_lines = explode($split_each_line_by, "$output_lines");
			}
		}

		if (is_array($output_lines)) {

			if ($filter_func_name) {
				$output_lines = array_filter($output_lines, $filter_func_name);
			}

			if ($map_func_name) {
				$output_lines = array_map($map_func_name, $output_lines);
			}

			$output_lines = array_filter($output_lines, 'trim');
			$output_lines = 'Array('.count($output_lines).")\n".implode("\n", array_map('get_to_print', $output_lines));
		}
	} else {

//* Note: to avoid memory limit, do only necessary things and move on.

		if ($split_each_line_by) {
			foreach ($output_lines as $text) {
				foreach (explode($split_each_line_by, $text) as $line) {
					if ($filter_func_name($line)) {
						$map_func_name($line);
					}
				}
			}
		} else {
			foreach ($output_lines as $line) {
				if ($filter_func_name($line)) {
					$map_func_name($line);
				}
			}
		}

		$output_lines = 'Array('.count($output_lines).')';
	}

	print_block("
		command_line = $command_line

		return_code = $return_code

		output_lines = $output_lines");

	flush();
}

$archive_arg = '-an "-air!'.$archive_folder_path.'\*_*.mht"';
$content_arg = '"-ir!*--*"';

//* "-ba" prints truncated filenames:
// run_test("$program_arg l -ba $archive_arg $content_arg", 'is_page_filename');

//* "-slt" prints full "Content location" URL:
// run_test("$program_arg l -slt $archive_arg $content_arg", 'is_page_filename', 'get_page_id');
run_test("$program_arg l -slt $archive_arg $content_arg", 'is_page_filename', 'add_saved_page');

if (TEST) {
	print_block('Saved pages hashes:');
	print_block($saved_page_hashes);

	print_block('Saved pages IDs:');
	print_block($saved_page_ids);
}

//* "-so" prints full HTML page content:
// run_test("$program_arg x -so $archive_arg $content_arg", 'is_relevant_url', 'get_page_id', '"');
run_test("$program_arg x -so $archive_arg $content_arg news *.htm *.html ? ?? ???", 'is_relevant_url', 'add_linked_page', '<a ');

if (TEST) {
	print_block('Saved pages:');
	print_block($saved_pages);

	print_block('Linked pages:');
	print_block($linked_pages);
}

if ($linked_pages) {
	print_block('Unsaved linked pages:');

	$sorted_pages = array();

	foreach ($linked_pages as $page_key => $same_page_entries) {
		$p = $same_page_entries[0];
		$sorted_pages["$p[rubric] $p[title]"] = $page_key;
	}

	ksort($sorted_pages);

	foreach ($sorted_pages as $page_key) {
		echo "\n	<p>$page_key";

		foreach ($linked_pages[$page_key] as $page_entry) {
			echo "
		<br>$page_entry[rubric], $page_entry[hash], $page_entry[id], $page_entry[time] -
		<a href=\"$page_entry[url]\">$page_entry[title]</a>";
		}

		echo "\n	</p>";
	}
}

?>
</body>
</html>