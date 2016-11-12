from models import Base


class UserCard(Base):
    @classmethod
    def table(cls):
        return super().table()('user_cards')
