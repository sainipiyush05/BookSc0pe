from utils.pdf_extractor import PDFExtractor
from utils.text_processor import TextProcessor
from models.search_index import SearchIndex
from bson import ObjectId

class DocumentIndexer:
    def __init__(self, db_connection):
        self.pdf_extractor = PDFExtractor()
        self.text_processor = TextProcessor()
        self.search_index = SearchIndex(db_connection)
    
    def index_document(self, book_id: str, file_path: str):
        print(f"Starting indexing for book: {book_id}")
        
        page_texts = self.pdf_extractor.extract_text_with_pages(file_path)
        total_words_indexed = 0
        
        for page_num, text in page_texts.items():
            keywords = self.text_processor.extract_keywords(text)
            
            for position, keyword in enumerate(keywords):
                self.search_index.add_index_entry(
                    word=keyword,
                    book_id=book_id,
                    page_number=page_num,
                    position=position
                )
                total_words_indexed += 1
        
        print(f"Indexing completed. Total words indexed: {total_words_indexed}")
        return total_words_indexed
    
    def search_documents(self, query: str, limit: int = 10):
        query_keywords = self.text_processor.extract_keywords(query)
        search_results = {}
        
        for keyword in query_keywords:
            results = self.search_index.search_word(keyword)
            
            for result in results:
                book_id = str(result['book_id'])
                
                if book_id not in search_results:
                    search_results[book_id] = {
                        'book_id': book_id,
                        'pages': set(),
                        'total_matches': 0,
                        'keywords_found': []
                    }
                
                search_results[book_id]['pages'].add(result['page_number'])
                search_results[book_id]['total_matches'] += result['frequency']
                search_results[book_id]['keywords_found'].append(keyword)
        
        final_results = []
        for book_id, data in search_results.items():
            data['pages'] = sorted(list(data['pages']))
            data['relevance_score'] = data['total_matches'] * len(data['keywords_found'])
            final_results.append(data)
        
        final_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return final_results[:limit]

