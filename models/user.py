from models import Base
from werkzeug.security import generate_password_hash, check_password_hash


class User(Base):
    @classmethod
    def table(cls):
        return super().table()('users')

    @classmethod
    def new(cls, username, password, email):
        pw_hash = generate_password_hash(password)
        return cls.create(
            username=username,
            username_lower=username.lower(),
            pw_hash=pw_hash,
            email=email
        )

    @classmethod
    def find_by_username(cls, username):
        return cls.find_first({'username_lower': username.lower()})

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False
