<?php

require(basename($_SERVER['PHP_SELF']).'_config.php');

$date_format = 'Y-m-d H:i:s';
$gmdate_format = 'D, d M Y H:i:s \G\M\T';	//* <- 'r' format gives "+0000" instead of "GMT"

define('NL', "\n");
define('IS_LOCALHOST', ($_SERVER['SERVER_ADDR'] === $_SERVER['REMOTE_ADDR']));

//* Wrapper to avoid PHP 8 Warning: Undefined array key:

function get_value_or_empty($array, $key) {
	if (array_key_exists($key, $array)) {
		if (is_array($array[$key])) {
			foreach ($array[$key] as $item) if ($item) {
				return $item;
			}
		} else {
			return $array[$key];
		}
	}
	return '';
}

function is_prefix($text, $part) { return (strpos($text, $part) === 0); }
// function is_postfix($text, $part) { return (strrpos($text, $part) === (strlen($text) - strlen($part))); }
// function is_prefix($text, $part) { return substr($text, 0, strlen($part)) === $part; }
// function is_postfix($text, $part) { return substr($text, -strlen($part)) === $part; }

if (!(
	IS_LOCALHOST
||	in_array($_SERVER['HTTP_HOST'], $allowed_hostnames)
)) {
	die(date('>Y'));
}

if (
	isset($allowed_cookies)
&&	is_array($allowed_cookies)
&&	!empty($allowed_cookies)
) {
	$has_allowed_cookie = false;

	foreach ($allowed_cookies as $key => $value) if (get_value_or_empty($_COOKIE, $key) === $value) {

		$has_allowed_cookie = true;

		break;
	}

	if (!$has_allowed_cookie) {
		die(date('>>Y'));
	}
}


$is_relative_to_request =
$is_relative_to_referer = false;

$self_hostname = get_value_or_empty($_SERVER, 'HTTP_HOST') ?: $default_hostname;
$self_protocol = get_value_or_empty($_SERVER, 'REQUEST_SCHEME') ?: $default_protocol;
$referer = get_value_or_empty($_SERVER, 'HTTP_REFERER') ?: '';

foreach (array(true, false) as $is_raw_prefix)
foreach ($proxified_protocols as $target_protocol => $substitute_target_server) {

	$self_root_folder = (
		($must_get_raw_content = $is_raw_prefix)
		? 'raw/'
		: ''
	).$target_protocol;

	if (
		!$substitute_target_server
	&&	is_prefix(
			$target_url = $_SERVER['REQUEST_URI']
		,	$self_root_prefix = "/$self_root_folder:"
		)
	) {
		$target_url = ltrim(substr($target_url, strlen($self_root_prefix)), '/');

		header("Location: /$self_root_folder/$target_url");

		die();
	}

	if ((
		$is_relative_to_request = (
			is_prefix(
				$target_url = $_SERVER['REQUEST_URI']
			,	$self_root_prefix = "/$self_root_folder/"
			)		//* <- root sub/folder here (nonexistent)
		||	is_prefix(
				$target_url = $_SERVER['QUERY_STRING']
			,	$self_root_prefix
			)		//* <- file.ext?/url/ syntax, if possible
		)
	) || (
		$is_relative_to_referer = ((
			is_prefix(
				$referer
			,	"$self_protocol://$self_hostname/$self_root_folder/"
			)
		) || (
			$substitute_target_server
		&&	is_prefix(
				$referer
			,	"$self_protocol://$self_hostname/$substitute_target_server"
			)
		))
	)) {
		$self_root_length = strlen($self_root_prefix);

		if ($substitute_target_server) {
			$target_path = substr(
				$target_server = $substitute_target_server
			,	0
			,	strpos($substitute_target_server, ':')
			);

			if ($is_relative_to_request) {
				$target_url = substr(
					$target_url
				,	strpos($target_url, $self_root_prefix) + $self_root_length
				);
			}
		} else {
			$self_root_prefix .= $target_server = substr(
				$target_url
			,	$self_root_length
			,	strpos($target_url, '/', $self_root_length) - $self_root_length + 1
			);

			if ($is_relative_to_request) {
				$target_url = substr(
					$target_url
				,	strlen($target_server) + $self_root_length
				);
			}

			$target_server = "$target_protocol://$target_server";
			$target_path = substr(
				$substitute_target_server = ltrim($self_root_prefix, '/')
			,	0
			,	strpos($substitute_target_server, '/')
			);
		}

		break 2;
	}
}

$response_headers = array();
$response_headers_text = '';

function get_header_line($curl, $header_line) {
	global $response_headers, $response_headers_text;

	$has_colon = (false !== strpos($header_line, ':'));
	$has_space = (false !== strpos($header_line, ' '));

	if ($has_colon || $has_space) {
		$separator = ($has_colon ? ':' : ' ');

		// if (IS_LOCALHOST) echo "$separator, $header_line<br>";

		list($key, $value) = array_map('trim', explode($separator, $header_line, 2));

		$response_headers_text .= NL."$key: $value";

		$low_key = strtolower(
			false !== strpos($key, '/')
			? explode('/', $key, 2)[0]
			: $key
		);

		if (!array_key_exists($low_key, $response_headers)) {
			$response_headers[$low_key] = array();
		}

		$response_headers[$low_key][] = $value;
	}

	return strlen($header_line);
}

function trim_info($text) {
	return trim(str_replace('-->', '-- >', $text));
}

function text_to_one_line($text) {
	return trim(str_replace("\r", '\\r', str_replace("\n", '\\n', $text)));
}

function mkdir_if_none($file_path) {
	if (
		strlen($dir_name = dirname($file_path))
	&&	!is_dir($dir_name)
	&&	!is_file($dir_name)
	) {
		mkdir($dir_name, 0755, true);
	}

	return $file_path;
}

//* Prepare request to target server:

if (
	$is_relative_to_request
||	$is_relative_to_referer
) {
	$data_dir = '';

	foreach ($data_dirs as $check_path) if (is_dir($check_path)) {

		$data_dir = $check_path;

		break;
	}

	$target_server_hash = md5("$target_server");
	$lock_file = mkdir_if_none("$data_dir/lock_files/$target_server_hash.lock");
	$cookie_file = mkdir_if_none("$data_dir/cookie_files/$target_server_hash.txt");

//* To support persistent cookie storage, use cURL instead of file_get_contents:

	$t0 = microtime();

	$curl_handle = curl_init($request_url = "$target_server$target_url");

	curl_setopt($curl_handle, CURLOPT_HEADER, 0);
	curl_setopt($curl_handle, CURLOPT_USERAGENT, $default_useragent);
	curl_setopt($curl_handle, CURLOPT_COOKIEFILE, $cookie_file);		//* http://php.net/manual/en/function.curl-setopt.php
	curl_setopt($curl_handle, CURLOPT_COOKIEJAR, $cookie_file);
	curl_setopt($curl_handle, CURLOPT_FOLLOWLOCATION, 1);
	curl_setopt($curl_handle, CURLOPT_MAXREDIRS, 10);
	curl_setopt($curl_handle, CURLOPT_CONNECTTIMEOUT, 10);
	curl_setopt($curl_handle, CURLOPT_RETURNTRANSFER, 1);
	curl_setopt($curl_handle, CURLOPT_AUTOREFERER, 1);
	curl_setopt($curl_handle, CURLOPT_FILETIME, 1);				//* http://php.net/manual/en/function.curl-getinfo.php
	curl_setopt($curl_handle, CURLOPT_HEADERFUNCTION, 'get_header_line');	//* https://stackoverflow.com/a/9183272
	curl_setopt($curl_handle, CURLINFO_HEADER_OUT, 1);

	if ($if_time_text = get_value_or_empty($_SERVER, 'HTTP_IF_MODIFIED_SINCE')) {
		curl_setopt($curl_handle, CURLOPT_TIMEVALUE, strtotime($if_time_text));
	}

//* Run request:

	if ($lock = fopen($lock_file, 'a')) {
		flock($lock, LOCK_EX);
	}

	$response_content = curl_exec($curl_handle);

	$response_info = curl_getinfo($curl_handle);
	curl_close($curl_handle);

	if ($lock) {
		flock($lock, LOCK_UN);
		fclose($lock);
		unset($lock);
	}

	$t1 = microtime();

//* Process response, received from request:

	header('X-Source-Headers: '.text_to_one_line($response_headers_text));

	if (IS_LOCALHOST) {
		header('X-JSON-Low-Key-Headers: '.text_to_one_line(json_encode($response_headers)));
		header('X-JSON-Curl-Info: '.text_to_one_line(json_encode($response_info)));
	}

	$http_code = intval(
		get_value_or_empty($response_info, 'http_code')
	?:	get_value_or_empty($response_headers, 'http')
	);

	$file_time = (
		get_value_or_empty($response_info, 'filetime')
	?:	get_value_or_empty($response_info, 'file_time')
	?:	get_value_or_empty($response_info, 'last_modified')
	?:	get_value_or_empty($response_headers, 'last-modified')
	);

	$file_time_text = gmdate($gmdate_format, $file_time);

	if (
		($file_time !== -1)
	&&	(
			$http_code === 304
		||	$file_time === $if_time_text
		||	$file_time_text === $if_time_text
		)
	) {
		header('HTTP/1.0 304 Not Modified');
		exit;
	}

//* Process response content to return back to client:

	$save_name = (
		get_value_or_empty($response_info, 'content_disposition')
	?:	get_value_or_empty($response_headers, 'content-disposition')
	);

	$file_type = (
		get_value_or_empty($response_info, 'content_type')
	?:	get_value_or_empty($response_headers, 'content-type')
	);

	$file_etag = (
		get_value_or_empty($response_info, 'etag')
	?:	get_value_or_empty($response_headers, 'etag')
	);

	$file_size = (
		get_value_or_empty($response_info, 'filesize')
	?:	get_value_or_empty($response_info, 'file_size')
	?:	get_value_or_empty($response_info, 'size_download')
	?:	get_value_or_empty($response_info, 'content_length')
	?:	get_value_or_empty($response_headers, 'content-length')
	);

	if ($response_content) {
		if ($http_code == 200) header('HTTP/1.1 200 OK'); else
		if ($http_code == 404) header('HTTP/1.1 404 Not Found'); else
		// if ($http_code == 403) header('HTTP/1.1 403 Forbidden'); else
		// if ($http_code == 405) header('HTTP/1.1 405 Not Allowed'); else
		header('HTTP/1.1 200 OK, who cares about '.$http_code);

		if ($file_time && $file_time !== -1) header('Last-Modified: '.$file_time_text);
		if ($file_etag && $file_etag !== -1) header('Etag: '.$file_etag);
		if ($file_type && $file_type !== -1) header('Content-Type: '.$file_type);
		if ($file_size && $file_size !== -1) header('Content-Length: '.$file_size);

		if ($save_name && $save_name !== -1) header('Content-Disposition: '.$save_name);
		else

//* Redefine filename for saving:

		if (substr($file_type, 0, 5) == 'image') {
			$save_name = explode('?', $request_url, 2)[0];
			// if ($save_name !== $request_url) {
				$save_name = strtr($save_name, ':/\\?*<>', ';,,&___');
				header('Content-Disposition: attachment; filename="'.$save_name.'"');
			// }
		} else

//* Autoreplace target site-related URLs in HTML to proxify its images, CSS, JS, etc:

		if (
			!$must_get_raw_content
		&&	$file_type
		// &&	strtolower(substr(explode('?', $request_url, 2)[0], -3)) != '.js'
		&&	(
				false !== strpos($file_type, 'html')
			||	false !== strpos($file_type, 'xml')
			// ||	false !== strpos($file_type, 'text')
			// ||	false !== strpos($response_content, '<html')
			// ||	false !== strpos($response_content, '<head')
			// ||	false !== strpos($response_content, '<body')
			// ||	preg_match('~[<](html|head|body)[\r\n\s/>]~isu', $response_content)
			)
		) {
			ksort($response_info);

			$target_path = "/$target_path/";
			$domain_parts = explode('.', preg_replace('~^([^/]*/+)?([^:/]+)(/.*)?$~u', '$2', $target_server));
			$domain_level_2 = implode('.', array_slice($domain_parts, -2));
			$response_content = '

request info:

'.trim_info(print_r($response_info, true)).'

response headers:

'.trim_info($response_headers_text).'

-->
'.
preg_replace('~(\s\w+=[\'"])([htps]+):/(/([^=\'"/]+\.)?'.$domain_level_2.')~iu', '$1/$2$3',
preg_replace('~(\s\w+=[\'"])//([^>])~iu', '$1'.$target_path.'$2',
preg_replace('~'.$target_server.'|(\s\w+=[\'"])/([^/>])~iu', '$1'.$self_root_prefix.'$2',
preg_replace('~([^/]+/+)?\.\./+~u', '',
$response_content))));
			$t2 = microtime();
			$response_content = '<!--
t_start	= '.date($date_format, ($t0 = explode(' ', $t0))[1]).', '.sprintf('%.6f', $t0 = $t0[1] + $t0[0]).'
t_end	= '.date($date_format, ($t1 = explode(' ', $t1))[1]).', '.sprintf('%.6f', $t1 = $t1[1] + $t1[0]).'
t_out	= '.date($date_format, ($t2 = explode(' ', $t2))[1]).', '.sprintf('%.6f', $t2 = $t2[1] + $t2[0]).'
request = '.($t1 - $t0).'
process	= '.($t2 - $t1).$response_content;
		}

		die($response_content);
	} else {
		header('HTTP/1.1 404 NO');

		die(
			'Error 404: <a href="'.$request_url.'">'.$request_url.'</a> is empty.'
		.NL.	'<!-- and this is for IE: -->'
		.NL.	str_repeat(' ', 500)
		);
	}
}
?>dummy