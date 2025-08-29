const authDiv = document.getElementById("auth");
const navMenu = document.getElementById("nav-menu");
const placeholder = document.getElementById("placeholder");
const channelsList = document.getElementById("channels-list");
const chatContent = document.getElementById("chat-content");
const notifications = document.getElementById("notifications");
const hiddenContainer = document.getElementById("hidden-messages-container");
const standardHeader = document.getElementById("standard-header");
const chatHeader = document.getElementById("chat-header");
let isAuthenticated = false;
let userAddress = null;
let activeContent = "channels"; // Default to channels when authenticated
let selectedChannel = null; // No channel selected initially
let ws = null; // WebSocket connection

// Generate color based on address hash
const colors = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEEAD",
    "#D4A5A5", "#9B59B6", "#3498DB", "#E74C3C", "#2ECC71"
];

function truncateAddress(address) {
    return `${address.slice(0, 5)}...${address.slice(-4)}`;
}

function updateWalletUI() {
    const notifications = JSON.parse(sessionStorage.getItem("w3chat_notifications") || "{}");
    const rejectNotifications = JSON.parse(sessionStorage.getItem("w3chat_reject_notifications") || "{}");
    const newMessages = JSON.parse(sessionStorage.getItem("w3chat_new_messages") || "{}");
    const hasNotifications = Object.keys(notifications).length > 0 || Object.keys(rejectNotifications).length > 0 ? " has-notifications" : "";
    const hasNewMessages = Object.keys(newMessages).length > 0 ? " has-new-messages" : "";
    console.log(`${hasNotifications}`);
    if (isAuthenticated) {
        if (activeContent === "chat" && selectedChannel) {
            // hide logo + profile
            console.log("In chat view, hiding nav menu");
        } else {
            // hide user-info
            navMenu.innerHTML = `
            <button id="nav-channels" class="icon-button${hasNewMessages}">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    <path d="M12 8a2 2 0 0 1-2 2H5l-4 4V9a2 2 0 0 1 2-2h7z"></path>
                </svg>
            </button>
            <button id="nav-notifications" class="icon-button${hasNotifications}">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
            </button>
        `;
            authDiv.innerHTML = `
            <button id="profile">${truncateAddress(userAddress)}</button>
            <div class="dropdown">
                <button id="toggle-theme">theme</button>
                <button id="disconnect-wallet">logout</button>
            </div>
        `;
            const toggleThemeButton = document.getElementById("toggle-theme");
            const currentTheme = localStorage.getItem("theme") || "light";
            document.body.setAttribute("data-theme", currentTheme);
            toggleThemeButton.addEventListener("click", () => {
                const newTheme = document.body.getAttribute("data-theme") === "light" ? "dark" : "light";
                document.body.setAttribute("data-theme", newTheme);
                localStorage.setItem("theme", newTheme);
            });
        }
    } else {
        navMenu.innerHTML = "";
        authDiv.innerHTML = `<button id="connect-wallet">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="20" height="20">
            <path d="M21 4H3a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z"></path>
            <path d="M21 14h-3a2 2 0 0 1 0-4h3"></path>
            <circle cx="16" cy="12" r="1"></circle>
        </svg>
        Connect Wallet
    </button>`;
    }
}

function updateContentUI() {
    if (!isAuthenticated) {
        standardHeader.classList.remove("hidden");
        chatHeader.classList.add("hidden");
        placeholder.classList.remove("hidden");
        channelsList.classList.add("hidden");
        chatContent.classList.add("hidden");
        notifications.classList.add("hidden");
    } else {
        standardHeader.classList.toggle("hidden", activeContent === "chat" && selectedChannel);
        chatHeader.classList.toggle("hidden", !(activeContent === "chat" && selectedChannel));
        placeholder.classList.add("hidden");
        channelsList.classList.toggle("hidden", activeContent !== "channels");
        chatContent.classList.toggle("hidden", activeContent !== "chat" || !selectedChannel);
        notifications.classList.toggle("hidden", activeContent !== "notifications");
        if (activeContent === "chat" && selectedChannel) {
            const messageInput = document.getElementById("message-input");
            if (messageInput) {
                messageInput.focus();
            }
        }
    }
}

function connectWebSocket(token) {
    return new Promise((resolve, reject) => {
        console.log("Connecting to WebSocket...");
        ws = new WebSocket(`ws://${window.location.host}/ws/chat?token=${token}`);

        const timeout = setTimeout(() => {
            console.log("WebSocket connection timed out after 3 seconds");
            ws.close(); // Force close WebSocket
            reject(new Error("WebSocket connection timed out"));
        }, 3000);

        ws.onopen = () => {
            console.log("WebSocket connected");
            clearTimeout(timeout); // Clear timeout on success
            resolve();
        };

        ws.onmessage = (event) => {
            handleWebSocket(event);
        };

        ws.onerror = (error) => {
            console.log("WebSocket error:", error);
            clearTimeout(timeout); // Clear timeout on error
            reject(new Error("Failed to connect WebSocket"));
        };

        ws.onclose = () => {
            console.log("WebSocket disconnected");
            ws = null;
            clearTimeout(timeout); // Clear timeout on close
            reject(new Error("WebSocket closed"));
        };
    });
}

function handleWebSocket(event) {
    console.log("WebSocket message received:", event.data);
    try {
        const data = JSON.parse(event.data);
        console.log("Parsed WebSocket message:", data);
        switch (data.type) {
            case "ack":
                handleAck(data);
                break;
            case "channel_request":
                handleChannelRequest(data);
                break;
            case "info":
                handleInfo(data);
                break;
            case "message":
                handleMessage(data);
                break;
            case "error":
                handleError(data);
                break;
            default:
                console.log("Unknown message type:", data.type);
        }
    } catch (error) {
        console.log("Failed to parse WebSocket message:", error.message);
    }
}

function handleAck(data) {
    console.log("Command acknowledged by server");
}

function createChannelRequestItem(data) {
    const requestItem = document.createElement("li");
    requestItem.className = "channel-request";
    requestItem.dataset.channelId = data.channel;
    requestItem.innerHTML = `
        <div class="request-text"><p>Channel request from ${data.from}</p></div>
        <div class="request-actions">
            <button class="reject">Reject</button>
            <button class="approve">Approve</button>
        </div>
    `;
    requestItem.title = `Channel request from ${data.from}`;
    return requestItem;
}

function createRejectNotificationItem(data, notificationId) {
    const notificationItem = document.createElement("li");
    notificationItem.className = "notification has-new-notifications";
    notificationItem.dataset.notificationId = notificationId;
    const pItem = document.createElement("p");
    pItem.textContent = data.message;
    notificationItem.appendChild(pItem);
    notificationItem.title = data.message;
    // Remove on click
    notificationItem.addEventListener("click", () => {
        notificationItem.remove();
        removeRejectNotification(notificationId);
    });
    return notificationItem;
}

function removeRejectNotification(notificationId) {
    const rejectNotifications = JSON.parse(sessionStorage.getItem("w3chat_reject_notifications") || "{}");
    delete rejectNotifications[notificationId];
    sessionStorage.setItem("w3chat_reject_notifications", JSON.stringify(rejectNotifications));
    console.log(`Removed reject notification ${notificationId} from sessionStorage`);
    updateWalletUI();
}

function attachChannelActionListener(requestItem, channel) {
    requestItem.addEventListener("click", (event) => {
        const buttonClass = event.target.className;
        if (buttonClass === "approve" || buttonClass === "reject") {
            const message = {
                type: buttonClass === "approve" ? "channel_approve" : "channel_reject",
                channel: channel
            };
            sendChannelAction(message, channel, requestItem);
        }
    });
}

function sendChannelAction(message, channel, requestItem) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.log("WebSocket not connected");
        return;
    }
    ws.send(JSON.stringify(message));
    console.log(`Sent ${message.type} for channel ${channel}`);
    requestItem.remove(); // Remove notification after action
    // Remove notification from sessionStorage
    const notifications = JSON.parse(sessionStorage.getItem("w3chat_notifications") || "{}");
    delete notifications[channel];
    sessionStorage.setItem("w3chat_notifications", JSON.stringify(notifications));
    console.log(`Removed notification for channel ${channel} from sessionStorage`);
    updateWalletUI(); // Update UI to reflect notification status
}

function handleChannelRequest(data) {
    console.log(`Channel request from ${data.from} for channel ${data.channel}`);
    const notificationsList = document.getElementById("notifications-list");
    if (!notificationsList) {
        console.log("Notifications list not found");
        return;
    }
    // Save notification to sessionStorage
    const notifications = JSON.parse(sessionStorage.getItem("w3chat_notifications") || "{}");
    notifications[data.channel] = data;
    sessionStorage.setItem("w3chat_notifications", JSON.stringify(notifications));
    console.log(`Saved notification for channel ${data.channel} to sessionStorage`);
    // Add notification to UI
    const requestItem = createChannelRequestItem(data);
    notificationsList.appendChild(requestItem);
    attachChannelActionListener(requestItem, data.channel);
    updateWalletUI(); // Update UI to show notification indicator
}

function restoreNotifications() {
    const notificationsList = document.getElementById("notifications-list");
    if (!notificationsList) {
        console.log("Notifications list not found");
        return;
    }
    const notifications = JSON.parse(sessionStorage.getItem("w3chat_notifications") || "{}");
    Object.values(notifications).forEach(data => {
        const requestItem = createChannelRequestItem(data);
        notificationsList.appendChild(requestItem);
        attachChannelActionListener(requestItem, data.channel);
    });
    console.log(`Restored ${Object.keys(notifications).length} notifications from sessionStorage`);
    // Restore reject notifications
    const rejectNotifications = JSON.parse(sessionStorage.getItem("w3chat_reject_notifications") || "{}");
    Object.entries(rejectNotifications).forEach(([notificationId, data]) => {
        const notificationItem = createRejectNotificationItem(data, notificationId);
        notificationsList.appendChild(notificationItem);
    });
    console.log(`Restored ${Object.keys(rejectNotifications).length} reject notifications from sessionStorage`);
}

function hide_channel_messages() {
    if (selectedChannel) {
        const prevMessages = document.getElementById(`channel-messages-${selectedChannel}`);
        if (prevMessages && hiddenContainer) {
            hiddenContainer.appendChild(prevMessages);
            console.log(`Moved channel-messages-${selectedChannel} to hidden container`);
        }
    } else {
        console.log("No previously selected channel to hide messages for");
    }
}

function handleInfo(data) {
    console.log("Info message:", data.message);
    if (data.message === "Channel created" && data.channel) {
        const channelsList = document.getElementById("channels");
        if (!channelsList || !hiddenContainer) {
            console.log("Channels list, hidden container not found");
            return;
        }
        // Check if channel already exists
        if (channelsList.querySelector(`li[data-channel-id="${data.channel}"]`)) {
            console.log(`Channel ${data.channel} already exists, skipping addition`);
            return;
        }
        // Remove "No channels available" if present
        if (channelsList.querySelector("li").textContent === "No channels available") {
            channelsList.innerHTML = "";
        }
        // Add new channel
        const channelItem = document.createElement("li");
        channelItem.className = `channel`;
        channelItem.dataset.channelId = data.channel;
        // Parse channel ID to extract other participant's address
        const [addr1, addr2] = data.channel.split(":");
        const otherAddress = addr1.toLowerCase() === userAddress.toLowerCase() ? addr2 : addr1;
        channelItem.textContent = truncateAddress(otherAddress);
        channelItem.title = otherAddress; // Full address in tooltip
        channelItem.addEventListener("click", () => {
            activeContent = "chat";
            // Hide previous channel messages
            if (data.channel !== selectedChannel) {
                hide_channel_messages();
                // Set new selected channel
                selectedChannel = data.channel;
                // Move new channel messages to chat-messages
                const elem_username = document.getElementById("user-info-username");
                elem_username.textContent = truncateAddress(otherAddress);
                elem_username.title = otherAddress; // Full address in tooltip
                const elem_avatar = document.getElementById("user-info-avatar");
                const hash = otherAddress.toLowerCase().split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
                const color = colors[hash % colors.length];
                const initials = otherAddress.slice(-2).toUpperCase();
                elem_avatar.innerHTML = `
    <circle cx="16" cy="16" r="16" fill="${color}"/>
    <text x="16" y="16" font-size="12" fill="var(--text)" text-anchor="middle" dominant-baseline="middle">${initials}</text>
`;
                const messagesDiv = document.getElementById(`channel-messages-${data.channel}`);
                const chatMessages = document.getElementById("chat-messages");
                if (messagesDiv && chatMessages) {
                    chatMessages.appendChild(messagesDiv);
                    console.log(`Moved channel-messages-${data.channel} to chat-messages`);
                }
            }
            // Clear new messages for this channel
            const newMessages = JSON.parse(sessionStorage.getItem("w3chat_new_messages") || "{}");
            delete newMessages[data.channel];
            sessionStorage.setItem("w3chat_new_messages", JSON.stringify(newMessages));
            console.log(`Cleared new messages for channel ${data.channel} from sessionStorage`);
            // Remove has-new-messages class from the selected channel
            const channelItem = channelsList.querySelector(`li[data-channel-id="${data.channel}"]`);
            if (channelItem) {
                channelItem.classList.remove("has-new-messages");
            }
            updateWalletUI();
            updateContentUI();
        });
        channelsList.appendChild(channelItem);
        // Create channel-specific messages container
        const messagesDiv = document.createElement("div");
        messagesDiv.id = `channel-messages-${data.channel}`;
        hiddenContainer.appendChild(messagesDiv);
    } else if (data.message.startsWith("Channel request rejected by")) {
        console.log("Channel request rejected:", data.message);
        const notificationsList = document.getElementById("notifications-list");
        if (!notificationsList) {
            console.log("Notifications list not found");
            return;
        }
        const notificationId = crypto.randomUUID();
        const notificationItem = createRejectNotificationItem({ message: data.message }, notificationId);
        const rejectNotifications = JSON.parse(sessionStorage.getItem("w3chat_reject_notifications") || "{}");
        rejectNotifications[notificationId] = { message: data.message };
        sessionStorage.setItem("w3chat_reject_notifications", JSON.stringify(rejectNotifications));
        console.log(`Saved reject notification ${notificationId} to sessionStorage`);
        notificationsList.appendChild(notificationItem);
        updateWalletUI();
    }
}

function scrollChatToBottom() {
    const chatMessages = document.getElementById("chat-messages");
    if (chatMessages) {
        chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: "smooth" });
    }
}

function handleMessage(data) {
    console.log(`Message in channel ${data.channel} from ${data.from}: ${data.data}`);
    const messagesDiv = document.getElementById(`channel-messages-${data.channel}`);
    if (!messagesDiv) {
        console.log(`Messages container for channel ${data.channel} not found`);
        return;
    }
    const messageDiv = document.createElement("div");
    messageDiv.className = `message${data.from.toLowerCase() === userAddress.toLowerCase() ? " own-message" : ""}`;
    messageDiv.textContent = `${data.data}`;
    messagesDiv.appendChild(messageDiv);
    scrollChatToBottom();
    // Save new message if not in the active channel
    if (data.channel !== selectedChannel || activeContent !== "chat") {
        const newMessages = JSON.parse(sessionStorage.getItem("w3chat_new_messages") || "{}");
        newMessages[data.channel] = newMessages[data.channel] || [];
        newMessages[data.channel].push({ from: data.from, data: data.data });
        sessionStorage.setItem("w3chat_new_messages", JSON.stringify(newMessages));
        console.log(`Saved new message for channel ${data.channel} in sessionStorage`);
        // Add has-new-messages class to the channel in the list
        const channelsList = document.getElementById("channels");
        if (channelsList) {
            const channelItem = channelsList.querySelector(`li[data-channel-id="${data.channel}"]`);
            if (channelItem) {
                channelItem.classList.add("has-new-messages");
            }
        }
        updateWalletUI();
    }
}

function handleError(data) {
    console.log("Error from server:", data.message);
}

function channelRequest() {
    const recipientAddressElement = document.getElementById("recipient-address");
    const recipientAddress = recipientAddressElement.value.trim().toLowerCase();
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
    recipientAddressElement.value = ""; // Clear input after sending request
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
        const timestamp = new Date().toISOString();
        const nonce = crypto.randomUUID();
        const message = `Sign this message to authenticate with w3chat: ${nonce} at ${timestamp}`;
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
    sessionStorage.removeItem("w3chat_reject_notifications");
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
        await connectWebSocket(w3chat_user.jwt);
        isAuthenticated = true;
        userAddress = w3chat_user.address;
        activeContent = "channels";
        selectedChannel = null;
    } catch (error) {
        console.log("Error checking existing connection:", error.message);
        localStorage.removeItem("w3chat_user");
        ws = null;
        return;
    }
}

function sendMessage() {
    if (!isAuthenticated) {
        console.log("User not authenticated");
        return;
    }
    const messageInput = document.getElementById("message-input");
    if (!messageInput) {
        console.log("Message input not found");
        return;
    }
    const message = messageInput.value;
    if (!message) {
        console.log("Cannot send empty message");
        return;
    }
    if (message.trim().length > 12000) {
        console.log("Message too long (max 12000 characters)");
        return;
    }
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.log("WebSocket not connected");
        return;
    }
    if (!selectedChannel) {
        console.log("No channel selected");
        return;
    }
    const messageData = {
        type: "channel",
        channel: selectedChannel,
        data: message
    };
    ws.send(JSON.stringify(messageData));
    console.log(`Sent message to channel ${selectedChannel}: ${message}`);
    messageInput.value = ""; // Clear input
}

document.addEventListener("DOMContentLoaded", () => {
    checkExistingConnection().then(() => {
        console.log("Existing connection checked");
        updateWalletUI();
        updateContentUI();
    });
    // Update UI on window resize to handle address truncation
    window.addEventListener("resize", () => {
        if (activeContent === "chat" && selectedChannel) {
            const [addr1, addr2] = selectedChannel.split(":");
            const otherAddress = addr1.toLowerCase() === userAddress.toLowerCase() ? addr2 : addr1;
            const elem_username = document.getElementById("user-info-username");
            elem_username.textContent = truncateAddress(otherAddress);
        }
        updateWalletUI();
        updateContentUI();
    });
    const header = document.querySelector("header");
    header.addEventListener("click", (e) => {
        if (e.target.id === "connect-wallet") {
            connectWallet();
        } else if (e.target.id === "disconnect-wallet") {
            disconnectWallet();
        } else if (e.target.id === "nav-channels") {
            if (activeContent !== "channels") {
                activeContent = "channels";
                updateContentUI();
                console.log("Switched to Channels");
            }
        } else if (e.target.id === "nav-notifications") {
            if (activeContent !== "notifications") {
                activeContent = "notifications";
                updateContentUI();
                console.log("Switched to Notifications");
            }
        } else if (e.target.id === "back-to-channels") {
            if (activeContent !== "channels") {
                activeContent = "channels";
                updateContentUI();
                console.log("Switched to Channels from chat");
            }
        }
    });
    const requestChannelBtn = document.getElementById("request-channel-btn");
    requestChannelBtn.addEventListener("click", channelRequest);
    const chatForm = document.getElementById("chat-form");
    const messageInput = document.getElementById("message-input");
    if (chatForm && messageInput) {
        chatForm.addEventListener("submit", (e) => {
            e.preventDefault(); // Prevent form submission from reloading page
            sendMessage();
        });
        messageInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault(); // Prevent newline
                sendMessage();
            }
        });
    }
});