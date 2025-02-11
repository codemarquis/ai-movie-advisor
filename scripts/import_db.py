"""
Script to import database schema and data from exported files
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
import json
from models.database import Base

def import_schema():
    """Import database schema from schema.sql"""
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    # Create tables using SQLAlchemy models
    Base.metadata.create_all(engine)
    print("Schema imported successfully")

def import_data():
    """Import data from data.json"""
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
        
        for table_name, rows in data.items():
            if rows:
                # Convert the first row's keys into column names
                columns = ', '.join(rows[0].keys())
                # Create the parameterized values string
                values = ', '.join([':' + key for key in rows[0].keys()])
                
                for row in rows:
                    query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
                    engine.execute(text(query), **row)
        
        print("Data imported successfully")
    except FileNotFoundError:
        print("No data.json file found. Skipping data import.")

if __name__ == "__main__":
    print("Importing database schema...")
    import_schema()
    
    print("Importing data...")
    import_data()
