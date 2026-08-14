import json
import os
import sys
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from sqlalchemy import create_engine, MetaData, Table, select, text
from sqlalchemy.orm import sessionmaker

def custom_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='ignore')
    raise TypeError(f"Type {type(obj)} not serializable")

def backup(database_url, output_path):
    print(f"Connecting to database to backup...")
    engine = create_engine(database_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    backup_data = {}
    
    with engine.connect() as conn:
        # Get tables in topological order (dependencies first)
        for table in metadata.sorted_tables:
            table_name = table.name
            # Skip system or metadata tables if any, but we want all user tables
            if table_name.startswith('pg_'):
                continue
            
            print(f"Backing up table: {table_name}...")
            # Query all rows
            stmt = select(table)
            result = conn.execute(stmt)
            
            # Fetch column names
            columns = table.columns.keys()
            
            # Fetch all rows as list of dicts
            rows = []
            for row in result:
                row_dict = dict(zip(columns, row))
                rows.append(row_dict)
                
            backup_data[table_name] = {
                "columns": columns,
                "rows": rows
            }
            print(f"Saved {len(rows)} rows for {table_name}.")
            
    with open(output_path, "w") as f:
        json.dump(backup_data, f, indent=2, default=custom_serializer)
        
    print(f"Backup successfully completed! File saved to {output_path}")

def restore(database_url, input_path):
    if not os.path.exists(input_path):
        print(f"Error: Backup file {input_path} does not exist.")
        return
        
    print(f"Loading backup data from {input_path}...")
    with open(input_path, "r") as f:
        backup_data = json.load(f)
        
    print(f"Connecting to target database...")
    engine = create_engine(database_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # We must disable triggers and foreign key checks during import, or insert in topological order
    use_replica_role = False
    try:
        with engine.connect() as test_conn:
            test_conn.execute(text("SET session_replication_role = 'replica';"))
            use_replica_role = True
            print("Verified permission to set session_replication_role = 'replica'.")
    except Exception as e:
        print(f"Warning: Cannot set session_replication_role (e.g. not superuser/owner): {e}. Relying on table dependency ordering.")

    with engine.begin() as conn:
        if use_replica_role:
            conn.execute(text("SET session_replication_role = 'replica';"))
            
        for table in metadata.sorted_tables:
            table_name = table.name
            if table_name not in backup_data:
                print(f"Skipping table {table_name} (no data in backup).")
                continue
                
            data = backup_data[table_name]
            rows = data["rows"]
            if not rows:
                print(f"Table {table_name} has 0 rows. Skipping insert.")
                continue
                
            print(f"Restoring {len(rows)} rows to table {table_name}...")
            
            # Clean existing data to avoid duplicates
            conn.execute(table.delete())
            
            # Insert rows
            conn.execute(table.insert(), rows)
            
            # Reset postgres sequences if the table has an serial/identity primary key
            for col in table.primary_key.columns:
                if col.type.__class__.__name__ in ['Integer', 'BigInteger']:
                    seq_query = f"SELECT pg_get_serial_sequence('{table_name}', '{col.name}')"
                    try:
                        seq_name_res = conn.execute(text(seq_query)).scalar()
                        if seq_name_res:
                            reset_query = f"SELECT setval('{seq_name_res}', COALESCE((SELECT MAX({col.name}) FROM {table_name}), 1), true)"
                            conn.execute(text(reset_query))
                            print(f"Reset sequence for {table_name}.{col.name}")
                    except Exception as seq_err:
                        print(f"Could not reset sequence for {table_name}: {seq_err}")
                        
        if use_replica_role:
            try:
                conn.execute(text("SET session_replication_role = 'origin';"))
                print("Restored session_replication_role to origin.")
            except Exception as e:
                pass

    print("Restore successfully completed!")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage:")
        print("  python backup_database.py backup <db_url> <output_file.json>")
        print("  python backup_database.py restore <db_url> <input_file.json>")
        sys.exit(1)
        
    action = sys.argv[1]
    db_url = sys.argv[2]
    file_path = sys.argv[3]
    
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    if action == "backup":
        backup(db_url, file_path)
    elif action == "restore":
        restore(db_url, file_path)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
