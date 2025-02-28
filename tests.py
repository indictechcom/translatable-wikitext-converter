import unittest
from app import convert_to_translatable_wikitext, process_double_name_space

class TestTranslatableWikitext(unittest.TestCase):
    
    def test_section_headers(self):
        self.assertEqual(
            convert_to_translatable_wikitext("==HELLO=="),
            "<translate>==HELLO==</translate>"  # Removed the \n\n that was expected
        )

    def test_file_tag_translations(self):
        self.assertEqual(
            convert_to_translatable_wikitext(
                "[[File:landscape.jpg |thumb |left |alt=sunset |Photo of a beautiful landscape]]"
            ),
            "[[File:landscape.jpg |thumb |left | <translate>alt=sunset </translate>|Photo of a beautiful landscape]]"
        )

    def test_internal_and_external_links(self):
        self.assertEqual(
            convert_to_translatable_wikitext(
                "This is a text with an [[internal link]] and an [https://openstreetmap.org external link]."
            ),
            "<translate>This is a text with an [[internal link]] and an [https://openstreetmap.org external link].</translate>"
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
            convert_to_translatable_wikitext("[[link]]"),
            "[[Special:MyLanguage/link|<translate>link</translate>]]"
        )

    def test_multiline_text(self):
        self.assertEqual(
            convert_to_translatable_wikitext("""
                hi iam charan
                <br>
                happy
                """),
            "\n<translate>hi iam charan</translate>\n<br>\n<translate>happy</translate>\n" 
        )

    def test_double_namespace_processing(self):
        self.assertEqual(
            process_double_name_space(
                "[[File:pretty hello word.png|alt=Hello everybody!]], [[File:smiley.png|alt=😂]] How are you?"
            ),
            "[[File:pretty hello word.png| <translate>alt=Hello everybody!</translate>]], [[File:smiley.png| <translate>alt=😂</translate>]] How are you?"
        )
    def test_double_namespace_without_list_case_1(self):
        self.assertEqual(
            process_double_name_space(
                "[[Help]]ing"
            ),
            "[[Special:MyLanguage/Help|<translate>Help</translate>]]<translate>ing</translate>"
        )
    def test_double_namespace_without_list_case_2(self):
        self.assertEqual(
            process_double_name_space(
                "[[Help]] ing"
            ),
            "[[Special:MyLanguage/Help|<translate>Help</translate>]]<translate> ing</translate>"
        )
if __name__ == '__main__':
    unittest.main()