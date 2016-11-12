from flask import g


class Query(object):
    def __init__(self, table):
        self.query = table

    def filter(self, filter_hash):
        self.query = self.query.filter(filter_hash)
        return self

    def order_by(self, *order_attributes):
        for order_attribute in order_attributes:
            self.query = self.query.order_by(order_attribute)
        return self

    def limit(self, limit):
        self.query = self.query.limit(limit)
        return self

    def skip(self, skip):
        self.query = self.query.skip(skip)
        return self

    def get(self, object_id):
        self.query = self.query.get(object_id)
        return self

    def get_all(self, *object_ids):
        self.query = self.query.get_all(*object_ids)
        return self

    def eq_join(self, attribute, other_table, **kwargs):
        self.query = self.query.eq_join(attribute, other_table, **kwargs)
        return self

    def without(self, without_hash):
        self.query = self.query.without(without_hash)
        return self

    def group(self, *group_args):
        self.query = self.query.group(*group_args)
        return self

    def zip(self):
        self.query = self.query.zip()
        return self

    def pluck(self, *attributes):
        self.query = self.query.pluck(*attributes)
        return self

    def get_field(self, attribute):
        self.query = self.query.get_field(attribute)
        return self

    def distinct(self):
        self.query = self.query.distinct()
        return self

    def count(self):
        self.query = self.query.count()
        return self.run()

    def update(self, update_hash):
        self.query = self.query.update(update_hash)
        return self.run()

    def insert(self, insert_hash, conflict):
        self.query = self.query.insert(insert_hash, conflict=conflict)
        return self.run()

    def delete(self):
        self.query = self.query.delete()
        return self.run()

    def sum(self, attribute):
        self.query = self.query.sum(attribute)
        return self.run()

    def uuid(self, string):
        self.query = self.query.uuid(string)
        return self.run()

    def run(self):
        return self.query.run(g.rdb_conn)
