import sqlite3
import os

def migrate():
    # Try to find the database
    db_paths = ['feeders_v7.db', 'instance/feeders_v7.db']
    db_path = None
    
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("Database not found! Checked: " + ", ".join(db_paths))
        return

    abs_path = os.path.abspath(db_path)
    print(f"Migrating database: {abs_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Debug: List existing columns
        print("--- Current Columns in 'feeders' ---")
        cursor.execute("PRAGMA table_info(feeders)")
        columns = [info[1] for info in cursor.fetchall()]
        print(columns)
        print("------------------------------------")
        
        # Helper to add column safely
        def add_column(table, column_def):
            col_name = column_def.split()[0]
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
                print(f"✅ Added column: {column_def} to {table}")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e):
                    print(f"ℹ️  Column already exists: {col_name} in {table}")
                else:
                    print(f"❌ Error adding {col_name} to {table}: {e}")

        # Feeders Table Updates
        add_column("feeders", "block_name VARCHAR(64)")
        add_column("feeders", "water_mode VARCHAR(16) DEFAULT 'AUTO'")
        add_column("feeders", "water_valve_state VARCHAR(16) DEFAULT 'CLOSED'")
        add_column("feeders", "last_stable_weight FLOAT DEFAULT 0.0")
        add_column("feeders", "maintenance_mode BOOLEAN DEFAULT 0")

        # Tanks Table Updates
        add_column("tanks", "block_name VARCHAR(64)")
        
        conn.commit()
        
        # Verify after update
        print("--- Updated Columns in 'feeders' ---")
        cursor.execute("PRAGMA table_info(feeders)")
        columns = [info[1] for info in cursor.fetchall()]
        print(columns)
        print("------------------------------------")
        
        conn.close()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
