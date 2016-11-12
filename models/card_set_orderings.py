from models import Base


class CardSetOrdering(Base):
    @classmethod
    def table(cls):
        return super().table()('card_set_orderings')

    @classmethod
    def ordered_sets(cls, ordering_id):
        return cls.filter({'ordering_id': ordering_id}).order_by('set_order').get_field('set_code').run()
