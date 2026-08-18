import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import sys
from datetime import datetime, timedelta
import random
import re
import warnings
warnings.filterwarnings('ignore')

# add path(backend)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# MySQL
from backend.mysql_database import MySQLRealEstateDB

class AuthenticationSystem:
    def __init__(self, db):
        self.db = db
        self.current_user = None
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_phone(self, phone):
        """Validate phone number (10 digits)"""
        return phone.isdigit() and len(phone) == 10
    
    def validate_password(self, password):
        """Validate password strength"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        return True, "Password is valid"
    
    def register(self, user_data):
        """User registration"""
        try:
            username = user_data.get('username')
            email = user_data.get('email')
            phone = user_data.get('phone')
            full_name = user_data.get('full_name')
            city = user_data.get('city')
            password = user_data.get('password')
            
            # Validation
            if not all([username, email, phone, full_name, password]):
                return False, "All fields are required"
            
            if not self.validate_email(email):
                return False, "Invalid email format"
            
            if not self.validate_phone(phone):
                return False, "Invalid phone number"
            
            is_valid, message = self.validate_password(password)
            if not is_valid:
                return False, message
            
            # Check user 
            if self.db.user_exists(username, email):
                return False, "Username or email already exists"
            
            user_id = self.db.create_user(username, password, email, phone, full_name, city)
            return True, f"Registration successful! User ID: {user_id}"
            
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def login(self, username, password):
        """User login"""
        try:
            if not username or not password:
                return False, "Username and password are required"
            
            user = self.db.authenticate_user(username, password)
            if user:
                self.current_user = user
                return True, f"Welcome back, {user['full_name']}!"
            else:
                return False, "Invalid username or password"
                
        except Exception as e:
            return False, f"Login failed: {str(e)}"
    
    def logout(self):
        """User logout"""
        if self.current_user:
            user_name = self.current_user['full_name']
            self.current_user = None
            return True, f"Goodbye, {user_name}!"
        else:
            return False, "No user is currently logged in!"
    
    def is_logged_in(self):
        """Check if user is logged in"""
        return self.current_user is not None
    
    def get_current_user(self):
        """Get current user details"""
        return self.current_user
    
    def change_password(self, current_password, new_password):
        """Change user password"""
        if not self.is_logged_in():
            return False, "Please login first"
        
        try:
            # Verify psss
            user = self.db.authenticate_user(
                self.current_user['username'], 
                current_password
            )
            if not user:
                return False, "Current password is incorrect"
            
            is_valid, message = self.validate_password(new_password)
            if not is_valid:
                return False, message

            # Update passs
            success = self.db.update_user_password(
                self.current_user['user_id'], 
                new_password
            )
            if success:
                return True, "Password changed successfully!"
            else:
                return False, "Failed to change password"
                
        except Exception as e:
            return False, f"Error changing password: {str(e)}"
    
    def update_profile(self, profile_data):
        """Update user profile"""
        if not self.is_logged_in():
            return False, "Please login first"
        
        try:
            success = self.db.update_user_profile(
                self.current_user['user_id'],
                profile_data.get('full_name'),
                profile_data.get('email'),
                profile_data.get('phone'),
                profile_data.get('city')
            )
            
            if success:
                # Update
                self.current_user.update(profile_data)
                return True, "Profile updated successfully!"
            else:
                return False, "Failed to update profile"
                
        except Exception as e:
            return False, f"Error updating profile: {str(e)}"

class RealEstateBackend:
    def __init__(self):
        self.db = MySQLRealEstateDB()
        self.auth = AuthenticationSystem(self.db)
        self.properties_df = None
        self.analysis_results = {}
        self.load_data_from_csv()
        
    def load_data_from_csv(self):
        """Load property data from CSV file or create sample data"""
        try:
            current_dir = os.path.dirname(__file__)
            project_root = os.path.dirname(current_dir)
            root_dir = os.path.dirname(project_root)
            
            candidate_paths = [
                os.path.join(project_root, 'data', 'properties.csv'),
                os.path.join(root_dir, 'data', 'properties.csv')
            ]
            
            loaded_path = None
            for path in candidate_paths:
                if os.path.exists(path):
                    loaded_path = path
                    break
            
            if loaded_path:
                print(f"📁 Loading properties CSV from: {loaded_path}")
                self.properties_df = pd.read_csv(loaded_path)
                print(f"✅ Successfully loaded {len(self.properties_df)} properties from CSV")
                self.ensure_required_columns()
            else:
                print("🔄 CSV file not found, creating sample data...")
                self.create_sample_data()
                
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            print("🔄 Creating sample data...")
            self.create_sample_data()
    
    def ensure_required_columns(self):
        """Ensure all required columns exist in the DataFrame"""
        required_columns = [
            'PropertyID', 'Title', 'City', 'Locality', 'Type', 'Price_Cr', 
            'Area_sqft', 'BHK', 'Price_per_sqft', 'Furnishing', 'TransactionType',
            'ListedDate', 'Available'
        ]
        
        for column in required_columns:
            if column not in self.properties_df.columns:
                if column == 'Available':
                    self.properties_df[column] = True
                elif column == 'Price_per_sqft':
                    # Calculate price per sqft if missing
                    self.properties_df[column] = (self.properties_df['Price_Cr'] * 10000000) / self.properties_df['Area_sqft']
                elif column == 'ListedDate':
                    self.properties_df[column] = datetime.now().strftime('%Y-%m-%d')
                else:
                    self.properties_df[column] = 'Unknown'
        
        print("✅ Verified all required columns")
    
    def create_sample_data(self):
        """Create sample property data"""
        print("🎲 Generating sample property data...")
        
        cities = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata']
        property_types = ['Apartment', 'Villa', 'Plot', 'Commercial']
        localities = {
            'Mumbai': ['Bandra', 'Andheri', 'Powai', 'Worli'],
            'Delhi': ['Dwarka', 'Saket', 'Rohini', 'Vasant Kunj'],
            'Bangalore': ['Whitefield', 'Koramangala', 'HSR Layout', 'Electronic City'],
            'Hyderabad': ['Gachibowli', 'Hitech City', 'Banjara Hills', 'Madhapur'],
            'Chennai': ['Adyar', 'Anna Nagar', 'T Nagar', 'OMR'],
            'Pune': ['Hinjewadi', 'Kothrud', 'Viman Nagar', 'Baner'],
            'Kolkata': ['Salt Lake', 'New Town', 'Park Street', 'Howrah']
        }
        
        property_data = []
        
        for i in range(100):
            city = random.choice(cities)
            locality = random.choice(localities[city])
            property_type = random.choice(property_types)
            
            base_prices = {
                'Mumbai': (1.5, 5.0), 'Delhi': (1.0, 3.5), 
                'Bangalore': (0.8, 2.5), 'Hyderabad': (0.7, 2.0),
                'Chennai': (0.6, 1.8), 'Pune': (0.5, 1.5),
                'Kolkata': (0.4, 1.2)
            }
            
            min_price, max_price = base_prices[city]
            price = round(random.uniform(min_price, max_price), 2)
            area = random.randint(800, 3000)
            bhk = random.randint(1, 4) if property_type == 'Apartment' else 0
            price_per_sqft = round((price * 10000000) / area, 2)
            
            property_data.append({
                'PropertyID': f'PROP_{i+1:03d}',
                'Title': f'{bhk if bhk > 0 else "Commercial"} BHK {property_type} in {locality}',
                'City': city,
                'Locality': locality,
                'Type': property_type,
                'Price_Cr': price,
                'Area_sqft': area,
                'BHK': bhk,
                'Price_per_sqft': price_per_sqft,
                'Furnishing': random.choice(['Fully Furnished', 'Semi Furnished', 'Unfurnished']),
                'TransactionType': random.choice(['New Booking', 'Resale']),
                'ListedDate': (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d'),
                'Available': True
            })
        
        self.properties_df = pd.DataFrame(property_data)
        
        # Save to CSV
        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(current_dir)
        csv_path = os.path.join(project_root, 'sample_real_estate_data.csv')
        
        try:
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            
            # Save CSV
            self.properties_df.to_csv(csv_path, index=False)
            print(f"✅ Created sample_real_estate_data.csv with {len(self.properties_df)} properties")
            print(f"📁 Saved at: {csv_path}")
            
            if os.path.exists(csv_path):
                file_size = os.path.getsize(csv_path)
                print(f"📊 File size: {file_size} bytes")
            else:
                print("❌ CSV file was not created!")
                
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")
            print("⚠️  Using in-memory data only")
    
    def get_filtered_properties(self, filters=None):
        """Get properties with optional filters"""
        if filters is None:
            filters = {}
        
        if self.properties_df is None or self.properties_df.empty:
            print("❌ No properties data available - creating sample data")
            self.create_sample_data()
            if self.properties_df is None:
                return []
        
        try:
            filtered_df = self.properties_df.copy()
            
            # Apply filters
            if filters.get('city'):
                filtered_df = filtered_df[filtered_df['City'] == filters['city']]
            if filters.get('type'):
                filtered_df = filtered_df[filtered_df['Type'] == filters['type']]
            if filters.get('min_price'):
                filtered_df = filtered_df[filtered_df['Price_Cr'] >= float(filters['min_price'])]
            if filters.get('max_price'):
                filtered_df = filtered_df[filtered_df['Price_Cr'] <= float(filters['max_price'])]
            if filters.get('bhk'):
                filtered_df = filtered_df[filtered_df['BHK'] == int(filters['bhk'])]
            if filters.get('available_only'):
                filtered_df = filtered_df[filtered_df['Available'] == True]
            
            if filters.get('limit'):
                filtered_df = filtered_df.head(int(filters['limit']))
            
            print(f"🔍 Found {len(filtered_df)} properties after filtering")
            
            properties_list = filtered_df.where(pd.notna(filtered_df), None).to_dict('records')
            
            # Ensure
            for prop in properties_list:
                if 'Available' not in prop:
                    prop['Available'] = True
                
                # Price_per_sqft 
                if 'Price_per_sqft' not in prop or prop['Price_per_sqft'] is None:
                    price = prop.get('Price_Cr', 0) or 0
                    area = prop.get('Area_sqft', 1) or 1
                    if area > 0:
                        prop['Price_per_sqft'] = round((float(price) * 10000000) / float(area), 2)
                    else:
                        prop['Price_per_sqft'] = 0
                
                # Convert numeric 
                if 'Price_Cr' in prop and prop['Price_Cr'] is not None:
                    prop['Price_Cr'] = float(prop['Price_Cr'])
                if 'Area_sqft' in prop and prop['Area_sqft'] is not None:
                    prop['Area_sqft'] = int(prop['Area_sqft'])
                if 'BHK' in prop and prop['BHK'] is not None:
                    prop['BHK'] = int(prop['BHK'])
                
                # Ensure string 
                if 'Title' not in prop or not prop['Title']:
                    prop['Title'] = f"Property in {prop.get('Locality', 'Unknown')}"
                if 'Locality' not in prop:
                    prop['Locality'] = 'Unknown'
                if 'Furnishing' not in prop:
                    prop['Furnishing'] = 'Unfurnished'
                if 'TransactionType' not in prop:
                    prop['TransactionType'] = 'New Booking'
            
            return properties_list
            
        except Exception as e:
            print(f"❌ Error filtering properties: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_property_by_id(self, property_id):
        """Get property details by property ID"""
        if self.properties_df is None or self.properties_df.empty:
            return None
        
        try:
            match = self.properties_df[self.properties_df['PropertyID'] == property_id]
            if match.empty:
                return None
            
            prop = match.iloc[0].to_dict()
            
            # Clean numeric and string values
            prop['Price_Cr'] = float(prop.get('Price_Cr', 0)) if pd.notna(prop.get('Price_Cr')) else 0.0
            prop['Area_sqft'] = int(prop.get('Area_sqft', 0)) if pd.notna(prop.get('Area_sqft')) else 0
            prop['BHK'] = int(prop.get('BHK', 0)) if pd.notna(prop.get('BHK')) else 0
            prop['Available'] = bool(prop.get('Available', True))
            if 'Price_per_sqft' not in prop or pd.isna(prop['Price_per_sqft']):
                if prop['Area_sqft'] > 0:
                    prop['Price_per_sqft'] = round((prop['Price_Cr'] * 10000000) / prop['Area_sqft'], 2)
                else:
                    prop['Price_per_sqft'] = 0.0
            else:
                prop['Price_per_sqft'] = float(prop['Price_per_sqft'])
                
            return prop
        except Exception as e:
            print(f"❌ Error fetching property {property_id}: {e}")
            return None
    
    def get_property_cities(self):
        """Get list of available cities"""
        if self.properties_df is None or self.properties_df.empty:
            print("⚠️  No properties data - returning default cities")
            return ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata']
        
        try:
            cities = sorted(self.properties_df['City'].unique().tolist())
            return cities
        except Exception as e:
            print(f"❌ Error getting cities: {e}")
            return ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata']
    
    def get_property_types(self):
        """Get list of available property types"""
        if self.properties_df is None or self.properties_df.empty:
            print("⚠️  No properties data - returning default types")
            return ['Apartment', 'Villa', 'Plot', 'Commercial']
        
        try:
            types = sorted(self.properties_df['Type'].unique().tolist())
            return types
        except Exception as e:
            print(f"❌ Error getting types: {e}")
            return ['Apartment', 'Villa', 'Plot', 'Commercial']
    
    def book_property(self, property_id, user_preferences):
        """Book a property"""
        if not self.auth.is_logged_in():
            return False, "Please login first"
        
        try:
            # Find the property 
            if self.properties_df is None:
                return False, "No properties data available"
            
            property_match = self.properties_df[self.properties_df['PropertyID'] == property_id]
            
            if property_match.empty:
                return False, "Property not found"
            
            property_data = property_match.iloc[0].to_dict()
            
            if not property_data.get('Available', False):
                return False, "Property is not available"
            
            # booking
            booking_id = self.db.create_booking(
                self.auth.current_user['user_id'],
                property_data,
                round(property_data.get('Price_Cr', 0) * 0.1, 2),
                property_data.get('Price_Cr', 0)
            )
            
            self.properties_df.loc[
                self.properties_df['PropertyID'] == property_id, 'Available'
            ] = False
            
            # Update CSV file if it exists
            self.update_csv_availability(property_id, False)
            self.save_booking_receipt(booking_id, property_data, user_preferences)
            
            return True, f"Booking successful! Booking ID: {booking_id}"
            
        except Exception as e:
            print(f"❌ Booking error: {e}")
            return False, f"Booking failed: {str(e)}"
    
    def update_csv_availability(self, property_id, available):
        """Update property availability in CSV"""
        try:
            current_dir = os.path.dirname(__file__)
            project_root = os.path.dirname(current_dir)
            root_dir = os.path.dirname(project_root)
            
            candidate_paths = [
                os.path.join(project_root, 'data', 'properties.csv'),
                os.path.join(root_dir, 'data', 'properties.csv'),
                os.path.join(project_root, 'sample_real_estate_data.csv')
            ]
            
            for csv_path in candidate_paths:
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    df.loc[df['PropertyID'] == property_id, 'Available'] = available
                    df.to_csv(csv_path, index=False)
                    print(f"✅ Updated property {property_id} availability to {available} in CSV: {csv_path}")
                    break
        except Exception as e:
            print(f"❌ Error updating CSV: {e}")
    
    def save_booking_receipt(self, booking_id, property_data, user_details):
        """Save booking receipt to file"""
        try:
            current_dir = os.path.dirname(__file__)
            project_root = os.path.dirname(current_dir)
            receipts_dir = os.path.join(project_root, 'output', 'receipts')
            os.makedirs(receipts_dir, exist_ok=True)
            
            receipt_content = f"""
            REALESTATE INDIA - BOOKING RECEIPT
            ==================================
            
            Booking ID: {booking_id}
            Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            PROPERTY DETAILS:
            ----------------
            Title: {property_data.get('Title', 'Unknown')}
            Location: {property_data.get('Locality', 'Unknown')}, {property_data.get('City', 'Unknown')}
            Type: {property_data.get('Type', 'Unknown')}
            BHK: {property_data.get('BHK', 'N/A')}
            Area: {property_data.get('Area_sqft', 0)} sqft
            Furnishing: {property_data.get('Furnishing', 'Unknown')}
            Transaction Type: {property_data.get('TransactionType', 'Unknown')}
            
            PRICING:
            --------
            Total Price: Rs.{property_data.get('Price_Cr', 0)} Crores
            Advance Amount: Rs.{round(property_data.get('Price_Cr', 0) * 0.1, 2)} Crores
            Balance Amount: Rs.{round(property_data.get('Price_Cr', 0) * 0.9, 2)} Crores
            
            CUSTOMER DETAILS:
            -----------------
            Name: {user_details['name']}
            Email: {user_details['email']}
            Phone: {user_details['phone']}
            
            Thank you for choosing RealEstate India!
            """
            
            receipt_file = os.path.join(receipts_dir, f"BOOKING_{booking_id}.txt")
            with open(receipt_file, 'w', encoding='utf-8') as f:
                f.write(receipt_content)
            
            print(f"✅ Receipt saved: {receipt_file}")
            return True
        except Exception as e:
            print(f"❌ Could not save receipt: {str(e)}")
            return False
    
    def get_user_bookings(self):
        """Get current user's bookings"""
        if not self.auth.is_logged_in():
            print("❌ User not logged in for bookings")
            return []
        
        try:
            user_id = self.auth.current_user['user_id']
            print(f"🔍 Fetching bookings for user ID: {user_id}")
            bookings = self.db.get_user_bookings(user_id)
            print(f"✅ Found {len(bookings)} bookings for user")
            return bookings
        except Exception as e:
            print(f"❌ Error getting user bookings: {e}")
            return []
    
    def analyze_properties(self):
        """Comprehensive property analysis"""
        if self.properties_df is None or self.properties_df.empty:
            print("⚠️  No properties data for analysis - creating sample data")
            self.create_sample_data()
            if self.properties_df is None:
                return {
                    'basic_stats': {
                        'total_properties': 0,
                        'average_price': 0,
                        'cities_covered': 0,
                        'property_types': {}
                    },
                    'city_stats': {},
                    'type_stats': {}
                }
        
        try:
            total_properties = len(self.properties_df)
            avg_price = self.properties_df['Price_Cr'].mean()
            total_cities = self.properties_df['City'].nunique()
            
            analysis = {
                'basic_stats': {
                    'total_properties': total_properties,
                    'average_price': round(avg_price, 2),
                    'cities_covered': total_cities,
                    'property_types': self.properties_df['Type'].value_counts().to_dict()
                },
                'city_stats': self.properties_df.groupby('City')['Price_Cr'].mean().round(2).to_dict(),
                'type_stats': self.properties_df['Type'].value_counts().to_dict()
            }
            
            return analysis
        except Exception as e:
            print(f"❌ Error in property analysis: {e}")
            return {
                'basic_stats': {
                    'total_properties': 0,
                    'average_price': 0,
                    'cities_covered': 0,
                    'property_types': {}
                },
                'city_stats': {},
                'type_stats': {}
            }
    
    def create_charts(self):
        """Create analysis charts"""
        if self.properties_df is None or self.properties_df.empty:
            print("⚠️  No properties data for charts")
            return False
            
        try:
            current_dir = os.path.dirname(__file__)
            project_root = os.path.dirname(current_dir)
            charts_dir = os.path.join(project_root, 'output', 'charts')
            os.makedirs(charts_dir, exist_ok=True)
            
            # Price distribution by city
            plt.figure(figsize=(10, 6))
            city_prices = self.properties_df.groupby('City')['Price_Cr'].mean().sort_values(ascending=False)
            plt.bar(city_prices.index, city_prices.values, color='skyblue')
            plt.title('Average Property Price by City')
            plt.xticks(rotation=45)
            plt.ylabel('Price (Rs. Cr)')
            plt.tight_layout()
            
            chart_path = os.path.join(charts_dir, 'city_prices.png')
            plt.savefig(chart_path)
            plt.close()
            
            # Property type distribution
            plt.figure(figsize=(8, 8))
            type_counts = self.properties_df['Type'].value_counts()
            plt.pie(type_counts.values, labels=type_counts.index, autopct='%1.1f%%', startangle=90)
            plt.title('Property Type Distribution')
            
            chart_path = os.path.join(charts_dir, 'type_distribution.png')
            plt.savefig(chart_path)
            plt.close()
            
            print("✅ Charts created successfully")
            return True
        except Exception as e:
            print(f"❌ Chart creation failed: {str(e)}")
            return False

# Test the backend
if __name__ == "__main__":
    backend = RealEstateBackend()
    print("✅ Backend initialized successfully!")
    print(f"📊 Total properties: {len(backend.properties_df) if backend.properties_df is not None else 0}")
    print(f"🏙️ Cities: {backend.get_property_cities()}")
    print(f"🏠 Types: {backend.get_property_types()}")
    
    # Test property filtering
    test_properties = backend.get_filtered_properties({'limit': 5})
    print(f"🔍 Test properties loaded: {len(test_properties)}")
    if test_properties:
        print("📋 Sample property:")
        print(json.dumps(test_properties[0], indent=2))