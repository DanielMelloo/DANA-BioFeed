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
        # Create a new one if needed, but for migration we expect it to exist.
        return

    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Helper to add column safely
        def add_column(table, column_def):
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
                print(f"Added column: {column_def} to {table}")
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e):
                    print(f"Column already exists: {column_def} in {table}")
                else:
                    print(f"Error adding {column_def} to {table}: {e}")

        # Feeders Table Updates
        add_column("feeders", "block_name VARCHAR(64)")
        add_column("feeders", "water_mode VARCHAR(16) DEFAULT 'AUTO'")
        add_column("feeders", "water_valve_state VARCHAR(16) DEFAULT 'CLOSED'")

        # Tanks Table Updates
        add_column("tanks", "block_name VARCHAR(64)")
        
        conn.commit()
        conn.close()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
