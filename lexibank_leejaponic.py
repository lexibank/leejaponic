import pathlib
import itertools

import attr
from clldutils.misc import nfilter, slug
from pylexibank import Lexeme, Dataset as BaseDataset


@attr.s
class LeeJaponicLexeme(Lexeme):
    AlternativeTranscription = attr.ib(default=None)


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "leejaponic"

    lexeme_class = LeeJaponicLexeme

    def cmd_download(self, args):
        self.raw_dir.xls2csv("supplementary.xlsx")
        self.raw_dir.xls2csv("Japonic_recovered.xlsx")

    def read_csv(self, name, header_index=0):
        rows = [
            [c.strip() for c in row] for i, row in
            enumerate(self.raw_dir.read_csv(name)[header_index:])
        ]
        return rows.pop(0), rows

    def cmd_makecldf(self, args):
        language_map = {}
        meaning_map = {}

        sourcemap = {
            lname: [r[1] for r in srcs]
            for lname, srcs in itertools.groupby(
                sorted(nfilter(self.raw_dir.read_csv("sources.csv"))), lambda r: r[0]
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

        args.writer.add_sources(*self.raw_dir.read_bib())

        for language in self.languages:
            lid = slug(language["NAME"])
            args.writer.add_language(
                ID=lid, Name=language["NAME"], Glottocode=language["GLOTTOCODE"])
            language_map[language["NAME"].strip()] = lid

        for concept in self.concepts:
            args.writer.add_concept(
                ID=slug(concept["ENGLISH"]),
                Name=concept["ENGLISH"],
                Concepticon_ID=concept["CONCEPTICON_ID"],
            )
            meaning_map[slug(concept["ENGLISH"])] = slug(concept["ENGLISH"])

        for i, (word, cognate) in enumerate(zip(sorted_(words), sorted_(cognates))):
            if not word[1]:
                continue
            if word[1] == "Nigata":
                word[1] = "Niigata"
            assert word[:2] == cognate[:2]

            lname = word[1]

            for index, concept in word_index_to_concept.items():
                cindex = (index - 1) * 2
                assert cognatesh[cindex] == concept

                for row in args.writer.add_lexemes(
                    Language_ID=slug(lname),
                    Parameter_ID=meaning_map[slug(concept)],
                    Value=word[index],
                    AlternativeTranscription=cognate[cindex],
                    Source=sourcemap[lname],
                ):
                    cs = cognate[cindex + 1]
                    for css in cs.split("&"):
                        css = css.strip()
                        if css != "?":
                            css = int(float(css))
                            args.writer.add_cognate(
                                lexeme=row, Cognateset_ID="%s-%s" % (index - 1, css))
