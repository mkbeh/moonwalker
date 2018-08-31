# -*- coding: utf-8 -*-

import json

from pymongo import MongoClient, errors
from pymongo import ReturnDocument
from pymongo import ASCENDING, DESCENDING
from bson.objectid import ObjectId


# DB_NAME = 'aggregators'


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class MongoDB(object):
    def __init__(self, db_name):
        try:
            cxn = MongoClient()
        except errors.AutoReconnect:
            raise RuntimeError()

        self.db_name = db_name

        self.db = cxn[self.db_name]
        self.collection = None

    def db_dump(self):
        pass

    def find(self, data, collection_name):
        self.collection = self.db[collection_name]

        list_ = []

        for item in self.collection.find(data):
            list_.append(item)

        return list_

    def find_one(self, data, collection_name):
        self.collection = self.db[collection_name]

        document = self.collection.find_one(data)

        return document

    def find_one_by_id(self, obj_id, collection_name):
        self.collection = self.db[collection_name]

        # Convert from string to ObjectId:
        document = self.collection.find_one({'_id': ObjectId(obj_id)})

        return document

    def find_one_and_update(self, filter_, data, collection_name, *args):
        self.collection = self.db[collection_name]

        for arg in args:
            if arg == '$set':
                record = self.collection.find_one_and_update(filter_, {'$set': data}, upsert=True,
                                                             return_document=ReturnDocument.AFTER)
                return record

            elif arg == '$inc':
                record = self.collection.find_one_and_update(filter_, {'$inc': data}, upsert=True,
                                                             return_document=ReturnDocument.AFTER)
                return record

    def find_one_and_update_by_id(self, obj_id, data, collection_name, *args):
        self.collection = self.db[collection_name]

        for arg in args:
            if arg == '$set':
                record = self.collection.find_one_and_update({'_id': ObjectId(obj_id)}, {'$set': data}, upsert=True,
                                                             return_document=ReturnDocument.AFTER)
                return record

            elif arg == '$inc':
                record = self.collection.find_one_and_update({'_id': ObjectId(obj_id)}, {'$inc': data}, upsert=True,
                                                             return_document=ReturnDocument.AFTER)
                return record

    def find_one_and_delete(self, filter_, collection_name, *args):
        self.collection = self.db[collection_name]

        for arg in args:
            if arg == '$set':
                record = self.collection.find_one_and_delete(filter_, collection_name)
                return record

            elif arg == '$inc':
                record = self.collection.find_one_and_update(filter_, collection_name)
                return record

    def insert_one(self, data, collection_name):
        self.collection = self.db[collection_name]

        document = self.collection.insert_one(data)

        return document

    def insert_many(self, documents, collection_name):
        self.collection = self.db[collection_name]
        self.collection.insert_many(documents)

    def delete_one(self, filter_, collection_name):
        self.collection = self.db[collection_name]

        self.collection.delete_one(filter_)

        return True

    def count(self, collection_name):
        self.collection = self.db[collection_name]

        return self.collection.count()

    def count_with_filter(self, filter_, collection_name):
        self.collection = self.db[collection_name]

        return self.collection.count(filter_)

    def find_with_sort(self, collection_name, field, sort=1):
        self.collection = self.db[collection_name]

        if sort == 1:
            sort = DESCENDING
        elif sort == 0:
            sort = ASCENDING

        docs_list = []

        for doc in self.collection.find().sort(field, sort):
            docs_list.append(doc)

        return docs_list

    def drop_collection(self, collection_name):
        self.collection = self.db[collection_name]

        self.collection.drop()

    def finish(self):
        self.db.logout()
