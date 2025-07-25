# backend/utils/advanced_indexer.py
import math
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

class AdvancedIndexer:
    def __init__(self, db_connection):
        self.db = db_connection
        self.search_index = self.db.search_index
        self.document_stats = self.db.document_stats
        
    def calculate_tf_idf(self, term: str, document_id: str, total_documents: int) -> float:
        """Calculate TF-IDF score for a term in a document"""
        # Get term frequency in document
        tf_data = self.search_index.find_one({
            'word': term.lower(),
            'book_id': ObjectId(document_id)
        })
        
        if not tf_data:
            return 0.0

        term_freq = tf_data['frequency']
        doc_length = tf_data.get('doc_length', 1)
        
        # Calculate TF (Term Frequency)
        tf = term_freq / doc_length
        
        # Calculate IDF (Inverse Document Frequency)
        docs_with_term = self.search_index.count_documents({'word': term.lower()})
        idf = math.log(total_documents / (docs_with_term + 1))
        
        return tf * idf
    
    def index_document_advanced(self, book_id: str, file_path: str):
        """Advanced indexing with TF-IDF calculations"""
        processor = MultiFormatProcessor()
        page_texts = processor.extract_text_with_pages(file_path)
        
        # Calculate document statistics
        total_words = 0
        word_frequencies = defaultdict(int)
        
        for page_num, text in page_texts.items():
            words = self._tokenize_text(text)
            total_words += len(words)
            
            for position, word in enumerate(words):
                word_frequencies[word.lower()] += 1
                
                # Store detailed index entry
                self.search_index.update_one(
                    {
                        'word': word.lower(),
                        'book_id': ObjectId(book_id),
                        'page_number': page_num
                    },
                    {
                        '$set': {
                            'word': word.lower(),
                            'book_id': ObjectId(book_id),
                            'page_number': page_num,
                            'position': position,
                            'doc_length': total_words
                        },
                        '$inc': {'frequency': 1}
                    },
                    upsert=True
                )
        
        # Store document statistics
        self.document_stats.update_one(
            {'book_id': ObjectId(book_id)},
            {
                '$set': {
                    'total_words': total_words,
                    'unique_words': len(word_frequencies),
                    'word_frequencies': dict(word_frequencies)
                }
            },
            upsert=True
        )
        
        return len(word_frequencies)
