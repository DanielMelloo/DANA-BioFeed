from main import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        with db.engine.connect() as conn:
            # Feeders Table Updates
            try:
                conn.execute(text("ALTER TABLE feeders ADD COLUMN block_name VARCHAR(64)"))
                print("Added block_name to feeders")
            except Exception as e:
                print(f"block_name exists or error: {e}")

            try:
                conn.execute(text("ALTER TABLE feeders ADD COLUMN water_mode VARCHAR(16) DEFAULT 'AUTO'"))
                print("Added water_mode to feeders")
            except Exception as e:
                print(f"water_mode exists or error: {e}")

            try:
                conn.execute(text("ALTER TABLE feeders ADD COLUMN water_valve_state VARCHAR(16) DEFAULT 'CLOSED'"))
                print("Added water_valve_state to feeders")
            except Exception as e:
                print(f"water_valve_state exists or error: {e}")

            # Tanks Table Updates
            try:
                conn.execute(text("ALTER TABLE tanks ADD COLUMN block_name VARCHAR(64)"))
                print("Added block_name to tanks")
            except Exception as e:
                print(f"block_name exists or error: {e}")
            
            conn.commit()

if __name__ == "__main__":
    migrate()
