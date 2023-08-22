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
	'computers',
	'culture',
	'index',
	'personal_feed',
	'science',
	'society',
	'sport',
	'world',
);

define('COLOR_STEP', 2);
define('COLOR_LENGTH', 6);
define('COLOR_PADDING', '0');

foreach ($words as $word) {
	$hash = md5($word);
	$hash2 = $hash.$hash;
	$cut_stop = strlen($hash);
	$color_pick = 0;
	$color_pick_lightness = 0;

	echo "
	<div>
		<p>$word: $hash</p>
		<table>
			<tr>";

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

				// $L = $R + $G + $B;
				$L = ($R * 1.5) + ($G * 2.2) + $B;

				// (1.5 + 2.2 + 1) * 255 / 3 = 399.5

				if ($L > 400 && $color_pick_lightness < $L) {
					$color_pick = $color_hex;
					$color_pick_lightness = $L;
				}

				echo "
				<td style='background-color: #$color_hex' title='L=$L'>$color_hex</td>";
			} else {
				echo "
				<td>$cut_part</td>";
			}
		}

		if (strlen($prefix) > 0) {
			echo "
			</tr><tr>";

			$next_prefix_length = strlen($prefix) - COLOR_STEP;
			$prefix = (
				$next_prefix_length > 0
				? str_repeat(COLOR_PADDING, $next_prefix_length)
				: ''
			);
			$suffix = str_repeat(COLOR_PADDING, COLOR_LENGTH - $cut_len - $next_prefix_length);

			goto next_prefix;
		} else {
			echo (
				$cut_len < COLOR_LENGTH
				? "
			</tr><tr>"
				: "
			</tr>
		</table>
		<div style='background-color: #$color_pick'>Color pick: $color_pick, lightness: $color_pick_lightness</div>
	</div>"
			);
		}
	}
}

?>
</body>
</html>