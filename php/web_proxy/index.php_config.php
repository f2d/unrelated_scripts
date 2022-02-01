<?php

//* Change this to your actual domain/address of this script host:

$default_hostname = 'www.example.com';
$default_protocol = 'http';
$default_useragent = $_SERVER['HTTP_USER_AGENT'] ?? 'Mozilla/5.0 (something)';



//* Use any name defined here to access the proxy script.
//* May be a real domain or a custom dummy from /etc/hosts:

$allowed_hostnames = array(
	$default_hostname
,	'localhost'
// ,	'etc.host'
// ,	'www2.example.com'
);



//* If any cookies are defined here, require any one as name + password for the proxy script:

$allowed_cookies = array(
//	'example-pass-key-name' => 'example-pass-key-value'
// ,	'q' => 'q'
// ,	'2022' => '2022-01-29 04:38:42'
);



//* Folder to store cookies given by target servers, etc:

$data_dirs = array(
	'linux' => '/srv/www/data/web_proxy'
,	'windows' => 'w:/home/localhost/cgi/data/web_proxy'
);



//* Folder to check trusted certificates:

$ssl_certs_dirs = array(
	'linux' => '/etc/ssl/certs'
,	'windows' => 'w:/ssl/curl.se/ca'
);



$proxified_protocols = array(

//* Proxified protocols used as subfolder before target site name:

	'ftp'   => 0
,	'ftps'  => 0
,	'http'  => 0
,	'https' => 0

//* Usage examples:
//*	https://proxy.hostname/?/http/target.hostname/
//*	https://proxy.hostname/https/target.hostname/
//*	https://proxy.hostname/http/target.hostname/path/to/file.ext?arg=value&etc

//* Proxified website shorthands:

,	'l'   => 'http://localhost/'
// ,	'ii'  => 'https://iichan.hk/'
// ,	'dan' => 'https://danbooru.donmai.us/'

//* Usage examples with content URL autoreplacement:
//*	https://proxy.hostname/?/l/
//*	https://proxy.hostname/l/
//*	https://proxy.hostname/ii/b/
//*	https://proxy.hostname/dan/post/123

//* Usage examples with content as is:
//*	https://proxy.hostname/?/raw/l/index.php
//*	https://proxy.hostname/raw/l/index.php

);
