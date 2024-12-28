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
class LoadConstants():

    def __init__(self, dir):
        self.path = Path(dir)
        self.IMPF, self.PERF = 'impf', 'perf'
        self.VERBS = self.open_file(self.path / 'biaspectives_relevant_list.txt') # set

        self.PHASE_V = self.open_file(self.path / self.IMPF / 'phase_n_byt_verbs.txt') # dict
        self.MODAL_V = self.open_file(self.path / self.IMPF / 'neg_modal_verbs.txt') # ADD
        self.MODAL_W = self.open_file(self.path / self.IMPF / 'neg_modal.txt')

        self.MODIFIERS_IMPF_PRE = self.open_file(self.path / self.IMPF / 'modifiers_impf_pre.txt')
        self.MODIFIERS_IMPF_POST = self.open_file(self.path / self.IMPF / 'modifiers_impf_post.txt')
        self.PARTICLES_IMPF_PRE = self.open_file(self.path / self.IMPF /'particles_imp.txt')

        self.MODIFIERS_PERF_PRE = self.open_file(self.path / self.PERF / 'modifiers_perf_pre.txt')

        # Available attributes are: POS, animacy, aspect, case, gender, involvement, mood, number, person, tense, transitivity and voice.
        self.gram_cat_prop = {
            'class': {'VERB', 'INFN', 'PRTF', 'GRND'},
            'case': {'nomn', 'gent', 'gen2' 'datv', 'accs', 'ablt', 'loc1', 'loc2'},
            'voice': {'actv', 'pasv'},
            'mood': {'indc', 'impr'},
            'tense': {'past', 'pres', 'futr'},
            'aspect': {self.IMPF, self.PERF},
            'transitivity': {'tran', 'intr'},
            'number': {'sing', 'plur'}, \
            'person': {'1per', '2per', '3per'},
            'gender': {'masc', 'femn', 'neut'}
            # 'confidence': {True, False, None} типа добавить в словарь с биаспективом потом
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


class Disambiguate():
    PATH = '/content/drive/MyDrive/words'
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
        needed = {'VERB', 'INFN', 'PRTF', 'GRND', 'NOUN', 'ADVB',
                  'PRCL', 'NUMB', 'NUMR', 'PNCT', 'ADJS', 'PRED', 'ADJF'} # число слово
        return tuple((t, inx) for inx, t in enumerate(premarked) if
                     str(t.tag)[:4] in needed or t.word == 'за')

    def biaspective(self, tokens_needed):
        return next(((t, inx) for t, inx in tokens_needed
                    if t.normal_form in Disambiguate.VERBS), None)

    def verb_gram_prof(self, verb_parsed, verb_index):
        bv_gram = {
            'inx': verb_index, 'word': verb_parsed.word,
            'lemma': verb_parsed.normal_form
        }
        class_, *gram = str(verb_parsed.tag).split(',')
        bv_gram['class'] = class_

        for prop in gram:
            if ' ' in prop:
                gram.extend(prop.split())
                gram.pop(gram.index(prop))

        for prop in gram:
            for gram_cat in Disambiguate.GRAM_CAT_PROP:
                if prop in Disambiguate.GRAM_CAT_PROP.get(gram_cat, ''):
                    bv_gram[gram_cat] = prop
        return bv_gram

    def split_sent(self, tokens_needed, by):
        left = tuple((filter(lambda tup: str(tup[0].tag)[:4] != 'NOUN',
                                     reversed(tokens_needed[:by]))))
        right = tuple(tokens_needed[by + 1:])
        return left, right

    # этого ещё
    def process_candidates(self, bi_verb, verb_cand):
        # сюда можно бинарный воткнуть НЕТ ФИНИТНОГО из процесс лефт
        # слева 2-ой гл от ДВГ или справа 1 гл от ДВГ может нести грамм инфу,
        # это потенциально тоже можно проанализировать, чтобы определить вид

        if verb_cand['class'] == bi_verb['class'] == 'INFN':

            bi_verb['aspect'] = verb_cand['aspect']
            # ваще в идеале они либо должны идти без финитных перед, либо
            # перед одним общим финитным
            return verb_cand['aspect'], False

        elif verb_cand['class'] == bi_verb['class'] == 'VERB':

            if verb_cand.get('number', '_') == bi_verb.get('number', '_') and \
            verb_cand.get('mood', '_') == bi_verb.get('mood', '_'):

                # хорошо бы ещё время вернуть в презенсе
                if verb_cand.get('tense', '_') == bi_verb.get('tense', '_') == 'past' and \
                verb_cand.get('gender', '_') == bi_verb.get('gender', '_') != '_':
                    bi_verb['aspect'] = verb_cand['aspect']
                    return verb_cand.get('aspect', ''), True

                elif verb_cand.get('tense', '_') == bi_verb.get('tense', '_') != '_' and \
                verb_cand.get('tense', '_') in ('pres', 'futr') and \
                verb_cand.get('person', '_') == bi_verb.get('person', '_') != '_':
                    bi_verb['aspect'] = verb_cand['aspect']
                    return verb_cand.get('aspect', '_'), True

                elif verb_cand.get('mood', '_') == 'impr':
                    return verb_cand.get('aspect', '_'), True

                return verb_cand.get('aspect', '_'), False
        return '_', False

    def process_left(self, left, bv_gram_prof):
        if left:
            prev_modal, prev_non_finite, status_no_answer, punct_prev, prev_neg = False, False, False, False, False

            left_len = len(left)
            for t, inx in left: # проверь потом, какой тут индекс, токена из
            # фильтрованной последовательности или исходной. Должно быть исходной
                tok_pos = str(t.tag)[:4]
                # iterating over reversed sequence
                if -~(bv_gram_prof.get('inx', -1) + ~inx) == 1:

                    if (tok_pos in ('VERB', 'INFN', 'PRED', 'ADJS')) \
                    and bv_gram_prof.get('class', '_') == 'INFN':
                        if t.normal_form in Disambiguate.PHASE:
                            return Disambiguate.IMPF, True
                        elif t.normal_form in Disambiguate.MODAL_V or t.word in Disambiguate.MODAL_W:
                            prev_modal = True
                        elif tok_pos in ('VERB', 'INFN'):
                            prev_non_finite = True

                    elif tok_pos == 'ADVB':
                        if t.normal_form in Disambiguate.MODIFIERS_PERF_PRE and \
                        'past' in bv_gram_prof.get('tense', '_'):
                            return Disambiguate.PERF, True
                        elif t.normal_form in Disambiguate.MODIFIERS_PERF_PRE and \
                        bv_gram_prof.get('tense', '_') in ('pres', 'futr'):
                            return Disambiguate.IMPF, True
                        elif t.word == 'ещё':
                            return Disambiguate.IMPF, True

                    elif tok_pos == 'PRCL':
                        if t.word == 'не':
                            if 'impr' in bv_gram_prof.get('mood', '_'):
                                return Disambiguate.IMPF, True
                            else:
                                prev_neg = True

                    elif tok_pos == 'PNCT':
                        punct_prev = True

                elif -~(bv_gram_prof.get('inx', -1) + ~inx) == 2:
                    if tok_pos == 'PRCL' and t.word == 'не' and prev_modal:
                        return Disambiguate.IMPF, True
                    else:
                        modal_before = True
                        prev_modal = False
                        if tok_pos == 'ADVB' and t.word == 'ещё' and prev_neg:
                            return Disambiguate.IMPF, True
                        else:
                            if tok_pos == 'ADVB' and prev_neg:
                                if t.normal_form in Disambiguate.MODIFIERS_IMPF_PRE:
                                    return Disambiguate.IMPF, True
                                elif t.normal_form in Disambiguate.MODIFIERS_PERF_PRE and \
                                'past' in bv_gram_prof.get('tense'):
                                    return Disambiguate.PERF, True
                            prev_neg = False
                modal_before = prev_modal

                if -~(bv_gram_prof.get('inx', -1) + ~inx) >= 2:
                    if t.normal_form in Disambiguate.MODIFIERS_IMPF_PRE and tok_pos == 'ADVB':
                        return Disambiguate.IMPF, True
                    elif tok_pos in ('VERB', 'INFN') and not modal_before and not prev_non_finite:
                        # prev_non_finite можно тоже возвращать, чтобы не анализировать правую подпоследовательность, ибо в таком случае вид нельзя будет определить
                        # homogenous sentence members

                        verb_cand_prof = self.verb_gram_prof(t, inx)
                        bv_aspect, confidence = self.process_candidates(bv_gram_prof, verb_cand_prof) # переиначить
                        return bv_aspect, confidence
        return '_', False

    def process_right(self, right, bv_gram_prof):
        if right:
            right_len = len(right)
            za_before, NUMR_prev, NUMB_prev = False, False, False

            for t, inx in right:
                tok_pos = str(t.tag)[:4]
                if inx - bv_gram_prof.get('inx', -1) == 1:
                        # past too ???
                        # bv_gram_prof.get('tense', '') and \
                        if t.word == 'ещё' and inx <= right_len - 2:
                            return Disambiguate.IMPF, True

                if t.word == 'за':
                    za_before = True

                if tok_pos == 'NUMB':
                    NUMB_prev = True

                if tok_pos in ('NUMR', 'ADJF'):
                    NUMR_prev = True
                # elif tok_pos == 'NUMR' and NUMR_prev:
                #     if NUMB_prev:
                #         NUMB_prev = False
                if tok_pos == 'NOUN':
                    if NUMB_prev or NUMR_prev:
                        if t.normal_form in Disambiguate.MODIFIERS_IMPF_POST and \
                        za_before and inx - bv_gram_prof.get('inx') >= 3:
                            return Disambiguate.PERF, False
                        elif t.normal_form in Disambiguate.MODIFIERS_IMPF_POST and \
                        not za_before and inx - bv_gram_prof.get('inx') >= 2:
                            return Disambiguate.IMPF, True
                        # else:
                        #     za_before, NUMR_prev, NUMB_prev = False, False, False
                    elif not NUMB_prev and not NUMR_prev and ('sing' in t.tag.NUMBERS):
                        if t.normal_form in Disambiguate.MODIFIERS_IMPF_POST and \
                        za_before and inx - bv_gram_prof.get('inx') >= 2:
                            return Disambiguate.PERF, False
                        elif t.normal_form in Disambiguate.MODIFIERS_IMPF_POST and \
                        not za_before and inx - bv_gram_prof.get('inx') >= 1:
                            return Disambiguate.IMPF, True
                        # else:
                        #     za_before, NUMR_prev, NUMB_prev = False, False, False
                if inx - bv_gram_prof.get('inx', -1) >= 1:
                    if tok_pos == 'ADVB':
                        if t.normal_form in Disambiguate.MODIFIERS_IMPF_PRE:
                            return Disambiguate.IMPF, True
                    elif tok_pos in ('VERB', 'INFN'):
                        # homogenous sentence members
                        verb_cand_prof = self.verb_gram_prof(t, inx)
                        bv_aspect, confidence = self.process_candidates(bv_gram_prof, verb_cand_prof) # переиначить
                        return bv_aspect, confidence
        return '_', False

    def define_aspect(self, bv_gram_prof, left, right):
        success_pre, success_post = None, None

        pre_bv_res, success_pre = self.process_left(left, bv_gram_prof)
        post_bv_res, success_post = self.process_right(right, bv_gram_prof)

        if success_pre and not success_post:
            return pre_bv_res, success_pre
        elif success_post and not success_pre:
            return post_bv_res, success_post
        else:
            # здесь можно добавить условие, тип если левое и правое неуверенно, но предсказание одно, то уверенно выдавать ответ
            return (pre_bv_res, success_pre) if pre_bv_res != '_' else (post_bv_res, success_post)

    def process(self, text):
        tokens = self.tokenize(text)
        premarked = self.premark_text(tokens)

        toks_inx_kv = self.proccess_seq(premarked)
        tokens_needed = self.findall_needed(premarked)

        bv = self.biaspective(tokens_needed)

        if str(bv[0].tag)[:4] in ('PRTF', 'GRND'):
        # проверь, могут ли причастия и деепричастия разных видов быть омонимичными
            return Disambiguate.IMPF, True if Disambiguate.IMPF in str(bv[0].tag) else Disambiguate.PERF, True

        bv_gram_prof = self.verb_gram_prof(bv[0], bv[-1])

        pre_bv, post_bv = self.split_sent(tokens_needed, by=bv_gram_prof['inx'])
        return self.define_aspect(bv_gram_prof, pre_bv, post_bv)
