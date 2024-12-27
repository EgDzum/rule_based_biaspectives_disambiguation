import unittest
from rule_based_biaspectives_disambiguation import LoadConstants


class TestLoadConstants(unittest.TestCase):
    def setUp(self) -> None:
        drive_link = 'C:/Users/egord/PycharmProjects/pythonProject41/words'
        self.variables = LoadConstants(drive_link)

    def test_input(self):
        self.assertIsInstance(self.variables.VERBS, set, 'Verbs should be stored as a set')
        self.assertIsInstance(self.variables.PHASE_V, set, 'Phase verbs should be stored as a set')
        self.assertIsInstance(self.variables.MODAL_V, set, 'Modal verbs should be stored as a set')
        self.assertIsInstance(self.variables.MODAL_W, set, 'add later')
        self.assertIsInstance(self.variables.MODIFIERS_IMPF_PRE, set, 'add later')
        self.assertIsInstance(self.variables.MODIFIERS_IMPF_POST, set, 'add later')
        self.assertIsInstance(self.variables.PARTICLES_IMPF_PRE, set, 'add later')
        self.assertIsInstance(self.variables.MODIFIERS_PERF_PRE, set, 'add later')

    def test_gram_prop_cat(self):
        gram_prop = {'class': {'GRND', 'INFN', 'PRTF', 'VERB'}}
        gram_prop_inverted = {'VERB': 'class', 'INFN': 'class', 'PRTF': 'class', 'GRND': 'class'}

        self.assertEqual(self.variables.gram_prop_cat(gram_prop), gram_prop_inverted)


if __name__ == '__main__':
    unittest.main()
