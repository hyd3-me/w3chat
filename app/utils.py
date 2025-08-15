# app/utils.py
import os
import json
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

# Pydantic model for authentication request
class AuthRequest(BaseModel):
    address: str
    message: str
    signature: str

def get_source_path():
    """Return the absolute path to the project root (w3chat/source)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def join_paths(*paths):
    """Join multiple paths into a single path."""
    return os.path.join(*paths)

def get_secret_data():
    """Read secret data from w3chat/data/SECRET_DATA.json."""
    secret_file = join_paths(get_source_path(), '..', 'data', 'SECRET_DATA.json')
    try:
        if not os.path.exists(secret_file):
            raise FileNotFoundError(f"Secret data file not found at {secret_file}")
        with open(secret_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load secret data: {str(e)}")

def get_secret_key():
    """Get SECRET_KEY from secret data, with a fallback."""
    secret_data = get_secret_data()
    secret_key = secret_data.get('SECRET_KEY')
    if not secret_key:
        raise ValueError("SECRET_KEY not found in secret data")
    return secret_key

# Initialize SECRET_KEY at module load
SECRET_KEY = get_secret_key()

def verify_signature(auth: AuthRequest):
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

def generate_jwt(address: str):
    """Generate JWT for the given address, return (success, token or message)."""
    try:
        payload = {
            "sub": address,
            "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return True, token
    except Exception as e:
        return False, f"JWT generation failed: {str(e)}"

def decode_jwt(token: str):
    """Decode JWT and return (success, address or message)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        address = payload.get("sub")
        if address is None:
            return False, "Invalid token: missing 'sub' field"
        return True, address
    except JWTError as e:
        return False, f"JWT verification failed: {str(e)}"