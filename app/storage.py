from fastapi import WebSocket
from app import utils
from app.routers.websocket import channels

async def ensure_channel(channel_name: str, websockets: list[WebSocket]) -> tuple[bool, str]:
    """Ensure a channel exists, creating it and subscribing websockets if it doesn't.

    Args:
        channel_name: The name of the channel to ensure.
        websockets: List of WebSocket connections to subscribe to the channel.

    Returns:
        Tuple[bool, str]: (success, message) where success is True if the channel exists or was created,
                          and False if an error occurred.
    """
    logger = utils.get_logger(__name__)
    try:
        if channel_name not in channels:
            channels[channel_name] = []
            logger.debug(f"Channel {channel_name} created")
        for ws in websockets:
            if ws not in channels[channel_name]:
                channels[channel_name].append(ws)
                logger.debug(f"Subscribed websocket to channel {channel_name}")
        return True, f"Channel {channel_name} ensured"
    except Exception as e:
        logger.error(f"Failed to ensure channel {channel_name}: {str(e)}")
        return False, f"Failed to ensure channel {channel_name}: {str(e)}"