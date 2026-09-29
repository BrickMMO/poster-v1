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

const FIREBASE_PATH = "k107"; // Path to k107 data in Realtime Database

// Define controls with their Firebase paths
const CONTROLS = {
    "fans-1": "fans-1",
    "lights-1": "lights-1",
    "room-1": "room-1"
};

/* ===========================
   APPLICATION STATE
   =========================== */

const state = {
    controls: {},
    isConnected: false,
    isLoading: true,
    database: null,
    listeners: {}
};

// Initialize control states
Object.keys(CONTROLS).forEach(key => {
    state.controls[key] = null;
    state.listeners[key] = null;
});

/* ===========================
   DOM ELEMENTS
   =========================== */

const elements = {
    buttons: {},
    connectionStatus: document.getElementById("connection-status")
};

// Build button element references dynamically
Object.keys(CONTROLS).forEach(key => {
    elements.buttons[key] = document.getElementById(`btn-${key.replace('_', '-')}`);
});

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
    Object.keys(CONTROLS).forEach(key => {
        const dbPath = CONTROLS[key];
        const ref = state.database.ref(`${FIREBASE_PATH}/${dbPath}`);
        
        state.listeners[key] = ref.on(
            "value",
            (snapshot) => {
                const value = snapshot.val();
                if (value !== null) {
                    state.controls[key] = value;
                    updateControlUI(key, value);
                }
                state.isLoading = false;
            },
            (error) => {
                console.error(`Error reading ${key}:`, error);
                showError(`Failed to read ${key} from Firebase`);
            }
        );
    });
}

/* ===========================
   UPDATE CONTROL UI
   =========================== */

function updateControlUI(controlKey, isActive) {
    const button = elements.buttons[controlKey];
    if (!button) return;

    // Update active/inactive state
    button.classList.remove("active", "inactive");
    button.classList.add(isActive ? "active" : "inactive");

    // Update accessibility
    button.setAttribute("aria-pressed", isActive);
}

/* ===========================
   TOGGLE CONTROL
   =========================== */

function toggleControl(controlKey) {
    if (state.isLoading || !state.isConnected) {
        return;
    }

    const currentValue = state.controls[controlKey];
    const newValue = !currentValue;

    // Optimistic UI update
    updateControlUI(controlKey, newValue);

    // Write to Firebase
    const dbPath = CONTROLS[controlKey];
    state.database
        .ref(`${FIREBASE_PATH}/${dbPath}`)
        .set(newValue)
        .then(() => {
            console.log(`${controlKey} toggled to ${newValue}`);
        })
        .catch((error) => {
            console.error(`Error toggling ${controlKey}:`, error);
            // Revert UI on error
            updateControlUI(controlKey, currentValue);
            showError(`Failed to toggle ${controlKey}`);
        });
}

/* ===========================
   EVENT LISTENERS
   =========================== */

function setupEventListeners() {
    Object.keys(CONTROLS).forEach(key => {
        const button = elements.buttons[key];
        if (!button) return;

        button.addEventListener("click", () => toggleControl(key));

        // Keyboard accessibility
        button.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                toggleControl(key);
            }
        });
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
        Object.keys(CONTROLS).forEach(key => {
            if (state.listeners[key]) {
                const dbPath = CONTROLS[key];
                state.database.ref(`${FIREBASE_PATH}/${dbPath}`).off("value", state.listeners[key]);
            }
        });
    }
});
