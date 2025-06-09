import pytest
import os
import json
from app import app as flask_app # Renaming to avoid conflict
from app import get_current_theme, set_current_theme

TEST_THEME_CONFIG_FILE = 'test_theme_config.json'

@pytest.fixture
def app_instance(): # Changed fixture name to avoid conflict with imported 'app' module
    # Setup: Ensure the app is configured for testing
    flask_app.config['TESTING'] = True
    flask_app.config['THEME_CONFIG_FILE'] = TEST_THEME_CONFIG_FILE

    # Create an application context
    with flask_app.app_context():
        # Clean up any existing test file before a test session (optional, usually handled per test)
        if os.path.exists(TEST_THEME_CONFIG_FILE):
            os.remove(TEST_THEME_CONFIG_FILE)
        yield flask_app # provide the app instance

    # Teardown: Clean up the test file after tests if it exists
    if os.path.exists(TEST_THEME_CONFIG_FILE):
        os.remove(TEST_THEME_CONFIG_FILE)

@pytest.fixture
def client(app_instance): # Depends on the app_instance fixture
    return app_instance.test_client()

# Helper function to clean up test file, to be used in tests
def cleanup_test_file():
    if os.path.exists(TEST_THEME_CONFIG_FILE):
        os.remove(TEST_THEME_CONFIG_FILE)

# Helper function to create test file with specific content
def create_test_config(theme_name):
    with open(TEST_THEME_CONFIG_FILE, 'w') as f:
        json.dump({'theme': theme_name}, f)

def test_get_theme_file_not_exists(app_instance):
    cleanup_test_file() # Ensure file does not exist
    # Call within app context as get_current_theme accesses app.config and calls set_current_theme
    with app_instance.app_context():
        theme = get_current_theme()
    assert theme == "light"
    assert os.path.exists(TEST_THEME_CONFIG_FILE)
    with open(TEST_THEME_CONFIG_FILE, 'r') as f:
        config = json.load(f)
    assert config == {"theme": "light"}
    cleanup_test_file()

def test_toggle_theme_route(app_instance, client):
    # Ensure app_instance.config is used by set_current_theme by calling it within app_context
    with app_instance.app_context():
        set_current_theme("light") # Start with light theme

    response = client.post('/toggle-theme')
    assert response.status_code == 302 # Redirect
    assert response.headers['Location'] == '/' # Redirects to index

    with open(TEST_THEME_CONFIG_FILE, 'r') as f:
        config = json.load(f)
    assert config == {"theme": "dark"}

    response = client.post('/toggle-theme')
    assert response.status_code == 302
    assert response.headers['Location'] == '/'

    with open(TEST_THEME_CONFIG_FILE, 'r') as f:
        config = json.load(f)
    assert config == {"theme": "light"}
    cleanup_test_file()

def test_get_theme_file_exists(app_instance):
    create_test_config("dark")
    # Call within app context
    with app_instance.app_context():
        theme = get_current_theme()
    assert theme == "dark"
    cleanup_test_file()

def test_set_theme(app_instance):
    cleanup_test_file()
    # Call within app context
    with app_instance.app_context():
        set_current_theme("dark")
    assert os.path.exists(TEST_THEME_CONFIG_FILE)
    with open(TEST_THEME_CONFIG_FILE, 'r') as f:
        config = json.load(f)
    assert config == {"theme": "dark"}

    with app_instance.app_context():
        set_current_theme("light")
    with open(TEST_THEME_CONFIG_FILE, 'r') as f:
        config = json.load(f)
    assert config == {"theme": "light"}
    cleanup_test_file()
