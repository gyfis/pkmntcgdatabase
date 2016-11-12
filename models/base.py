import rethinkdb as r
from models import Query
from abc import ABCMeta, abstractclassmethod


class Base(object):
    __metaclass__ = ABCMeta

    @abstractclassmethod
    def table(self):
        return r.table

    @classmethod
    def create(cls, **kwargs):
        kwargs.update({'created_at': r.now()})
        return cls.insert(kwargs)['generated_keys'][0]

    @classmethod
    def get(cls, object_id):
        object_data = Query(cls.table()).get(object_id).run()
        return cls(object_data) if object_data else None

    @classmethod
    def get_all(cls, *object_ids):
        return Query(cls.table()).get_all(*object_ids)

    @classmethod
    def filter(cls, filter_hash):
        return Query(cls.table()).filter(filter_hash)

    @classmethod
    def find_first(cls, find_hash):
        object_data = list(Query(cls.table()).filter(find_hash).limit(1).run())
        return cls(object_data[0]) if object_data else None

    @classmethod
    def insert(cls, insert_hash, conflict="error"):
        return Query(cls.table()).insert(insert_hash, conflict=conflict)

    @classmethod
    def query(cls):
        return Query(cls.table())

    @classmethod
    def uuid(cls, string):
        return Query(r).uuid(string)

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def update(self, update_hash):
        return Query(self.table()).get(self.get_id()).update(update_hash)

    def delete(self):
        return Query(self.table()).get(self.get_id()).delete()

    def get_id(self):
        return self['id']
