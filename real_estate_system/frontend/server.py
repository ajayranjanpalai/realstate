import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import threading

# path to backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.real_estate_backend import RealEstateBackend

class RealEstateHandler(http.server.SimpleHTTPRequestHandler):
    # Shared backend 
    _backend = None
    _backend_lock = threading.Lock()
    
    @classmethod
    def get_backend(cls):
        """Get or create the shared backend instance"""
        with cls._backend_lock:
            if cls._backend is None:
                cls._backend = RealEstateBackend()
                print("✅ Backend instance created")
            return cls._backend
    
    def __init__(self, *args, **kwargs):
        # Get backend 
        self.backend = self.get_backend()
        # Set server file
        self.directory = os.path.join(os.path.dirname(__file__))
        super().__init__(*args, directory=self.directory, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        print(f"🔍 GET request: {self.path}")
        
        if self.path.startswith('/api/'):
            self.handle_api_get()
        else:
            clean_path = self.path.split('?')[0]
            if clean_path in ['/', '']:
                self.path = '/templates/login.html'
            elif clean_path == '/dashboard':
                self.path = '/templates/dashboard.html'
            elif clean_path == '/properties':
                self.path = '/templates/properties.html'
            elif clean_path == '/bookings':
                self.path = '/templates/bookings.html'
            elif clean_path == '/profile':
                self.path = '/templates/profile.html'
            elif clean_path == '/analysis':
                self.path = '/templates/analysis.html'
            elif clean_path in ['/property-detail', '/templates/property_detail.html']:
                self.path = '/templates/property_detail.html'
            else:
                self.path = clean_path
            
            file_path = os.path.join(self.directory, self.path.lstrip('/'))
            print(f"📁 Serving file: {file_path}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                if self.path.startswith('/api/'):
                    self.send_json_error(404, "API endpoint not found")
                    return
                else:
                    self.send_error(404, f"File not found: {self.path}")
                    return
            
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        print(f"🔍 POST request: {self.path}")
        
        if self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.send_json_error(404, "Endpoint not found")

    def do_DELETE(self):
        """Handle DELETE requests"""
        print(f"🔍 DELETE request: {self.path}")
        if self.path.startswith('/api/bookings/'):
            booking_id = self.path.split('/')[-1]
            success, msg = self.backend.cancel_booking(booking_id)
            self.send_json_response({'success': success, 'message': msg})
        else:
            self.send_json_error(404, "Endpoint not found")
    
    def handle_api_get(self):
        """Handle API GET requests"""
        try:
            if self.path == '/api/user':
                self.get_current_user()
            elif self.path.startswith('/api/property?'):
                self.get_single_property()
            elif self.path.startswith('/api/properties'):
                self.get_properties()
            elif self.path == '/api/cities':
                self.get_cities()
            elif self.path == '/api/types':
                self.get_types()
            elif self.path == '/api/bookings':
                self.get_bookings()
            elif self.path == '/api/analysis':
                self.get_analysis()
            else:
                self.send_json_error(404, "API endpoint not found")
        except Exception as e:
            print(f"❌ API GET Error: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_error(500, f"Internal server error: {str(e)}")
    
    def handle_api_post(self):
        """Handle API POST requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            if self.path == '/api/login':
                self.login(data)
            elif self.path == '/api/register':
                self.register(data)
            elif self.path == '/api/logout':
                self.logout()
            elif self.path == '/api/book':
                self.book_property(data)
            elif self.path == '/api/change-password':
                self.change_password(data)
            elif self.path == '/api/update-profile':
                self.update_profile(data)
            elif self.path == '/api/cancel_booking':
                booking_id = data.get('booking_id')
                success, msg = self.backend.cancel_booking(booking_id)
                self.send_json_response({'success': success, 'message': msg})
            else:
                self.send_json_error(404, "API endpoint not found")
        except json.JSONDecodeError:
            self.send_json_error(400, "Invalid JSON in request body")
        except Exception as e:
            print(f"❌ API POST Error: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_error(500, f"Internal server error: {str(e)}")
    
    def get_current_user(self):
        """Get current user info"""
        try:
            user = self.backend.auth.get_current_user()
            print(f"🔍 Current user check: {user['username'] if user else 'None'}")
            self.send_json_response({
                'success': user is not None,
                'user': user
            })
        except Exception as e:
            print(f"❌ Error getting current user: {e}")
            self.send_json_response({
                'success': False,
                'user': None,
                'message': 'Failed to get user information'
            })
    
    def get_properties(self):
        """Get properties with optional filters"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            filters = {}
            if 'city' in query_params and query_params['city']:
                filters['city'] = query_params['city'][0]
            if 'type' in query_params and query_params['type']:
                filters['type'] = query_params['type'][0]
            if 'min_price' in query_params and query_params['min_price']:
                filters['min_price'] = query_params['min_price'][0]
            if 'max_price' in query_params and query_params['max_price']:
                filters['max_price'] = query_params['max_price'][0]
            if 'bhk' in query_params and query_params['bhk']:
                filters['bhk'] = query_params['bhk'][0]
            if 'limit' in query_params and query_params['limit']:
                filters['limit'] = int(query_params['limit'][0])
            
            print(f"🔍 Loading properties with filters: {filters}")
            properties = self.backend.get_filtered_properties(filters)
            
            print(f"✅ Found {len(properties)} properties")
            
            self.send_json_response({
                'success': True,
                'properties': properties,
                'count': len(properties)
            })
            
        except Exception as e:
            print(f"❌ Error getting properties: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'message': f'Failed to load properties: {str(e)}',
                'properties': []
            })

    def get_single_property(self):
        """Get single property by ID"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            prop_id = query_params.get('id', [None])[0]
            
            if not prop_id:
                self.send_json_error(400, "Property ID is required")
                return
            
            property_data = self.backend.get_property_by_id(prop_id)
            if property_data:
                self.send_json_response({
                    'success': True,
                    'property': property_data
                })
            else:
                self.send_json_error(404, "Property not found")
        except Exception as e:
            print(f"❌ Error getting single property: {e}")
            self.send_json_error(500, f"Error: {str(e)}")
    
    def get_cities(self):
        """Get available cities"""
        try:
            cities = self.backend.get_property_cities()
            print(f"✅ Found {len(cities)} cities: {cities}")
            self.send_json_response({
                'success': True,
                'cities': cities
            })
        except Exception as e:
            print(f"❌ Error getting cities: {e}")
            self.send_json_response({
                'success': False,
                'cities': [],
                'message': 'Failed to load cities'
            })
    
    def get_types(self):
        """Get available property types"""
        try:
            types = self.backend.get_property_types()
            print(f"✅ Found {len(types)} types: {types}")
            self.send_json_response({
                'success': True,
                'types': types
            })
        except Exception as e:
            print(f"❌ Error getting types: {e}")
            self.send_json_response({
                'success': False,
                'types': [],
                'message': 'Failed to load property types'
            })
    
    def get_bookings(self):
        """Get user bookings"""
        try:
            if not self.backend.auth.is_logged_in():
                self.send_json_response({
                    'success': False,
                    'message': 'Please login first',
                    'bookings': []
                })
                return
            
            bookings = self.backend.get_user_bookings()
            print(f"✅ Found {len(bookings)} bookings for user")
            self.send_json_response({
                'success': True,
                'bookings': bookings
            })
            
        except Exception as e:
            print(f"❌ Error getting bookings: {e}")
            self.send_json_response({
                'success': False,
                'message': f'Failed to load bookings: {str(e)}',
                'bookings': []
            })
    
    def get_analysis(self):
        """Get property analysis"""
        try:
            analysis = self.backend.analyze_properties()
            self.backend.create_charts()
            self.send_json_response({
                'success': True,
                'analysis': analysis
            })
        except Exception as e:
            print(f"❌ Error getting analysis: {e}")
            self.send_json_response({
                'success': False,
                'analysis': {},
                'message': 'Failed to load analysis'
            })
    
    def login(self, data):
        """Handle login"""
        try:
            print(f"🔐 Login attempt for user: {data.get('username')}")
            success, message = self.backend.auth.login(
                data.get('username'), 
                data.get('password')
            )
            
            if success:
                user = self.backend.auth.get_current_user()
                print(f"✅ Login successful: {user['username']}")
            else:
                print(f"❌ Login failed: {message}")
                
            self.send_json_response({
                'success': success,
                'message': message,
                'user': self.backend.auth.get_current_user() if success else None
            })
        except Exception as e:
            print(f"❌ Login error: {e}")
            self.send_json_response({
                'success': False,
                'message': f'Login error: {str(e)}'
            })
    
    def register(self, data):
        """Handle registration"""
        try:
            success, message = self.backend.auth.register(data)
            self.send_json_response({
                'success': success,
                'message': message
            })
        except Exception as e:
            print(f"❌ Registration error: {e}")
            self.send_json_response({
                'success': False,
                'message': f'Registration error: {str(e)}'
            })
    
    def logout(self):
        """Handle logout"""
        try:
            print("🚪 Logout request")
            success, message = self.backend.auth.logout()
            self.send_json_response({
                'success': success,
                'message': message
            })
        except Exception as e:
            print(f"❌ Logout error: {e}")
            self.send_json_response({
                'success': False,
                'message': f'Logout error: {str(e)}'
            })
    
    def book_property(self, data):
        """Handle property booking"""
        try:
            if not self.backend.auth.is_logged_in():
                self.send_json_response({
                    'success': False,
                    'message': 'Please login first'
                })
                return
                
            success, message = self.backend.book_property(
                data.get('property_id'),
                data.get('user_preferences', {})
            )
            self.send_json_response({
                'success': success,
                'message': message
            })
        except Exception as e:
            print(f"❌ Booking error: {e}")
            self.send_json_response({
                'success': False,
                'message': f'Booking error: {str(e)}'
            })
    
    def change_password(self, data):
        """Handle password change"""
        try:
            if not self.backend.auth.is_logged_in():
                self.send_json_response({
                    'success': False,
                    'message': 'Please login first'
                })
                return
                
            success, message = self.backend.auth.change_password(
                data.get('current_password'),
                data.get('new_password')
            )
            self.send_json_response({
                'success': success,
                'message': message
            })
        except Exception as e:
            print(f"❌ Password change error: {e}")
            self.send_json_response({
                'success': False,
                'message': f'Password change error: {str(e)}'
            })
    
    def update_profile(self, data):
        """Handle profile update"""
        try:
            if not self.backend.auth.is_logged_in():
                self.send_json_response({
                    'success': False,
                    'message': 'Please login first'
                })
                return
                
            success, message = self.backend.auth.update_profile(data)
            self.send_json_response({
                'success': success,
                'message': message
            })
        except Exception as e:
            print(f"❌ Profile update error: {e}")
            self.send_json_response({
                'success': False,
                'message': f'Profile update error: {str(e)}'
            })
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))
    
    def send_json_error(self, status_code, message):
        """Send JSON error response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        error_response = {
            'success': False,
            'error': True,
            'message': message,
            'status_code': status_code
        }
        self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to show detailed logs"""
        print(f"🌐 {format % args}")

def run_server(port=None):
    """Run the web server"""
    if port is None:
        port = int(os.environ.get("PORT", 8000))

    # Change to frontend directory
    frontend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(frontend_dir)
    
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"📁 Frontend directory: {frontend_dir}")
    
    # Check if required directories exist
    templates_dir = os.path.join(frontend_dir, 'templates')
    static_dir = os.path.join(frontend_dir, 'static')
    
    print(f"📁 Templates directory exists: {os.path.exists(templates_dir)}")
    print(f"📁 Static directory exists: {os.path.exists(static_dir)}")
    
    socketserver.TCPServer.allow_reuse_address = True
    handler = RealEstateHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🚀 Real Estate System running on http://127.0.0.1:{port}")
        print(f"🔗 Access URL: http://localhost:{port}")
        print("📱 Open http://127.0.0.1:{port} or http://localhost:{port} in your web browser")
        print("⏹️  Press Ctrl+C to stop the server")
        print("🔐 Session management: ENABLED")
        print("🔄 API endpoints: READY")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    run_server()