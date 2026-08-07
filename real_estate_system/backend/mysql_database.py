import os
import mysql.connector
import pandas as pd
from datetime import datetime
import hashlib
from decimal import Decimal
import json

class MySQLRealEstateDB:
    def __init__(self, host=None, user=None, password=None, database=None, port=None):
        self.host = host or os.environ.get('MYSQL_HOST', 'localhost')
        self.user = user or os.environ.get('MYSQL_USER', 'root')
        self.password = password or os.environ.get('MYSQL_PASSWORD', 'Ajay@2006')
        self.database = database or os.environ.get('MYSQL_DATABASE', 'real_estate_db')
        self.port = port or int(os.environ.get('MYSQL_PORT', 3306))
        self.connection = None
        try:
            self.connect()
        except Exception as e:
            print(f"⚠️ Initial database connection attempt warning: {e}")
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port
            )
            print("✅ Connected to MySQL database successfully")
        except mysql.connector.Error as e:
            print(f"❌ Database connection failed ({self.host}:{self.port}): {e}")
            raise
    
    def get_connection(self):
        """Get database connection"""
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
    
    # User management methods
    def create_user(self, username, password, email, phone, full_name, city):
        """Create new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            hashed_password = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password, email, phone, full_name, city)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (username, hashed_password, email, phone, full_name, city))
            
            conn.commit()
            user_id = cursor.lastrowid
            return user_id
        except mysql.connector.IntegrityError as e:
            if 'username' in str(e):
                raise Exception("Username already exists")
            elif 'email' in str(e):
                raise Exception("Email already exists")
            else:
                raise Exception("User creation failed")
        except Exception as e:
            raise Exception(f"Error creating user: {str(e)}")
        finally:
            cursor.close()
    
    def authenticate_user(self, username, password):
        """Authenticate user"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            hashed_password = self.hash_password(password)
            cursor.execute('''
                SELECT user_id, username, email, phone, full_name, city 
                FROM users WHERE username = %s AND password = %s
            ''', (username, hashed_password))
            
            user = cursor.fetchone()
            return user
        except Exception as e:
            raise Exception(f"Authentication error: {str(e)}")
        finally:
            cursor.close()
    
    def user_exists(self, username, email):
        """Check if user exists"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT user_id FROM users WHERE username = %s OR email = %s
            ''', (username, email))
            
            user = cursor.fetchone()
            return user is not None
        finally:
            cursor.close()
    
    def update_user_password(self, user_id, new_password):
        """Update user password"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            hashed_password = self.hash_password(new_password)
            cursor.execute('''
                UPDATE users SET password = %s WHERE user_id = %s
            ''', (hashed_password, user_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            raise Exception(f"Error updating password: {str(e)}")
        finally:
            cursor.close()
    
    def update_user_profile(self, user_id, full_name, email, phone, city):
        """Update user profile"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET full_name = %s, email = %s, phone = %s, city = %s 
                WHERE user_id = %s
            ''', (full_name, email, phone, city, user_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            raise Exception(f"Error updating profile: {str(e)}")
        finally:
            cursor.close()
    
    # Booking management methods
    def create_booking(self, user_id, property_data, amount_advance, total_amount):
        """Create new booking with property details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO bookings (
                    user_id, property_id, property_title, property_city, property_locality,
                    property_type, property_price, property_area, property_bhk,
                    amount_advance, total_amount
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                property_data.get('PropertyID', ''),
                property_data.get('Title', ''),
                property_data.get('City', ''),
                property_data.get('Locality', ''),
                property_data.get('Type', ''),
                float(property_data.get('Price_Cr', 0)),  # Convert to float
                int(property_data.get('Area_sqft', 0)),
                int(property_data.get('BHK', 0)),
                float(amount_advance),  # Convert to float
                float(total_amount)     # Convert to float
            ))
            
            conn.commit()
            booking_id = cursor.lastrowid
            return booking_id
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error creating booking: {str(e)}")
        finally:
            cursor.close()
    
    def get_user_bookings(self, user_id):
        """Get user's bookings with full property details"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute('''
                SELECT 
                    booking_id,
                    property_id,
                    property_title,
                    property_city,
                    property_locality,
                    property_type,
                    CAST(property_price AS DECIMAL(10,2)) as property_price,
                    property_area,
                    property_bhk,
                    booking_date,
                    status,
                    CAST(amount_advance AS DECIMAL(10,2)) as amount_advance,
                    CAST(total_amount AS DECIMAL(10,2)) as total_amount
                FROM bookings 
                WHERE user_id = %s
                ORDER BY booking_date DESC
            ''', (user_id,))
            
            bookings = cursor.fetchall()
            
            # Convert Decimal to float for JSON serialization
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
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute('''
                SELECT DISTINCT 
                    property_id,
                    property_title,
                    property_city,
                    property_locality,
                    property_type,
                    CAST(property_price AS DECIMAL(10,2)) as property_price,
                    property_area,
                    property_bhk
                FROM bookings 
                ORDER BY property_city, property_price
            ''')
            
            properties = cursor.fetchall()
            
            # Convert Decimal to float for JSON serialization
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

# Test the database connection
if __name__ == "__main__":
    try:
        db = MySQLRealEstateDB()
        print("✅ MySQL Database connection test successful!")
        
        # Test Decimal conversion
        test_data = {
            'amount': Decimal('10.50'),
            'price': Decimal('1000000.75'),
            'name': 'Test',
            'list': [Decimal('1.5'), Decimal('2.5')],
            'nested': {'value': Decimal('99.99')}
        }
        
        converted = db.convert_decimal_to_float(test_data)
        print("✅ Decimal conversion test successful!")
        print(f"Original: {test_data}")
        print(f"Converted: {converted}")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")