<!doctype html>
<html>
<head>
	<meta charset="utf-8">
	<title>Get the brightest color hex from each word hash.</title>
	<style>
		div { background-color: lightgray; margin: 1em 0; padding: 1em; }
		table { background-color: black; }
	</style>
</head>
<body>
<?php

$words = array(
	'auto',
	'business',
	'computers',
	'culture',
	'incident',
	'index',
	'personal_feed',
	'politics',
	'science',
	'society',
	'sport',
	'world',
);

define('PAD_UP', 3);
define('COLOR_LIGHT_MIN', 400);	//* <- (1.5 + 2.2 + 1) * 255 / 3 = 399.5
define('COLOR_STEP', 2);
define('COLOR_LENGTH', 6);
define('COLOR_PADDING', '0');
define('COLOR_PADDING_UP', 'f');
define('NEW_ROW', '
			</tr><tr>');
define('EMPTY_ROW_PAT', '~\s*<tr>\s*</tr>~i');

function get_color_lightness ($color_hex) {
	list($R, $G, $B) = array_map('hexdec', str_split($color_hex, COLOR_STEP));

	return ($R * 1.5) + ($G * 2.2) + $B;
	// return $R + $G + $B;
}

function get_color_output ($cut_part, $prefix = '', $suffix = '', $index = 0) {
	global $color_pick, $color_pick_lightness;

	if ($cut_part) {
		$color_hex = "$prefix$cut_part$suffix";
		$L = get_color_lightness ($color_hex);

		if (
			$L > COLOR_LIGHT_MIN
		&&	(
				!$color_pick[$index]
			||	$L > $color_pick_lightness[$index]
			)
		) {
			$color_pick[$index] = $color_hex;
			$color_pick_lightness[$index] = $L;
		}

		return "
				<td style='background-color: #$color_hex' title='L=$L'>$color_hex</td>";
	} else {
		return "
				<td>$cut_part</td>";
	}
}

foreach ($words as $word) {
	$hash = md5($word);
	$hash2 = $hash.$hash;
	$cut_stop = strlen($hash);
	$color_pick = array(0);
	$color_pick_lightness = array(0);
	$output = array("
	<div>
		<p>$word: $hash</p>
		<table>
			<tr>");

	for (
		$cut_len = COLOR_STEP;
		$cut_len <= COLOR_LENGTH;
		$cut_len += COLOR_STEP
	) {
		$prefix = str_repeat(COLOR_PADDING, COLOR_LENGTH - $cut_len);
		$suffix = '';
next_prefix:
		if ($is_color_padded = PAD_UP && !!($prefix || $suffix)) {

			$prefix_up = str_replace(COLOR_PADDING, COLOR_PADDING_UP, $prefix);
			$suffix_up = str_replace(COLOR_PADDING, COLOR_PADDING_UP, $suffix);
		}

		for (
			$cut_start = 0;
			$cut_start < $cut_stop;
			$cut_start += COLOR_STEP
		) {
			$cut_part = substr($hash2, $cut_start, $cut_len);
			$output[0] .= get_color_output ($cut_part, $prefix, $suffix);

			if ($is_color_padded) {
				$index = ($cut_len > COLOR_STEP ? 1 : 2);

				if ($index & PAD_UP) {
					$output[$index] .= get_color_output ($cut_part, $prefix_up, $suffix_up, $index);
				}
			}
		}

		foreach ($output as &$each) {
			$each .= NEW_ROW;
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

		if ($cut_len >= COLOR_LENGTH) {
			$output_rows = '';
			$output_pick = '';

			ksort($color_pick);

			foreach ($color_pick as $index => $color_hex) {
				$output_rows .= $output[$index].NEW_ROW;
				$output_pick .= "
			<div style='background-color: #$color_hex'>Color pick $index: $color_hex, lightness: {$color_pick_lightness[$index]}</div>";
			}

			echo preg_replace(EMPTY_ROW_PAT, '', "$output_rows
			</tr>
		</table>$output_pick
	</div>");
		}
	}
}

?>
</body>
</html>