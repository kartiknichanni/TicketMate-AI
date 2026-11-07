import os
import uuid
import json
import qrcode
from functools import wraps
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db
from google import genai

load_dotenv()

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
app = Flask(__name__, template_folder=str(BASE_DIR / "templates"),
            static_folder=str(BASE_DIR / "static"))
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ticketmate_super_secret_hackathon_2026")
CORS(app)

QR_FOLDER = os.path.join("static", "qrcodes")
os.makedirs(QR_FOLDER, exist_ok=True)

# Initialize Gemini Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = None
if GEMINI_API_KEY and GEMINI_API_KEY != "your_actual_gemini_api_key_here":
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Warning: Gemini client initialization error: {e}")

# ==========================================
# AUTHENTICATION DECORATOR
# ==========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json:
                return jsonify({"status": "error", "message": "Authentication required. Please log in."}), 401
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# FRONTEND TEMPLATE ROUTES
# ==========================================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/bus")
def bus_page():
    return render_template("bus.html")

@app.route("/train")
def train_page():
    return render_template("train.html")

@app.route("/hotels")
def hotels_page():
    return render_template("hotels.html")

@app.route("/events")
def events_page():
    return render_template("events.html")

@app.route("/attractions")
def attractions_page():
    return render_template("attractions.html")

@app.route("/assistant")
@app.route("/chat")
def assistant_page():
    return render_template("assistant.html")

@app.route("/bookings")
@login_required
def bookings_page():
    return render_template("bookings.html")

@app.route("/profile")
@login_required
def profile_page():
    return render_template("profile.html")

@app.route("/payment")
@login_required
def payment_page():
    return render_template("payment.html")


# ==========================================
# AUTHENTICATION & STUDENT PROFILE APIS
# ==========================================
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    phone = data.get("phone", "").strip()
    college = data.get("college", "").strip()
    student_id = data.get("student_id", "").strip()

    if not name or not email or not password:
        return jsonify({"status": "error", "message": "Name, email, and password are required."}), 400

    hashed_pw = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (name, email, phone, college, student_id, password_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, email, phone, college, student_id, hashed_pw))
        conn.commit()
        user_id = cursor.lastrowid

        session["user_id"] = user_id
        session["user_name"] = name
        session["user_email"] = email

        return jsonify({
            "status": "success",
            "message": "Student registered and authenticated.",
            "user": {"id": user_id, "name": name, "email": email, "college": college, "student_id": student_id}
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Email is already registered."}), 409
    finally:
        conn.close()

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"status": "error", "message": "Invalid email or password."}), 401

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]

    return jsonify({
        "status": "success",
        "message": "Login successful.",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "college": user["college"],
            "student_id": user["student_id"]
        }
    }), 200

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success", "message": "Session terminated successfully."}), 200

@app.route("/api/auth/profile", methods=["GET", "PUT"])
@login_required
def user_profile():
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "GET":
        cursor.execute("SELECT id, name, email, phone, college, student_id, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return jsonify({"status": "success", "profile": dict(user)}), 200

    if request.method == "PUT":
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        phone = data.get("phone", "").strip()
        college = data.get("college", "").strip()
        student_id = data.get("student_id", "").strip()

        cursor.execute("""
            UPDATE users SET name = COALESCE(NULLIF(?, ''), name),
                             phone = COALESCE(NULLIF(?, ''), phone),
                             college = COALESCE(NULLIF(?, ''), college),
                             student_id = COALESCE(NULLIF(?, ''), student_id)
            WHERE id = ?
        """, (name, phone, college, student_id, user_id))
        conn.commit()

        cursor.execute("SELECT id, name, email, phone, college, student_id FROM users WHERE id = ?", (user_id,))
        updated = cursor.fetchone()
        conn.close()

        session["user_name"] = updated["name"]
        return jsonify({"status": "success", "message": "Profile updated successfully.", "profile": dict(updated)}), 200


# ==========================================
# STRUCTURED TRAVEL SEARCH APIS
# ==========================================
def query_services_by_type(stype, source=None, destination=None, date=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT s.*, 
               (SELECT COUNT(*) FROM service_units su WHERE su.service_id = s.id AND su.is_booked = 0) as available_units
        FROM services s
        WHERE LOWER(s.service_type) = ?
    """
    params = [stype.lower()]

    if source:
        query += " AND LOWER(s.source) LIKE ?"
        params.append(f"%{source.lower()}%")
    if destination:
        query += " AND LOWER(s.destination) LIKE ?"
        params.append(f"%{destination.lower()}%")
    if date:
        query += " AND s.journey_date = ?"
        params.append(date)

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.route("/api/search/buses", methods=["GET"])
def search_buses():
    source = request.args.get("source", "").strip()
    destination = request.args.get("destination", "").strip()
    date = request.args.get("date", "").strip()
    return jsonify({"status": "success", "data": query_services_by_type("bus", source, destination, date)}), 200

@app.route("/api/search/trains", methods=["GET"])
def search_trains():
    source = request.args.get("source", "").strip()
    destination = request.args.get("destination", "").strip()
    date = request.args.get("date", "").strip()
    return jsonify({"status": "success", "data": query_services_by_type("train", source, destination, date)}), 200

@app.route("/api/search/hotels", methods=["GET"])
def search_hotels():
    destination = request.args.get("destination", "").strip()
    date = request.args.get("date", "").strip()
    return jsonify({"status": "success", "data": query_services_by_type("hotel", None, destination, date)}), 200

@app.route("/api/search/attractions", methods=["GET"])
def search_attractions():
    destination = request.args.get("destination", "").strip()
    return jsonify({"status": "success", "data": query_services_by_type("attraction", None, destination, None)}), 200

@app.route("/api/search/events", methods=["GET"])
def search_events():
    destination = request.args.get("destination", "").strip()
    return jsonify({"status": "success", "data": query_services_by_type("event", None, destination, None)}), 200

@app.route("/api/services/<int:service_id>/availability", methods=["GET"])
def get_service_availability(service_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,))
    service = cursor.fetchone()
    if not service:
        conn.close()
        return jsonify({"status": "error", "message": "Service not found."}), 404

    cursor.execute("SELECT id, unit_identifier, is_booked FROM service_units WHERE service_id = ?", (service_id,))
    units = [dict(r) for r in cursor.fetchall()]
    conn.close()

    available_units = [u for u in units if u["is_booked"] == 0]
    return jsonify({
        "status": "success",
        "service": dict(service),
        "total_units": len(units),
        "available_count": len(available_units),
        "units": units
    }), 200


# ==========================================
# GEMINI AI TRAVEL ASSISTANT (CONVERSATIONAL PLANNING)
# ==========================================
@app.route("/api/chat", methods=["POST"])
def gemini_conversational_assistant():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    history = data.get("history", [])  # List of {"role": "user"|"model", "text": "..."}

    if not user_message:
        return jsonify({"status": "error", "message": "Message parameter is required."}), 400

    if not gemini_client:
        return jsonify({
            "status": "error",
            "reply": "The AI assistant service is temporarily unconfigured. Please configure GEMINI_API_KEY."
        }), 503

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, s.service_type, s.title, s.source, s.destination, s.departure_time, 
               s.arrival_time, s.journey_date, s.price,
               (SELECT COUNT(*) FROM service_units su WHERE su.service_id = s.id AND su.is_booked = 0) as seats_left
        FROM services s
    """)
    inventory = [dict(r) for r in cursor.fetchall()]
    conn.close()

    system_instruction = f"""
You are TicketMate AI, an expert, warm, and highly structured travel planner for Indian travelers.
All inventory items below are part of our [DEMO INVENTORY].

REAL DATABASE INVENTORY GROUND TRUTH:
{json.dumps(inventory, indent=2)}

CRITICAL OPERATIONAL RULES:
1. ONLY recommend services that exist in the inventory above.
2. Quoted prices (in INR), timings, source, destination, and IDs MUST match the database inventory.
3. NEVER invent imaginary trains, bus routes, seat counts, or hotel rates.
4. CONVERSATIONAL PLANNING REQUIREMENT:
   - If the user says something general like "I want to travel to Mysuru", do not just dump services.
   - Ask clarifying follow-ups for: (a) Starting location, (b) Date of travel, (c) Number of passengers, and (d) Mode preference (Bus vs Train).
5. When presenting matching options, format them clearly with:
   - Title
   - Time
   - Price (INR)
   - Available Seats
   - Direct Call-To-Action: "You can book this on our Bus/Train page or proceed to checkout."
6. If no inventory matches, inform the user honestly and suggest looking at available demo routes (Bengaluru to Mysuru or Chennai).
7. Keep responses concise, helpful, and natural.
"""

    prompt = f"{system_instruction}\n\nRecent Conversation History:\n"
    for turn in history[-6:]:
        speaker = "User" if turn.get("role") == "user" else "Assistant"
        prompt += f"{speaker}: {turn.get('text')}\n"

    prompt += f"\nUser: {user_message}\nAssistant:"

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return jsonify({
            "status": "success",
            "reply": response.text,
            "relevant_services": [s for s in inventory if s["destination"].lower() in user_message.lower() or (s["source"] and s["source"].lower() in user_message.lower())]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"AI Engine error: {str(e)}"}), 500


# ==========================================
# BOOKING, DEMO PAYMENT & QR TICKET GENERATION
# ==========================================
@app.route("/api/bookings/create", methods=["POST"])
@login_required
def create_booking_intent():
    data = request.get_json() or {}
    service_id = data.get("service_id")
    unit_id = data.get("unit_id")
    passenger_name = data.get("passenger_name", "").strip()
    passenger_email = data.get("passenger_email", "").strip()
    passenger_phone = data.get("passenger_phone", "").strip()

    if not all([service_id, unit_id, passenger_name, passenger_email, passenger_phone]):
        return jsonify({"status": "error", "message": "All passenger and seat details are required."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,))
    service = cursor.fetchone()
    if not service:
        conn.close()
        return jsonify({"status": "error", "message": "Selected service does not exist."}), 404

    cursor.execute("SELECT * FROM service_units WHERE id = ? AND service_id = ?", (unit_id, service_id))
    unit = cursor.fetchone()
    if not unit:
        conn.close()
        return jsonify({"status": "error", "message": "Invalid seat or room selection."}), 400

    if unit["is_booked"] == 1:
        conn.close()
        return jsonify({"status": "error", "message": "Seat/Unit is already occupied. Please pick another."}), 409

    booking_ref = f"TM-{uuid.uuid4().hex[:8].upper()}"

    cursor.execute("""
        INSERT INTO bookings (
            booking_ref, user_id, service_id, passenger_name, passenger_email,
            passenger_phone, unit_allocated, journey_date, total_amount,
            payment_status, booking_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', 'CONFIRMED')
    """, (
        booking_ref, session["user_id"], service_id, passenger_name, passenger_email,
        passenger_phone, unit["unit_identifier"], service["journey_date"], service["price"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Booking initiated. Complete DEMO PAYMENT to confirm.",
        "booking_ref": booking_ref,
        "amount": service["price"],
        "unit_id": unit_id,
        "service_title": service["title"]
    }), 201

@app.route("/api/payment/demo-process", methods=["POST"])
@login_required
def process_demo_payment():
    data = request.get_json() or {}
    booking_ref = data.get("booking_ref")
    payment_method = data.get("payment_method", "").lower()
    demo_auth_token = data.get("demo_auth_token", "VALID_DEMO_AUTH")

    if not booking_ref or payment_method not in ['upi', 'card', 'netbanking', 'wallet']:
        return jsonify({"status": "error", "message": "Invalid payment parameters or unsupported payment method."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE booking_ref = ? AND user_id = ?", (booking_ref, session["user_id"]))
    booking = cursor.fetchone()
    if not booking:
        conn.close()
        return jsonify({"status": "error", "message": "Booking record not found or access denied."}), 404

    if booking["payment_status"] == "PAID":
        conn.close()
        return jsonify({"status": "error", "message": "This booking has already been paid and confirmed."}), 400

    if demo_auth_token == "FAIL":
        cursor.execute("UPDATE bookings SET payment_status = 'FAILED' WHERE booking_ref = ?", (booking_ref,))
        conn.commit()
        conn.close()
        return jsonify({"status": "error", "message": "DEMO PAYMENT failed: Bank simulated decline."}), 402

    try:
        cursor.execute("""
            UPDATE service_units 
            SET is_booked = 1 
            WHERE service_id = ? AND unit_identifier = ? AND is_booked = 0
        """, (booking["service_id"], booking["unit_allocated"]))

        if cursor.rowcount == 0:
            conn.rollback()
            conn.close()
            return jsonify({"status": "error", "message": "Unit was taken by another user during payment."}), 409

        payment_ref = f"PAY-DEMO-{uuid.uuid4().hex[:10].upper()}"

        qr_content = f"TICKETMATE VERIFIED DEMO PASS\nRef: {booking_ref}\nPassenger: {booking['passenger_name']}\nAllocated: {booking['unit_allocated']}\nDate: {booking['journey_date']}\nPayment Ref: {payment_ref}\nStatus: PAID"
        qr_img = qrcode.make(qr_content)
        qr_filename = f"{booking_ref}.png"
        qr_filepath = os.path.join(QR_FOLDER, qr_filename)
        qr_img.save(qr_filepath)

        cursor.execute("""
            UPDATE bookings 
            SET payment_id = ?, payment_method = ?, payment_status = 'PAID', qr_code_path = ?
            WHERE booking_ref = ?
        """, (payment_ref, payment_method, f"/static/qrcodes/{qr_filename}", booking_ref))

        cursor.execute("""
            INSERT INTO payments (payment_ref, booking_ref, user_id, amount, payment_method, status)
            VALUES (?, ?, ?, ?, ?, 'SUCCESS')
        """, (payment_ref, booking_ref, session["user_id"], booking["total_amount"], payment_method))

        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "DEMO PAYMENT successful! Ticket confirmed.",
            "payment_ref": payment_ref,
            "booking_ref": booking_ref,
            "qr_code_url": f"/static/qrcodes/{qr_filename}"
        }), 200

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"status": "error", "message": f"Payment processing failure: {str(e)}"}), 500

@app.route("/api/bookings/my-bookings", methods=["GET"])
@login_required
def list_my_bookings():
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, s.title as service_title, s.service_type, s.source, s.destination, 
               s.departure_time, s.arrival_time, s.description
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
    """, (user_id,))
    bookings = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({"status": "success", "count": len(bookings), "data": bookings}), 200

@app.route("/api/bookings/<booking_ref>", methods=["GET"])
@login_required
def get_booking_details(booking_ref):
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, s.title as service_title, s.service_type, s.source, s.destination,
               s.departure_time, s.arrival_time
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        WHERE b.booking_ref = ? AND b.user_id = ?
    """, (booking_ref, user_id))
    booking = cursor.fetchone()
    conn.close()

    if not booking:
        return jsonify({"status": "error", "message": "Booking not found or access denied."}), 404

    return jsonify({"status": "success", "booking": dict(booking)}), 200

@app.route("/api/bookings/<booking_ref>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_ref):
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE booking_ref = ? AND user_id = ?", (booking_ref, user_id))
    booking = cursor.fetchone()

    if not booking:
        conn.close()
        return jsonify({"status": "error", "message": "Booking not found or unauthorized."}), 404

    if booking["booking_status"] == "CANCELLED":
        conn.close()
        return jsonify({"status": "error", "message": "Booking is already cancelled."}), 400

    cursor.execute("""
        UPDATE service_units 
        SET is_booked = 0 
        WHERE service_id = ? AND unit_identifier = ?
    """, (booking["service_id"], booking["unit_allocated"]))

    cursor.execute("""
        UPDATE bookings 
        SET booking_status = 'CANCELLED', payment_status = 'REFUNDED'
        WHERE booking_ref = ?
    """, (booking_ref,))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": f"Booking {booking_ref} cancelled. Seat released."
    }), 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)