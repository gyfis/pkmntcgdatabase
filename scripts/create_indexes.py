import rethinkdb as r

r.connect('localhost', 28015).repl()

cards = r.db('pkmntcgdb').table('cards')
sets = r.db('pkmntcgdb').table('card_sets')
user_cards = r.db('pkmntcgdb').table('user_cards')
card_set_orderings = r.db('pkmntcgdb').table('card_set_orderings')

sets.index_create('set_name').run()
user_cards.index_create('card_id').run()
card_set_orderings.index_create('set_code').run()

