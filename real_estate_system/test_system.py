# test_system.py
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

try:
    from backend.mysql_database import MySQLRealEstateDB
    print("✅ MySQL database module imported successfully!")
    
    from backend.real_estate_backend import RealEstateBackend
    print("✅ Backend module imported successfully!")
    
    # Test database connection
    db = MySQLRealEstateDB()
    print("✅ Database connection successful!")
    
    # Test backend initialization
    backend = RealEstateBackend()
    print("✅ Backend initialized successfully!")
    
    print("\n🎉 All tests passed! The system is ready to run.")
    print("🚀 Run: cd frontend && python server.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n🔧 Troubleshooting steps:")
    print("1. Make sure MySQL is running")
    print("2. Check database credentials in mysql_database.py")
    print("3. Verify all required packages are installed")
    print("4. Check the file structure is correct")