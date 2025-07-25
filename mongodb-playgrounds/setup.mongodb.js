// Database setup
use('desidoc_library')

// Create collections
db.createCollection('books')
db.createCollection('search_index')

// Create indexes for better performance
db.books.createIndex({title: 1})
db.books.createIndex({author: 1})
db.books.createIndex({subject: 1})
db.search_index.createIndex({word: 1, book_id: 1})
db.search_index.createIndex({book_id: 1, page_number: 1})
