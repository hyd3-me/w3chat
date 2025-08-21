const authDiv = document.getElementById("auth");
const placeholder = document.getElementById("placeholder");
const channelsList = document.getElementById("channels-list");
const chatContent = document.getElementById("chat-content");
const notifications = document.getElementById("notifications");
let isAuthenticated = false;
let userAddress = null;
let activeContent = "channels"; // Default to channels when authenticated
let selectedChannel = null; // No channel selected initially
let ws = null; // WebSocket connection

function truncateAddress(address) {
    return `${address.slice(0, 5)}...${address.slice(-4)}`;
}

function updateWalletUI() {
    if (isAuthenticated) {
        authDiv.innerHTML = `
            <span>Connected: ${truncateAddress(userAddress)}</span>
            <button id="disconnect-wallet">Disconnect Wallet</button>
        `;
    } else {
        authDiv.innerHTML = `<button id="connect-wallet">Connect Wallet</button>`;
    }
}

function updateContentUI() {
    if (!isAuthenticated) {
        placeholder.style.display = "block";
        channelsList.style.display = "none";
        chatContent.style.display = "none";
        notifications.style.display = "none";
    } else {
        placeholder.style.display = "none";
        channelsList.style.display = activeContent === "channels" ? "block" : "none";
        chatContent.style.display = activeContent === "chat" && selectedChannel ? "block" : "none";
        notifications.style.display = activeContent === "notifications" ? "block" : "none";
    }
}

function connectWebSocket(token) {
    console.log("Connecting to WebSocket...");
    ws = new WebSocket(`ws://${window.location.host}/ws/chat?token=${token}`);

    ws.onopen = () => {
        console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
        console.log("WebSocket message received:", event.data);
    };

    ws.onerror = (error) => {
        console.log("WebSocket error:", error);
    };

    ws.onclose = () => {
        console.log("WebSocket disconnected");
        ws = null;
    };
}

async function checkWalletConnection() {
    if (typeof window.ethereum === "undefined") {
        console.log("MetaMask is not installed. Please install it to continue.");
        return false;
    }
    console.log("MetaMask detected! Ready to connect.");
    return true;
}

async function connectWallet() {
    console.log("Connecting to wallet...");
    try {
        if (!await checkWalletConnection()) {
            throw new Error("MetaMask not installed");
        }

        // Request account access
        const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
        const address = accounts[0];
        console.log(`Connected: ${address}`);

        // Sign message
        const message = "Sign to authenticate with w3chat";
        const signature = await window.ethereum.request({
            method: "personal_sign",
            params: [message, address]
        });
        console.log("Signature obtained:", signature);

        // Verify with server
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ address, message, signature })
        });
        const data = await response.json();

        if (response.ok) {
            console.log("Authentication successful, JWT:", data.token);
            localStorage.setItem("jwt", data.token);
            isAuthenticated = true;
            userAddress = address;
            activeContent = "channels";
            selectedChannel = null; // No channel selected
            updateWalletUI();
            updateContentUI();
            connectWebSocket(data.token);
        } else {
            console.log("Authentication failed:", data.detail);
            throw new Error(data.detail);
        }
    } catch (error) {
        console.log("Error:", error.message);
    }
}

function disconnectWallet() {
    console.log("Disconnecting wallet...");
    if (ws) {
        ws.close();
        console.log("WebSocket closing...");
    }
    isAuthenticated = false;
    userAddress = null;
    activeContent = "channels";
    selectedChannel = null;
    localStorage.removeItem("jwt");
    updateWalletUI();
    updateContentUI();
}

document.addEventListener("DOMContentLoaded", () => {
    updateWalletUI();
    updateContentUI();
    authDiv.addEventListener("click", (e) => {
        if (e.target.id === "connect-wallet") {
            connectWallet();
        } else if (e.target.id === "disconnect-wallet") {
            disconnectWallet();
        }
    });
});