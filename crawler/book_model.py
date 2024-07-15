from peewee import *

db = SqliteDatabase('books.db')

class Book(Model):
    title = CharField()
    author = CharField()
    description = CharField()
    genres = CharField()
    imgUrl = CharField()
    url = CharField()

    class Meta:
        database = db
