import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'desidoc_library')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'documents/uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    DEFAULT_SEARCH_LIMIT = 10
    MAX_SEARCH_LIMIT = 100
    MIN_WORD_LENGTH = 3
    MAX_WORDS_PER_PAGE = 10000
