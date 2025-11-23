from functools import wraps
from flask import request, jsonify
from app.models.feeder import Feeder

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        feeder = Feeder.query.filter_by(token=token).first()
        if not feeder:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(feeder, *args, **kwargs)
    
    return decorated
