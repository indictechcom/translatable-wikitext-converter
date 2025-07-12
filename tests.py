import unittest
from app import convert_to_translatable_wikitext, process_double_brackets

class TestTranslatableWikitext(unittest.TestCase):

    def test_section_headers(self):
        self.assertEqual(
            convert_to_translatable_wikitext("==HELLO=="),
            "<translate>==HELLO==</translate>"  # Removed the \n\n that was expected
        )

    def test_file_tag_translations(self):
        self.assertEqual(
            convert_to_translatable_wikitext(
                '[[File:landscape.jpg |thumb |left | alt=sunset |Photo of a beautiful landscape]]'
            ),
            '[[File:landscape.jpg|thumb|{{dirstart}}|alt=<translate>sunset</translate>|<translate>Photo of a beautiful landscape</translate>]]'
        )

    def test_internal_and_external_links(self):
        self.assertEqual(
            convert_to_translatable_wikitext(
                'This is a text with an [[internal link]] and an [https://openstreetmap.org external link].'
            ),
            '<translate>This is a text with an [[<tvar name=0>Special:MyLanguage</tvar>/Internal link|internal link]] and an [<tvar name=url0>https://openstreetmap.org</tvar> external link].</translate>'
        )
    
    def test_category_with_translation(self):
        self.assertEqual(
            convert_to_translatable_wikitext("[[Category:Wikipedia]]"),
            "[[Category:Wikipedia{{#translation:}}]]"
        )
    
    def test_notoc_preserved(self):
        self.assertEqual(
            convert_to_translatable_wikitext("__NOTOC__"),
            "__NOTOC__"
        )
    
    def test_simple_internal_link(self):
        self.assertEqual(
            convert_to_translatable_wikitext('[[link]]'),
            '<translate>[[<tvar name=0>Special:MyLanguage</tvar>/Link|link]]</translate>'
        )
    
    def test_multiline_text(self):
        self.assertEqual(
            convert_to_translatable_wikitext('\nhi iam charan\n<br>\nhappy\n\n'),
            '\n<translate>hi iam charan</translate>\n<br>\n<translate>happy</translate>\n\n' 
        )
    
    def test_double_namespace_processing(self):
        self.assertEqual(
            convert_to_translatable_wikitext(
                '[[File:pretty hello word.png | alt=Hello everybody!]] [[File:smiley.png|alt=🙂]] How are you?'
            ),
            '[[File:pretty hello word.png|alt=<translate>Hello everybody!</translate>]] <translate><tvar name=icon0>[[File:smiley.png|alt=🙂]]</tvar> How are you?</translate>'
        )
    
    def test_double_namespace_without_list_case_1(self):
        self.assertEqual(
            convert_to_translatable_wikitext(
                '[[Help]]ing'
            ),
            '<translate>[[<tvar name=0>Special:MyLanguage</tvar>/Help|Help]]ing</translate>'
        )
    
    def test_double_namespace_without_list_case_2(self):
        self.assertEqual(
            convert_to_translatable_wikitext(
                '[[Help]] ing'
            ),
            '<translate>[[<tvar name=0>Special:MyLanguage</tvar>/Help|Help]] ing</translate>'
        )

    def test_template_simple(self):
        self.assertEqual(
            convert_to_translatable_wikitext("{{Template Name}}"),
            "{{Template Name}}"
        )

    def test_template_with_parameters(self):
        self.assertEqual(
            convert_to_translatable_wikitext("{{Template|param1=Value 1|Value 2}}"),
            "{{Template|param1=Value 1|Value 2}}"
        )

    def test_template_nested_in_text(self):
        self.assertEqual(
            convert_to_translatable_wikitext('Some text with {{a template here}} and more text.'),
            '<translate>Some text with</translate> {{A template here}} <translate>and more text.</translate>'
        )

    def test_nowiki_tag(self):
        self.assertEqual(
            convert_to_translatable_wikitext("Some text with <nowiki>[[Raw link]]</nowiki> content."),
            "<translate>Some text with</translate> <nowiki><translate>[[Raw link]]</translate></nowiki> <translate>content.</translate>"
        )
    
    def test_blockquote_tag(self):
        self.assertEqual(
            convert_to_translatable_wikitext("<blockquote>This is a quote.</blockquote>"),
            "<blockquote><translate>This is a quote.</translate></blockquote>"
        )

    def test_poem_tag(self):
        self.assertEqual(
            convert_to_translatable_wikitext("<poem>Line 1\nLine 2</poem>"),
            "<poem><translate>Line 1\nLine 2</translate></poem>"
        )

    def test_code_tag_with_tvar(self):
        # Assuming process_code_tag assigns tvar names sequentially starting from 0
        self.assertEqual(
            convert_to_translatable_wikitext("Here is <code>some code</code> for you."),
            "<translate>Here is <code><tvar name=code0>some code</tvar></code> for you.</translate>"
        )

    def test_div_tag(self):
        self.assertEqual(
            convert_to_translatable_wikitext("<div>Div content here.</div>"),
            "<div><translate>Div content here.</translate></div>"
        )

    def test_hiero_tag(self):
        self.assertEqual(
            convert_to_translatable_wikitext("<hiero>hieroglyphics</hiero>"),
            "<hiero><translate>hieroglyphics</translate></hiero>"
        )

    def test_sub_sup_tags(self):
        self.assertEqual(
            convert_to_translatable_wikitext("H<sub>2</sub>O and E=mc<sup>2</sup>"),
            "<translate>H</translate><sub><translate>2</translate></sub><translate>O and E=mc</translate><sup><translate>2</translate></sup>"
        )

    def test_math_tag(self):
        self.assertEqual(
            convert_to_translatable_wikitext("<math>x^2 + y^2 = z^2</math>"),
            "<math>x^2 + y^2 = z^2</math>"
        )

    def test_small_tag(self):
        self.assertEqual(
            convert_to_translatable_wikitext("<small>Small text</small>"),
            "<small><translate>Small text</translate></small>"
        )
  
    def test_image_with_upright(self):
        self.assertEqual(
            convert_to_translatable_wikitext("[[File:Example.jpg|upright=1.5|A larger image]]"),
            "[[File:Example.jpg|upright=1.5|<translate>A larger image</translate>]]"
        )

    def test_multiple_elements_in_one_line(self):
        self.assertEqual(
            convert_to_translatable_wikitext("Hello world! [[Link]] {{Template}} [https://meta.wikimedia.org/wiki/Main_Page Home]"),
            '<translate>Hello world! [[<tvar name=0>Special:MyLanguage</tvar>/Link|Link]]</translate> {{Template}} <translate>[<tvar name=url0>https://meta.wikimedia.org/wiki/Main_Page</tvar> Home]</translate>'
        )

    def test_text_around_br_tag(self):
        self.assertEqual(
            convert_to_translatable_wikitext("First line.<br>Second line."),
            "<translate>First line.</translate><br><translate>Second line.</translate>"
        )

    def test_empty_string_input(self):
        self.assertEqual(
            convert_to_translatable_wikitext(""),
            ""
        )
    
    def test_whitespace_only_input(self):
        self.assertEqual(
            convert_to_translatable_wikitext("   \n\t "),
            "   \n\t "
        )

    def test_list_items(self):
        self.assertEqual(
            convert_to_translatable_wikitext("* Item 1\n** Sub-item 1.1\n* Item 2"),
            "* <translate>Item 1</translate>\n** <translate>Sub-item 1.1</translate>\n* <translate>Item 2</translate>\n"
        )

    def test_definition_list(self):
        self.assertEqual(
            convert_to_translatable_wikitext(";Term\n:Definition\n:Description"),
            "; <translate>Term</translate>\n: <translate>Definition</translate>\n: <translate>Description</translate>\n"
        )

if __name__ == '__main__':
    unittest.main(exit=False, failfast=True)
