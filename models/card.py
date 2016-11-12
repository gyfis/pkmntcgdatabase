from models import Base


class Card(Base):
    @classmethod
    def table(cls):
        return super().table()('cards')
