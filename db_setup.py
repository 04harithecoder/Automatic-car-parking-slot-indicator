"""
Run this ONCE to create the database and table.
    python db_setup.py
"""

import mysql.connector
from db_config import DB_CONFIG

def setup():
    # Connect without selecting a DB first
    conn = mysql.connector.connect(
        host     = DB_CONFIG["host"],
        user     = DB_CONFIG["user"],
        password = DB_CONFIG["password"]
    )
    cur = conn.cursor()

    # Create database
    cur.execute("CREATE DATABASE IF NOT EXISTS parking_db")
    cur.execute("USE parking_db")

    # Create slots table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            slot_id      INT PRIMARY KEY,
            is_occupied  TINYINT(1) DEFAULT 0,
            owner_name   VARCHAR(50)  DEFAULT '',
            phone        VARCHAR(15)  DEFAULT '',
            vehicle_no   VARCHAR(15)  DEFAULT '',
            entry_time   DATETIME     DEFAULT NULL
        )
    """)

    # Insert 10 slots if not already present
    for i in range(1, 11):
        cur.execute("""
            INSERT IGNORE INTO slots (slot_id, is_occupied)
            VALUES (%s, 0)
        """, (i,))

    conn.commit()
    cur.close()
    conn.close()
    print("✔  parking_db created!")
    print("✔  slots table ready with 10 slots!")

if __name__ == "__main__":
    setup()
