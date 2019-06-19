from itertools import groupby

import attr
from clldutils.misc import nfilter, slug
from clldutils.path import Path
from pylexibank.dataset import Dataset as BaseDataset
from pylexibank.dataset import Lexeme


@attr.s
class LeeJaponicLexeme(Lexeme):
    AlternativeTranscription = attr.ib(default=None)


class Dataset(BaseDataset):
    dir = Path(__file__).parent
    id = "leejaponic"

    lexeme_class = LeeJaponicLexeme

    def cmd_download(self, **kw):
        self.raw.xls2csv("supplementary.xlsx")
        self.raw.xls2csv("Japonic_recovered.xlsx")

    def read_csv(self, name, header_index=0):
        rows = [
            [c.strip() for c in row] for i, row in enumerate(self.raw.read_csv(name)[header_index:])
        ]

        return rows.pop(0), rows

    def cmd_install(self, **kw):
        language_map = {}
        meaning_map = {}

        concept_map = {c.gloss: c.id for c in self.concepticon.conceptsets.values()}

        sourcemap = {
            lname: [r[1] for r in srcs]
            for lname, srcs in groupby(
                sorted(nfilter(self.raw.read_csv("sources.csv"))), lambda r: r[0]
            )
        }

        wordsh, words = self.read_csv("supplementary.Sheet1.csv", header_index=0)
        cognatesh, cognates = self.read_csv("Japonic_recovered.Sheet1.csv", header_index=1)

        def concepts(h, step):
            lookup = h[2:]
            return {x + 2: lookup[x] for x in range(0, len(lookup), step)}

        def sorted_(l):
            return sorted(l, key=lambda r: r[:2])

        word_index_to_concept = concepts(wordsh, 1)

        with self.cldf as ds:
            ds.add_sources(*self.raw.read_bib())

            for language in self.languages:
                lid = slug(language["NAME"])
                ds.add_language(ID=lid, Name=language["NAME"], Glottocode=language["GLOTTOCODE"])
                language_map[language["NAME"].strip()] = lid

            for i, (word, cognate) in enumerate(zip(sorted_(words), sorted_(cognates))):
                if not word[1]:
                    continue
                if word[1] == "Nigata":
                    word[1] = "Niigata"
                assert word[:2] == cognate[:2]

                lname = word[1]

                for index, concept in word_index_to_concept.items():
                    if word[index] == "?":
                        continue
                    cindex = (index - 1) * 2
                    assert cognatesh[cindex] == concept

                    meaning_n = '{0}'.format(slug(concept))

                    if meaning_n not in meaning_map:
                        meaning_map[meaning_n] = '{0}_l{1}'.format(slug(concept), i)

                        ds.add_concept(ID=meaning_map[meaning_n], Name=concept,
                                       Concepticon_ID=concept_map.get(concept.upper()))
                    else:
                        ds.add_concept(ID=meaning_map[meaning_n], Name=concept,
                                       Concepticon_ID=concept_map.get(concept.upper()))

                    if concept.upper() not in concept_map:
                        self.unmapped.add_concept(ID=meaning_map[meaning_n], Name=concept)

                    for row in ds.add_lexemes(
                        Language_ID=slug(lname),
                        Parameter_ID=meaning_map[meaning_n],
                        Value=word[index],
                        AlternativeTranscription=cognate[cindex],
                        Source=sourcemap[lname],
                    ):
                        cs = cognate[cindex + 1]
                        for css in cs.split("&"):
                            css = css.strip()
                            if css != "?":
                                css = int(float(css))
                                ds.add_cognate(
                                    lexeme=row, Cognateset_ID="%s-%s" % (index - 1, css)
                                )
