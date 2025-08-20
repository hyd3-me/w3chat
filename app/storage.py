from fastapi import WebSocket
from app import utils

class Storage:
    """Manages WebSocket connections, channels, and channel requests."""
    def __init__(self):
        self.connections = {}  # Store active WebSocket connections
        self.channels = {}  # Store channel subscriptions as a dictionary of lists
        self.channel_requests = {}  # Store channel requests as a dictionary
        self.logger = utils.get_logger(__name__)

    async def add_connection(self, address: str, websocket: WebSocket) -> None:
        """Add a WebSocket connection for the given address."""
        if address not in self.connections:
            self.connections[address] = []
        self.connections[address].append(websocket)
        self.logger.info("New WebSocket connection established")

    async def remove_connection(self, address: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection for the given address."""
        if address in self.connections:
            self.connections[address].remove(websocket)
            if not self.connections[address]:
                del self.connections[address]
        self.logger.info("WebSocket connection closed")

    async def add_channel(self, channel_name: str) -> None:
        """Add a new channel if it doesn't exist."""
        if channel_name not in self.channels:
            self.channels[channel_name] = []
        self.logger.debug("Channel added")

    async def subscribe_to_channel(self, channel_name: str, addresses: list[str]) -> tuple[bool, str]:
        """Subscribe a list of addresses to a channel."""
        for address in addresses:
            if not utils.is_valid_address(address):
                self.logger.warning(f"Invalid address for subscription: {address}")
                return False, f"Invalid address: {address}"
            if address not in self.channels[channel_name]:
                self.channels[channel_name].append(address)
                self.logger.debug(f"Subscribed address {address} to channel {channel_name}")
        return True, "Subscription successful"

    async def add_channel_request(self, channel_name: str, sender_address: str) -> None:
        """Store a channel request."""
        self.channel_requests[channel_name] = {"from": sender_address}
        self.logger.debug("Channel request created")

    async def notify_channel_creation(self, channel_name: str) -> None:
        """Notify all subscribers of a channel about its creation."""
        recipient_addresses = self.channels.get(channel_name, [])
        for address in recipient_addresses:
            recipient_connections = self.connections.get(address, [])
            for ws in recipient_connections:
                try:
                    await ws.send_json({"type": "info", "message": "Channel created", "channel": channel_name})
                except (WebSocketDisconnect, RuntimeError) as e:
                    self.logger.debug(f"Failed to notify {address} in channel {channel_name}: {str(e)}")
                    continue
        self.logger.debug(f"Notified subscribers of channel {channel_name} creation")

    async def delete_channel(self, channel_name: str) -> tuple[bool, str]:
        """Delete a channel if it exists."""
        try:
            if channel_name in self.channels:
                del self.channels[channel_name]
                return True, f"Channel {channel_name} deleted successfully"
            return True, f"Channel {channel_name} does not exist"
        except Exception as e:
            self.logger.error(f"Failed to delete channel {channel_name}: {str(e)}")
            return False, f"Failed to delete channel {channel_name}: {str(e)}"

    async def delete_channel_request(self, channel_name: str) -> tuple[bool, str]:
        """Delete a channel request if it exists."""
        try:
            if channel_name in self.channel_requests:
                del self.channel_requests[channel_name]
                return True, f"Channel request {channel_name} deleted successfully"
            return True, f"Channel request {channel_name} does not exist"
        except Exception as e:
            self.logger.error(f"Failed to delete channel request {channel_name}: {str(e)}")
            return False, f"Failed to delete channel request {channel_name}: {str(e)}"

    async def ensure_channel(self, channel_name: str, addresses: list[str]) -> tuple[bool, str]:
        """Ensure a channel exists, creating it and subscribing addresses if it doesn't."""
        try:
            if channel_name not in self.channels:
                self.channels[channel_name] = []
                self.logger.debug(f"Channel {channel_name} created")
            for address in addresses:
                if not utils.is_valid_address(address):
                    self.logger.warning(f"Invalid address for channel {channel_name}: {address}")
                    return False, f"Invalid address: {address}"
                if address not in self.channels[channel_name]:
                    self.channels[channel_name].append(address)
                    self.logger.debug(f"Subscribed address {address} to channel {channel_name}")
            return True, f"Channel {channel_name} ensured"
        except Exception as e:
            self.logger.error(f"Failed to ensure channel {channel_name}: {str(e)}")
            return False, f"Failed to ensure channel {channel_name}: {str(e)}"
    
    async def channel_exists(self, channel_name: str) -> bool:
        """Check if a channel exists.

        Args:
            channel_name: The name of the channel to check.

        Returns:
            bool: True if the channel exists, False otherwise.
        """
        return channel_name in self.channels