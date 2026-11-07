import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = "ticketmate.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table (Students)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        college TEXT,
        student_id TEXT,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Travel & Event Services Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_type TEXT NOT NULL CHECK(service_type IN ('bus', 'train', 'hotel', 'attraction', 'event')),
        title TEXT NOT NULL,
        source TEXT,
        destination TEXT NOT NULL,
        departure_time TEXT,
        arrival_time TEXT,
        journey_date TEXT NOT NULL,
        stops TEXT,
        checkin_time TEXT,
        checkout_time TEXT,
        description TEXT,
        image_url TEXT,
        price REAL NOT NULL,
        total_units INTEGER NOT NULL
    )
    """)

    # 3. Service Units (Seats / Rooms / Passes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id INTEGER NOT NULL,
        unit_identifier TEXT NOT NULL,
        is_booked INTEGER DEFAULT 0 CHECK(is_booked IN (0, 1)),
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
    )
    """)

    # 4. Bookings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_ref TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        service_id INTEGER NOT NULL,
        passenger_name TEXT NOT NULL,
        passenger_email TEXT NOT NULL,
        passenger_phone TEXT NOT NULL,
        unit_allocated TEXT NOT NULL,
        journey_date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        payment_id TEXT,
        payment_method TEXT,
        payment_status TEXT DEFAULT 'PENDING' CHECK(payment_status IN ('PENDING', 'PAID', 'FAILED', 'REFUNDED')),
        booking_status TEXT DEFAULT 'CONFIRMED' CHECK(booking_status IN ('CONFIRMED', 'CANCELLED')),
        qr_code_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (service_id) REFERENCES services (id)
    )
    """)

    # 5. Payments Table (Audit trail)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_ref TEXT UNIQUE NOT NULL,
        booking_ref TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_method TEXT NOT NULL CHECK(payment_method IN ('upi', 'card', 'netbanking', 'wallet')),
        status TEXT NOT NULL CHECK(status IN ('SUCCESS', 'FAILED')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (booking_ref) REFERENCES bookings (booking_ref),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM services")
    if cursor.fetchone()[0] == 0:
        seed_data(cursor)
        conn.commit()

    conn.close()
    print("Database initialized and verified successfully.")

def seed_data(cursor):
    # Pre-seed demo student account
    demo_password_hash = generate_password_hash("Student@123")
    cursor.execute("""
        INSERT INTO users (name, email, phone, college, student_id, password_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("Kallanagouda Patil", "demo.student@ticketmate.ai", "9876543210", "VTU Engineering", "1VA22CS045", demo_password_hash))

    demo_services = [
        # Buses
        ('bus', '[DEMO INVENTORY] KSRTC Airavat Club Class', 'Bengaluru', 'Mysuru', '07:30 AM', '10:45 AM', '2026-11-10', 'Kengeri, Mandya, Srirangapatna', None, None, 'Premium AC Volvo multi-axle sleeper bus.', '/static/images/bus1.jpg', 450.0, 6),
        ('bus', '[DEMO INVENTORY] VRL Multi-Axle Volvo', 'Bengaluru', 'Chennai', '10:00 PM', '05:30 AM', '2026-11-10', 'Electronic City, Hosur, Vellore', None, None, 'Comfortable night service with charging ports.', '/static/images/bus2.jpg', 850.0, 6),
        
        # Trains
        ('train', '[DEMO INVENTORY] Vande Bharat Express (20608)', 'Bengaluru', 'Chennai', '05:45 AM', '10:15 AM', '2026-11-10', 'KSR Bengaluru, Katpadi Jn, Chennai Central', None, None, 'High-speed chair car executive travel.', '/static/images/train1.jpg', 1080.0, 8),
        ('train', '[DEMO INVENTORY] Shatabdi Express (12007)', 'Bengaluru', 'Mysuru', '11:00 AM', '01:00 PM', '2026-11-10', 'Bengaluru Cantt, Mandya, Mysuru Jn', None, None, 'Superfast express with complimentary breakfast.', '/static/images/train2.jpg', 520.0, 8),
        
        # Hotels
        ('hotel', '[DEMO INVENTORY] Grand Heritage Palace Hotel', 'Mysuru', 'Mysuru', None, None, '2026-11-10', 'Near Mysore Palace North Gate', '12:00 PM', '11:00 AM', 'Heritage stay with free high-speed WiFi and pool.', '/static/images/hotel1.jpg', 2400.0, 4),
        ('hotel', '[DEMO INVENTORY] Royal Orchid Metropole', 'Mysuru', 'Mysuru', None, None, '2026-11-10', 'JBS Road, Mysuru', '01:00 PM', '11:00 AM', 'Colonial-style luxury accommodation with breakfast.', '/static/images/hotel2.jpg', 3800.0, 3),

        # Attractions
        ('attraction', '[DEMO INVENTORY] Mysore Palace Fast-Track Entry', 'Mysuru', 'Mysuru', '10:00 AM', '05:30 PM', '2026-11-10', 'Varaha Gate Entry', None, None, 'Skip-the-line entrance pass with audio guide headset.', '/static/images/attraction1.jpg', 150.0, 20),
        ('attraction', '[DEMO INVENTORY] Chamundi Hill & Temple Guided Pass', 'Mysuru', 'Mysuru', '06:00 AM', '07:00 PM', '2026-11-10', 'Chamundeshwari Steps Base', None, None, 'Entry and priority darshan pass.', '/static/images/attraction2.jpg', 100.0, 20),

        # Events
        ('event', '[DEMO INVENTORY] Karnataka State Tech Conclave 2026', 'Bengaluru', 'Bengaluru', '09:00 AM', '06:00 PM', '2026-11-10', 'Palace Grounds, Gate 4', None, None, 'Annual hackathon, tech keynotes, and recruiter fair.', '/static/images/event1.jpg', 399.0, 15)
    ]

    for item in demo_services:
        cursor.execute("""
            INSERT INTO services (
                service_type, title, source, destination, departure_time, arrival_time,
                journey_date, stops, checkin_time, checkout_time, description, image_url, price, total_units
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)
        service_id = cursor.lastrowid
        stype = item[0]
        units_count = item[13]

        for i in range(1, units_count + 1):
            if stype == 'bus':
                unit_identifier = f"Seat {i:02d}"
            elif stype == 'train':
                unit_identifier = f"Coach C1-{i:02d}"
            elif stype == 'hotel':
                unit_identifier = f"Room {100 + i}"
            else:
                unit_identifier = f"Pass #{i:03d}"

            cursor.execute("""
                INSERT INTO service_units (service_id, unit_identifier, is_booked)
                VALUES (?, ?, 0)
            """, (service_id, unit_identifier))

if __name__ == "__main__":
    init_db()