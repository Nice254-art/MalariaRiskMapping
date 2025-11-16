# database.py
import sqlite3
import hashlib
import os
from datetime import datetime

def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect('malaria_users.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create predictions history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            prediction TEXT NOT NULL,
            confidence REAL NOT NULL,
            features_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify a stored password against its hash"""
    return hash_password(password) == password_hash

def add_user(username, email, password):
    """Add a new user to the database"""
    conn = sqlite3.connect('malaria_users.db')
    c = conn.cursor()
    
    password_hash = hash_password(password)
    
    try:
        c.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_user(username):
    """Get user by username"""
    conn = sqlite3.connect('malaria_users.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    
    return user

def save_prediction(user_id, latitude, longitude, prediction, confidence, features):
    """Save prediction to history"""
    conn = sqlite3.connect('malaria_users.db')
    c = conn.cursor()
    
    c.execute(
        '''INSERT INTO predictions 
           (user_id, latitude, longitude, prediction, confidence, features_json) 
           VALUES (?, ?, ?, ?, ?, ?)''',
        (user_id, latitude, longitude, prediction, confidence, features)
    )
    
    conn.commit()
    conn.close()

def get_user_predictions(user_id):
    """Get prediction history for a user"""
    conn = sqlite3.connect('malaria_users.db')
    c = conn.cursor()
    
    c.execute(
        'SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC',
        (user_id,)
    )
    predictions = c.fetchall()
    conn.close()
    
    return predictions

# Initialize database when this module is imported
init_db()