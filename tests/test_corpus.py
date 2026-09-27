"""Data-integrity tests: malformed timings and meaningful repeated speech."""
import unittest
from scripts.corpus import normalize_cues, parse_srt


class Captions(unittest.TestCase):
    def test_rolling_line_carryover(self):
        raw = '1\n00:00:00,000 --> 00:00:01,990\n \nالسلام عليكم\n\n2\n00:00:01,990 --> 00:00:02,000\nالسلام عليكم\n \n\n3\n00:00:02,000 --> 00:00:04,000\nالسلام عليكم\nعن الجن\n'
        result = normalize_cues(parse_srt(raw))
        self.assertEqual([s['text'] for s in result], ['السلام عليكم', 'عن الجن'])
        self.assertEqual(result[1]['cue'], 3)

    def test_repetition_after_gap_and_inside_line_is_kept(self):
        cues = [{'cue': 1, 'start': 0, 'end': 1, 'text': 'نعم نعم'},
                {'cue': 2, 'start': 3, 'end': 4, 'text': 'نعم نعم'}]
        self.assertEqual([s['text'] for s in normalize_cues(cues)], ['نعم نعم', 'نعم نعم'])

    def test_non_monotonic_starts_rejected(self):
        with self.assertRaisesRegex(ValueError, 'monotonic'):
            parse_srt('1\n00:00:03,000 --> 00:00:04,000\nabc\n\n2\n00:00:01,000 --> 00:00:02,000\ndef')

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            parse_srt('')

    def test_negative_duration_rejected(self):
        with self.assertRaisesRegex(ValueError, 'non-positive'):
            parse_srt('1\n00:00:04,000 --> 00:00:03,000\nabc')


if __name__ == '__main__':
    unittest.main()
