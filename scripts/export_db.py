"""
Script to export database schema and data for migration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, MetaData
from models.database import Base
import json

def export_schema():
    """Export database schema as SQL"""
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    # Create schema.sql
    with open('schema.sql', 'w') as f:
        for table in Base.metadata.sorted_tables:
            f.write(str(table.compile(engine)) + ';\n\n')

def export_data():
    """Export table data as JSON for easy import"""
    engine = create_engine(os.getenv('DATABASE_URL'))
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    data = {}
    for table in metadata.sorted_tables:
        result = engine.execute(table.select())
        data[table.name] = [dict(row) for row in result]
    
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    print("Exporting database schema...")
    export_schema()
    print("Schema exported to schema.sql")
    
    print("Exporting data...")
    export_data()
    print("Data exported to data.json")
