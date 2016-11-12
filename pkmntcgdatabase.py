import os
from functools import reduce

import rethinkdb as r
from rethinkdb.errors import RqlDriverError
from flask import Flask, g, request, abort, render_template, flash, redirect, url_for, make_response
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_required, confirm_login, logout_user, login_user, current_user
from flask_misaka import markdown
from waitress import serve
from copy import copy
from forms import LoginForm, SignupForm
from models import User, Card, Collection, UserCard, CardSet, CardSetOrdering
from services.color_service import get_colors
from const import RARITY_HASH, NORMALIZED_REPLACE_PAIRS
from services.fulltext_service import check_and_add_fulltext_search_field, refresh_fulltext_search_field

RDB_HOST = os.environ.get('RDB_HOST') or 'localhost'
RDB_PORT = os.environ.get('RDB_PORT') or 28015
PKMN_DB = 'pkmntcgdb'

app = Flask(__name__)
Bootstrap(app)
app.config.from_object('config')

login_manager = LoginManager()
login_manager.init_app(app)


CARDS_PER_PAGE = 30


def _get_color_gradients(count):
    return get_colors(2 * count)


def _card_text_for_edition_type(edition_type):
    return edition_type.replace('-', ' ').replace('_', ' ').capitalize()


def _total_number_of_cards_for_user(user_id):
    return UserCard.filter({'user_id': user_id}).sum('count')


def _total_number_of_cards_for_user_with_collection(user_id, collection_id):
    return UserCard.filter({'user_id': user_id, 'collection_id': collection_id}).sum('count')


def _user_collections(user_id):
    return Collection.filter({'user_id': user_id}).order_by('created_at').run()


def _selected_collection_for_user(user_id):
    return Collection.get(User.get(user_id).selected_collection) if user_id else None


def _user_card_primary_id(user_id, card_id, collection_id, edition):
    return UserCard.uuid('{}_{}_{}_{}'.format(user_id, card_id, collection_id, edition))


def _set_editions_in_order(normalized_set_name):
    card_set = CardSet.find_first({'normalized_set_name': normalized_set_name})
    return card_set.editions.keys()


def _user_set_editions_in_order(normalized_set_name):
    card_set = CardSet.find_first({'normalized_set_name': normalized_set_name})
    return [_card_text_for_edition_type(edition) for edition in card_set.editions]


def _get_user_cards(user_id, page):
    cards = Card.get_all(*list(UserCard.filter({'user_id': user_id}).filter(r.row['count'] > 0).get_field('card_id').run()))

    total_pages = ((copy(cards).count().run() - 1) // CARDS_PER_PAGE) + 1

    cards = cards.skip(CARDS_PER_PAGE * (page - 1))
    cards = cards.limit(CARDS_PER_PAGE).run()

    cards = list(cards)
    return cards, page, str(total_pages)


def _get_user_cards_data(user_id, collection_id):
    if collection_id:
        user_hash = {'user_id': user_id, 'collection_id': collection_id}
    else:
        user_hash = {'user_id': user_id}

    user_card_query = UserCard.filter(user_hash).filter(r.row['count'] > 0).pluck(
        'set_code', 'edition_superset', 'card_id'
    ).distinct().eq_join('card_id', Card.table()).without({'right': 'id'}).zip()

    card_edition_data = copy(user_card_query).group('set_code', 'edition_superset').count()
    total_cards_data = user_card_query.group('set_code').pluck('number').distinct().count()

    return card_edition_data, total_cards_data


def _get_collection_id(user_id, collection_name):
    if not collection_name:
        return None
    return Collection.find_first({'user_id': user_id, 'name': collection_name}).get_id() or None


def _get_collection_data(user_id, collection_name):
    # list of set data, sorted by set number
    # for each set, I want a list of editions + a special 'collection' list
    # each of these editions need a color, current_number, total_number and name of the edition

    collection_id = _get_collection_id(user_id, collection_name)

    card_edition_data, total_cards_data = _get_user_cards_data(user_id, collection_id)

    sets = {}

    for set_card_edition in card_edition_data:
        set_code, edition = set_card_edition

        count = card_edition_data[set_card_edition]
        if set_code not in sets:
            sets[set_code] = {}

        sets[set_code][edition] = count

    if not total_cards_data:
        return {'sets': [], 'ordered_sets': [],
                'collection_name': collection_name,
                'user_id': user_id, 'username': User.get(user_id).username}

    for set_code in total_cards_data:
        sets[set_code]['total_cards'] = total_cards_data[set_code]

    for card_set in CardSet.filter(lambda cs: cs['code'].match('|'.join(sets.keys()))).run():
        if card_set['code'] not in sets.keys():
            continue
        sets[card_set['code']]['set_total_cards'] = card_set['total_cards']
        sets[card_set['code']]['raw_data'] = card_set

        for edition in card_set['editions']:
            sets[card_set['code']]['set_{}'.format(edition)] = card_set['editions'][edition]

    ordered_sets = [set_code for set_code in list(CardSetOrdering.ordered_sets(1)) if set_code in sets.keys()]

    sets = {k[0]: k[1] for k in filter(lambda kv: 'raw_data' in kv[1], sets.items())}
    for set_code in sets:
        card_set_hash = sets[set_code]

        sets[set_code]['normalized_card_set'] = card_set_hash['raw_data']['normalized_set_name']
        sets[set_code]['card_set'] = card_set_hash['raw_data']['set_name']

        number_of_editions = len(card_set_hash['raw_data']['editions']) + 1
        colors = _get_color_gradients(number_of_editions)

        card_set_data = 'Set cards#{}#{}#{}#{}'.format(card_set_hash['total_cards'], card_set_hash['set_total_cards'], colors[0], colors[1])

        set_lines = [('Set cards', card_set_hash['total_cards'], card_set_hash['set_total_cards'], colors[0])]

        current_color = 0

        for edition in card_set_hash['raw_data']['editions']:
            current_color += 1
            card_set_data += '${}#{}#{}#{}#{}'.format(_card_text_for_edition_type(edition),
                                                      card_set_hash[edition] if edition in card_set_hash else 0,
                                                      card_set_hash['set_{}'.format(edition)],
                                                      colors[2 * current_color],
                                                      colors[2 * current_color + 1])

            set_lines.append(
                (
                    edition,
                    card_set_hash[edition] if edition in card_set_hash else 0,
                    card_set_hash['set_{}'.format(edition)],
                    colors[2 * current_color]
                )
            )

        sets[set_code]['data'] = card_set_data
        sets[set_code]['lines'] = set_lines

    return {
        'sets': sets,
        'ordered_sets': ordered_sets,
        'collection_name': collection_name,
        'user_id': user_id,
        'username': User.get(user_id).username
    }


def _get_card_set_data(user_id, collection_name, set_name):
    cards_in_set = list(Card.filter({'card_set': set_name}).order_by('number').run())

    user_hash = {'user_id': user_id}
    if collection_name:
        user_hash['collection_id'] = _get_collection_id(user_id, collection_name)

    user_cards_data = list(UserCard.filter(r.row['count'] > 0).filter(user_hash).run())

    for card in cards_in_set:
        card['edition_counts'] = {}
        for edition in card['editions']:
            edition_superset = edition['type'].split('-')[0]
            user_card_data = list(filter(lambda user_card: (user_card['card_code'], user_card['edition_superset']) == (card['card_code'], edition_superset), user_cards_data))
            card['edition_counts'][edition_superset] = reduce(lambda left, right: {'count': left['count'] + right['count']}, user_card_data)['count'] if user_card_data else 0

    return {
        'normalized_set_name': _normalized_card_set(set_name),
        'set_name': set_name,
        'cards': cards_in_set,
        'editions': _user_set_editions_in_order(_normalized_card_set(set_name)),
        'edition_keys': _set_editions_in_order(_normalized_card_set(set_name)),
        'collection_name': collection_name
    }


def _normalized_card_set(card_set):
    normalized_card_set = str(card_set).strip().lower()
    for original, replace in NORMALIZED_REPLACE_PAIRS:
        normalized_card_set = normalized_card_set.replace(original, replace)
    return normalized_card_set


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    card = Card.find_first({'card_code': 'xy11-77'})
    return render_template("index.html")


@app.route('/fulltext_refresh', methods=['GET'])
def fulltext_refresh():
    check_and_add_fulltext_search_field()
    refresh_fulltext_search_field()
    return 'Done'


@login_required
@app.route('/profile', methods=['GET'])
def profile():
    return render_template('profile.html')


@app.route('/u/<path:path>', methods=['GET'])
def user_cards(path):
    return render_template('user_cards.html')


@login_required
@app.route('/set_selected_collection', methods=['POST'])
def set_selected_collection():
    collection_id = request.json['collection_id']

    User.get(current_user.get_id()).update({'selected_collection': collection_id})
    return ''


@app.route('/set_data_head', methods=['POST'])
def set_data_head():
    split_path = request.json['url'].split('/')
    user_query = split_path[2].split('@')

    # TODO: ERROR IndexError: list index out of range

    username = user_query[0]

    user = User.find_by_username(username)
    if not user:
        abort(404)

    return render_template('widgets/user_cards_head.jinja2', user_id=user.get_id(), username=username)


@app.route('/set_data', methods=['POST'])
def set_data():
    split_path = request.json['url'].split('/')
    user_query = split_path[2].split('@')

    collection_name = user_query[1] if len(user_query) > 1 else ''
    collection_name = collection_name.replace('%20', ' ')
    username = user_query[0]

    user = User.find_by_username(username)
    if not user:
        abort(404)

    if len(split_path) > 3:
        normalized_set_name = split_path[3]

        card_set = CardSet.find_first({'normalized_set_name': normalized_set_name}).set_name
        if not card_set:
            abort(404)

        return render_template('widgets/single_set_dashboard.jinja2', **_get_card_set_data(user.get_id(), collection_name, card_set))

    else:
        return render_template('widgets/set_dashboard.jinja2', **_get_collection_data(user.get_id(), collection_name))


@app.route("/cards", methods=['GET'])
def list_cards():
    return render_template('cards.html')


@app.route("/cards", methods=['POST'])
def change_cards():
    count = request.json['count']
    card_id, card_code, card_number, card_set_n, edition = request.json['card_ct_id'].split('|')
    collection_id = request.json['collection_id']

    user_id = request.json['user_id']

    UserCard.insert({
        'id': _user_card_primary_id(user_id, card_id, collection_id, edition),
        'count': count,
        'user_id': user_id,
        'card_id': card_id,
        'card_code': card_code,
        'edition': edition.lower(),
        'edition_superset': edition.lower().split('-')[0],
        'collection_id': collection_id
    }, conflict='update')

    return ''


@app.route("/search_cards", methods=['POST'])
def search_cards():
    search_query = request.json['url'][1:]
    if not search_query:
        searched_terms = []
        search_args = {}
    else:
        search_args = {arg.split('=')[0]: arg.split('=')[1] for arg in search_query.split('&')}
        searched_terms = search_args['q'].lower().split('%20')

    searched_cards = Card.query()
    card_set_orderings = CardSetOrdering.table()

    if searched_terms:
        for searched_term in searched_terms:
            searched_cards = searched_cards.filter(lambda card: card['fulltext'].split().contains(searched_term))

        total_pages = ((copy(searched_cards).count() - 1) // CARDS_PER_PAGE) + 1

        searched_cards = searched_cards.eq_join('set_code', card_set_orderings, index='set_code').without({
            'right': 'id'
        }).zip().order_by('number', 'set_order')

        if 'page' in search_args:
            searched_cards = searched_cards.skip(CARDS_PER_PAGE * (int(search_args['page']) - 1)).limit(CARDS_PER_PAGE)
            page = search_args['page']
        else:
            searched_cards = searched_cards.limit(CARDS_PER_PAGE)
            page = 1

        searched_cards = searched_cards.run()

        cards = list(searched_cards)

        per_line = str(search_args['per_line']) if 'per_line' in search_args else None

        if not per_line:
            per_line = request.cookies.get('per_line')

        if not per_line:
            per_line = int(request.json['w']) // 350

    else:
        cards = []
        page = 0
        total_pages = 0
        per_line = 0

    response = make_response(render_template('widgets/card_widget.jinja2', cards=cards,
                                             page=page, total_pages=total_pages, per_line=per_line,
                                             searched_terms=searched_terms))

    if 'per_line' in search_args:
        response.set_cookie('per_line', per_line)

    return response


@app.route("/collection", methods=["POST"])
def collection():
    args = request.json

    user_id = args['user_id']
    collection_op_type = args['op_type']
    collection_name = args['collection_name']

    if collection_op_type == 'new':
        Collection.create(name=collection_name, user_id=user_id)
    elif collection_op_type == 'edit':
        Collection.get(args['collection_id']).update({'name': collection_name})

    return ''


@app.route("/delete_collection", methods=["POST"])
def delete_collection():
    args = request.json

    user_id = args['user_id']
    collection_id = args['collection_id']
    selected_collection_id = User.get(user_id).selected_collection
    Collection.get(collection_id).delete()
    UserCard.filter({'collection_id': collection_id, 'user_id': user_id}).delete()

    if selected_collection_id == collection_id:
        User.get(user_id).update({
            'selected_collection': Collection.find_first({'user_id': user_id}).get_id()
        })

    return ''


@app.route("/profile_collections", methods=['POST'])
def profile_collections():
    return render_template('widgets/profile_collections.jinja2', collections=_user_collections(current_user.get_id()))


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data

        user = User.find_by_username(username)
        if user:
            if user.check_password(password):
                remember = form.remember_me.data
                if login_user(user, remember=remember):
                    flash('Logged in!', 'success')
                    return redirect(url_for("index"))
                else:
                    flash('Sorry, but you could not log in.', 'danger')
            else:
                flash('Sorry, but you could not log in.', 'danger')
        else:
            flash('Invalid username.', 'danger')
    else:
        for field_name, error_messages in form.errors.items():
            for err in error_messages:
                flash('error with {}: {}'.format(field_name.replace('_', ' '), err), 'danger')
    return render_template("login.html", form=form)


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data
        email = form.email.data

        if User.find_by_username(username):
            flash('Sorry, but this username is already taken.', 'warning')
        else:
            user = User.get(User.new(username, password, email))
            collection_id = Collection.create(name=form.collection_name.data or 'My collection', user_id=user.get_id())
            user.update({'selected_collection': collection_id})
            remember = form.remember_me.data
            if login_user(user, remember=remember):
                flash("Logged in!", 'success')
                return redirect(url_for("index"))
            else:
                flash("Sorry, but you could not log in.", 'danger')
    else:
        for field_name, error_messages in form.errors.items():
            for err in error_messages:
                flash('error with {}: {}'.format(field_name.replace('_', ' '), err), 'danger')

    return render_template("signup.html", form=form)


@app.route("/reauth", methods=["GET", "POST"])
@login_required
def reauth():
    if request.method == "POST":
        confirm_login()
        flash(u"Reauthenticated.", 'success')
        return redirect(request.args.get("next") or url_for("index"))
    login()


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", 'Success')
    return redirect(url_for("index"))


@app.route("/changelog")
def changelog():
    with open(os.path.join(app.root_path, 'CHANGELOG.md')) as file:
        text = file.read()
        return markdown(text)


@app.errorhandler(404)
def page_not_found(_):
    return "not found :'(", 404


@app.before_request
def before_request():
    try:
        g.rdb_conn = r.connect(host=RDB_HOST, port=RDB_PORT, db=PKMN_DB)
    except RqlDriverError:
        abort(503, "No database connection could be established.")


@app.teardown_request
def teardown_request(_):
    try:
        g.rdb_conn.close()
    except AttributeError:
        pass


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):

    if endpoint == 'static':
        filename = values['filename']
        if 'css' in filename or 'js' in filename:
            filename = values.get('filename', None)
            if filename:
                file_path = os.path.join(app.root_path,
                                         endpoint, filename)
                values['q'] = int(os.stat(file_path).st_mtime)

    return url_for(endpoint, **values)


@app.context_processor
def utility_processor():
    def unique_card_edition_id(card, edition_type):
        return '|'.join([card['id'], card['card_code'], str(card['number']), normalized_card_set(card['card_set']), edition_type])

    def unique_card_id(card):
        return card['id'] + '|' + str(card['number']) + '|' + normalized_card_set(card['card_set'])

    def normalized_card_set(card_set):
        return _normalized_card_set(card_set)

    def image_exists(path):
        return os.path.exists(os.path.join(app.root_path, 'static', path))

    def card_count_for_edition_and_user(user_id, card_id, collection_id, edition_type):
        user_card = UserCard.get(_user_card_primary_id(user_id, card_id, collection_id, edition_type))
        if user_card:
            return user_card.count
        else:
            return 0

    def total_number_of_cards_for_user(user_id):
        return _total_number_of_cards_for_user(user_id)

    def user_collections(user_id):
        return _user_collections(user_id)

    def selected_collection_for_user(user_id):
        return _selected_collection_for_user(user_id)

    def card_text_for_edition_type(edition_type):
        return _card_text_for_edition_type(edition_type)

    def find_card_with_code(card_code):
        return Card.find_first({'card_code': card_code}) or None

    return dict(unique_card_edition_id=unique_card_edition_id, unique_card_id=unique_card_id,
                normalized_card_set=normalized_card_set,
                card_count_for_edition_and_user=card_count_for_edition_and_user,
                total_number_of_cards_for_user=total_number_of_cards_for_user,
                user_collections=user_collections, selected_collection_for_user=selected_collection_for_user,
                find_card_with_code=find_card_with_code,
                image_exists=image_exists, card_text_for_edition_type=card_text_for_edition_type,
                RARITY_HASH=RARITY_HASH)

if __name__ == '__main__':
    # app.run(debug=True)
    serve(app, host='127.0.0.1', port=5000)
