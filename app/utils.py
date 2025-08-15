# app/utils.py
import os
import json

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
    secret_key = secret_data.get('SECRET_KEY', '')
    if not secret_key:
        raise ValueError("SECRET_KEY not found in secret data")
    return secret_key