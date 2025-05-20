import os
import sqlite3
import subprocess
import sys
import json
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from flasgger import Swagger, swag_from
from flask_cors import CORS, cross_origin


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
Swagger(app)

# TensorFlow klasörünün yolunu sys.path'e ekleyelim
tensorflow_path = os.path.join(os.path.dirname(__file__), 'tensorflow')
sys.path.append(tensorflow_path)

# JWT ayarları
app.config['JWT_SECRET_KEY'] = 'cokgizlitokensifre1234567890'
jwt = JWTManager(app)

DB_FILE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    if not os.path.exists(DB_FILE):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)
        # Admin kullanıcısı oluştur, parolası '123'
        hashed_password = generate_password_hash('123')
        cursor.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", ('admin', hashed_password, 'admin'))
        
        conn.commit()
        conn.close()

# Öneri fonksiyonu (örnek olarak yerleştirdim, gerçek kodunuzdan farklı olabilir)
def recommend_film(name):
    try:
        from tf.predict import predict 
        processed_result = predict(name)
        return processed_result
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/signup', methods=['POST'])
@swag_from('swagger/signup.yml')
def register():
    if not request.json or 'email' not in request.json or 'password' not in request.json or 'role' not in request.json:
        return jsonify({'error': 'Invalid request format'}), 400
    
    email = request.json['email']
    password = request.json['password']
    role = request.json['role']
    
    if role not in ['user', 'admin']:
        return jsonify({'error': 'Invalid role'}), 400
    
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", (email, hashed_password, role))
        conn.commit()
        return jsonify({'message': 'Registration successful'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'User already exists'}), 409
    finally:
        conn.close()

@app.route('/signin', methods=['POST'])
@swag_from('swagger/signin.yml')
def login():

    if not request.json or 'email' not in request.json or 'password' not in request.json:
        return jsonify({'error': 'Invalid request format'}), 400
    
    email = request.json['email']
    password = request.json['password']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    if user and check_password_hash(user['password'], password):
        # Kullanıcı kimliği doğrulandıysa
        access_token = create_access_token(identity=email)
        return jsonify({'access_token': access_token, 'role': user['role']}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/process', methods=['POST'])
@jwt_required()
@swag_from('swagger/process.yml')
def process():
    if not request.json or 'name' not in request.json:
        return jsonify({'error': 'Invalid request format'}), 400
    
    name = request.json['name']
    processed_result = recommend_film(name)
    movies = processed_result.tolist() 
    result = jsonify({'movies': movies})
    return result

@app.route('/users', methods=['POST'])
@jwt_required()
@swag_from('swagger/users.yml')
def get_users():
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Kullanıcı rolü kontrolü (sadece admin)
    cursor.execute("SELECT role FROM users WHERE email = ?", (current_user,))
    user_role = cursor.fetchone()
    
    if user_role['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    # Admin ise tüm kullanıcıları listele
    cursor.execute("SELECT email, role, password FROM users")
    users = cursor.fetchall()
    
    conn.close()
    user_list = [{'email': user['email'], 'password': user['password'], 'role': user['role']} for user in users]
    return jsonify({'users': user_list}), 200

@app.route('/user/delete', methods=['POST'])
@jwt_required()
@swag_from('swagger/delete_user.yml')
def delete_user():
    current_user = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Kullanıcı rolü kontrolü (sadece admin)
    cursor.execute("SELECT role FROM users WHERE email = ?", (current_user,))
    user_role = cursor.fetchone()
    
    if user_role['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    if not request.json or 'email' not in request.json:
        return jsonify({'error': 'Invalid request format'}), 400
    
    email = request.json['email']

    # Kullanıcıyı veritabanından sil
    cursor.execute("DELETE FROM users WHERE email = ?", (email,))
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'User deleted successfully'}), 200

if __name__ == '__main__':
    create_table()
    app.run(debug=True)
