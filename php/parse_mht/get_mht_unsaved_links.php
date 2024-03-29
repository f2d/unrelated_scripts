<!doctype html>
<html>
<head>
	<meta charset="utf-8">
	<title>Get unsaved links from dzen.ru/yandex news MHT files with 7z and eDecoder</title>
	<style>
		details p { margin: 2em 0; }
		details summary { cursor: pointer; }
	</style>
</head>
<body>
	<pre>Running:</pre>
<?php

ini_set('max_execution_time', 9999);
ini_set('error_reporting', E_ALL);

$current_folder_path = '.'; // dirname($_SERVER['SCRIPT_FILENAME']);
$archive_folder_path = "$current_folder_path/mht";			//* <- default, subfolder near this script

$include_list_file = "$current_folder_path/get_mht_include_list.txt";	//* <- optional, overrides $archive_folder_path
$exclude_list_file = "$current_folder_path/get_mht_exclude_list.txt";	//* <- lists contain one path or filename wildcard per line without quotes

$program_exe_name = $program_arg = '7z.exe';				//* <- bare exe name used if not found in $program_folders
$program_folders = array(
	'C:/Program Files/7-Zip'
,	'C:/Programs/7-Zip'
,	'D:/Program Files/7-Zip'
,	'D:/Programs/7-Zip'
);

$return_codes = array(
	0 => 'OK.'
,	1 => 'Warning: non fatal error(s), e.g. files locked by other application.'
,	2 => 'Fatal error.'
,	7 => 'Command line error.'
,	8 => 'Not enough memory.'
,	255 => 'User stopped the process.'
);

$descriptor_spec = array(
	0 => array('pipe', 'r')	//* stdin is a pipe that the child will read from
,	1 => array('pipe', 'w')	//* stdout is a pipe that the child will write to
,	2 => array('pipe', 'w')	//* stderr is a pipe that the child will write to
);

$generic_rubrics = array(
	'index'
,	'none'
,	'no rubric'
,	'personal_feed'
);

$last_saved_file_name = $last_saved_file_type = '';
$saved_html_file_names = array();
$saved_page_hashes = array();
$saved_page_ids = array();
$saved_pages = array();
$linked_pages = array();
$page_id_by_hash = array();

define('TEST', false);
define('TEST_PIPE_SPLITS', false);
define('TEST_SRC_TEXT', false);
define('COLORED_RUBRICS', true);

define('NL', "\n");
define('CUT_PLACEHOLDER', '(...)');
define('JOIN_DELIMITER', ' | ');
define('TRIM_JOINED_CHARS', CUT_PLACEHOLDER.JOIN_DELIMITER);
define('A_HREF_PAT', '~(?:^|\s)href="?([^"]+)~i');
define('A_TEXT_PAT', '~(?:^|>)([^<>]+)(?:$|<)~i');
define('P_HASH_LENGTH', 32);
define('P_HASH_PAT', '~--(\w{32})\b~i');
define('P_SLUG_PAT', '~[/?&]([^/?&#]+)--(?:\w{32})\b~i');
define('P_ID_PAT', '~[?&]persistent_id=([^&#]+)~i');
define('P_TIME_PAT', '~[?&]t=([^&#]+)~i');
define('RUBRIC_PAT', '~[?&]rubric=([^&#]+)~i');
define('CONTENT_NAME_PAT', '~^(?:[^?#]*?/+)*([^/?#]+)(?:$|[?#])~');
define('CONTENT_TYPE_PAT', '~Content[^a-z]+type\s*=\s*(\S[^\r\n]*)~i');
define('CONTENT_URL_PAT', '~Content[^a-z]+location\s*=\s*(\S[^\r\n]*)~i');

if (COLORED_RUBRICS) {
	define('COLOR_WEIGHT_R', 1.5);
	define('COLOR_WEIGHT_G', 2.2);
	define('COLOR_WEIGHT_B', 1);

	define('COLOR_LIGHTNESS_MAX', ceil((255 * COLOR_WEIGHT_R) + (255 * COLOR_WEIGHT_G) + (255 * COLOR_WEIGHT_B)));
	define('COLOR_LIGHTNESS_THRESHOLD', floor(COLOR_LIGHTNESS_MAX / 3));

	define('COLOR_STEP', 2);
	define('COLOR_LENGTH', 6);
	define('COLOR_PADDING', '0');

	function get_hex_color_from_hash ($hash) {

		$hash2 = $hash.$hash;
		$cut_stop = strlen($hash);
		$color_pick = 0;
		$color_pick_lightness = 0;

		for (
			$cut_len = COLOR_STEP;
			$cut_len <= COLOR_LENGTH;
			$cut_len += COLOR_STEP
		) {
			$prefix = str_repeat(COLOR_PADDING, COLOR_LENGTH - $cut_len);
			$suffix = '';
	next_prefix:
			for (
				$cut_start = 0;
				$cut_start < $cut_stop;
				$cut_start += COLOR_STEP
			) {
				if ($cut_part = substr($hash2, $cut_start, $cut_len)) {

					$color_hex = "$prefix$cut_part$suffix";

					list($R, $G, $B) = array_map('hexdec', str_split($color_hex, COLOR_STEP));

					$L = (
						($R * COLOR_WEIGHT_R)
					+	($G * COLOR_WEIGHT_G)
					+	($B * COLOR_WEIGHT_B)
					);

					if (
						$L > COLOR_LIGHTNESS_THRESHOLD
					&&	$L > $color_pick_lightness
					) {
						$color_pick = $color_hex;
						$color_pick_lightness = $L;
					}
				}
			}

			if (strlen($prefix) > 0) {

				$next_prefix_length = strlen($prefix) - COLOR_STEP;
				$prefix = (
					$next_prefix_length > 0
					? str_repeat(COLOR_PADDING, $next_prefix_length)
					: ''
				);
				$suffix = str_repeat(COLOR_PADDING, COLOR_LENGTH - $cut_len - $next_prefix_length);

				goto next_prefix;
			}
		}

		return $color_pick.dechex(
			ceil(
				pow(
					($color_pick_lightness - COLOR_LIGHTNESS_THRESHOLD)
				/	(COLOR_LIGHTNESS_MAX - COLOR_LIGHTNESS_THRESHOLD)
				,	3
				) * 232
			) + 23
		);
	}
}

function trim_joined_tail ($text) {
	return trim(rtrim($text, TRIM_JOINED_CHARS));
}

function get_all_parts_joined_cut ($parts, $max_length = 128) {

	if (!$parts) return false;

	$text = (
		is_array($parts)
		? implode(JOIN_DELIMITER, array_filter(array_map('trim_joined_tail', $parts)))
		: trim($parts)
	);

	return (
		mb_strlen($text > $max_length, 'utf-8')
		? trim_joined_tail(mb_substr($text, 0, $max_length - strlen(CUT_PLACEHOLDER), 'utf-8')).CUT_PLACEHOLDER
		: $text
	);
}

function get_all_parts_by_pat ($text, $pat) {
	return (
		$text
	&&	strlen($text)
	&&	preg_match_all($pat, $text, $match)
		? $match[1]
		: false
	);
}

function get_part_by_pat ($text, $pat, $target_length = 0) {
	return (
		$text
	&&	strlen($text)
	&&	preg_match($pat, $text, $match)
	&&	($target_length > 0 ? $target_length === strlen($match[1]) : true)
		? $match[1]
		: false
	);
}

function get_link_text   ($text) { return get_all_parts_by_pat ($text, A_TEXT_PAT); }
function get_link_url    ($text) { return get_part_by_pat ($text, A_HREF_PAT); }
function get_page_hash   ($text) { return get_part_by_pat ($text, P_HASH_PAT, P_HASH_LENGTH); }
function get_page_id     ($text) { return get_part_by_pat ($text,   P_ID_PAT); }
function get_page_rubric ($text) { return get_part_by_pat ($text, RUBRIC_PAT); }
function get_page_slug   ($text) { return get_part_by_pat ($text, P_SLUG_PAT); }
function get_page_time   ($text) { return get_part_by_pat ($text, P_TIME_PAT); }

function get_a_parts ($text) {
	return (
		($page_url = get_link_url($text))
	&&	($page_hash = get_page_hash($page_url))
	&&	($page_title = get_all_parts_joined_cut(get_link_text($text)))
		? array(
			'id'     => get_page_id($page_url) ?: 'no id'
		,	'url'    => $page_url
		,	'hash'   => $page_hash
		,	'time'   => (intval($t = get_page_time($page_url)) > 0 ? date(DATE_ATOM, $t) : 'no time')
		// ,	'slug'   => str_replace('_', ' ', get_page_slug($page_url) ?: 'no slug')
		,	'title'  => $page_title
		,	'rubric' => get_page_rubric($page_url) ?: 'no rubric'
		) : false
	);
}

function sort_linked_pages ($a, $b) {
	return (
		($a['time']	<=> $b['time'])
	?:	($a['id']	<=> $b['id'])
	?:	($a['hash']	<=> $b['hash'])
	?:	($a['rubric']	<=> $b['rubric'])
	// ?:	($a['title']	<=> $b['title'])
	// ?:	($a['slug']	<=> $b['slug'])
	?:	($a['url']	<=> $b['url'])
	);
}

function add_saved_page ($page_url) {
	global $saved_page_hashes, $saved_page_ids;

	if (($page_hash = get_page_hash($page_url)) && !in_array($page_hash, $saved_page_hashes)) array_push($saved_page_hashes, $page_hash);
	if (($page_id   = get_page_id  ($page_url)) && !in_array($page_id,   $saved_page_ids))    array_push($saved_page_ids,    $page_id);

	return $page_hash;
}

function add_linked_page ($text) {
	global $saved_page_hashes, $saved_page_ids, $saved_pages, $linked_pages, $page_id_by_hash;

	if (
		($text = html_entity_decode($text))
	&&	($page_entry = get_a_parts ($text))
	) {
		$page_id    = $page_entry['id'];
		$page_url   = $page_entry['url'];
		$page_hash  = $page_entry['hash'];
		$page_title = $page_entry['title'];
		// $page_titles = array(
		//	$page_entry['slug'],
		//	$page_entry['title']
		// );

		if (
			in_array($page_hash, $saved_page_hashes)
		||	in_array($page_id,   $saved_page_ids)
		) {
			$pages = &$saved_pages;
		} else {
			$pages = &$linked_pages;

			if (TEST_SRC_TEXT) $page_entry['source_text'] = htmlspecialchars($text);
		}

		if (array_key_exists($page_hash, $page_id_by_hash)) {
			$page_key = $page_id_by_hash[$page_hash];
		} else {
			$page_key = $page_id_by_hash[$page_hash] = $page_id;
		}

		if (!array_key_exists($page_key, $pages)) {
			$pages[$page_key] = array();
		}

		$pages_for_this_key = &$pages[$page_key];

		if (!array_key_exists($page_url, $pages_for_this_key)) {

			unset($page_entry['title']);
			// $page_entry['titles'] = $page_titles;
			$page_entry['titles'] = array($page_title);
			$pages_for_this_key[$page_url] = &$page_entry;

		} else {
			$titles_for_this_url = &$pages_for_this_key[$page_url]['titles'];

			// foreach ($page_titles as $page_title)
			if (!in_array($page_title, $titles_for_this_url)) {

				array_push($titles_for_this_url, $page_title);
			} else {
				return false;
			}
		}
	}

	return $page_entry;
}

function is_page_filename ($text) {
	global $saved_html_file_names, $last_saved_file_name, $last_saved_file_type;

	$is_hash = !!get_page_hash ($text);

	if (!$is_hash) {
		if (!strlen($text = trim($text))) {
			if (
				$last_saved_file_type === 'text/html'
			&&	strlen($last_saved_file_name)
			&&	preg_match(CONTENT_NAME_PAT, $last_saved_file_name, $match)
			&&	strlen($name = $match[1])
			&&	!in_array($name, $saved_html_file_names)
			) {
				array_push($saved_html_file_names, $name);

				echo "\n\"$name\"";
			}

			$last_saved_file_name = $last_saved_file_type = '';
		}
		else if ($type = get_part_by_pat ($text, CONTENT_TYPE_PAT)) $last_saved_file_type = $type;
		else if ($name = get_part_by_pat ($text, CONTENT_URL_PAT))  $last_saved_file_name = $name;
	}

	return $is_hash;
}

function is_relevant_url ($text) {
	return (
		($text = html_entity_decode($text))
	&&	($page_url = get_link_url ($text))
	&&	!!get_page_hash ($page_url)
	&&	(
			false !== strpos($page_url, '/instory/')
		||	false !== strpos($page_url, '/story/')
		)
	);
}

function get_quoted ($var) { return '"'.trim($var, '"').'"'; }
function get_quoted_exclude_arg ($ext) { return get_quoted("-xr!*.$ext"); }
function get_quoted_include_arg ($ext) {
	global $archive_folder_path;

	return get_quoted("-air!$archive_folder_path\\*.$ext");
}

function get_to_print ($var) { return print_r($var, true); }
function print_block ($var) {
	echo('
	<pre>'.htmlspecialchars(get_to_print($var)).'
	</pre>');
}

function var_dump_block ($var) {
	echo '<pre>';
	var_dump($var);
	echo '</pre>';
}

function run_test ($command_line, $filter_func_name = '', $map_func_name = '', $split_each_line_by = '') {
	global $descriptor_spec, $return_codes;

	echo("
	<details>
		<summary style=\"background-color: lightgray\">(click for details) command: $command_line</summary>
		<div>");

	flush();

	$process = proc_open($command_line, $descriptor_spec, $pipes);
	$stdout = $pipes[1];

	$output_buffer = '';
	$output_lines = 0;
	$return_code = 0;
	$flush_time = 0;

	if (!$split_each_line_by) {
		$split_each_line_by = NL;
	}

	$splitter_length = strlen($split_each_line_by);

	while (
		is_string($output_part = stream_get_line($stdout, 0))
	&&	strlen($output_part)
	) {
		$output_buffer .= $output_part;
		$split_lines = 0;

		while (is_int($nearest_split_pos = strpos($output_buffer, $split_each_line_by))) {

			$line = substr($output_buffer, 0, $nearest_split_pos);
			$output_buffer = substr($output_buffer, $nearest_split_pos + $splitter_length);
			$output_lines++;
			$split_lines++;

			if ($filter_func_name($line)) {
				$map_func_name($line);

				if (TEST_PIPE_SPLITS) echo '+';
			} else	if (TEST_PIPE_SPLITS) echo '-';
		}

		if (TEST_PIPE_SPLITS) {
			if (
				!is_int($nearest_split_pos)
			&&	strlen($output_buffer)
			) {
				echo($split_lines ? NL.'|' : '|');
			}
		} else {
			echo($split_lines ? NL.'.' : '.');
		}

		$read_time = time();

		if ($flush_time !== $read_time) {
			$flush_time = $read_time;

			flush();
		}
	}

	if (strlen($output_buffer)) {
		$output_lines++;

		if ($filter_func_name($output_buffer)) {
			$map_func_name($output_buffer);

			if (TEST_PIPE_SPLITS) echo 'V';
		} else	if (TEST_PIPE_SPLITS) echo 'X';
	} else		if (TEST_PIPE_SPLITS) echo '0';

	$process_status = proc_get_status($process);
	$return_code = $process_status['exitcode'];

//* Close any pipes before calling proc_close in order to avoid a deadlock:

	foreach ($pipes as $pipe) if ($pipe) fclose($pipe);

	proc_close($process);

	$status_message = (
		array_key_exists($return_code, $return_codes)
		? $return_codes[$return_code]
		: 'Unknown error.'
	);

	echo("
		</div>
	</details>
	<details>
		<summary style=\"background-color: lightblue\">(click for details) result: $return_code. $status_message</summary>
		<div style=\"background-color: lightcyan\">output_lines = $output_lines</div>
	</details>");

	flush();
}

foreach ($program_folders as $path)
if (is_file($program_exe_path = "$path/$program_exe_name")) {
	$program_arg = get_quoted($program_exe_path);

	break;
}

$archive_arg = '-an '.(
	is_file($include_list_file)
	? get_quoted("-air@$include_list_file")
	: implode(' ', array_map('get_quoted_include_arg', array(
		'mht',
		'mhtml',
	)))
);

$content_arg = '"-ir!*--*"';
$content_exclude_arg = (
	is_file($exclude_list_file)
	? get_quoted("-xr@$exclude_list_file")
	: implode(' ', array_map('get_quoted_exclude_arg', array(
		'css',
		'gif',
		'jpeg',
		'jpg',
		'js',
		'png',
		'svg',
		'webp',
	)))
);

//* "-ba" prints truncated filenames:
// run_test("$program_arg l -ba $archive_arg $content_arg", 'is_page_filename');

//* "-slt" prints full "Content location" URL:
run_test("$program_arg l -slt $archive_arg $content_exclude_arg", 'is_page_filename', 'add_saved_page');

if (TEST) {
	print_block('Saved pages hashes:');
	print_block($saved_page_hashes);

	print_block('Saved pages IDs:');
	print_block($saved_page_ids);
}

if (count($saved_html_file_names)) {
	natsort($saved_html_file_names);

	$content_arg .= ' "'.implode('" "', $saved_html_file_names).'"';
}

//* "-so" prints full HTML page content:
run_test("$program_arg x -so $archive_arg $content_arg", 'is_relevant_url', 'add_linked_page', '<a ');

if (TEST) {
	print_block('Saved pages:');
	print_block($saved_pages);

	print_block('Linked pages:');
	print_block($linked_pages);
}

if ($linked_pages) {
	$pages_by_rubric = array();

	foreach ($linked_pages as $page_key => &$same_page_entries) {

		foreach ($same_page_entries as &$page_entry)
		if (array_key_exists('titles', $page_entry)) {

			$page_entry['title'] = get_all_parts_joined_cut($page_entry['titles']);
			unset($page_entry['titles']);
		}

		usort($same_page_entries, 'sort_linked_pages');
		$p = $same_page_entries[0];

		foreach ($same_page_entries as &$page_entry)
		if (!in_array($page_entry['rubric'], $generic_rubrics)) {
			$p = $page_entry;

			break;
		}

		$rubric = $p['rubric'];

		if (!array_key_exists($rubric, $pages_by_rubric)) {
			$pages_by_rubric[$rubric] = array();
		}

		$pages_by_rubric[$rubric][$p['title']] = $page_key;
	}

//* To prevent foreach ref value bugs:
	unset($page_entry);

	print_block('Unsaved linked pages - '.count($linked_pages).' IDs in '.count($pages_by_rubric).' rubrics:');

	ksort($pages_by_rubric);

	foreach ($pages_by_rubric as $rubric => &$page_keys_by_title) {

		echo '
	<details'.(COLORED_RUBRICS ? ' style="background-color: #'.get_hex_color_from_hash(md5($rubric)).'"' : '').'>
		<summary>('.count($page_keys_by_title).') '.$rubric.'</summary>';

		ksort($page_keys_by_title);

		foreach ($page_keys_by_title as $page_key) {

			echo "
		<p>$page_key<br>";

//* To detect ref value bugs:
			if (TEST)
			foreach ($linked_pages[$page_key] as $page_entry)
			if ($page_key != $page_entry['id']) {

				var_dump_block ($page_key);
				var_dump_block ($linked_pages[$page_key]);

				break;
			}

			$done_titles = array();

			foreach ($linked_pages[$page_key] as $page_entry) {

				$title = (
					array_key_exists('titles', $page_entry)
					? get_all_parts_joined_cut($page_entry['titles'])
					: (
					array_key_exists('title', $page_entry)
					? $page_entry['title']
					: 'no title'
					)
				);

				if (in_array($title, $done_titles)) {
					continue;
				}

				array_push($done_titles, $title);

				$hint = (
					array_key_exists('source_text', $page_entry)
					? " title=\"$page_entry[source_text]\""
					: ''
				);

				echo "
			$page_entry[id],
			$page_entry[time],
			$page_entry[rubric],
			$page_entry[hash] -
			<a href=\"$page_entry[url]\"$hint>$title</a>
			<br>";
			}

			echo '
		</p>';
		}

		echo '
	</details>';
	}
}

?>
</body>
</html>