from models import Base


class Collection(Base):
    @classmethod
    def table(cls):
        return super().table()('collections')
