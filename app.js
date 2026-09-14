/* ===========================
   FIREBASE CONFIGURATION
   ===========================
   Replace these values with your Firebase project credentials.
   You can find these in Firebase Console > Project Settings > Your App
*/

const firebaseConfig = {
    apiKey: "AIzaSyAT00cUhl_nAqMAwGJDrtti_rl8opyXZV8",
    authDomain: "brickmmoposter.firebaseapp.com",
    databaseURL: "https://brickmmoposter-default-rtdb.firebaseio.com",
    projectId: "brickmmoposter",
    storageBucket: "brickmmoposter.firebasestorage.app",
    messagingSenderId: "836270662076",
    appId: "1:836270662076:web:861e5edd84e39dabd50bb9"
};

const FIREBASE_PATH = "poster-1"; // Path to your poster data in Realtime Database

/* ===========================
   APPLICATION STATE
   =========================== */

const state = {
    fans: null,
    lights: null,
    isConnected: false,
    isLoading: true,
    database: null,
    listeners: {
        fans: null,
        lights: null
    }
};

/* ===========================
   DOM ELEMENTS
   =========================== */

const elements = {
    fansCard: document.getElementById("fans-card"),
    lightsCard: document.getElementById("lights-card"),
    fansStatus: document.getElementById("fans-status"),
    lightsStatus: document.getElementById("lights-status"),
    fansButton: document.getElementById("fans-button"),
    lightsButton: document.getElementById("lights-button"),
    connectionStatus: document.getElementById("connection-status")
};

/* ===========================
   INITIALIZATION
   =========================== */

document.addEventListener("DOMContentLoaded", () => {
    initializeFirebase();
    setupEventListeners();
});

/* ===========================
   FIREBASE INITIALIZATION
   =========================== */

function initializeFirebase() {
    try {
        // Initialize Firebase
        const app = firebase.initializeApp(firebaseConfig);
        state.database = firebase.database(app);

        // Test connection and load initial data
        setupRealtimeListeners();
        setConnectionStatus(true);
    } catch (error) {
        console.error("Firebase initialization error:", error);
        setConnectionStatus(false);
        showError("Failed to connect to Firebase");
    }
}

/* ===========================
   REAL-TIME LISTENERS
   =========================== */

function setupRealtimeListeners() {
    // Listen for fans changes
    const fansRef = state.database.ref(`${FIREBASE_PATH}/fans`);
    state.listeners.fans = fansRef.on(
        "value",
        (snapshot) => {
            const value = snapshot.val();
            if (value !== null) {
                state.fans = value;
                updateControlUI("fans", value);
            }
            state.isLoading = false;
        },
        (error) => {
            console.error("Error reading fans:", error);
            showError("Failed to read fans from Firebase");
        }
    );

    // Listen for lights changes
    const lightsRef = state.database.ref(`${FIREBASE_PATH}/lights`);
    state.listeners.lights = lightsRef.on(
        "value",
        (snapshot) => {
            const value = snapshot.val();
            if (value !== null) {
                state.lights = value;
                updateControlUI("lights", value);
            }
            state.isLoading = false;
        },
        (error) => {
            console.error("Error reading lights:", error);
            showError("Failed to read lights from Firebase");
        }
    );
}

/* ===========================
   UPDATE CONTROL UI
   =========================== */

function updateControlUI(control, isActive) {
    const card = control === "fans" ? elements.fansCard : elements.lightsCard;
    const statusElement = control === "fans" ? elements.fansStatus : elements.lightsStatus;

    // Remove loading class
    card.classList.remove("loading");

    // Update active/inactive state
    card.classList.remove("active", "inactive");
    card.classList.add(isActive ? "active" : "inactive");

    // Update status text
    const statusText = isActive ? "ON" : "OFF";
    statusElement.innerHTML = `<span class="status-text">${statusText}</span>`;

    // Update accessibility
    const button = control === "fans" ? elements.fansButton : elements.lightsButton;
    button.setAttribute("aria-pressed", isActive);
}

/* ===========================
   TOGGLE CONTROL
   =========================== */

function toggleControl(control) {
    if (state.isLoading || !state.isConnected) {
        return;
    }

    const currentValue = control === "fans" ? state.fans : state.lights;
    const newValue = !currentValue;

    // Optimistic UI update
    updateControlUI(control, newValue);

    // Write to Firebase
    state.database
        .ref(`${FIREBASE_PATH}/${control}`)
        .set(newValue)
        .then(() => {
            console.log(`${control} toggled to ${newValue}`);
        })
        .catch((error) => {
            console.error(`Error toggling ${control}:`, error);
            // Revert UI on error
            updateControlUI(control, currentValue);
            showError(`Failed to toggle ${control}`);
        });
}

/* ===========================
   EVENT LISTENERS
   =========================== */

function setupEventListeners() {
    elements.fansButton.addEventListener("click", () => toggleControl("fans"));
    elements.lightsButton.addEventListener("click", () => toggleControl("lights"));

    // Keyboard accessibility
    elements.fansButton.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            toggleControl("fans");
        }
    });

    elements.lightsButton.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            toggleControl("lights");
        }
    });
}

/* ===========================
   CONNECTION STATUS
   =========================== */

function setConnectionStatus(isConnected) {
    state.isConnected = isConnected;
    const statusElement = elements.connectionStatus;
    const statusLabel = statusElement.querySelector(".status-label");

    statusElement.classList.remove("connected", "disconnected");

    if (isConnected) {
        statusElement.classList.add("connected");
        statusLabel.textContent = "Connected to Firebase";
    } else {
        statusElement.classList.add("disconnected");
        statusLabel.textContent = "Disconnected from Firebase";
    }
}

/* ===========================
   ERROR HANDLING
   =========================== */

function showError(message) {
    console.error(message);
    // You can extend this to show error notifications in the UI
    // For now, we just log to console
}

/* ===========================
   CLEANUP (optional)
   =========================== */

window.addEventListener("beforeunload", () => {
    if (state.database) {
        if (state.listeners.fans) {
            state.database.ref(`${FIREBASE_PATH}/fans`).off("value", state.listeners.fans);
        }
        if (state.listeners.lights) {
            state.database.ref(`${FIREBASE_PATH}/lights`).off("value", state.listeners.lights);
        }
    }
});
