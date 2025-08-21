const authDiv = document.getElementById("auth");
const placeholder = document.getElementById("placeholder");
const chat = document.getElementById("chat");
const notifications = document.getElementById("notifications");
let isAuthenticated = false;
let userAddress = null;
let activeContent = "chat"; // Default to chat when authenticated

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
    placeholder.style.display = isAuthenticated ? "none" : "block";
    chat.style.display = isAuthenticated && activeContent === "chat" ? "block" : "none";
    notifications.style.display = isAuthenticated && activeContent === "notifications" ? "block" : "none";
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
            activeContent = "chat";
            updateWalletUI();
            updateContentUI();
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
    isAuthenticated = false;
    userAddress = null;
    activeContent = "chat";
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