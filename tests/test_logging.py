# tests/test_logging.py
from app import utils

def test_logging_in_testing_mode():
    """Test that logging in testing mode writes ERROR messages to test.log."""
    
    # Ensure log directory and files are clean
    log_dir = utils.join_paths(utils.get_data_path(), 'logs')
    log_file = utils.join_paths(log_dir, 'test.log')
    
    # Setup logging and trigger error
    utils.setup_logging()
    unique_message = utils.trigger_test_error()

    # Check that log file exists
    assert utils.path_exists(log_file), "Log file was not created"

    # Check log file contents
    with open(log_file, 'r') as f:
        log_content = f.read()
    assert unique_message in log_content, f"Expected error message '{unique_message}' not found in log"