
def test_valid(cldf_dataset, cldf_logger):
    assert cldf_dataset.validate(log=cldf_logger)


# "Lexical data consist of 59 lists of 210 basic vocabularies"
def test_languages(cldf_dataset, cldf_logger):
    assert len(list(cldf_dataset['LanguageTable'])) == 59


def test_parameters(cldf_dataset, cldf_logger):
    assert len(list(cldf_dataset['ParameterTable'])) == 210


def test_sources(cldf_dataset, cldf_logger):
    assert len(cldf_dataset.sources) == 5

# "The cognate sets were encoded into binary states showing 
# presence (‘1’) or absence (‘0’) of a cognate, which resulted\
# in a 59x675 matrix"
# ...we actually get 677?
def test_cognates(cldf_dataset, cldf_logger):
    cogsets = {c['Cognateset_ID'] for c in cldf_dataset['CognateTable']}
    assert len(cogsets) == 677
