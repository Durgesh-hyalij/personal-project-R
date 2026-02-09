import jwt
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import os

TOKEN_EXPIRATION_HOURS = 24

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password_hash, password):
    return check_password_hash(password_hash , password)

def create_token(user_id , is_admin = False):
    payload = {
        'user_id' : user_id,
        'is_admin' : is_admin,
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS)
    }
    Secret_key = current_app.config["SECRET_KEY"]
    return jwt.encode(payload , Secret_key , algorithm="HS256")

def decode_token(token):
    try:
        Secret_key = current_app.config["SECRET_KEY"]
        return jwt.decode(token, Secret_key, algorithms=['HS256'])
    except:
        return None
    
def get_current_user():
    from models import User

    if 'Authorization' not in request.headers:
        return None, jsonify({
            'error' : 'Token is Missing'
        }),401
    
    auth_header = request.headers['Authorization']

    if not auth_header.startswith('Bearer'):
         return None, jsonify({
            'error' : 'Token is Missing'
        }),401
    
    token = auth_header.split(' ')[1] #we are using this because " bearer 34324343(token) "  but we want only token not bearer

    data = decode_token(token)

    if not data:
        return None, (jsonify({'error': 'Token is invalid or expired'}), 401)

    current_user = User.query.get(data['user_id'])  
    if not current_user:
        return None, (jsonify({'error': 'User not found'}), 401)
    
    # Success! Return user
    return current_user, None