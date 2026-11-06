import sqlite3

DB_PATH = "ticketmate.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Services Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_type TEXT NOT NULL,
        title TEXT NOT NULL,
        source TEXT,
        destination TEXT,
        departure_time TEXT,
        arrival_time TEXT,
        journey_date TEXT,
        stops TEXT,
        checkin_time TEXT,
        checkout_time TEXT,
        price REAL NOT NULL,
        total_units INTEGER NOT NULL
    )
    """)

    # 2. Units/Inventory Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        unit_identifier TEXT NOT NULL,
        is_booked INTEGER DEFAULT 0,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    )
    """)

    # 3. Bookings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_ref TEXT UNIQUE NOT NULL,
        service_id INTEGER NOT NULL,
        passenger_name TEXT NOT NULL,
        passenger_email TEXT NOT NULL,
        passenger_phone TEXT NOT NULL,
        unit_allocated TEXT NOT NULL,
        journey_date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        qr_code_path TEXT,
        booking_status TEXT DEFAULT 'CONFIRMED',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (service_id) REFERENCES services (id)
    )
    """)

    conn.commit()

    # Seed mock data if table is empty
    cursor.execute("SELECT COUNT(*) FROM services")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_data(cursor)
        conn.commit()

    conn.close()
    print("Database initialized and seeded successfully.")

def seed_data(cursor):
    demo_services = [
        ('bus', 'InterCity Express Bus', 'Bengaluru', 'Mysuru', '07:30 AM', '11:00 AM', '2026-11-10', 'Kengeri, Mandya, Srirangapatna', None, None, 450.0, 4),
        ('bus', 'KSRTC Airavat Club Class', 'Bengaluru', 'Chennai', '10:00 PM', '05:30 AM', '2026-11-10', 'Hosur, Krishnagiri, Vellore', None, None, 950.0, 4),
        ('train', 'Vande Bharat Express', 'Bengaluru', 'Chennai', '05:45 AM', '10:15 AM', '2026-11-10', 'KSR Bengaluru, Katpadi Junction, Chennai Central', None, None, 1080.0, 4),
        ('train', 'Shatabdi Express', 'Bengaluru', 'Mysuru', '11:00 AM', '01:00 PM', '2026-11-10', 'Bengaluru Cantt, Kengeri, Mysuru Jn', None, None, 520.0, 4),
        ('hotel', 'Grand Heritage Palace Hotel', None, 'Mysuru', None, None, '2026-11-10', 'Near Mysore Palace', '12:00 PM', '11:00 AM', 3200.0, 3),
        ('attraction', 'Mysore Palace Guided Entry Pass', None, 'Mysuru', '10:00 AM', '05:30 PM', '2026-11-10', 'Varaha Gate Entry', None, None, 150.0, 10),
        ('event', 'Bengaluru Tech Fest 2026', None, 'Bengaluru', '09:00 AM', '06:00 PM', '2026-11-10', 'Palace Grounds, Gate 4', None, None, 799.0, 5)
    ]

    for item in demo_services:
        cursor.execute("""
            INSERT INTO services (service_type, title, source, destination, departure_time, arrival_time, journey_date, stops, checkin_time, checkout_time, price, total_units)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)
        service_id = cursor.lastrowid

        stype = item[0]
        units_count = item[11]
        for i in range(1, units_count + 1):
            if stype == 'bus':
                unit_name = f"Seat {i:02d}"
            elif stype == 'train':
                unit_name = f"Coach C1-{i:02d}"
            elif stype == 'hotel':
                unit_name = f"Room {100 + i}"
            else:
                unit_name = f"Pass #{i:03d}"
            
            cursor.execute("""
                INSERT INTO service_units (service_id, unit_identifier, is_booked)
                VALUES (?, ?, 0)
            """, (service_id, unit_name))

if __name__ == "__main__":
    init_db()