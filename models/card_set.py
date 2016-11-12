from models import Base


class CardSet(Base):
    @classmethod
    def table(cls):
        return super().table()('card_sets')
