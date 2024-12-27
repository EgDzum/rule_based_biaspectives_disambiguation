import unittest
import pymorphy3
from tools import Disambiguate


class TestDisambiguate(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = Disambiguate()
        self.tokens = self.analyzer.tokenize('мама мыла раму')
        self.premarked = self.analyzer.premark_text(self.tokens)

    def test_tokenize(self):
        self.assertListEqual(self.analyzer.tokenize('мама мыла раму'), ['мама', 'мыла', 'раму'])
        self.assertListEqual(self.analyzer.tokenize(''), [])
        self.assertListEqual(self.analyzer.tokenize('папа мыл раму.'), ['папа', 'мыл', 'раму', '.'])

    def test_premark_text(self):
        self.assertIsInstance(self.premarked[0], pymorphy3.analyzer.Parse)

    def test_findall_needed(self):
        self.assertIsInstance(self.analyzer.findall_needed(self.premarked), tuple, 'Output should be stored as a tuple')
        self.assertIsInstance(
            self.analyzer.findall_needed(self.premarked)[0][0],
            pymorphy3.analyzer.Parse,
            'First value of output must be pymorphy object of type Parse'
        )
        self.assertIsInstance(
            self.analyzer.findall_needed(self.premarked)[0][1],
            int,
            'Second value of output must be index of type int'
        )

    # def test_biaspective(self):
    #     pass
    #
    # def test_verb_gram_prof(self):
    #     pass


if __name__ == '__main__':
    unittest.main()
