
// ==========================================
// TICKETMATE AI - FRONTEND JAVASCRIPT
// Member 1 - Frontend
// ==========================================

// Get HTML elements
const categoryButtons = document.querySelectorAll(".category-btn");
const searchForm = document.getElementById("searchForm");

const fromGroup = document.getElementById("fromGroup");
const toGroup = document.getElementById("toGroup");
const peopleGroup = document.getElementById("peopleGroup");

const fromInput = document.getElementById("from");
const toInput = document.getElementById("to");
const travelDate = document.getElementById("travelDate");
const peopleInput = document.getElementById("people");

const dateLabel = document.getElementById("dateLabel");
const results = document.getElementById("results");

const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const chatMessages = document.getElementById("chatMessages");

// Current selected category
let selectedCategory = "bus";

// Set today's date as the minimum journey date
const today = new Date();
const localToday = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0")
].join("-");

travelDate.min = localToday;

// ==========================================
// CATEGORY SELECTION
// ==========================================

categoryButtons.forEach(button => {

    button.addEventListener("click", () => {

        // Remove active class from all buttons
        categoryButtons.forEach(btn => {
            btn.classList.remove("active");
        });

        // Activate selected button
        button.classList.add("active");

        // Get selected category
        selectedCategory = button.dataset.category;

        updateSearchForm();
    });

});

// ==========================================
// UPDATE SEARCH FORM BASED ON CATEGORY
// ==========================================

function updateSearchForm() {

    // Reset visibility
    fromGroup.style.display = "flex";
    toGroup.style.display = "flex";
    peopleGroup.style.display = "flex";

    // Reset labels and placeholders
    fromInput.required = true;
    toInput.required = true;

    fromInput.placeholder = "Departure city";
    toInput.placeholder = "Destination city";

    dateLabel.textContent = "Journey Date";
    peopleGroup.querySelector("label").textContent =
        "Passengers";

    if (selectedCategory === "bus") {

        fromGroup.style.display = "flex";
        toGroup.style.display = "flex";

        fromInput.placeholder = "Departure city";
        toInput.placeholder = "Destination city";

        dateLabel.textContent = "Journey Date";
        peopleGroup.querySelector("label").textContent =
            "Passengers";

    }

    else if (selectedCategory === "train") {

        fromGroup.style.display = "flex";
        toGroup.style.display = "flex";

        fromInput.placeholder = "Departure station";
        toInput.placeholder = "Destination station";

        dateLabel.textContent = "Travel Date";
        peopleGroup.querySelector("label").textContent =
            "Passengers";

    }

    else if (selectedCategory === "hotel") {

        fromGroup.style.display = "none";
        toGroup.style.display = "flex";

        fromInput.required = false;
        toInput.placeholder = "City or hotel destination";

        dateLabel.textContent = "Check-in Date";
        peopleGroup.querySelector("label").textContent =
            "Guests";

    }

    else if (selectedCategory === "attraction") {

        fromGroup.style.display = "none";
        toGroup.style.display = "flex";

        fromInput.required = false;
        toInput.placeholder = "City or attraction";

        dateLabel.textContent = "Visit Date";
        peopleGroup.querySelector("label").textContent =
            "Visitors";

    }

    else if (selectedCategory === "event") {

        fromGroup.style.display = "none";
        toGroup.style.display = "flex";

        fromInput.required = false;
        toInput.placeholder = "City or event name";

        dateLabel.textContent = "Event Date";
        peopleGroup.querySelector("label").textContent =
            "Tickets";

    }
}

// ==========================================
// SEARCH FORM
// ==========================================

searchForm.addEventListener("submit", function(event) {

    event.preventDefault();

    const searchData = {
        category: selectedCategory,
        from: fromInput.value.trim(),
        to: toInput.value.trim(),
        date: travelDate.value,
        people: Number(peopleInput.value)
    };

    // Validate required fields
    if (!searchData.to) {
        alert("Please enter your destination.");
        return;
    }

    if (!searchData.date) {
        alert("Please select a date.");
        return;
    }

    if (searchData.people < 1) {
        alert("Please enter at least 1 passenger or guest.");
        return;
    }

    if (
        (selectedCategory === "bus" ||
         selectedCategory === "train") &&
        !searchData.from
    ) {
        alert("Please enter your departure location.");
        return;
    }

    // Show integration message
    results.innerHTML = `
        <div class="result-card">
            <h3>🔍 ${searchData.category.toUpperCase()} SEARCH</h3>
            <p><strong>From:</strong>
                ${searchData.from || "Not applicable"}</p>
            <p><strong>Destination:</strong>
                ${searchData.to}</p>
            <p><strong>Date:</strong>
                ${searchData.date}</p>
            <p><strong>Passengers / Guests:</strong>
                ${searchData.people}</p>
            <p style="margin-top: 15px; color: #635bff;">
                Search details captured successfully.
                Live results will appear after backend API integration.
            </p>
        </div>
    `;

    console.log("TicketMate Search Request:", searchData);

});

// ==========================================
// AI CHAT INTERFACE
// ==========================================

chatForm.addEventListener("submit", function(event) {

    event.preventDefault();

    const message = chatInput.value.trim();

    if (!message) {
        return;
    }

    // Display user's message
    const userMessage = document.createElement("div");
    userMessage.className = "user-message";
    userMessage.textContent = message;

    chatMessages.appendChild(userMessage);

    // Display backend integration notice
    const botMessage = document.createElement("div");
    botMessage.className = "bot-message";
    botMessage.textContent =
        "Your message has been entered. Gemini AI will be connected through the backend.";

    chatMessages.appendChild(botMessage);

    // Clear input
    chatInput.value = "";

    // Scroll to latest message
    chatMessages.scrollTop = chatMessages.scrollHeight;

});

// ==========================================
// INITIALIZE WEBSITE
// ==========================================

updateSearchForm();

console.log("TicketMate AI frontend loaded successfully!");
