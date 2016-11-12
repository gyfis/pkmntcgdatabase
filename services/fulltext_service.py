from const import FULLTEXT_REMOVED_CHARS, FULLTEXT_REPLACED_CHARS
from models import Card
import rethinkdb as r


def _normalize_for_fulltext(fulltext_string):
    normalized_fulltext_string = fulltext_string

    for char in FULLTEXT_REMOVED_CHARS:
        normalized_fulltext_string = normalized_fulltext_string.replace(char, '')

    for char in FULLTEXT_REPLACED_CHARS:
        normalized_fulltext_string = normalized_fulltext_string.replace(char, FULLTEXT_REPLACED_CHARS[char])

    return normalized_fulltext_string


def _check(card):
    fulltext_string = _normalize_for_fulltext(
        '{}{}{} {}'.format(
            card['Name'].lower(),
            ' {}'.format(str(card['number']).lower()) if card['number'] else '',
            '/' + str(card['cards_in_set']) if 'cards_in_set' in card else '',
            card['card_set'].lower()
        )
    )

    return fulltext_string


def check_and_add_fulltext_search_field():
    cards = Card.filter(~r.row.has_fields('fulltext')).run()
    for card in cards:
        fulltext_string = _check(card)
        Card.get(card['id']).update({'fulltext': fulltext_string})


def refresh_fulltext_search_field():
    cards = Card.filter(r.row.has_fields('fulltext')).run()
    for card in cards:
        fulltext_string = _check(card)
        Card.get(card['id']).update({'fulltext': fulltext_string})
