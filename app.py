# Frontend Template Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/bookings")
def view_bookings():
    return render_template("bookings.html")

@app.route("/chat")
@app.route("/assistant")
def assistant_chat():
    return render_template("assistant.html")

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

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/profile")
def profile_page():
    return render_template("profile.html")