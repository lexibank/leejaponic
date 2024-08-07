import pathlib
import itertools

import attr
from clldutils.misc import nfilter, slug
import pylexibank


@attr.s
class LeeJaponicLexeme(pylexibank.Lexeme):
    AlternativeTranscription = attr.ib(default=None)


class Dataset(pylexibank.Dataset):
    dir = pathlib.Path(__file__).parent
    id = "leejaponic"
    writer_options = dict(keep_languages=False, keep_parameters=False)
    lexeme_class = LeeJaponicLexeme
    form_spec = pylexibank.FormSpec(replacements=[("オンボ", ""), ("シッポ", "")])

    def cmd_download(self, args):
        self.raw_dir.xls2csv("supplementary.xlsx")
        self.raw_dir.xls2csv("Japonic_recovered.xlsx")

    def read_csv(self, name, header_index=0):
        rows = [
            [c.strip() for c in row]
            for i, row in enumerate(self.raw_dir.read_csv(name)[header_index:])
        ]
        return rows.pop(0), rows

    def cmd_makecldf(self, args):
        language_map = args.writer.add_languages(lookup_factory="Name")

        concept_map = args.writer.add_concepts(
            id_factory=lambda x: x.id.split("-")[-1] + "_" + slug(x.english), lookup_factory="Name"
        )

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

        def sorted_(lang):
            return sorted(lang, key=lambda r: r[:2])

        word_index_to_concept = concepts(wordsh, 1)

        args.writer.add_sources()
        
        new_idx = 1000
        for i, (word, cognate) in enumerate(zip(sorted_(words), sorted_(cognates))):
            if not word[1]:
                continue
            if word[1] == "Nigata":
                word[1] = "Niigata"
            assert word[:2] == cognate[:2]

            lname = word[1]
            
            cogs = {}
            cogidx = 1
            for index, concept in word_index_to_concept.items():
                cindex = (index - 1) * 2
                assert cognatesh[cindex] == concept

                cs = cognate[cindex + 1]
                cogn = cs.split("&")[0].strip()
                if cogn == "?":
                    cogid = cogidx 
                    cogidx += 1
                elif cogn in cogs:
                    cogid = cogs[cogn]
                else:
                    cogs[cogn] = cogidx
                    cogidx += 1
                    cogid = cogs[cogn]
                for row in args.writer.add_lexemes(
                    Language_ID=language_map[lname],
                    Parameter_ID=concept_map[concept],
                    Value=word[index],
                    AlternativeTranscription=cognate[cindex],
                    Source=sourcemap[lname],
                    Cognacy=cogid
                ):
                    cs = cognate[cindex + 1]
                    for css in cs.split("&"):
                        css = css.strip()
                        if css != "?":
                            css = int(float(css))
                            args.writer.add_cognate(
                                lexeme=row, Cognateset_ID="%s-%s" % (index - 1, css)
                            )
