from app import utils

def test_generate_channel_name():
    """Test channel name generation from two addresses."""
    address_1 = "0xabcdef1234567890abcdef1234567890abcdef12"
    address_2 = "0x1234567890abcdef1234567890abcdef12345678"
    channel_name = utils.generate_channel_name(address_1, address_2)
    assert channel_name == f"{address_2}:{address_1}"  # address_2 < address_1 lexicographically
    # Test reverse order
    channel_name_reverse = utils.generate_channel_name(address_2, address_1)
    assert channel_name_reverse == channel_name

def test_generate_jwt():
    """Test JWT token generation and decoding."""
    # Valid address
    valid_address = "0x1234567890abcdef1234567890abcdef12345678"
    
    # Test case 1: Generate and decode valid token
    success, token = utils.generate_jwt(valid_address)
    assert success, f"Failed to generate token: {token}"
    assert isinstance(token, str), "Token should be a string"

def test_decode_jwt_valid():
    """Test JWT token decoding for a valid address."""
    valid_address = "0x1234567890abcdef1234567890abcdef12345678"
    success, token = utils.generate_jwt(valid_address)
    success, decoded_address = utils.decode_jwt(token)
    assert success, f"Failed to decode token: {decoded_address}"
    assert decoded_address == valid_address, f"Decoded address {decoded_address} does not match {valid_address}"