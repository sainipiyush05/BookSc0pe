from flask import Blueprint, request, jsonify, session, redirect, url_for
from models.user import User
from functools import wraps
import jwt

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            payload = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
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

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user_model = User(db)
    user = user_model.authenticate_user(username, password)
    
    if user:
        token = user_model.generate_jwt_token(user['_id'], user['role'])
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'role': user['role'],
                'full_name': user['profile']['full_name'],
                'department': user['department'],
                'permissions': user['permissions']
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/register', methods=['POST'])
@login_required
@role_required(['librarian', 'admin'])
def register():
    """User registration endpoint (admin only)"""
    data = request.get_json()
    
    required_fields = ['username', 'email', 'password', 'role', 'full_name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    user_model = User(db)
    
    # Check if user already exists
    existing_user = user_model.collection.find_one({'username': data['username']})
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 409
    
    try:
        result = user_model.create_user(data)
        return jsonify({
            'message': 'User created successfully',
            'user_id': str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500
