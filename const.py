FULLTEXT_REMOVED_CHARS = ["#", "&", "'", ".", "_", "’"]
FULLTEXT_REPLACED_CHARS = {'é': 'e'}

RARITY_HASH = {"bog": '', "br": 'BREAK', "bt": 'Rare', "c": 'Common', "cr": 'Crystal', "ex": 'EX', "fa": 'FA',
               "h": 'Holo', "lg": 'LEGEND', "lv": 'LvX', "mcdonalds": '', "p": 'Promo', "pccp": '', "pr": 'Prime',
               "r": 'Rare', "rumble": '', "sc": 'Secret', "sh": 'Shining', "si": '', "st": 'Star', "u": 'Uncommon',
               'bihd': "BisharpHalfDeck", 'exhd': "ExcadrillHalfDeck",
               'gyhd': "GyaradosHalfDeck", 'la2hd': "Latias2HalfDeck",
               'lahd': "LatiasHalfDeck", 'lo2hd': "Latios2HalfDeck",
               'lohd': "LatiosHalfDeck", 'luhd': "LucarioHalfDeck",
               'mahd': "ManaphyHalfDeck", 'mihd': "MinunHalfDeck",
               'nohd': "NoivernHalfDeck", 'pilhd': "PikachuLibreHalfDeck",
               'plhd': "PlusleHalfDeck", 'rahd': "RaichuHalfDeck",
               'suhd': "SuicuneHalfDeck", 'syhd': "SylveonHalfDeck",
               'wihd': "WigglytuffHalfDeck", 'zohd': "ZoroarkHalfDeck"}

FIRST_EDITION_SETS = ['neo-destiny', 'neo-revelation', 'neo-discovery', 'neo-genesis', 'gym-challenge',
                      'gym-heroes', 'team-rocket', 'fossil', 'jungle', 'base-set']

NORMALIZED_REPLACE_PAIRS = [('& ', ''), (' ', '-'), ("'", ''), ('(', ''), (')', ''), ('pop', 'pop-series')]
