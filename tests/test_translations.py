"""Prevent silent translation gaps, stale source mappings and false completion."""
import hashlib
import json
import unittest

from scripts.corpus import parse_srt
from scripts.translations import prepare, validate_segments


class Translations(unittest.TestCase):
    def setUp(self):
        self.source = [{'cue': 1, 'start': 0.24, 'end': 2.55, 'text': 'أ'},
                       {'cue': 3, 'start': 2.56, 'end': 5.59, 'text': 'ب'},
                       {'cue': 5, 'start': 5.6, 'end': 8.589, 'text': 'ج'}]
        self.data = json.dumps(self.source).encode()
        self.original = b'original-srt-fixture'
        self.draft = {'episode_id': '3sVCCYYmuzU', 'complete': False,
                      'source_segments_sha256': hashlib.sha256(self.data).hexdigest(),
                      'source_srt_sha256': hashlib.sha256(self.original).hexdigest(),
                      'segments': [{'source_segment_index': 0, 'text': 'First.'},
                                   {'source_segment_index': 2, 'text': 'Third.'}]}

    def test_partial_keeps_original_timing_and_exposes_first_gap(self):
        text, manifest = prepare(self.draft, self.data, self.original)
        cues = parse_srt(text)
        self.assertEqual([c['start'] for c in cues], [0.24, 5.6])
        self.assertEqual(manifest['next_source_segment_index'], 1)
        self.assertFalse(manifest['complete_coverage'])
        self.assertEqual(manifest['cue_map'][1]['source_cue'], 5)

    def test_false_completion_rejected(self):
        self.draft['complete'] = True
        with self.assertRaisesRegex(ValueError, 'untranslated'):
            validate_segments(self.draft, self.source)

    def test_duplicate_source_rejected(self):
        self.draft['segments'].append(self.draft['segments'][-1])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate_segments(self.draft, self.source)

    def test_stale_normalization_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Normalized source hash'):
            prepare(self.draft, self.data + b' ', self.original)

    def test_full_coverage_does_not_imply_editorial_review(self):
        self.draft['segments'].insert(1, {'source_segment_index': 1, 'text': 'Second.'})
        _, manifest = prepare(self.draft, self.data, self.original)
        self.assertTrue(manifest['complete_coverage'])
        self.assertIsNone(manifest['reviewed_at'])
        self.assertIsNone(manifest['next_source_segment_index'])


if __name__ == '__main__':
    unittest.main()
