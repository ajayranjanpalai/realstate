# generate_csv.py
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

def main():
    print("🎲 Generating sample real estate data...")
    
    try:
        from backend.real_estate_backend import RealEstateBackend
        
        # Create backend instance which will generate CSV
        backend = RealEstateBackend()
        
        # Check if properties were loaded/generated
        if backend.properties_df is not None:
            print(f"✅ Successfully generated {len(backend.properties_df)} properties")
            print(f"📁 CSV file should be at: {os.path.join(os.path.dirname(__file__), 'sample_real_estate_data.csv')}")
            
            # Display some sample data
            print("\n📋 Sample Properties:")
            print(backend.properties_df[['PropertyID', 'Title', 'City', 'Price_Cr']].head(10).to_string(index=False))
        else:
            print("❌ Failed to generate properties data")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()