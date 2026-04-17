import sqlite3
import os

db_path = 'ats_database.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE parsed_data ADD COLUMN raw_text TEXT')
        conn.commit()
        print('Successfully added raw_text column to parsed_data table.')
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            print('Column raw_text already exists.')
        else:
            print(f'Operational error: {e}')
    except Exception as e:
        print(f'An error occurred: {e}')
    finally:
        conn.close()
else:
    print(f'Database {db_path} not found.')
