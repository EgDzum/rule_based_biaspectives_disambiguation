import unittest
from tools import Disambiguate
import pymorphy3


class TestDisambiguate(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = Disambiguate()

    def test_tokenize(self):
        self.assertListEqual(self.analyzer.tokenize('мама мыла раму'), ['мама', 'мыла', 'раму'])
        self.assertListEqual(self.analyzer.tokenize(''), [])
        self.assertListEqual(self.analyzer.tokenize('папа мыл раму.'), ['папа', 'мыл', 'раму', '.'])

    def test_premark_text(self):
        tokens1 = self.analyzer.tokenize('мама мыла раму')
        premarked = self.analyzer.premark_text(tokens1)
        self.assertIsInstance(premarked[0], pymorphy3.analyzer.Parse)

    # def test_biaspective(self):
    #     pass
    #
    # def test_verb_gram_prof(self):
    #     pass


if __name__ == '__main__':
    unittest.main()
