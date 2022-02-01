<?php

//* About this script:
//* It allows to simply pass a HTTP GET request to a web page or file and get the result.
//* It may be simpler to set up for some read-only use cases than a SOCKS proxy, etc.
//* It may work on a shared hosting with PHP and no way to setup custom executables, which was the reason to create this script.
//* It works best from web root folder and with all paths autoredirected to it on a separate (sub)domain name dedicated to it.
//* As a usable fallback, query argument syntax should work, i.e. "path/to/index.php?target://site/url".

require(basename($_SERVER['PHP_SELF']).'_config.php');

define('NL', "\n");
define('IS_LOCALHOST', $_ENV['LOCAL_CLIENT'] ?? ($_SERVER['SERVER_ADDR'] === $_SERVER['REMOTE_ADDR']));

if (!(
	IS_LOCALHOST
||	in_array($_SERVER['HTTP_HOST'], $allowed_hostnames)
)) {
	die(date('>Y'));
}

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
function get_path_after_prefix($path, $prefix, $trim_chars = ':/.?') { return ltrim(substr($path, strlen($prefix)), $trim_chars); }
function get_domain_and_last_part_from_url($url, $number_of_parts = 2) {

	if (preg_match('~^
		(?P<BeforeDomain>
			(?:
				(?P<Protocol>[^:/?#]+)
			:)?
		//+)?
		(?P<Domain>[^:/?#]+)
		(?P<Path>/.*)?
	$~ux', $url, $match)) {

		$domain = $match['Domain'];
		$domain_parts = explode('.', $domain);
		$last_parts = array_slice($domain_parts, -$number_of_parts);

		return array(
			$domain
		,	implode('.', $last_parts)
		,	$match['Protocol']
		,	$match['Path']
		);
	}
}

function get_path_dir_from_url($path) {

	if ($i = strpos ($path, '?')) $path = substr($path, 0, $i);
	if ($i = strrpos($path, '/')) $path = substr($path, 0, $i+1);

	return $path;
}

function get_self() {
	return (
		get_value_or_empty($_SERVER, 'PHP_SELF')
	?:	get_value_or_empty($_SERVER, 'SCRIPT_NAME')
	?:	get_value_or_empty($_SERVER, 'DOCUMENT_URI')
	);
}

function get_self_root() {
	$url = $_SERVER['REQUEST_URI'];
	$path = get_self();

	if (is_prefix($url, $path_with_query = "$path/?")) return $path_with_query;
	if (is_prefix($url, $path_with_query = "$path?")) return $path_with_query;
	if (is_prefix($url, $path)) return $path;

	$path = get_path_dir_from_url($path);
	$path = '/'.trim($path, '/');

	if (is_prefix($url, $path_with_query = "$path/?")) return $path_with_query;
	if (is_prefix($url, $path_with_query = "$path?")) return $path_with_query;
	if (is_prefix($url, $path)) return $path;

	if (is_prefix($url, $path_with_query = "/?")) return $path_with_query;

	return '';
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

define('DATE_FORMAT', 'Y-m-d H:i:s');
define('GMDATE_FORMAT', 'D, d M Y H:i:s \G\M\T');	//* <- 'r' format gives "+0000" instead of "GMT"

$is_relative_to_request =
$is_relative_to_referer = false;

$self_root = get_self_root();
$self_hostname = get_value_or_empty($_SERVER, 'HTTP_HOST') ?: $default_hostname;
$self_protocol = get_value_or_empty($_SERVER, 'REQUEST_SCHEME') ?: $default_protocol;
$referer = get_value_or_empty($_SERVER, 'HTTP_REFERER');
$target_url = get_path_after_prefix($_SERVER['REQUEST_URI'], $self_root);
$try_protocol_prefixes = array('', 'raw/');

$target_root_prefix =
$target_path =
$target_server =
$target_protocol =
$target_protocol_folder = '';

foreach ($try_protocol_prefixes as $must_get_raw_content => $raw_prefix)
foreach ($proxified_protocols as $target_protocol => $target_server_substitute) {

	$target_protocol_folder = "$raw_prefix$target_protocol";

//* Redirect "?/protocol://url/" to "/protocol/url/":

	if (
		!$target_server_substitute
	&&	is_prefix(
			$target_url
		,	"$target_protocol_folder://"
		)
	) {
		$target_url = get_path_after_prefix($target_url, $target_protocol_folder);

		header("Location: $self_root/$target_protocol_folder/$target_url");

		die();
	}

	$target_root_prefix = "$self_root/$target_protocol_folder/";

//* Target server stated in URL, explicit or substitute:

	if (

		$is_relative_to_request = ((
			is_prefix(
				$target_url
			,	"$target_protocol_folder/"
			)
		) || (
			$target_server_substitute
		&&	is_prefix(
				$target_url
			,	"$target_server_substitute/"
			)
		))
	) {
		if ($target_server = $target_server_substitute) {
			$target_path = get_path_after_prefix($target_url, $target_protocol_folder, '/.');
		} else {
			list($target_server, $target_path) = explode('/', get_path_after_prefix($target_url, $target_protocol_folder), 2);
			$target_path = ltrim($target_path, '/.');
			$target_root_prefix .= "$target_server/";
			$target_server = "$target_protocol://$target_server/";
		}

		goto got_target;
	}
}

$self_root_prefix = "$self_protocol://$self_hostname/$self_root";

foreach ($try_protocol_prefixes as $must_get_raw_content => $raw_prefix)
foreach ($proxified_protocols as $target_protocol => $target_server_substitute) {

	$target_protocol_folder = "$raw_prefix$target_protocol";
	$target_root_prefix = "$self_root/$target_protocol_folder/";

//* Get server from referer instead of fixing relative links in proxified pages, CSS, etc:

	if (
		$is_relative_to_referer = ((
			is_prefix(
				$referer
			,	$target_server_prefix = "$self_root_prefix/$target_protocol_folder/"
			)
		) || (
			$target_server_substitute
		&&	is_prefix(
				$referer
			,	$target_server_prefix = "$self_root_prefix/$target_server_substitute/"
			)
		))
	) {
		$target_path = ltrim($_SERVER['REQUEST_URI'], '/.');

		if ($target_server = $target_server_substitute) {
			;
		} else {
			$target_url = get_path_after_prefix($referer, $target_server_prefix);
			$target_server = explode('/', get_path_after_prefix($target_url, $target_protocol_folder), 2)[0];
			$target_root_prefix .= "$target_server/";
			$target_server = "$target_protocol://$target_server/";
		}

		goto got_target;
	}
}

got_target:

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

if ($target_request_url = "$target_server$target_path")
// if (0)
if (
	$is_relative_to_request
||	$is_relative_to_referer
) {
	$data_dir = '';
	$ssl_certs_dir = '';

	foreach ($data_dirs as $check_path) if (is_dir($check_path)) {

		$data_dir = $check_path;

		break;
	}

	if ($data_dir) {
		$target_server_hash = md5("$target_server");
		$lock_file = mkdir_if_none("$data_dir/lock_files/$target_server_hash.lock");
		$cookie_file = mkdir_if_none("$data_dir/cookie_files/$target_server_hash.txt");
	}

//* To support persistent cookie storage, use cURL instead of file_get_contents.
//* See manual for available options:
//* http://php.net/manual/en/function.curl-getinfo.php
//* http://php.net/manual/en/function.curl-setopt.php

	$t0 = microtime();

	$curl_handle = curl_init($target_request_url);

	curl_setopt($curl_handle, CURLINFO_HEADER_OUT, 1);
	curl_setopt($curl_handle, CURLOPT_AUTOREFERER, 1);
	curl_setopt($curl_handle, CURLOPT_CONNECTTIMEOUT, 10);
	curl_setopt($curl_handle, CURLOPT_FILETIME, 1);
	curl_setopt($curl_handle, CURLOPT_FOLLOWLOCATION, 1);
	curl_setopt($curl_handle, CURLOPT_HEADER, 0);
	curl_setopt($curl_handle, CURLOPT_HEADERFUNCTION, 'get_header_line');	//* https://stackoverflow.com/a/9183272
	curl_setopt($curl_handle, CURLOPT_MAXREDIRS, 10);
	curl_setopt($curl_handle, CURLOPT_POST, 0);
	curl_setopt($curl_handle, CURLOPT_RETURNTRANSFER, 1);
	curl_setopt($curl_handle, CURLOPT_TIMEOUT, 120);
	curl_setopt($curl_handle, CURLOPT_USERAGENT, $default_useragent);
	// curl_setopt($curl_handle, CURLOPT_USERAGENT, IS_LOCALHOST ? "$default_useragent $_SERVER[PHP_SELF]" : $default_useragent);
	// curl_setopt($curl_handle, CURLOPT_VERBOSE, 1);

	if ($data_dir) {
		curl_setopt($curl_handle, CURLOPT_COOKIEFILE, $cookie_file);
		curl_setopt($curl_handle, CURLOPT_COOKIEJAR, $cookie_file);
	}

	if ($ssl_certs_dir) {
		curl_setopt($curl_handle, CURLOPT_CAPATH, $ssl_certs_dir);
	} else {
		curl_setopt($curl_handle, CURLOPT_SSL_VERIFYHOST, 0);
		curl_setopt($curl_handle, CURLOPT_SSL_VERIFYPEER, 0);
	}

	if ($if_time_text = get_value_or_empty($_SERVER, 'HTTP_IF_MODIFIED_SINCE')) {
		curl_setopt($curl_handle, CURLOPT_TIMEVALUE, strtotime($if_time_text));
	}

//* Run request:

	if ($data_dir && ($lock = fopen($lock_file, 'a'))) {
		flock($lock, LOCK_EX);
	}

	$response_content = curl_exec($curl_handle);
	$response_error = curl_errno($curl_handle);
	$response_info = curl_getinfo($curl_handle);

	curl_close($curl_handle);

	if ($data_dir && $lock) {
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

	$file_time_text = gmdate(GMDATE_FORMAT, $file_time);

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

//* The file is intended for download, not view:

		if ($save_name && $save_name !== -1) header('Content-Disposition: '.$save_name);
		else

//* Redefine filename for saving:

		if (
			!$must_get_raw_content
		&&	is_prefix($file_type, 'image')
		) {
			$save_name = explode('?', $target_request_url, 2)[0];
			$save_name = strtr($save_name, ':/\\?*<>', ';,,&___');
			header('Content-Disposition: attachment; filename="'.$save_name.'"');
		} else

//* Autoreplace target site-related URLs in HTML to proxify its images, CSS, JS, etc:

		if (
			!$must_get_raw_content
		&&	$file_type
		&&	(
				false !== strpos($file_type, 'html')
			||	false !== strpos($file_type, 'xml')
			// ||	false !== strpos($file_type, 'text')
			// ||	preg_match('~[<](html|head|body)[\r\n\s/>]~isu', $response_content)
			)
		) {
			ksort($response_info);

			$default_target_protocol = (
				$target_server_substitute
				? $raw_prefix.explode(':', $target_server, 2)[0]
				: $target_protocol_folder
			);

			list(
				$target_domain
			,	$target_domain_last_part
			,	$request_protocol
			// ,	$request_path
			) =
			get_domain_and_last_part_from_url($target_server);

			$target_folder = get_path_dir_from_url($target_path);
			// $target_path = "/$target_path/";

			if (1) {

//* Use callback replacement:
//* (?J) modifier for duplicate names for subpatterns: https://www.php.net/manual/en/reference.pcre.pattern.modifiers.php#121546

				$pat_url = '~
				(?P<Before>
					\s
					[\w-]*
					(src|href)
					[\w-]*
					=
				)(?J)(?:
					(?P<Quote>")	(?P<URL>	[^"]+			)(?=$|	"	)
				|	(?P<Quote>\')	(?P<URL>	[^\']+			)(?=$|	\'	)
				|			(?P<URL>	[^\'"\s>][^\s>]*	)(?=$|	[\s>]	)
				)~ux';

				function get_replaced_url($match) {
					global $self_root, $default_target_protocol, $proxified_protocols;
					global $target_server, $target_server_substitute;
					global $target_domain, $target_domain_last_part, $request_protocol;
					global $target_folder, $target_root_prefix;

					$url = "$match[URL]";
					$len = strlen($url);

					if ($len > 0) {
						if ($url[0] === '/') {
							$url_trim = ltrim($url, '/');

				//* Proxify link to a server with given name and omitted protocol:

							if (
								$len > 1
							&&	$url[1] === '/'
							) {
								$url = "$self_root/$default_target_protocol/$url_trim";
							} else {

				//* Proxify link on current server with omitted name, relative to root folder:

								$url = "$target_root_prefix$url_trim";
							}
						} else {
							$url_without_query = explode('?', $url, 2)[0];

				//* Link to a server with given name and protocol:

							if (false !== strpos($url_without_query, '://')) {
								list(
									$url_domain
								,	$url_domain_last_part
								,	$url_protocol
								,	$url_path
								) =
								get_domain_and_last_part_from_url($url_without_query);

								if ($url_domain_last_part === $target_domain_last_part) {
									$url_path = ltrim($url_path, '/');

									if (array_key_exists($url_protocol, $proxified_protocols)) {
										$url = (

				//* Proxify link to current server with given name and protocol,
				//* replace it with substitute prefix subfolder,
				//* conflate HTTP and HTTPS, but keep apart HTTP and FTP:

											$target_server_substitute
										&&	$url_domain === $target_domain
										&&	$url_protocol[0] === $request_protocol[0]
											? "$target_root_prefix$url_path"

				//* Proxify link to sibling domain, but keep its protocol and name:

											: "$self_root/$url_protocol/$url_domain/$url_path"
										);
									}
								}
							} else

				//* Proxify link relative to current folder, but skip unslashed URLs like "mailto:":

							if (false === strpos(explode('/', $url_without_query, 2)[0], ':')) {
								$url = "$target_root_prefix$target_folder$url";
							}
						}
					}

					return "$match[Before]$match[Quote]$url";
				}

				function get_replaced_content($content) {
					global $pat_url;

					return preg_replace_callback($pat_url, 'get_replaced_url', $content);
				}

			} else {

//* Use multiple replacements:

				$replacements = array(
					array('~(\s\w+=[\'"])([^?#\'">]+/+)?\.+/+~u', '$1$2')
				,	array('~(\s\w+=[\'"])/([^/])|\b'.$target_server.'\b~iu', '$1'.$self_root.'/$2')
				,	array('~(\s\w+=[\'"])//+([^>])~iu', '$1'.$self_root.'/'.$default_target_protocol.'/$2')
				// ,	array('~(\s\w+=[\'"])/([^/>])|\b'.$target_server.'\b~iu', '$1'.$target_root_prefix.'$2')
				// ,	array('~(\s\w+=[\'"])//([^>])~iu', '$1'.$target_path.'$2')
				,	array('~(\s\w+=[\'"])([?]|[^:/?#\'">]+[/?#\'">])~u', '$1'.$self_root.'/'.$target_folder.'$2')
				,	array('~(\s\w+=[\'"])([htps]+)://(([^=\'"/>]+\.)?'.$target_domain_last_part.')~iu', '$1'.$self_root.'/$2/$3')
				);

				function get_replaced_content($content) {
					global $replacements;

					$replaced = $content;

					foreach ($replacements as $replace) {
						$replaced = preg_replace($replace[0], $replace[1], $replaced);
					}

					return $replaced;
				}
			}

//* Autoreplace line by line, may be faster or eat less memory, may be not:

			if (1) {
				$replaced_content = implode(NL, array_map('get_replaced_content', explode(NL, $response_content)));
			} else {

//* Autoreplace all content at once:

				$replaced_content = get_replaced_content($response_content);
			}

			$t2 = microtime();
			$response_content = '<!--
t_start	= '.date(DATE_FORMAT, ($t0 = explode(' ', $t0))[1]).', '.sprintf('%.6f', $t0 = $t0[1] + $t0[0]).'
t_end	= '.date(DATE_FORMAT, ($t1 = explode(' ', $t1))[1]).', '.sprintf('%.6f', $t1 = $t1[1] + $t1[0]).'
t_out	= '.date(DATE_FORMAT, ($t2 = explode(' ', $t2))[1]).', '.sprintf('%.6f', $t2 = $t2[1] + $t2[0]).'
request = '.($t1 - $t0).'
process	= '.($t2 - $t1).'
source size	= '.strlen($response_content).'
processed size	= '.strlen($replaced_content).(isset($replacements) ? '

replacements:

'.trim_info(print_r($replacements, true)) : '').'

request info:

'.trim_info(print_r($response_info, true)).'

response headers:

'.trim_info($response_headers_text).'

-->
'.trim($replaced_content);
			header('Content-Length: '.strlen($response_content));
		}

		die($response_content);
	} else {
		header('HTTP/1.1 404 NO');

		die(
			'<a href="'.$target_request_url.'">'.$target_request_url.'</a> is empty.'
		.NL.	"<br><br>cURL ErrNo:<br>$response_error"
		.NL.	"<br><br>Headers:<br>$response_headers_text"
		.NL.	"<br><br>Content:<br>$response_content"
		.NL.	'<!-- and this is for IE: -->'
		.NL.	str_repeat(' ', 500)
		);
	}
}

no_target:

if (IS_LOCALHOST) {
	var_dump($_SERVER);

	die("
		Debug info:
	<br>	self			= [ $_SERVER[PHP_SELF]		]
	<br>	self_script_name	= [ $_SERVER[SCRIPT_NAME]	]
	<br>	self_document_uri	= [ $_SERVER[DOCUMENT_URI]	]
	<br>	self_request_url	= [ $_SERVER[REQUEST_URI]	]
	<br>	self_protocol		= [ $self_protocol		]
	<br>	self_hostname		= [ $self_hostname		]
	<br>	self_root		= [ $self_root			]
	<br>	referer			= [ $referer			]
	<br>	is_relative_to_referer	= [ $is_relative_to_referer	]
	<br>	is_relative_to_request	= [ $is_relative_to_request	]
	<br>	must_get_raw_content	= [ $must_get_raw_content	]
	<br>	target_root_prefix	= [ $target_root_prefix		]
	<br>	target_url		= [ $target_url			]
	<br>	target_protocol		= [ $target_protocol		]
	<br>	target_server		= [ $target_server		]
	<br>	target_path		= [ $target_path		]
	<br>	target_request_url	= [ $target_request_url		]
	");
}
?>dummy