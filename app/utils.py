# app/utils.py
import os
import json
import re
import logging
import logging.config
import logging.handlers
import uuid
from web3 import Web3
from eth_account.messages import encode_defunct
from jose import jwt, JWTError
from datetime import datetime, timedelta
from pydantic import BaseModel

# Constants
W3 = Web3()
TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"
SECRET_KEY = None  # Initialize to None, set below
LOGGER_PREFIX = "w3chat"

# Pydantic model for authentication request
class AuthRequest(BaseModel):
    address: str
    message: str
    signature: str

def set_environment_variable(name: str, value: str) -> None:
    """Set an environment variable."""
    os.environ[name] = value

def join_paths(*paths: str) -> str:
    """Join multiple paths into a single path."""
    return os.path.join(*paths)

def remove_path(path: str) -> None:
    """Remove a file or directory."""
    if os.path.exists(path):
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)

def get_source_path() -> str:
    """Return the absolute path to the project root (w3chat/source)."""
    return os.path.abspath(join_paths(os.path.dirname(__file__), '..'))

def get_data_path() -> str:
    """Return the absolute path to the data directory (w3chat/data)."""
    return os.path.abspath(join_paths(get_source_path(), '..', 'data'))

def path_exists(path: str) -> bool:
    """Check if a given path exists."""
    return os.path.exists(path)

def get_secret_data() -> dict:
    """Read secret data from w3chat/data/SECRET_DATA.json."""
    secret_file = join_paths(get_data_path(), 'SECRET_DATA.json')
    try:
        if not os.path.exists(secret_file):
            raise FileNotFoundError(f"Secret data file not found at {secret_file}")
        with open(secret_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load secret data: {str(e)}")

def get_secret_key() -> str:
    """Get SECRET_KEY from secret data, with a fallback."""
    secret_data = get_secret_data()
    secret_key = secret_data.get('SECRET_KEY')
    if not secret_key:
        raise ValueError("SECRET_KEY not found in secret data")
    return secret_key

# Initialize SECRET_KEY at module load
SECRET_KEY = get_secret_key()

def verify_signature(auth: AuthRequest) -> tuple[bool, str]:
    """Verify the signature in AuthRequest, return (success, message)."""
    try:
        w3 = Web3()
        message_hash = encode_defunct(text=auth.message)
        recovered_address = W3.eth.account.recover_message(
            message_hash, signature=auth.signature
        )
        if recovered_address.lower() != auth.address.lower():
            return False, "Invalid signature"
        return True, "Signature is valid"
    except Exception as e:
        return False, f"Signature verification failed: {str(e)}"

def generate_jwt(address: str) -> tuple[bool, str]:
    """Generate JWT for the given address, return (success, token or message)."""
    try:
        if not is_valid_address(address):
            return False, "Invalid Ethereum address"
        payload = {
            "sub": address,
            "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return True, token
    except Exception as e:
        return False, f"JWT generation failed: {str(e)}"

def decode_jwt(token: str) -> tuple[bool, str]:
    """Decode JWT and return (success, address or message)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        address = payload.get("sub")
        if address is None:
            return False, "Invalid token: missing 'sub' field"
        return True, address
    except JWTError as e:
        return False, f"JWT verification failed: {str(e)}"

def get_logger(name: str) -> logging.Logger:
    """Return a logger with name prefixed by 'w3chat'."""
    return logging.getLogger(f"{'.'.join([LOGGER_PREFIX, name]) if name else LOGGER_PREFIX}")

def setup_logging() -> None:
    from .config import config_map
    """Setup logging based on the specified mode."""
    mode = os.getenv('MODE', 'development')
    config_class = config_map.get(mode, config_map['default'])
    config = config_class()

    # Ensure log directory exists
    if config.LOG_TO_FILE:
        log_dir = os.path.dirname(config.LOG_FILE)
        if not os.path.exists(log_dir):
            if not os.access(os.path.dirname(log_dir), os.W_OK):
                raise PermissionError(f"No write permissions for directory {os.path.dirname(log_dir)}")
            os.makedirs(log_dir)

    # Configure logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': config.LOG_FORMAT,
                'datefmt': config.LOG_DATEFMT
            }
        },
        'handlers': {},
        'root': {
            'level': config.LOG_LEVEL,
            'handlers': []
        }
    }

    # Add console handler if enabled
    if getattr(config, 'LOG_TO_CONSOLE', False):
        logging_config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'level': config.LOG_LEVEL,
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        }
        logging_config['root']['handlers'].append('console')

    # Add file handler if enabled
    if config.LOG_TO_FILE:
        logging_config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': config.LOG_LEVEL,
            'formatter': 'default',
            'filename': config.LOG_FILE,
            'maxBytes': config.LOG_MAX_BYTES,
            'backupCount': config.LOG_BACKUP_COUNT
        }
        logging_config['root']['handlers'].append('file')

    logging.config.dictConfig(logging_config)

def trigger_test_error():
    """Log a test error message with a unique string and return it."""
    logger = get_logger(__name__)
    unique_message = f"Test error {uuid.uuid4()}"
    logger.error(unique_message)
    return unique_message

def generate_channel_name(address_1: str, address_2: str) -> str:
    """Generate channel name from two addresses, ordered lexicographically."""
    sorted_addresses = sorted([address_1, address_2])
    return f"{sorted_addresses[0]}:{sorted_addresses[1]}"

def is_channel_participant(channel_name: str, address: str) -> bool:
    """Check if the address is a participant in the channel.

    Args:
        channel_name: The name of the channel (format: address1:address2).
        address: The address to check.

    Returns:
        bool: True if the address is a participant, False otherwise.
    """
    try:
        address1, address2 = channel_name.split(":")
        return address.lower() in {address1.lower(), address2.lower()}
    except ValueError:
        return False

def is_valid_address(address: str) -> bool:
    """Check if the given address is a valid Ethereum address."""
    # Check if address matches the pattern: 0x followed by 40 hexadecimal characters
    pattern = r"^0x[a-fA-F0-9]{40}$"
    return bool(re.match(pattern, address))

def is_valid_channel_name(channel_name: str) -> bool:
    """Check if the given channel name is valid.

    Args:
        channel_name: The name of the channel to validate.

    Returns:
        bool: True if the channel name is valid, False otherwise.
    """
    # Channel names should be in the format address1:address2
    pattern = r"^0x[a-fA-F0-9]{40}:0x[a-fA-F0-9]{40}$"
    return bool(re.match(pattern, channel_name))