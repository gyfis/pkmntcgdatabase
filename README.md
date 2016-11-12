# pkmntcgdb.com
This is the source code of the pkmntcgdb.com website. It's written in Python - Flask(+ Jinja2) and uses RethinkDB as the database.

# Website endpoints
The website has couple of endpoints, namely
- Homepage _/_ _/index_
- Card search _/cards_
- User page _/u/|username|_
- User profile _/profile_
- Login, SignUp, Logout _/login_ _/signup_ _/logout_

# Database structure
There are some models used in the website. I should have used a more sql-like database, but RethinkDB was chosen because it enabled me to develop the website rapidly, because of its stellar python api (which is now hidden under a Query model, with probably unnecessary duplicities).

## The models in the database
### User             
   -> has many UserCards, Collections
### Collection       
   -> has many UserCards, belongs to User
### CardSetOrdering
   -> has many CardSets
### CardSet          
   -> has many Cards, belongs to CardSetOrdering
### Card             
   -> has many UserCards, belongs to CardSet
### UserCard         
   -> belongs to User, Card, Collection

# What needs to be done
Right now the website is pretty much stable, though there are no tests. Adding these would be great!
Also, the ordering of Card editions is random right now, so that's something I'd like to change.

I'll be happy for any ideas, reported issues and pull requests!