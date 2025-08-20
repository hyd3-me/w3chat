import pytest
from app import utils

@pytest.mark.asyncio
async def test_ensure_channel(store):
    """Test channel creation with store.ensure_channel."""
    user_1_address = "0x1234567890abcdef1234567890abcdef12345678"
    user_2_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    channel_name = utils.generate_channel_name(user_1_address, user_2_address)
    
    # Clean up channel state
    success, msg = await store.delete_channel(channel_name)
    
    # Test case: Create channel with valid addresses
    success, msg = await store.ensure_channel(channel_name, [user_1_address, user_2_address])
    assert success, f"Failed to create channel: {msg}"
    assert channel_name in store.channels, f"Channel {channel_name} not in store.channels"
    assert user_1_address in store.channels[channel_name], f"User 1 not in channel {channel_name}"
    assert user_2_address in store.channels[channel_name], f"User 2 not in channel {channel_name}"

@pytest.mark.asyncio
async def test_ensure_channel_invalid_address(store):
    """Test channel creation with an invalid address."""
    user_1_address = "0x1234567890abcdef1234567890abcdef12345678"
    invalid_address = "0xInvalidAddress"
    channel_name = utils.generate_channel_name(user_1_address, invalid_address)
    
    success, msg = await store.ensure_channel(channel_name, [user_1_address, invalid_address])
    assert not success, "Should fail for invalid address"
    assert f"Invalid channel name: {channel_name}" in msg, f"Expected error message, got: {msg}"
    assert channel_name not in store.channels, f"Channel {channel_name} should not be created"