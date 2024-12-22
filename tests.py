import unittest 

from app import convert_to_translatable_wikitext
from app import process_double_name_space
class TestClass(unittest.TestCase):
    def test_section(self):
        self.assertEqual(convert_to_translatable_wikitext("==HELLO=="),"<translate>==HELLO==</translate>")
    def test_hastag(self):
        self.assertEqual(convert_to_translatable_wikitext("[[File:landscape.jpg |thumb |left |alt=sunset |Photo of a beautiful landscape]]"),"<translate>[[File:English Wikipedia screenshot.png|thumb|Wikipedia homepage]]</translate>")
    def test_hastag(self):
         self.assertEqual(convert_to_translatable_wikitext("This is a text with an [[internal link]] and an [https://openstreetmap.org external link]."),"This is a text with an [[<tvar name=1>Special:MyLanguage/internal link</tvar>|internal link]] and an [<tvar name=\"url\">https://openstreetmap.org</tvar> external link].") 
    def test_hastag2(self):
         self.assertEqual(convert_to_translatable_wikitext(">[[Category:Wikipedia]]"),"<tranlate>[[Category:Wikipedia{{#translation:}}]]</translate>")
    def test_hastag3(self):
         self.assertEqual(convert_to_translatable_wikitext("__NOTOC__"),"__NOTOC__")
    def test_hastag4(self):
         self.assertEqual(convert_to_translatable_wikitext("[[link]]"),"[[<special:my language/link|<translate>link</translate>]]")
    def test_hastag5(self):
         self.assertEqual(convert_to_translatable_wikitext("""
                hi iam charan
                <br>
                happy
                """),
                """<translate>hi iam charan</translate>
                <br>
                <translate>happy</translate>
                """)
    def test_doublenamespace(self):
         self.assertEqual(process_double_name_space("[[File:pretty hello word.png|alt=Hello everybody!]], [[File:smiley.png|alt=🙂]] How are you?"),"[[File:pretty hello word.png|alt=Hello everybody!]], <tvar name=\"icon\">[[File:smiley.png|alt=🙂]]</tvar> How are you?)")
    def test_hastag6(self):
         self.assertEqual(convert_to_translatable_wikitext("* This is a long list:** There are more than 160 words in this list,** or there are more than 8 items.* So it is better to split it in several smaller units.* But we must exclude bullet points from translate tags to keep the list accessible."),"""
         * <translate>This is a long list:</translate>
** <translate>There are more than 160 words in this list,</translate>
** <translate>or there are more than 8 items.</translate>
* <translate>So it is better to split it in several smaller units.</translate>
* <translate>But we must exclude bullet points from translate tags to keep the list accessible.</translate>    
         """)
     
if __name__ == '__main__':

    unittest.main()