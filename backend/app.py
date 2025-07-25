from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
import os
import sys
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import json
import jwt
from datetime import datetime, timedelta
from functools import wraps
import re
import time
import logging

# PDF Processing imports
import PyPDF2
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

# Download required NLTK data (run once)
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    print("✅ NLTK data downloaded successfully")
except Exception as e:
    print(f"⚠️  NLTK download warning: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Basic configuration class
class Config:
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://127.0.0.1:27017/')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'desidoc_library')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'documents/uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Initialize Flask app
app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
CORS(app)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# PDF Processing Class
class PDFProcessor:
    def __init__(self):
        self.stemmer = PorterStemmer()
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        print("✅ PDF Processor initialized")
    
    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF with page-level mapping"""
        page_texts = {}
        total_pages = 0
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        text = page.extract_text()
                        page_texts[page_num] = text
                    except Exception as e:
                        print(f"Warning: Could not extract text from page {page_num}: {e}")
                        page_texts[page_num] = ""
                        
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return {}, 0
            
        return page_texts, total_pages
    
    def process_text_for_search(self, text):
        """Process text for search indexing"""
        if not text:
            return []
            
        try:
            # Convert to lowercase and tokenize
            words = word_tokenize(text.lower())
            
            # Remove stop words and non-alphabetic tokens
            processed_words = []
            for word in words:
                if (word.isalpha() and 
                    len(word) > 2 and 
                    word not in self.stop_words):
                    # Apply stemming
                    stemmed_word = self.stemmer.stem(word)
                    processed_words.append(stemmed_word)
            
            return processed_words
        except Exception as e:
            print(f"Error processing text: {e}")
            return []
    
    def create_search_index(self, book_id, page_texts):
        """Create search index entries for the document"""
        index_entries = []
        
        for page_num, text in page_texts.items():
            if not text.strip():
                continue
                
            processed_words = self.process_text_for_search(text)
            
            if not processed_words:
                continue
            
            # Count word frequencies
            word_freq = {}
            for word in processed_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Create index entries
            for word, frequency in word_freq.items():
                index_entries.append({
                    'word': word,
                    'book_id': book_id,
                    'page_number': page_num,
                    'frequency': frequency,
                    'position': processed_words.index(word) if word in processed_words else 0
                })
        
        return index_entries

# Enhanced database connection with comprehensive error handling
def create_robust_database_connection(max_retries=3):
    """Create database connection with multiple fallback strategies"""
    print("=" * 60)
    print("🔍 INITIALIZING DATABASE CONNECTION")
    print("=" * 60)
    
    connection_configs = [
        {
            'uri': 'mongodb://127.0.0.1:27017/',
            'name': 'Local IPv4'
        },
        {
            'uri': 'mongodb://localhost:27017/',
            'name': 'Local hostname'
        },
        {
            'uri': 'mongodb://127.0.0.1:27017/desidoc_library',
            'name': 'Direct database'
        }
    ]
    
    for config in connection_configs:
        for attempt in range(max_retries):
            try:
                print(f"📡 Attempting connection: {config['name']} (attempt {attempt + 1}/{max_retries})")
                
                client = MongoClient(
                    config['uri'],
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=20000
                )
                
                # Test connection
                client.admin.command('ping')
                db = client[app.config['DATABASE_NAME']]
                
                # Test database operations
                collections = db.list_collection_names()
                
                print(f"✅ Database connection successful!")
                print(f"   URI: {config['uri']}")
                print(f"   Database: {db.name}")
                print(f"   Collections: {len(collections)}")
                print("=" * 60)
                
                return client, db
                
            except (ServerSelectionTimeoutError, ConnectionFailure) as e:
                print(f"❌ Connection failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                break
    
    print("❌ ALL DATABASE CONNECTION ATTEMPTS FAILED")
    print("⚠️  Switching to fallback mode")
    print("=" * 60)
    return None, None

# Initialize database connection and PDF processor
client, db = create_robust_database_connection()
pdf_processor = PDFProcessor()

# Fallback User Management System
class FallbackUserManager:
    """In-memory user management for when database is unavailable"""
    
    def __init__(self):
        print("⚠️  Initializing fallback user management system")
        self.users = {
            'admin': {
                'password_hash': generate_password_hash('Admin@123'),
                'role': 'admin',
                'full_name': 'System Administrator',
                'department': 'DESIDOC',
                'email': 'admin@desidoc.drdo.in',
                'permissions': {
                    'document_access': ['public', 'internal', 'confidential', 'restricted'],
                    'upload_documents': True,
                    'user_management': True,
                    'system_admin': True
                }
            },
            'scientist': {
                'password_hash': generate_password_hash('Scientist@123'),
                'role': 'scientist',
                'full_name': 'Test Scientist',
                'department': 'DRDO',
                'email': 'scientist@desidoc.drdo.in',
                'permissions': {
                    'document_access': ['public', 'internal', 'confidential'],
                    'upload_documents': True
                }
            },
            'student': {
                'password_hash': generate_password_hash('Student@123'),
                'role': 'student',
                'full_name': 'Test Student',
                'department': 'Academic',
                'email': 'student@desidoc.drdo.in',
                'permissions': {
                    'document_access': ['public'],
                    'upload_documents': False
                }
            }
        }
        self.pending_requests = []
    
    def authenticate_user(self, username, password):
        """Authenticate user against in-memory storage"""
        user_data = self.users.get(username)
        if user_data and check_password_hash(user_data['password_hash'], password):
            return {
                '_id': f"fallback_{username}",
                'username': username,
                'role': user_data['role'],
                'profile': {'full_name': user_data['full_name']},
                'department': user_data['department'],
                'email': user_data['email'],
                'permissions': user_data['permissions'],
                'is_active': True
            }
        return None
    
    def generate_jwt_token(self, user_id, role, username):
        """Generate JWT token"""
        payload = {
            'user_id': str(user_id),
            'role': role,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=8)
        }
        return jwt.encode(payload, app.secret_key, algorithm='HS256')
    
    def create_pending_user(self, user_data):
        """Store pending user request"""
        request_data = {
            'id': len(self.pending_requests) + 1,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending',
            **user_data
        }
        self.pending_requests.append(request_data)
        print(f"📝 Registration request logged: {user_data['username']}")
        return str(request_data['id']), "Access request submitted successfully"

# Database-backed User Management System
class DatabaseUserManager:
    """Full user management with MongoDB backend"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.users_collection = self.db.users
        self.roles_collection = self.db.role_permissions
        self.pending_users_collection = self.db.pending_users
        self.init_default_roles()
        print("✅ Database user management initialized")
    
    def init_default_roles(self):
        """Initialize default role permissions"""
        default_roles = [
            {
                "role": "scientist",
                "permissions": {
                    "document_access": ["public", "internal", "confidential"],
                    "search_features": ["basic", "advanced"],
                    "upload_documents": True,
                    "download_documents": True,
                    "max_downloads_per_day": 100
                }
            },
            {
                "role": "student",
                "permissions": {
                    "document_access": ["public"],
                    "search_features": ["basic"],
                    "upload_documents": False,
                    "download_documents": True,
                    "max_downloads_per_day": 10
                }
            },
            {
                "role": "librarian",
                "permissions": {
                    "document_access": ["public", "internal", "confidential"],
                    "search_features": ["basic", "advanced"],
                    "upload_documents": True,
                    "download_documents": True,
                    "user_management": True,
                    "max_downloads_per_day": 200
                }
            },
            {
                "role": "admin",
                "permissions": {
                    "document_access": ["public", "internal", "confidential", "restricted"],
                    "search_features": ["basic", "advanced"],
                    "upload_documents": True,
                    "download_documents": True,
                    "user_management": True,
                    "system_admin": True,
                    "max_downloads_per_day": 500
                }
            },
            {
                "role": "guest",
                "permissions": {
                    "document_access": ["public"],
                    "search_features": ["basic"],
                    "upload_documents": False,
                    "download_documents": False,
                    "max_downloads_per_day": 5
                }
            }
        ]
        
        for role_data in default_roles:
            try:
                self.roles_collection.update_one(
                    {"role": role_data["role"]},
                    {"$set": role_data},
                    upsert=True
                )
            except Exception as e:
                print(f"Warning: Could not initialize role {role_data['role']}: {e}")
    
    def authenticate_user(self, username, password):
        """Authenticate user against database"""
        try:
            user = self.users_collection.find_one({'username': username, 'is_active': True})
            if user and check_password_hash(user['password_hash'], password):
                # Update last login
                self.users_collection.update_one(
                    {'_id': user['_id']},
                    {'$set': {'last_login': datetime.now()}}
                )
                return user
        except Exception as e:
            print(f"Authentication error: {e}")
        return None
    
    def generate_jwt_token(self, user_id, role, username):
        """Generate JWT token"""
        payload = {
            'user_id': str(user_id),
            'role': role,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=8)
        }
        return jwt.encode(payload, app.secret_key, algorithm='HS256')
    
    def create_pending_user(self, user_data):
        """Create pending user registration request"""
        try:
            # Check if username/email already exists
            existing_user = self.users_collection.find_one({
                '$or': [
                    {'username': user_data['username']},
                    {'email': user_data['email']}
                ]
            })
            
            existing_pending = self.pending_users_collection.find_one({
                '$or': [
                    {'username': user_data['username']},
                    {'email': user_data['email']}
                ]
            })
            
            if existing_user or existing_pending:
                return None, "Username or email already exists"
            
            request_data = {
                'full_name': user_data['full_name'],
                'username': user_data['username'],
                'email': user_data['email'],
                'employee_id': user_data.get('employee_id', ''),
                'department': user_data['department'],
                'requested_role': user_data['requested_role'],
                'justification': user_data['justification'],
                'supervisor_email': user_data.get('supervisor_email', ''),
                'status': 'pending',
                'request_date': datetime.now()
            }
            
            result = self.pending_users_collection.insert_one(request_data)
            return str(result.inserted_id), "Access request submitted successfully"
            
        except Exception as e:
            print(f"Error creating pending user: {e}")
            return None, f"Failed to submit request: {str(e)}"
    
    def create_default_admin(self):
        """Create default admin user if none exists"""
        try:
            admin_exists = self.users_collection.find_one({'role': 'admin'})
            if not admin_exists:
                admin_data = {
                    'username': 'admin',
                    'email': 'admin@desidoc.drdo.in',
                    'password_hash': generate_password_hash('Admin@123'),
                    'role': 'admin',
                    'department': 'DESIDOC',
                    'security_clearance': 'restricted',
                    'created_date': datetime.now(),
                    'last_login': None,
                    'is_active': True,
                    'profile': {
                        'full_name': 'System Administrator',
                        'employee_id': 'DRDO2024001',
                        'designation': 'Administrator',
                        'contact_number': ''
                    },
                    'permissions': {
                        'document_access': ['public', 'internal', 'confidential', 'restricted'],
                        'upload_documents': True,
                        'user_management': True,
                        'system_admin': True
                    }
                }
                
                result = self.users_collection.insert_one(admin_data)
                print(f"✅ Default admin user created: {result.inserted_id}")
                return True
            else:
                print("✅ Admin user already exists")
                return True
        except Exception as e:
            print(f"❌ Failed to create admin user: {e}")
            return False

# Initialize user manager based on database availability
if db is not None:
    try:
        user_manager = DatabaseUserManager(db)
        user_manager.create_default_admin()
        print("✅ Using database-backed user management")
    except Exception as e:
        print(f"❌ Database user manager failed: {e}")
        user_manager = FallbackUserManager()
        print("⚠️  Switched to fallback user management")
else:
    user_manager = FallbackUserManager()
    print("⚠️  Using fallback user management (no database)")

# Authentication decorators
def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session-based authentication first
        if 'logged_in' in session and session['logged_in']:
            request.current_user = {
                'user_id': session.get('user_id', 'session_user'),
                'username': session.get('username', 'unknown'),
                'role': session.get('role', 'guest'),
                'permissions': session.get('permissions', {}),
                'full_name': session.get('full_name', session.get('username', 'User')),
                'department': session.get('department', 'Unknown')
            }
            return f(*args, **kwargs)
        
        # Check JWT token authentication
        token = request.headers.get('Authorization')
        if not token and 'auth_token' in session:
            token = f"Bearer {session['auth_token']}"
        
        if not token:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            
            # Set basic user info from token
            request.current_user = {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'role': payload['role'],
                'permissions': {},
                'full_name': payload['username'],
                'department': 'Unknown'
            }
            
        except jwt.ExpiredSignatureError:
            if request.is_json:
                return jsonify({'error': 'Token expired'}), 401
            return redirect(url_for('login'))
        except jwt.InvalidTokenError:
            if request.is_json:
                return jsonify({'error': 'Invalid token'}), 401
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Authentication error: {e}")
            if request.is_json:
                return jsonify({'error': 'Authentication failed'}), 401
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            user_role = request.current_user.get('role')
            if user_role not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Main routes
@app.route('/')
def index():
    """Main landing page"""
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('dashboard'))
    if 'auth_token' in session:
        try:
            payload = jwt.decode(session['auth_token'], app.secret_key, algorithms=['HS256'])
            return redirect(url_for('dashboard'))
        except:
            session.clear()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page and handler"""
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        # Get form data
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '')
        
        print(f"=== LOGIN ATTEMPT ===")
        print(f"Username: {username}")
        print(f"Role: {role}")
        
        if not username or not password:
            return render_template('login.html', error='Username and password are required')
        
        # Authenticate user
        user = user_manager.authenticate_user(username, password)
        
        if user:
            print(f"✅ Authentication successful for: {username}")
            
            # Check if role matches (for database users)
            if hasattr(user, 'get') and user.get('role') != role and role:
                print(f"❌ Role mismatch: user role={user.get('role')}, selected role={role}")
                return render_template('login.html', error='Invalid role selected for this user')
            
            # Store user info in session
            session['logged_in'] = True
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['profile']['full_name']
            session['department'] = user.get('department', 'Unknown')
            session['permissions'] = user.get('permissions', {})
            
            # Also generate JWT token for API access
            token = user_manager.generate_jwt_token(user['_id'], user['role'], user['username'])
            session['auth_token'] = token
            
            print(f"✅ Session created for: {username}")
            print(f"🔄 Redirecting to dashboard...")
            
            if request.is_json:
                return jsonify({
                    'message': 'Login successful',
                    'token': token,
                    'user': {
                        'username': user['username'],
                        'role': user['role'],
                        'full_name': user['profile']['full_name']
                    }
                })
            else:
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
        
        print(f"❌ Authentication failed for: {username}")
        error_msg = 'Invalid username or password'
        if request.is_json:
            return jsonify({'error': error_msg}), 401
        return render_template('login.html', error=error_msg)
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        error_msg = 'An error occurred during login. Please try again.'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        return render_template('login.html', error=error_msg)

@app.route('/logout')
def logout():
    """User logout"""
    username = session.get('username', 'Unknown')
    session.clear()
    print(f"🚪 User logged out: {username}")
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration request page"""
    if request.method == 'GET':
        return render_template('signup.html')
    
    try:
        # Get form data
        data = request.form.to_dict()
        
        # Validate required fields
        required_fields = ['full_name', 'username', 'email', 'department', 'requested_role', 'justification']
        missing_fields = [field for field in required_fields if not data.get(field, '').strip()]
        
        if missing_fields:
            error_msg = f'Please fill in all required fields: {", ".join(missing_fields)}'
            return render_template('signup.html', error=error_msg)
        
        # Process registration request
        request_id, message = user_manager.create_pending_user(data)
        
        if request_id:
            success_msg = f'{message}. You will be contacted once your request is reviewed.'
            return render_template('signup.html', success=success_msg)
        else:
            return render_template('signup.html', error=message)
            
    except Exception as e:
        print(f"Signup error: {e}")
        error_msg = 'An error occurred while processing your request. Please try again.'
        return render_template('signup.html', error=error_msg)

# Document Upload Route
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    """Document upload page and handler"""
    if request.method == 'GET':
        return render_template('upload.html', user=request.current_user)
    
    try:
        # Check upload permissions
        user_permissions = request.current_user.get('permissions', {})
        if not user_permissions.get('upload_documents', False):
            flash('You do not have permission to upload documents.', 'error')
            return redirect(url_for('dashboard'))
        
        # Validate file upload
        if 'file' not in request.files:
            flash('No file selected for upload.', 'error')
            return render_template('upload.html', user=request.current_user)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected for upload.', 'error')
            return render_template('upload.html', user=request.current_user)
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            flash('Only PDF files are allowed.', 'error')
            return render_template('upload.html', user=request.current_user)
        
        # Get form data
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        subject = request.form.get('subject', '').strip()
        isbn = request.form.get('isbn', '').strip()
        classification = request.form.get('classification', 'public')
        
        if not title:
            flash('Document title is required.', 'error')
            return render_template('upload.html', user=request.current_user)
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        
        # Process PDF and extract text
        print(f"📄 Processing PDF: {unique_filename}")
        page_texts, total_pages = pdf_processor.extract_text_from_pdf(file_path)
        
        if not page_texts:
            flash('Failed to extract text from PDF. Please check the file.', 'error')
            os.remove(file_path)  # Clean up
            return render_template('upload.html', user=request.current_user)
        
        # Create book record
        book_data = {
            'title': title,
            'author': author,
            'isbn': isbn,
            'subject': subject,
            'classification': classification,
            'total_pages': total_pages,
            'file_path': file_path,
            'original_filename': filename,
            'unique_filename': unique_filename,
            'uploaded_by': request.current_user['user_id'],
            'uploader_name': request.current_user['full_name'],
            'upload_date': datetime.now(),
            'status': 'active'
        }
        
        # Save to database
        if db is not None:
            try:
                # Insert book record
                book_result = db.books.insert_one(book_data)
                book_id = str(book_result.inserted_id)
                
                # Create search index
                print(f"🔍 Creating search index for book: {book_id}")
                index_entries = pdf_processor.create_search_index(book_id, page_texts)
                
                # Insert search index entries
                if index_entries:
                    db.search_index.insert_many(index_entries)
                    print(f"✅ Indexed {len(index_entries)} word entries")
                
                flash(f'Document "{title}" uploaded and indexed successfully! ({len(index_entries)} words indexed)', 'success')
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                print(f"Database error during upload: {e}")
                flash('Failed to save document to database.', 'error')
                if os.path.exists(file_path):
                    os.remove(file_path)  # Clean up
                return render_template('upload.html', user=request.current_user)
        else:
            flash('Database not available. Document uploaded but not indexed.', 'warning')
            return render_template('upload.html', user=request.current_user)
            
    except Exception as e:
        print(f"Upload error: {e}")
        flash('An error occurred during upload. Please try again.', 'error')
        return render_template('upload.html', user=request.current_user)

# Document Search Route
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search_documents():
    """Document search page and handler"""
    if request.method == 'GET':
        return render_template('search.html', user=request.current_user)
    
    try:
        query = request.form.get('query', '').strip()
        if not query:
            flash('Please enter a search query.', 'error')
            return render_template('search.html', user=request.current_user)
        
        # Get user access levels
        user_permissions = request.current_user.get('permissions', {})
        allowed_access_levels = user_permissions.get('document_access', ['public'])
        
        if db is not None:
            # Process search query
            processed_query = pdf_processor.process_text_for_search(query)
            
            if not processed_query:
                flash('No valid search terms found.', 'error')
                return render_template('search.html', user=request.current_user)
            
            print(f"🔍 Searching for: {processed_query}")
            
            # Search in index
            search_results = []
            book_matches = {}
            
            for word in processed_query:
                # Find documents containing this word
                matches = list(db.search_index.find({'word': word}))
                
                for match in matches:
                    book_id = match['book_id']
                    
                    if book_id not in book_matches:
                        book_matches[book_id] = {
                            'pages': set(),
                            'total_matches': 0,
                            'words_found': set()
                        }
                    
                    book_matches[book_id]['pages'].add(match['page_number'])
                    book_matches[book_id]['total_matches'] += match['frequency']
                    book_matches[book_id]['words_found'].add(word)
            
            # Get book details and filter by access level
            for book_id, match_data in book_matches.items():
                try:
                    book = db.books.find_one({'_id': ObjectId(book_id)})
                    
                    if book and book.get('classification', 'public') in allowed_access_levels:
                        search_results.append({
                            'book_id': book_id,
                            'title': book['title'],
                            'author': book['author'],
                            'subject': book.get('subject', ''),
                            'classification': book.get('classification', 'public'),
                            'pages': sorted(list(match_data['pages'])),
                            'total_matches': match_data['total_matches'],
                            'words_found': list(match_data['words_found']),
                            'upload_date': book['upload_date'].strftime('%Y-%m-%d'),
                            'uploader_name': book.get('uploader_name', 'Unknown')
                        })
                except Exception as e:
                    print(f"Error processing book {book_id}: {e}")
                    continue
            
            # Sort by relevance (total matches)
            search_results.sort(key=lambda x: x['total_matches'], reverse=True)
            
            print(f"✅ Search completed: {len(search_results)} results found")
            
            return render_template('search.html', 
                                 user=request.current_user,
                                 query=query,
                                 results=search_results,
                                 total_results=len(search_results))
        else:
            flash('Search functionality requires database connection.', 'error')
            return render_template('search.html', user=request.current_user)
            
    except Exception as e:
        print(f"Search error: {e}")
        flash('An error occurred during search. Please try again.', 'error')
        return render_template('search.html', user=request.current_user)

# Browse Documents Route
@app.route('/browse')
@login_required
def browse_documents():
    """Browse all available documents"""
    try:
        user_permissions = request.current_user.get('permissions', {})
        allowed_access_levels = user_permissions.get('document_access', ['public'])
        
        if db is not None:
            # Get all books user has access to
            books = list(db.books.find({'status': 'active'}))
            accessible_books = []
            
            for book in books:
                if book.get('classification', 'public') in allowed_access_levels:
                    book_info = {
                        'id': str(book['_id']),
                        'title': book['title'],
                        'author': book['author'],
                        'subject': book.get('subject', ''),
                        'classification': book.get('classification', 'public'),
                        'total_pages': book.get('total_pages', 0),
                        'upload_date': book['upload_date'].strftime('%Y-%m-%d'),
                        'uploaded_by': book.get('uploader_name', 'Unknown')
                    }
                    accessible_books.append(book_info)
            
            # Sort by upload date (newest first)
            accessible_books.sort(key=lambda x: x['upload_date'], reverse=True)
            
            return render_template('browse.html', 
                                 user=request.current_user,
                                 books=accessible_books,
                                 total_books=len(accessible_books))
        else:
            flash('Browse functionality requires database connection.', 'error')
            return render_template('browse.html', user=request.current_user, books=[])
            
    except Exception as e:
        print(f"Browse error: {e}")
        flash('An error occurred while browsing documents.', 'error')
        return render_template('browse.html', user=request.current_user, books=[])

# Dashboard route with working navigation
@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard for all user roles"""
    user_info = {
        'username': request.current_user['username'],
        'role': request.current_user['role'],
        'full_name': request.current_user['full_name'],
        'department': request.current_user['department']
    }
    
    print(f"📊 Dashboard accessed by: {user_info['username']} ({user_info['role']})")
    
    # Get statistics if database is available
    stats = {'total_books': 0, 'total_searches': 0, 'total_users': 0}
    if db is not None:
        try:
            stats['total_books'] = db.books.count_documents({'status': 'active'})
            stats['total_users'] = db.users.count_documents({'is_active': True})
            stats['total_searches'] = db.search_index.count_documents({})
        except:
            pass
    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DESIDOC Dashboard - {user_info['role'].title()}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .dashboard-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2rem 0;
            }}
            .feature-card {{
                transition: transform 0.2s;
                border: none;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .feature-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            }}
            .status-badge {{
                font-size: 0.9rem;
                padding: 0.5rem 1rem;
            }}
            .action-btn {{
                width: 100%;
                margin-bottom: 0.5rem;
                padding: 0.75rem;
                font-weight: 500;
            }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="/dashboard">
                    <i class="fas fa-book-open me-2"></i>DESIDOC Library System
                </a>
                <div class="navbar-nav ms-auto">
                    <span class="navbar-text me-3">
                        <i class="fas fa-user me-1"></i>Welcome, {user_info['full_name']}
                    </span>
                    <a class="nav-link" href="/logout">
                        <i class="fas fa-sign-out-alt me-1"></i>Logout
                    </a>
                </div>
            </div>
        </nav>
        
        <div class="dashboard-header">
            <div class="container">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h1><i class="fas fa-tachometer-alt me-2"></i>{user_info['role'].title()} Dashboard</h1>
                        <p class="lead mb-0">Defence Scientific Information & Documentation Centre</p>
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="badge bg-light text-dark fs-6">
                            <i class="fas fa-shield-alt me-1"></i>{user_info['role'].upper()}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="container mt-4">
            <div class="row">
                <div class="col-lg-8">
                    <div class="card feature-card mb-4">
                        <div class="card-header bg-success text-white">
                            <h4><i class="fas fa-check-circle me-2"></i>System Status: Operational</h4>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-success">
                                <h5><i class="fas fa-rocket me-2"></i>🎉 DESIDOC Library Search System is Fully Operational!</h5>
                                <p>Document upload, search, and browse features are now active and ready for use.</p>
                                <hr>
                                <div class="row">
                                    <div class="col-md-6">
                                        <p><strong><i class="fas fa-user me-1"></i>User:</strong> {user_info['username']}</p>
                                        <p><strong><i class="fas fa-id-badge me-1"></i>Full Name:</strong> {user_info['full_name']}</p>
                                    </div>
                                    <div class="col-md-6">
                                        <p><strong><i class="fas fa-user-tag me-1"></i>Role:</strong> {user_info['role']}</p>
                                        <p><strong><i class="fas fa-building me-1"></i>Department:</strong> {user_info['department']}</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-body text-center">
                                            <i class="fas fa-search fa-2x text-primary mb-2"></i>
                                            <h6>Document Search</h6>
                                            <a href="/search" class="btn btn-primary action-btn">
                                                <i class="fas fa-search me-1"></i>Search Documents
                                            </a>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-body text-center">
                                            <i class="fas fa-upload fa-2x text-success mb-2"></i>
                                            <h6>Upload Documents</h6>
                                            <a href="/upload" class="btn btn-success action-btn">
                                                <i class="fas fa-upload me-1"></i>Upload Document
                                            </a>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-body text-center">
                                            <i class="fas fa-list fa-2x text-info mb-2"></i>
                                            <h6>Browse Library</h6>
                                            <a href="/browse" class="btn btn-info action-btn">
                                                <i class="fas fa-list me-1"></i>Browse All Documents
                                            </a>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-body text-center">
                                            <i class="fas fa-cog fa-2x text-secondary mb-2"></i>
                                            <h6>System Status</h6>
                                            <a href="/api/status" class="btn btn-outline-secondary action-btn" target="_blank">
                                                <i class="fas fa-external-link-alt me-1"></i>API Status
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4">
                    <div class="card feature-card mb-4">
                        <div class="card-header">
                            <h5><i class="fas fa-chart-bar me-2"></i>Library Statistics</h5>
                        </div>
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span><i class="fas fa-book me-1"></i>Total Documents</span>
                                <span class="badge bg-primary status-badge">{stats['total_books']}</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span><i class="fas fa-users me-1"></i>Active Users</span>
                                <span class="badge bg-info status-badge">{stats['total_users']}</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span><i class="fas fa-search me-1"></i>Indexed Words</span>
                                <span class="badge bg-success status-badge">{stats['total_searches']}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card feature-card mb-4">
                        <div class="card-header">
                            <h5><i class="fas fa-cogs me-2"></i>System Health</h5>
                        </div>
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span><i class="fas fa-shield-check me-1"></i>Authentication</span>
                                <span class="badge bg-success status-badge">✓ Active</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span><i class="fas fa-database me-1"></i>Database</span>
                                <span class="badge bg-{'success' if db is not None else 'warning'} status-badge">
                                    {'✓ Connected' if db is not None else '⚠ Fallback'}
                                </span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span><i class="fas fa-upload me-1"></i>Document Upload</span>
                                <span class="badge bg-success status-badge">✓ Active</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span><i class="fas fa-search me-1"></i>Search Engine</span>
                                <span class="badge bg-success status-badge">✓ Active</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <span><i class="fas fa-file-pdf me-1"></i>PDF Processing</span>
                                <span class="badge bg-success status-badge">✓ Active</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card feature-card">
                        <div class="card-header">
                            <h5><i class="fas fa-info-circle me-2"></i>Quick Info</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>System Version:</strong> v1.0.0</p>
                            <p><strong>Login Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p><strong>Session Type:</strong> {'Database' if db is not None else 'Fallback'}</p>
                            <p><strong>PDF Processor:</strong> Active</p>
                            <hr>
                            <div class="d-grid">
                                <a href="/signup" class="btn btn-outline-primary btn-sm">
                                    <i class="fas fa-user-plus me-1"></i>Request New Account
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="bg-light mt-5 py-4">
            <div class="container text-center">
                <p class="text-muted mb-0">
                    <i class="fas fa-shield-alt me-1"></i>DESIDOC Library Search System - 
                    Defence Research and Development Organisation
                </p>
            </div>
        </footer>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return dashboard_html

# API routes
@app.route('/api/status')
def api_status():
    """System status API"""
    return jsonify({
        'status': 'operational',
        'database': 'connected' if db is not None else 'fallback',
        'user_management': 'active',
        'authentication': 'active',
        'pdf_processing': 'active',
        'search_engine': 'active',
        'upload_system': 'active',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/test')
def api_test():
    """Test API endpoint"""
    return jsonify({
        'message': 'DESIDOC API is working correctly',
        'database_status': 'connected' if db is not None else 'fallback_mode',
        'user_manager': type(user_manager).__name__,
        'pdf_processor': 'active',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/user-info')
@login_required
def api_user_info():
    """Get current user information"""
    return jsonify({
        'user': request.current_user,
        'session_active': True,
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    if request.is_json:
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('login.html', error='Page not found. Please login to continue.'), 404

@app.errorhandler(403)
def forbidden(error):
    if request.is_json:
        return jsonify({'error': 'Access forbidden'}), 403
    return render_template('login.html', error='Access denied. Please check your permissions.'), 403

@app.errorhandler(500)
def internal_error(error):
    if request.is_json:
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('login.html', error='System error. Please try again later.'), 500

# Startup function
def initialize_system():
    """Initialize system components"""
    print("🚀 DESIDOC Library Search System Initialization")
    print("=" * 60)
    
    # Create required directories
    directories = [
        app.config['UPLOAD_FOLDER'],
        'logs',
        'frontend/templates',
        'frontend/static'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Directory ensured: {directory}")
        except Exception as e:
            print(f"⚠️  Could not create directory {directory}: {e}")
    
    # System status summary
    print("=" * 60)
    print("📊 SYSTEM STATUS SUMMARY")
    print("=" * 60)
    print(f"🗄️  Database: {'✅ Connected' if db is not None else '⚠️  Fallback Mode'}")
    print(f"👤 User Management: {'✅ Database-backed' if isinstance(user_manager, DatabaseUserManager) else '⚠️  In-memory fallback'}")
    print(f"🔐 Authentication: ✅ Active")
    print(f"📄 PDF Processing: ✅ Active")
    print(f"🔍 Search Engine: ✅ Active")
    print(f"📤 Upload System: ✅ Active")
    print(f"🌐 Web Interface: ✅ Ready")
    print("=" * 60)
    print("🔑 DEFAULT CREDENTIALS")
    print("=" * 60)
    print("Admin: admin / Admin@123")
    print("Scientist: scientist / Scientist@123")
    print("Student: student / Student@123")
    print("=" * 60)
    print("🌍 ACCESS URLS")
    print("=" * 60)
    print("Main: http://localhost:5000")
    print("Login: http://localhost:5000/login")
    print("Dashboard: http://localhost:5000/dashboard")
    print("Upload: http://localhost:5000/upload")
    print("Search: http://localhost:5000/search")
    print("Browse: http://localhost:5000/browse")
    print("Signup: http://localhost:5000/signup")
    print("API Status: http://localhost:5000/api/status")
    print("=" * 60)

if __name__ == '__main__':
    initialize_system()
    app.run(debug=True, host='0.0.0.0', port=5000)
