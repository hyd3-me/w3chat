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