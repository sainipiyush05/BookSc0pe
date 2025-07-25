import nltk
import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from typing import List

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class TextProcessor:
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
    
    def clean_text(self, text: str) -> str:
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = text.lower()
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def tokenize_and_process(self, text: str) -> List[str]:
        cleaned_text = self.clean_text(text)
        tokens = word_tokenize(cleaned_text)
        
        processed_tokens = [
            self.stemmer.stem(token) 
            for token in tokens 
            if token not in self.stop_words and len(token) > 2
        ]
        
        return processed_tokens
    
    def extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        processed_tokens = self.tokenize_and_process(text)
        keywords = [token for token in processed_tokens if len(token) >= min_length]
        return list(set(keywords))
