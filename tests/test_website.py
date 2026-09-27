"""Regression for footnotes in tables being numbered after later paragraphs."""
import re
import unittest
from website.build import render

class WebsiteCitations(unittest.TestCase):
    def test_first_use_order_including_tables_and_repeat(self):
        source='''# Heading

Opening.[^a]

| Work | Note |
| --- | --- |
| Book | Text.[^b] |

After table.[^c] Again.[^a]

## References

[^c]: Third source.
[^b]: Second source.
[^a]: First source.
'''
        body,_=render(source)
        labels=re.findall(r'class="footnote-ref"[^>]*>\[(\d+)\]</a>',body)
        self.assertEqual(labels,['1','2','3','1'])
        self.assertLess(body.index('id="fn:a"'),body.index('id="fn:b"'))
        self.assertLess(body.index('id="fn:b"'),body.index('id="fn:c"'))
        self.assertIn('href="#fnref2:a"',body)

    def test_missing_definition_rejected(self):
        with self.assertRaises(ValueError):
            render('Text.[^a][^missing]\n\n[^a]: Source.\n')
