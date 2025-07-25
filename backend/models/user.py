# backend/models/user.py
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
from bson import ObjectId

class User:
    def __init__(self, db_connection):
        self.db = db_connection
        self.collection = self.db.users
        self.roles_collection = self.db.role_permissions
    
    def create_user(self, user_data):
        """Create new user with role-based permissions"""
        user_document = {
            'username': user_data['username'],
            'email': user_data['email'],
            'password_hash': generate_password_hash(user_data['password']),
            'role': user_data['role'],
            'department': user_data.get('department', ''),
            'security_clearance': user_data.get('security_clearance', 'public'),
            'created_date': datetime.now(),
            'last_login': None,
            'is_active': True,
            'profile': {
                'full_name': user_data.get('full_name', ''),
                'employee_id': user_data.get('employee_id', ''),
                'designation': user_data.get('designation', ''),
                'contact_number': user_data.get('contact_number', '')
            }
        }
        
        # Set role-based permissions
        permissions = self.get_role_permissions(user_data['role'])
        user_document['permissions'] = permissions
        
        return self.collection.insert_one(user_document)
    
    def authenticate_user(self, username, password):
        """Authenticate user and return user data"""
        user = self.collection.find_one({'username': username, 'is_active': True})
        
        if user and check_password_hash(user['password_hash'], password):
            # Update last login
            self.collection.update_one(
                {'_id': user['_id']},
                {'$set': {'last_login': datetime.now()}}
            )
            return user
        return None
    
    def get_role_permissions(self, role):
        """Get permissions for specific role"""
        role_data = self.roles_collection.find_one({'role': role})
        if role_data:
            return role_data['permissions']
        
        # Default permissions for unknown roles
        return {
            'document_access': ['public'],
            'search_features': ['basic'],
            'upload_documents': False,
            'download_documents': False,
            'annotation_rights': False,
            'collaboration_tools': False,
            'analytics_access': False
        }
    
    def generate_jwt_token(self, user_id, role):
        """Generate JWT token for session management"""
        payload = {
            'user_id': str(user_id),
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=8)  # 8-hour session
        }
        return jwt.encode(payload, 'your-secret-key', algorithm='HS256')
