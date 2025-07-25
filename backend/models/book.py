from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

class Book:
    def __init__(self, db_connection):
        self.db = db_connection
        self.collection = self.db.books
    
    def add_book(self, book_data):
        book_document = {
            'title': book_data['title'],
            'author': book_data['author'],
            'isbn': book_data.get('isbn', ''),
            'subject': book_data.get('subject', ''),
            'publication_date': book_data.get('publication_date', ''),
            'total_pages': book_data.get('total_pages', 0),
            'file_path': book_data['file_path'],
            'upload_date': datetime.now(),
            'status': 'active'
        }
        return self.collection.insert_one(book_document)
    
    def get_all_books(self):
        return list(self.collection.find({'status': 'active'}))
    
    def get_book_by_id(self, book_id):
        return self.collection.find_one({'_id': ObjectId(book_id)})
    
    def update_book(self, book_id, update_data):
        return self.collection.update_one(
            {'_id': ObjectId(book_id)},
            {'$set': update_data}
        )
    
    def delete_book(self, book_id):
        return self.collection.update_one(
            {'_id': ObjectId(book_id)},
            {'$set': {'status': 'deleted'}}
        )
