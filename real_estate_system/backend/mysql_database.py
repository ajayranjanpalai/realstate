import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
from decimal import Decimal
import json

# Safe console printing for Windows cp1252 environments
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    import mysql.connector
    HAS_MYSQL_CONNECTOR = True
except ImportError:
    HAS_MYSQL_CONNECTOR = False

class MySQLRealEstateDB:
    def __init__(self, host=None, user=None, password=None, database=None, port=None):
        self.host = host or os.environ.get('MYSQL_HOST', 'localhost')
        self.user = user or os.environ.get('MYSQL_USER', 'root')
        self.password = password or os.environ.get('MYSQL_PASSWORD', 'Ajay@2006')
        self.database = database or os.environ.get('MYSQL_DATABASE', 'real_estate_db')
        self.port = port or int(os.environ.get('MYSQL_PORT', 3306))
        self.connection = None
        self.use_sqlite = False
        
        self.connect()

    def connect(self):
        """Establish database connection with automatic SQLite fallback"""
        if HAS_MYSQL_CONNECTOR:
            try:
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    port=self.port,
                    connection_timeout=3
                )
                self.use_sqlite = False
                print("✅ Connected to MySQL database successfully")
                return
            except Exception as e:
                print(f"⚠️ MySQL connection unavailable ({self.host}:{self.port}): {e}")

        # Fallback to SQLite
        print("🔄 Falling back to SQLite database for storage...")
        self.use_sqlite = True
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_dir = os.path.join(base_dir, 'data')
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, 'real_estate.db')
        
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.init_sqlite_tables()
        print(f"✅ Connected to SQLite database successfully at {db_path}")

    def init_sqlite_tables(self):
        """Initialize SQLite tables if using SQLite fallback"""
        cursor = self.connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                full_name TEXT,
                city TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                property_id TEXT,
                property_title TEXT,
                property_city TEXT,
                property_locality TEXT,
                property_type TEXT,
                property_price REAL,
                property_area INTEGER,
                property_bhk INTEGER,
                booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'CONFIRMED',
                amount_advance REAL,
                total_amount REAL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        ''')
        self.connection.commit()
        cursor.close()

    def get_connection(self):
        """Get active database connection"""
        if self.use_sqlite:
            if not self.connection:
                self.connect()
            return self.connection
        else:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            return self.connection

    def hash_password(self, password):
        """Hash password for security"""
        return hashlib.sha256(password.encode()).hexdigest()

    def convert_decimal_to_float(self, data):
        """Convert Decimal objects to float for JSON serialization"""
        if isinstance(data, dict):
            return {k: self.convert_decimal_to_float(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.convert_decimal_to_float(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        else:
            return data

    def create_user(self, username, password, email, phone, full_name, city):
        """Create new user"""
        hashed_password = self.hash_password(password)
        conn = self.get_connection()

        if self.use_sqlite:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO users (username, password, email, phone, full_name, city)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (username, hashed_password, email, phone, full_name, city))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                if 'username' in str(e):
                    raise Exception("Username already exists")
                elif 'email' in str(e):
                    raise Exception("Email already exists")
                else:
                    raise Exception("User creation failed")
            finally:
                cursor.close()
        else:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO users (username, password, email, phone, full_name, city)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (username, hashed_password, email, phone, full_name, city))
                conn.commit()
                return cursor.lastrowid
            except mysql.connector.IntegrityError as e:
                if 'username' in str(e):
                    raise Exception("Username already exists")
                elif 'email' in str(e):
                    raise Exception("Email already exists")
                else:
                    raise Exception("User creation failed")
            finally:
                cursor.close()

    def authenticate_user(self, username, password):
        """Authenticate user"""
        hashed_password = self.hash_password(password)
        conn = self.get_connection()

        if self.use_sqlite:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    SELECT user_id, username, email, phone, full_name, city 
                    FROM users WHERE username = ? AND password = ?
                ''', (username, hashed_password))
                row = cursor.fetchone()
                return dict(row) if row else None
            finally:
                cursor.close()
        else:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute('''
                    SELECT user_id, username, email, phone, full_name, city 
                    FROM users WHERE username = %s AND password = %s
                ''', (username, hashed_password))
                return cursor.fetchone()
            finally:
                cursor.close()

    def user_exists(self, username, email):
        """Check if user exists"""
        conn = self.get_connection()

        if self.use_sqlite:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    SELECT user_id FROM users WHERE username = ? OR email = ?
                ''', (username, email))
                return cursor.fetchone() is not None
            finally:
                cursor.close()
        else:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    SELECT user_id FROM users WHERE username = %s OR email = %s
                ''', (username, email))
                return cursor.fetchone() is not None
            finally:
                cursor.close()

    def update_user_password(self, user_id, new_password):
        """Update user password"""
        hashed_password = self.hash_password(new_password)
        conn = self.get_connection()

        if self.use_sqlite:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE users SET password = ? WHERE user_id = ?
                ''', (hashed_password, user_id))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                cursor.close()
        else:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE users SET password = %s WHERE user_id = %s
                ''', (hashed_password, user_id))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                cursor.close()

    def update_user_profile(self, user_id, full_name, email, phone, city):
        """Update user profile"""
        conn = self.get_connection()

        if self.use_sqlite:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE users 
                    SET full_name = ?, email = ?, phone = ?, city = ? 
                    WHERE user_id = ?
                ''', (full_name, email, phone, city, user_id))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                cursor.close()
        else:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE users 
                    SET full_name = %s, email = %s, phone = %s, city = %s 
                    WHERE user_id = %s
                ''', (full_name, email, phone, city, user_id))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                cursor.close()

    def create_booking(self, user_id, property_data, amount_advance, total_amount):
        """Create new booking with property details"""
        conn = self.get_connection()

        params = (
            user_id,
            property_data.get('PropertyID', ''),
            property_data.get('Title', ''),
            property_data.get('City', ''),
            property_data.get('Locality', ''),
            property_data.get('Type', ''),
            float(property_data.get('Price_Cr', 0)),
            int(property_data.get('Area_sqft', 0)),
            int(property_data.get('BHK', 0)),
            float(amount_advance),
            float(total_amount)
        )

        if self.use_sqlite:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO bookings (
                        user_id, property_id, property_title, property_city, property_locality,
                        property_type, property_price, property_area, property_bhk,
                        amount_advance, total_amount
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', params)
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                conn.rollback()
                raise Exception(f"Error creating booking: {str(e)}")
            finally:
                cursor.close()
        else:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO bookings (
                        user_id, property_id, property_title, property_city, property_locality,
                        property_type, property_price, property_area, property_bhk,
                        amount_advance, total_amount
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', params)
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                conn.rollback()
                raise Exception(f"Error creating booking: {str(e)}")
            finally:
                cursor.close()

    def get_user_bookings(self, user_id):
        """Get user's bookings with full property details"""
        conn = self.get_connection()

        if self.use_sqlite:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    SELECT 
                        booking_id, property_id, property_title, property_city, property_locality,
                        property_type, property_price, property_area, property_bhk,
                        booking_date, status, amount_advance, total_amount
                    FROM bookings 
                    WHERE user_id = ?
                    ORDER BY booking_date DESC
                ''', (user_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                print(f"❌ Error in get_user_bookings: {e}")
                return []
            finally:
                cursor.close()
        else:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute('''
                    SELECT 
                        booking_id, property_id, property_title, property_city, property_locality,
                        property_type,
                        CAST(property_price AS DECIMAL(10,2)) as property_price,
                        property_area, property_bhk, booking_date, status,
                        CAST(amount_advance AS DECIMAL(10,2)) as amount_advance,
                        CAST(total_amount AS DECIMAL(10,2)) as total_amount
                    FROM bookings 
                    WHERE user_id = %s
                    ORDER BY booking_date DESC
                ''', (user_id,))
                bookings = cursor.fetchall()
                converted_bookings = []
                for booking in bookings:
                    converted_booking = {}
                    for key, value in booking.items():
                        if isinstance(value, Decimal):
                            converted_booking[key] = float(value)
                        elif isinstance(value, datetime):
                            converted_booking[key] = value.isoformat()
                        else:
                            converted_booking[key] = value
                    converted_bookings.append(converted_booking)
                return converted_bookings
            except Exception as e:
                print(f"❌ Error in get_user_bookings: {e}")
                return []
            finally:
                cursor.close()

    def get_all_properties(self):
        """Get all properties for frontend display"""
        conn = self.get_connection()

        if self.use_sqlite:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    SELECT DISTINCT 
                        property_id, property_title, property_city, property_locality,
                        property_type, property_price, property_area, property_bhk
                    FROM bookings 
                    ORDER BY property_city, property_price
                ''')
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                print(f"❌ Error in get_all_properties: {e}")
                return []
            finally:
                cursor.close()
        else:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute('''
                    SELECT DISTINCT 
                        property_id, property_title, property_city, property_locality,
                        property_type,
                        CAST(property_price AS DECIMAL(10,2)) as property_price,
                        property_area, property_bhk
                    FROM bookings 
                    ORDER BY property_city, property_price
                ''')
                properties = cursor.fetchall()
                converted_properties = []
                for prop in properties:
                    converted_prop = {}
                    for key, value in prop.items():
                        if isinstance(value, Decimal):
                            converted_prop[key] = float(value)
                        else:
                            converted_prop[key] = value
                    converted_properties.append(converted_prop)
                return converted_properties
            except Exception as e:
                print(f"❌ Error in get_all_properties: {e}")
                return []
            finally:
                cursor.close()

if __name__ == "__main__":
    db = MySQLRealEstateDB()
    print(f"✅ DB test complete. Using SQLite: {db.use_sqlite}")