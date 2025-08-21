const authDiv = document.getElementById("auth");
const placeholder = document.getElementById("placeholder");
const channelsList = document.getElementById("channels-list");
const chatContent = document.getElementById("chat-content");
const notifications = document.getElementById("notifications");
const requestChannelBtn = document.getElementById("request-channel-btn");
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
        handleWebSocket(event);
    };

    ws.onerror = (error) => {
        console.log("WebSocket error:", error);
    };

    ws.onclose = () => {
        console.log("WebSocket disconnected");
        ws = null;
    };
}

function handleWebSocket(event) {
    console.log("WebSocket message received:", event.data);
}

function channelRequest() {
    const recipientAddress = document.getElementById("recipient-address").value;
    if (!recipientAddress || !recipientAddress.match(/^0x[a-fA-F0-9]{40}$/)) {
        console.log("Invalid recipient address");
        return;
    }
    if (recipientAddress.toLowerCase() === userAddress.toLowerCase()) {
        console.log("Cannot create channel with self");
        return;
    }
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.log("WebSocket not connected");
        return;
    }
    console.log("Sending channel request for:", recipientAddress);
    ws.send(JSON.stringify({
        type: "channel_request",
        to: recipientAddress
    }));
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
            localStorage.setItem("w3chat_user", JSON.stringify({ jwt: data.token, address: address }));
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
    localStorage.removeItem("w3chat_user");
    updateWalletUI();
    updateContentUI();
}

async function checkExistingConnection() {
    if (!await checkWalletConnection()) {
        return;
    }
    try {
        const accounts = await window.ethereum.request({ method: "eth_accounts" });
        if (accounts.length === 0) {
            console.log("No connected accounts found");
            localStorage.removeItem("w3chat_user");
            return;
        }
        const userData = localStorage.getItem("w3chat_user");
        if (!userData) {
            console.log("No user data in localStorage");
            return;
        }
        const w3chat_user = JSON.parse(userData);
        if (accounts[0].toLowerCase() !== w3chat_user.address.toLowerCase()) {
            console.log("Connected account does not match stored address");
            localStorage.removeItem("w3chat_user");
            return;
        }
        // Try to connect WebSocket
        connectWebSocket(w3chat_user.jwt);
        isAuthenticated = true;
        userAddress = w3chat_user.address;
        activeContent = "channels";
        selectedChannel = null;
    } catch (error) {
        console.log("Error checking existing connection:", error.message);
        localStorage.removeItem("w3chat_user");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    checkExistingConnection().then(() => {
        console.log("Existing connection checked");
        updateWalletUI();
        updateContentUI();
    });
    authDiv.addEventListener("click", (e) => {
        if (e.target.id === "connect-wallet") {
            connectWallet();
        } else if (e.target.id === "disconnect-wallet") {
            disconnectWallet();
        }
    });
    requestChannelBtn.addEventListener("click", channelRequest);
});