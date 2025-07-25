# backend/utils/search_engine.py
class SearchEngine:
    def __init__(self, db_connection):
        self.db = db_connection
        self.search_index = db_connection.search_index
        self.books = db_connection.books
        
    def search_with_relevance(self, query: str, limit: int = 10) -> List[Dict]:
        """Advanced search with TF-IDF relevance scoring"""
        query_terms = self._process_query(query)
        
        # Get total document count for IDF calculation
        total_docs = self.books.count_documents({'status': 'active'})
        
        # Find documents containing query terms
        search_results = defaultdict(lambda: {
            'pages': set(),
            'total_matches': 0,
            'term_scores': {},
            'page_matches': defaultdict(int)
        })
        
        for term in query_terms:
            # Find all documents containing this term
            term_results = list(self.search_index.find({'word': term.lower()}))
            
            for result in term_results:
                book_id = str(result['book_id'])
                page_num = result['page_number']
                
                # Calculate TF-IDF score for this term
                tf_idf_score = self._calculate_tf_idf(
                    term, result, total_docs
                )
                
                search_results[book_id]['pages'].add(page_num)
                search_results[book_id]['total_matches'] += result['frequency']
                search_results[book_id]['term_scores'][term] = tf_idf_score
                search_results[book_id]['page_matches'][page_num] += result['frequency']
        
        # Calculate final relevance scores
        final_results = []
        for book_id, data in search_results.items():
            # Get book information
            book_info = self.books.find_one({'_id': ObjectId(book_id)})
            if not book_info:
                continue
            
            # Calculate combined relevance score
            relevance_score = sum(data['term_scores'].values())
            
            # Boost score based on page concentration
            page_concentration_bonus = len(data['pages']) / book_info.get('total_pages', 1)
            final_score = relevance_score * (1 + page_concentration_bonus)
            
            result_item = {
                'book_id': book_id,
                'title': book_info['title'],
                'author': book_info['author'],
                'pages': sorted(list(data['pages'])),
                'page_matches': dict(data['page_matches']),
                'total_matches': data['total_matches'],
                'relevance_score': final_score,
                'term_scores': data['term_scores'],
                'keywords_found': list(data['term_scores'].keys())
            }
            final_results.append(result_item)
        
        # Sort by relevance score
        final_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return final_results[:limit]
    
    def _calculate_tf_idf(self, term: str, result: Dict, total_docs: int) -> float:
        """Calculate TF-IDF score"""
        # Term Frequency
        tf = result['frequency'] / result.get('doc_length', 1)
        
        # Document Frequency
        df = self.search_index.count_documents({'word': term.lower()})
        
        # Inverse Document Frequency
        idf = math.log(total_docs / (df + 1))
        
        return tf * idf
