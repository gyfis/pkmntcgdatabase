import rethinkdb as r

r.connect('localhost', 28015).repl()

db_name = 'pkmntcgdb'
cards = r.db(db_name).table('cards')
sets = r.db(db_name).table('card_sets')
user_cards = r.db(db_name).table('user_cards')
card_set_orderings = r.db(db_name).table('card_set_orderings')

sets.index_create('set_name').run()
user_cards.index_create('card_id').run()
card_set_orderings.index_create('set_code').run()
