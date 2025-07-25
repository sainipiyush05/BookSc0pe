from bson import ObjectId

class SearchIndex:
    def __init__(self, db_connection):
        self.db = db_connection
        self.collection = self.db.search_index
    
    def add_index_entry(self, word, book_id, page_number, position):
        index_entry = {
            'word': word.lower(),
            'book_id': ObjectId(book_id) if isinstance(book_id, str) else book_id,
            'page_number': page_number,
            'position': position,
            'frequency': 1
        }
        
        existing = self.collection.find_one({
            'word': word.lower(),
            'book_id': ObjectId(book_id) if isinstance(book_id, str) else book_id,
            'page_number': page_number
        })
        
        if existing:
            self.collection.update_one(
                {'_id': existing['_id']},
                {'$inc': {'frequency': 1}}
            )
        else:
            self.collection.insert_one(index_entry)
    
    def search_word(self, word):
        return list(self.collection.find({'word': word.lower()}))
    
    def get_book_words(self, book_id):
        return list(self.collection.find({'book_id': ObjectId(book_id)}))
    
    def delete_book_index(self, book_id):
        return self.collection.delete_many({'book_id': ObjectId(book_id)})
