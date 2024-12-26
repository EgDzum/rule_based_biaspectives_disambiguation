from pathlib import Path
from itertools import zip_longest
from pymorphy3 import MorphAnalyzer
from pymorphy3.tokenizers import simple_word_tokenize


def singleton(cls):
    instances = {}

    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return getinstance


@singleton
class LoadConstants:

    def __init__(self, dir):
        self.path = Path(dir)
        self.IMPF, self.PERF = 'impf', 'perf'
        self.VERBS = self.open_file(self.path / 'biaspectives_relevant_list.txt') # set

        self.PHASE_V = self.open_file(self.path / self.IMPF / 'phase_n_byt_verbs.txt') # dict
        self.MODAL_V = self.open_file(self.path / self.IMPF / 'neg_modal_verbs.txt') # ADD
        self.MODAL_W = self.open_file(self.path / self.IMPF / 'neg_modal.txt')

        self.MODIFIERS_IMPF_PRE = self.open_file(self.path / self.IMPF / 'modifiers_impf_pre.txt')
        self.MODIFIERS_IMPF_POST = self.open_file(self.path / self.IMPF / 'modifiers_impf_pre.txt')
        self.PARTICLES_IMPF_PRE = self.open_file(self.path / self.IMPF /'particles_imp.txt')

        self.MODIFIERS_PERF_PRE = self.open_file(self.path / self.PERF / 'modifiers_perf_pre.txt')

        self.gram_cat_prop = {
            'class': {'VERB', 'INFN', 'PRTF', 'GRND'},
            'case': {'nomn', 'gent', 'gen2' 'datv', 'accs', 'ablt', 'loc1', 'loc2'},
            'voice': {'actv', 'pasv'},
            'mood': {'indc', 'impr'},
            'tense': {'past', 'pres', 'futr'},
            'aspect': {self.IMPF, self.PERF},
            'transitivity': {'tran', 'intr'},
            'number': {'sing', 'plur'},
            'person': {'1per', '2per', '3per'},
            'gender': {'masc', 'femn', 'neut'}
        }

    def open_file(self, path):
        with open(path, 'r', encoding='utf8') as f:
            return set(f.read().split())

    def gram_prop_cat(self, gram_cat_prop_d):
        empty_placeholder = tuple()
        inverted_dict = {}
        for k, v in gram_cat_prop_d.items():
            inverted_dict.update(dict(zip_longest(v, empty_placeholder, fillvalue=k)))
        return inverted_dict


class Disambiguate:
    PATH = 'C:/Users/egord/PycharmProjects/pythonProject41/words'
    CONS = LoadConstants(PATH)
    IMPF, PERF = CONS.IMPF, CONS.PERF
    GRAM_CAT_PROP = CONS.gram_cat_prop
    GRAM_PROP_CAT = CONS.gram_prop_cat
    VERBS = CONS.VERBS

    PHASE, MODAL_V, MODAL_W = CONS.PHASE_V, CONS.MODAL_V, CONS.MODAL_W

    MODIFIERS_IMPF_PRE = CONS.MODIFIERS_IMPF_PRE
    MODIFIERS_PERF_PRE = CONS.MODIFIERS_PERF_PRE

    MODIFIERS_IMPF_POST = CONS.MODIFIERS_IMPF_POST

    PARTICLES_IMPF_PRE = CONS.PARTICLES_IMPF_PRE

    def __init__(self):
        self.ma = MorphAnalyzer()

    def tokenize(self, text):
        return simple_word_tokenize(text)

    def premark_text(self, tokens):
        return tuple(self.ma.parse(t)[0] for t in tokens if t)

    def proccess_seq(self, premarked):
        return {t: inx for inx, t in enumerate(premarked)}

    def findall_needed(self, premarked):
        needed = {'VERB', 'INFV', 'PRTF', 'GRND',
                  'ADVB ', 'PRCL', 'NUMB', 'NUMR', 'PNCT'} # число слово
        return tuple((t, inx) for inx, t in enumerate(premarked) if
                     t.tag[:4] in needed or t.word == 'за')

    def biaspective(self, tokens_needed):
        return next(((t, inx) for t, inx in tokens_needed
                    if t.normal_form in Disambiguate.VERBS), None)

    def verb_gram_prof(self, verb_parsed, verb_index):
        bv_gram = {
            'inx': verb_index, 'word': verb_parsed.word,
            'lemma': verb_parsed.normal_form
        }
        class_, *gram = verb_parsed.tag.split(',')
        bv_gram['class'] = class_

        for prop in gram:
            if ' ' in prop:
                gram.extend(prop.split())
                gram.pop(prop.index())

        for prop in gram:
            for gram_cat in Disambiguate.GRAM_CAT_PROP:
                if prop in Disambiguate.GRAM_CAT_PROP.get(gram_cat, ''):
                    bv_gram[gram_cat] = prop
        return bv_gram

    def split_sent(self, tokens_needed, by):
        left = tuple(reversed(tokens_needed[:by[-1]]))
        right = tuple(tokens_needed[by[-1] + 1])
        return left, right

    def __process_candidates(self, bi_verb, verb_cand, toks_inx_kv):
        verb_cand = self.verb_gram_prof(verb_cand, toks_inx_kv[verb_cand])

    def process_left(self, left, bv_gram):
        prev_modal, status_no_answer, punct_prev, prev_neg = False, False, False, False

        left_len = len(left)
        for t, inx in left: # проверь потом, какой тут индекс, токена из
        # фильтрованной последовательности или исходной. Должно быть исходной
            tok_pos = t.tag[:4]
            # 10, 9 (-8), 10; 10 - 8 - 1 = 1
            # 10, 8 (-7), 10; 10 - 7 - 1 = 2

            # iterating over reversed sequence
            if bv_gram['inx'] + ~inx - 1 == 1:

                if (tok_pos in ('VERB', 'INFV')) \
                and bv_gram['class'] == 'INFV':
                    if t.normal_form in Disambiguate.PHASE:
                        return Disambiguate.IMPF, True
                    elif t.normal_form in Disambiguate.MODAL_V or t.word in Disambiguate.MODAL_W:
                        prev_modal = True
                    else:
                        status_no_answer = True

                elif tok_pos == 'ADVB':
                    if t.normal_form in Disambiguate.MODIFIERS_IMPF_PRE:
                        return Disambiguate.IMPF, True
                    elif t.normal_form in Disambiguate.MODIFIERS_PERF_PRE and \
                    'past' in bv_gram['tense']:
                        return Disambiguate.PERF, True

                elif tok_pos == 'PRCL':
                    if t.word == 'не':
                        if 'impr' in bv_gram['mood']:
                            return Disambiguate.IMPF, True
                        else:
                            prev_neg = True
                    elif t.word in ('еще', 'ещё') and \
                    bv_gram['tense'] in ('pres', 'futr'):
                        return Disambiguate.IMPF, True

                elif tok_pos == 'PNCT':
                    punct_prev = True

            elif bv_gram['inx'] + ~inx - 1 == 2:
                if tok_pos == 'PRCL' and t.word == 'не' and prev_modal:
                    return Disambiguate.IMPF, True
                else:
                    modal_before = True
                    prev_modal = False
                    if tok_pos == 'PRCL' and t.word in ('еще', 'ещё') and \
                    prev_neg and bv_gram['tense'] in ('pres', 'futr'):
                        return Disambiguate.IMPF, True
                    else:
                        if tok_pos == 'ADVB' and prev_neg:
                            if t.normal_form in Disambiguate.MODIFIERS_IMPF_PRE:
                                return Disambiguate.IMPF, True
                            elif t.normal_form in Disambiguate.MODIFIERS_PERF_PRE and \
                            'past' in bv_gram['tense']:
                                return Disambiguate.PERF, True
                        prev_neg = False

            if bv_gram['inx'] - inx - left_len >= 2:
                if tok_pos in ('VERB', 'INFV') and not modal_before:
                    # homogenous sentence members
                    bv_aspect = Disambiguate.__process_candidates(bv_gram, t) # переиначить
                    return bv_aspect, True
                else:
                    return "_", True

    # def process_right(self, right, bv_gram):
    #     right_len = len(right)
    #     za_before,  = False
    #
    #     for t, inx in right:
    #         if t.word == 'за':
    #             pass
    #         if inx - bv_gram['inx'] == 1:
    #             if tok_pos == 'ADVB':
    #                 if t.normal_form in Disambiguate.MODIFIERS_IMPF_POST:
    #                     return Disambiguate.IMPF, True
    #                 elif t.normal_form in Disambiguate.MODIFIERS_PERF_PRE and \
    #                 'past' in bv_gram['tense']:
    #                     return Disambiguate.PERF, True

    # переписать с бв_грем_проф
    def define_aspect(self, bv, left, right):
        if bv['class'] == 'IMPV':
            pre_bv_res, success = Disambiguate.process_left(bv, left)
            if not success:
                post_bv_res, success = Disambiguate.process_right(bv, right)
        else:
            post_bv_res, success = Disambiguate.process_right(bv, right)
            if not success:
                pre_bv_res, success = Disambiguate.process_left(bv, left)


    @classmethod
    def process(self, text):
        tokens = Disambiguate.tokenize(text)
        premarked = Disambiguate.premark_text(tokens)

        toks_inx_kv = Disambiguate.proccess_seq(premarked)
        tokens_needed = Disambiguate.findall_needed(toks_inx_kv)

        bv = Disambiguate.biaspective(tokens_needed)

        if bv[0].tag[:4] in ('PRTF', 'GRND'):
        # проверь, могут ли причастия и деепричастия разных видов быть омонимичными
            return Disambiguate.IMPF, True if Disambiguate.IMPF in bv[0].tag else Disambiguate.PERF, True

        bv_gram_prof = Disambiguate.verb_gram_prof(bv[0], bv[-1])

        pre_bv, post_bv = Disambiguate.split_sent(tokens_needed, by=bv_gram_prof['inx'])
        Disambiguate.define_aspect(bv_gram_prof, pre_bv, post_bv)
