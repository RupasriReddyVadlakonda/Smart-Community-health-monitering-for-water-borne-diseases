const API_BASE = "http://127.0.0.1:5000";
let currentUser = localStorage.getItem("current_user");

// Update nav on load
window.addEventListener("load", () => {
    if (currentUser) {
        showPage("dashboard-page");
        document.getElementById("nav-links").style.display = "block";
    } else {
        showPage("login-page");
        document.getElementById("nav-links").style.display = "none";
    }
});

function switchPage(pageName) {
    showPage(pageName);
    // clear error messages
    document.querySelectorAll(".error").forEach(el => el.style.display = "none");
}

function showPage(pageName) {
    document.querySelectorAll(".page").forEach(page => {
        page.classList.remove("active");
    });
    document.getElementById(pageName).classList.add("active");
}

async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value.trim();
    const errorDiv = document.getElementById("login-error");

    errorDiv.style.display = "none";

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem("current_user", username);
            currentUser = username;
            showPage("dashboard-page");
            document.getElementById("nav-links").style.display = "block";
            document.getElementById("login-username").value = "";
            document.getElementById("login-password").value = "";
        } else {
            errorDiv.textContent = data.error || "Login failed";
            errorDiv.style.display = "block";
        }
    } catch (error) {
        errorDiv.textContent = "Connection error: " + error.message;
        errorDiv.style.display = "block";
    }
}

async function handleSignup(event) {
    event.preventDefault();
    const username = document.getElementById("signup-username").value.trim();
    const password = document.getElementById("signup-password").value.trim();
    const errorDiv = document.getElementById("signup-error");

    errorDiv.style.display = "none";

    if (password.length < 6) {
        errorDiv.textContent = "Password must be at least 6 characters";
        errorDiv.style.display = "block";
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            alert("Signup successful! Please login.");
            switchPage("login-page");
            document.getElementById("signup-username").value = "";
            document.getElementById("signup-password").value = "";
        } else {
            errorDiv.textContent = data.error || "Signup failed";
            errorDiv.style.display = "block";
        }
    } catch (error) {
        errorDiv.textContent = "Connection error: " + error.message;
        errorDiv.style.display = "block";
    }
}

async function handlePredict(event) {
    event.preventDefault();
    const temperature = parseFloat(document.getElementById("temperature").value);
    const rainfall = parseFloat(document.getElementById("rainfall").value);
    const turbidity = parseFloat(document.getElementById("turbidity").value);
    const contamination = parseFloat(document.getElementById("contamination").value);
    const errorDiv = document.getElementById("predict-error");
    const resultDiv = document.getElementById("result");

    errorDiv.style.display = "none";
    resultDiv.style.display = "none";

    try {
        const response = await fetch(`${API_BASE}/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ temperature, rainfall, turbidity, contamination })
        });

        const data = response.json();

        const result = await data;

        if (response.ok) {
            const score = (result.prediction * 100).toFixed(1);
            let recommendation = "";
            if (result.risk_level === "HIGH") {
                recommendation = "⚠️ Do NOT drink. Boil water before use. Seek medical advice if symptoms develop.";
            } else if (result.risk_level === "MODERATE") {
                recommendation = "⚡ Caution advised. Use boiled water or water filters.";
            } else {
                recommendation = "✅ Safe to drink. Continue normal precautions.";
            }

            document.getElementById("result-score").textContent = score + "%";
            document.getElementById("result-level").textContent = result.risk_level;
            document.getElementById("result-recommendation").textContent = recommendation;
            resultDiv.style.display = "block";
        } else {
            errorDiv.textContent = result.error || "Prediction failed";
            errorDiv.style.display = "block";
        }
    } catch (error) {
        errorDiv.textContent = "Connection error: " + error.message;
        errorDiv.style.display = "block";
    }
}

function logout() {
    localStorage.removeItem("current_user");
    currentUser = null;
    document.getElementById("nav-links").style.display = "none";
    switchPage("login-page");
    document.getElementById("login-username").value = "";
    document.getElementById("login-password").value = "";
}
