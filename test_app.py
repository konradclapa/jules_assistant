import pytest
import os
import json
import requests # Added import for requests.exceptions
from unittest.mock import patch, MagicMock
from app import app as flask_app # Renaming to avoid conflict
from app import get_current_theme, set_current_theme, get_weather_for_lodz

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

TEST_API_KEY = "test_api_key_123"

@patch('app.requests.get')
def test_get_weather_success(mock_get, app_instance):
    mock_geo_response = MagicMock()
    mock_geo_response.status_code = 200
    mock_geo_response.json.return_value = [{"lat": 51.7592, "lon": 19.4560}]

    mock_weather_response = MagicMock()
    mock_weather_response.status_code = 200
    mock_weather_response.json.return_value = {"main": {"temp": 25.5}}

    def side_effect_func(url, params, timeout):
        if "geo" in url:
            return mock_geo_response
        return mock_weather_response
    mock_get.side_effect = side_effect_func

    with app_instance.app_context():
        result = get_weather_for_lodz(TEST_API_KEY)

    assert result == {"temperature": 25.5, "emoji": ":)", "error": None}
    assert mock_get.call_count == 2

@patch('app.requests.get')
def test_get_weather_geocoding_error(mock_get, app_instance):
    mock_geo_error_response = MagicMock()
    mock_geo_error_response.status_code = 404
    mock_geo_error_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_geo_error_response) # Make it raise an error
    # Or, to test the "City not found" case by empty list:
    # mock_geo_error_response.json.return_value = []
    mock_get.return_value = mock_geo_error_response

    with app_instance.app_context():
        result = get_weather_for_lodz(TEST_API_KEY)

    assert result["error"] is not None
    # Example check, the exact message depends on how you implemented error reporting
    assert "Geocoding API request failed" in result["error"] or "City (Lodz) not found" in result["error"]
    assert result["temperature"] is None
    assert mock_get.call_count == 1


@patch('app.requests.get')
def test_get_weather_weather_api_error(mock_get, app_instance):
    mock_geo_response = MagicMock()
    mock_geo_response.status_code = 200
    mock_geo_response.json.return_value = [{"lat": 51.7592, "lon": 19.4560}]

    mock_weather_error_response = MagicMock()
    mock_weather_error_response.status_code = 500
    mock_weather_error_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_weather_error_response)


    def side_effect_func(url, params, timeout):
        if "geo" in url:
            return mock_geo_response
        return mock_weather_error_response
    mock_get.side_effect = side_effect_func

    with app_instance.app_context():
        result = get_weather_for_lodz(TEST_API_KEY)

    assert result["error"] is not None
    assert "Weather API request failed" in result["error"]
    assert result["temperature"] is None
    assert mock_get.call_count == 2

@patch('app.requests.get')
def test_get_weather_lodz_temp_below_20(mock_get, app_instance):
    mock_geo_response = MagicMock()
    mock_geo_response.status_code = 200
    mock_geo_response.json.return_value = [{"lat": 51.7592, "lon": 19.4560}]

    mock_weather_response = MagicMock()
    mock_weather_response.status_code = 200
    mock_weather_response.json.return_value = {"main": {"temp": 15.0}}

    def side_effect_func(url, params, timeout):
        if "geo" in url:
            return mock_geo_response
        return mock_weather_response
    mock_get.side_effect = side_effect_func

    with app_instance.app_context():
        result = get_weather_for_lodz(TEST_API_KEY)

    assert result == {"temperature": 15.0, "emoji": ":(", "error": None}
    assert mock_get.call_count == 2

@patch('app.requests.get')
def test_get_weather_lodz_temp_equals_20(mock_get, app_instance):
    mock_geo_response = MagicMock()
    mock_geo_response.status_code = 200
    mock_geo_response.json.return_value = [{"lat": 51.7592, "lon": 19.4560}]

    mock_weather_response = MagicMock()
    mock_weather_response.status_code = 200
    mock_weather_response.json.return_value = {"main": {"temp": 20.0}}

    def side_effect_func(url, params, timeout):
        if "geo" in url:
            return mock_geo_response
        return mock_weather_response
    mock_get.side_effect = side_effect_func

    with app_instance.app_context():
        result = get_weather_for_lodz(TEST_API_KEY)

    assert result == {"temperature": 20.0, "emoji": None, "error": None} # Emoji is None for 20 deg
    assert mock_get.call_count == 2


@patch('app.get_weather_for_lodz')
def test_index_route_button1_click_weather_success(mock_get_weather_func, client, app_instance):
    # Ensure the app uses a known API key for this test, even if .env is not loaded or is different
    # For os.getenv to work as expected in app.py, we might need to set it here
    original_env_key = os.environ.get('OPENWEATHER_API_KEY')
    os.environ['OPENWEATHER_API_KEY'] = TEST_API_KEY
    # If your app directly uses app.config for the key, this would be enough:
    # app_instance.config['OPENWEATHER_API_KEY'] = TEST_API_KEY

    mock_get_weather_func.return_value = {"temperature": 22.0, "emoji": ":)", "error": None}

    response = client.post('/', data={'button1': 'Click'})
    assert response.status_code == 200

    html_content = response.get_data(as_text=True)
    assert "22.0°C :)" in html_content
    assert "Weather in Lodz, Poland:" in html_content # This is the message set in index()
    mock_get_weather_func.assert_called_once_with(TEST_API_KEY)

    # Clean up environment variable
    if original_env_key is None:
        del os.environ['OPENWEATHER_API_KEY']
    else:
        os.environ['OPENWEATHER_API_KEY'] = original_env_key

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
