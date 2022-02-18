from django.conf import settings
from pymongo import MongoClient
from pymongo.database import Database

connection_string = 'mongodb://{}:{}@{}/?directConnection=true&serverSelectionTimeoutMS=2000'.format(
    settings.MONGO_USER, settings.MONGO_PASSWORD, settings.MONGO_HOST)

__client = MongoClient(connection_string)

mongoDb: Database = __client.doffy
