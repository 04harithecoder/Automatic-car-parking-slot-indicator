"""
DB Manager — all MySQL operations for parking system.
Used by parking_main.py
"""

import mysql.connector
from datetime import datetime
from db_config import DB_CONFIG


def _conn():
    """Get a fresh DB connection."""
    return mysql.connector.connect(**DB_CONFIG)


# ─────────────────────────────────────────────────────────────
#   READ
# ─────────────────────────────────────────────────────────────
def get_all_slots():
    """
    Returns list of 10 dicts (index 0 = slot 1):
      { slot_id, is_occupied, owner_name, phone, vehicle_no, entry_time }
    Free slots have is_occupied=0 and empty strings.
    """
    conn = _conn()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM slots ORDER BY slot_id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_available_count():
    """Returns number of free slots."""
    conn = _conn()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM slots WHERE is_occupied = 0")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count


# ─────────────────────────────────────────────────────────────
#   ENTRY
# ─────────────────────────────────────────────────────────────
def enter_vehicle(owner_name, phone, vehicle_no):
    """
    Assigns first free slot to the vehicle.
    Returns assigned slot_id (1-based) or None if full.
    """
    conn = _conn()
    cur  = conn.cursor()

    # Find first free slot
    cur.execute("""
        SELECT slot_id FROM slots
        WHERE is_occupied = 0
        ORDER BY slot_id
        LIMIT 1
    """)
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return None   # parking full

    slot_id = row[0]

    # Mark occupied
    cur.execute("""
        UPDATE slots
        SET is_occupied = 1,
            owner_name  = %s,
            phone       = %s,
            vehicle_no  = %s,
            entry_time  = %s
        WHERE slot_id = %s
    """, (owner_name, phone, vehicle_no, datetime.now(), slot_id))

    conn.commit()
    cur.close()
    conn.close()
    return slot_id


# ─────────────────────────────────────────────────────────────
#   EXIT
# ─────────────────────────────────────────────────────────────
def exit_vehicle(slot_id):
    """
    Clears a slot by slot_id.
    Returns True if success, False if slot was already free.
    """
    conn = _conn()
    cur  = conn.cursor()

    # Check slot is occupied
    cur.execute("SELECT is_occupied FROM slots WHERE slot_id = %s", (slot_id,))
    row = cur.fetchone()

    if not row or row[0] == 0:
        cur.close()
        conn.close()
        return False   # already free

    cur.execute("""
        UPDATE slots
        SET is_occupied = 0,
            owner_name  = '',
            phone       = '',
            vehicle_no  = '',
            entry_time  = NULL
        WHERE slot_id = %s
    """, (slot_id,))

    conn.commit()
    cur.close()
    conn.close()
    return True
