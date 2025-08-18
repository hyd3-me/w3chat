# tests/conftest.py
import pytest
import json
from fastapi.testclient import TestClient
from web3 import Web3
from app.main import app
from app import utils

@pytest.fixture(autouse=True, scope="session")
def set_testing_mode():
    """Set MODE=testing for all tests."""
    utils.set_environment_variable('MODE', 'testing')

@pytest.fixture(scope="session")
def client():
    """Provide a FastAPI test client."""
    return TestClient(app)

@pytest.fixture(scope="session")
def web3():
    """Provide a Web3 instance."""
    return Web3()

@pytest.fixture(scope="session")
def user_account(web3):
    """Provide a test user account, reusing or creating a wallet in SECRET_DATA.json."""
    secret_data = utils.get_secret_data()
    
    if 'address' in secret_data and 'private_key' in secret_data:
        account = web3.eth.account.from_key(secret_data["private_key"])
    else:
        account = web3.eth.account.create()
        secret_data.update({
            "address": account.address,
            "private_key": account.key.hex()
        })
        secret_file = utils.join_paths(utils.get_data_path(), 'SECRET_DATA.json')
        with open(secret_file, "w") as f:
            json.dump(secret_data, f, indent=2)
    
    return account