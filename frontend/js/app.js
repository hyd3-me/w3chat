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

document.addEventListener("DOMContentLoaded", () => {
    updateWalletUI();
    updateContentUI();
    authDiv.addEventListener("click", (e) => {
        if (e.target.id === "connect-wallet") {
            isAuthenticated = true;
            userAddress = "0x1234567890abcdef1234567890abcdef12345678"; // Mock address
            activeContent = "chat"; // Default to chat
            updateWalletUI();
            updateContentUI();
        } else if (e.target.id === "disconnect-wallet") {
            isAuthenticated = false;
            userAddress = null;
            activeContent = "chat"; // Reset to chat
            updateWalletUI();
            updateContentUI();
        }
    });
});