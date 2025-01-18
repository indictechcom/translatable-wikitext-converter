import unittest
from app import convert_to_translatable_wikitext, process_double_name_space
class TestTranslatableWikitext(unittest.TestCase):
    
    def test_section_headers(self):
        self.assertEqual(
            convert_to_translatable_wikitext("==HELLO=="),
            "<translate>==HELLO==\n\n</translate>"
        )
    def test_file_tag_translations(self):
        self.assertEqual(
            convert_to_translatable_wikitext(
                "[[File:landscape.jpg |thumb |left |alt=sunset |Photo of a beautiful landscape]]"
            ),
            "[[File:landscape.jpg |thumb |left |alt=<translate>sunset </translate>|Photo of a beautiful landscape]]"
        )
    def test_internal_and_external_links(self):
        self.assertEqual(
            convert_to_translatable_wikitext(
                "This is a text with an [[internal link]] and an [https://openstreetmap.org external link]."
            ),
            "This is a text with an [[<tvar name=1>Special:MyLanguage/internal link</tvar>|internal link]] and an [<tvar name=\"url\">https://openstreetmap.org</tvar> external link]."
        )
    def test_category_with_translation(self):
        self.assertEqual(
            convert_to_translatable_wikitext("[[Category:Wikipedia]]"),
            "\n[[Category:Wikipedia{{#translation:}}]]\n"
        )
    def test_notoc_preserved(self):
        self.assertEqual(
            convert_to_translatable_wikitext("__NOTOC__"),
            "__NOTOC__"
        )
    def test_simple_internal_link(self):
        self.assertEqual(
            convert_to_translatable_wikitext("[[link]]"),
            "\n[[Special:MyLanguage/link|<translate>link</translate> ]]\n"
        )
    def test_multiline_text(self):
        self.assertEqual(
            convert_to_translatable_wikitext("""
                hi iam charan
                <br>
                happy
                """),
            "<translate>hi iam charan</translate>\n<br>\n<translate>happy</translate>"
        )
    def test_double_namespace_processing(self):
        self.assertEqual(
            process_double_name_space(
                "[[File:pretty hello word.png|alt=Hello everybody!]], [[File:smiley.png|alt=🙂]] How are you?"
            ),
            "[[File:pretty hello word.png|alt=<translate>Hello everybody!</translate>]], [[File:smiley.png|alt=<translate>🙂</translate>]] How are you?"
        )
    def test_list_with_translate_tags(self):
        self.assertEqual(
            convert_to_translatable_wikitext(
                "* This is a long list:** There are more than 160 words in this list,** or there are more than 8 items."
                "* So it is better to split it in several smaller units.* But we must exclude bullet points from "
                "translate tags to keep the list accessible."
            ),
            "*<translate> This is a long list</translate>:\n\n**<translate> There are more than 160 words in this list,</translate>\n\n**<translate> or there are more than 8 items.* So it is better to split it in several smaller units.* But we must exclude bullet points from translate tags to keep the list accessible.</translate>"
        )
if __name__ == '__main__':
    unittest.main()