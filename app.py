import json
import os
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv() # Load .env file here

app.config.setdefault('THEME_CONFIG_FILE', 'theme_config.json')

def get_current_theme():
    try:
        with open(app.config['THEME_CONFIG_FILE'], 'r') as f:
            config = json.load(f)
            return config.get('theme', 'light')
    except (FileNotFoundError, json.JSONDecodeError):
        # If file not found or JSON is invalid, default to 'light' and recreate the file.
        # Need to ensure app context for set_current_theme if called from here,
        # or pass app explicitly. For simplicity, we assume app context is available.
        set_current_theme('light')
        return 'light'

def set_current_theme(theme_name):
    with open(app.config['THEME_CONFIG_FILE'], 'w') as f:
        json.dump({'theme': theme_name}, f)

def get_weather_for_lodz(api_key):
    city_name = "Lodz"
    country_code = "PL"
    # Initialize weather_data with all expected keys to avoid KeyErrors in template
    weather_data = {"temperature": None, "error": None, "emoji": None}

    # Step 1: Geocoding
    geo_url = "http://api.openweathermap.org/geo/1.0/direct"
    geo_params = {
        "q": f"{city_name},{country_code}",
        "limit": 1,
        "appid": api_key
    }
    try:
        response = requests.get(geo_url, params=geo_params, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        geo_data = response.json()
        if not geo_data: # Check if the list is empty
            weather_data["error"] = "City (Lodz) not found by Geocoding API."
            return weather_data

        # Ensure geo_data[0] exists and has lat/lon
        if isinstance(geo_data, list) and len(geo_data) > 0:
            lat = geo_data[0].get("lat")
            lon = geo_data[0].get("lon")
        else:
            lat, lon = None, None

        if lat is None or lon is None:
            weather_data["error"] = "Latitude or Longitude not found in Geocoding response."
            return weather_data

    except requests.exceptions.Timeout:
        weather_data["error"] = "Geocoding API request timed out."
        return weather_data
    except requests.exceptions.HTTPError as e:
        weather_data["error"] = f"Geocoding API request failed with HTTP status: {e.response.status_code}"
        return weather_data
    except requests.exceptions.RequestException as e: # Catch other request-related errors
        weather_data["error"] = f"Geocoding API request failed: {e}"
        return weather_data
    except ValueError as e: # Handles JSON decoding errors
        weather_data["error"] = f"Error parsing Geocoding JSON response: {e}"
        return weather_data

    # Step 2: Weather Data
    weather_url = "https://api.openweathermap.org/data/2.5/weather"
    weather_params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"
    }
    try:
        response = requests.get(weather_url, params=weather_params, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors
        current_weather = response.json()

        temp = current_weather.get("main", {}).get("temp")

        if temp is not None:
            weather_data["temperature"] = float(temp) # Ensure temp is float
            if weather_data["temperature"] > 20:
                weather_data["emoji"] = ":)"
            elif weather_data["temperature"] < 20:
                weather_data["emoji"] = ":("
            # If temp == 20, emoji remains None as per user spec
        else:
            weather_data["error"] = "Temperature data (main.temp) not found in weather API response."

    except requests.exceptions.Timeout:
        weather_data["error"] = "Weather API request timed out."
    except requests.exceptions.HTTPError as e:
        weather_data["error"] = f"Weather API request failed with HTTP status: {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        weather_data["error"] = f"Weather API request failed: {e}"
    except ValueError as e: # Handles JSON decoding errors
        weather_data["error"] = f"Error parsing Weather JSON response: {e}"

    return weather_data

@app.route('/', methods=['GET', 'POST'])
def index():
    api_key = os.getenv("OPENWEATHER_API_KEY")
    current_theme = get_current_theme()
    message = "Please click a button."
    weather_info = {"temperature": None, "error": None, "emoji": None} # Ensure this is always defined

    if request.method == 'POST':
        if 'button1' in request.form:
            if api_key:
                weather_info = get_weather_for_lodz(api_key)
                if weather_info.get("error"):
                    message = "Failed to fetch weather."
                elif weather_info.get("temperature") is not None:
                    message = "Weather in Lodz, Poland:"
                else:
                    message = "Weather data not available or an unknown error occurred."
                    if not weather_info.get("error"):
                        weather_info["error"] = message
            else:
                message = "API Key for weather service is not configured."
                weather_info["error"] = message
        elif 'button2' in request.form:
            message = "Button 2 was clicked!"

    return render_template('index.html', message=message, current_theme=current_theme, weather_info=weather_info)

@app.route('/toggle-theme', methods=['POST'])
def toggle_theme():
    current_theme = get_current_theme()
    new_theme = 'dark' if current_theme == 'light' else 'light'
    set_current_theme(new_theme)
    return redirect(url_for('index'))

def get_weather_by_coords(lat, lon, api_key):
    weather_data = {"temperature": None, "error": None, "emoji": None}
    weather_url = "https://api.openweathermap.org/data/2.5/weather"
    weather_params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"
    }
    try:
        response = requests.get(weather_url, params=weather_params, timeout=10)
        response.raise_for_status()
        current_weather = response.json()
        temp = current_weather.get("main", {}).get("temp")

        if temp is not None:
            weather_data["temperature"] = float(temp)
            if weather_data["temperature"] > 20:
                weather_data["emoji"] = ":)"
            elif weather_data["temperature"] < 20:
                weather_data["emoji"] = ":("
        else:
            weather_data["error"] = "Temperature data (main.temp) not found in weather API response."

    except requests.exceptions.Timeout:
        weather_data["error"] = "Weather API request timed out."
    except requests.exceptions.HTTPError as e:
        weather_data["error"] = f"Weather API request failed with HTTP status: {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        weather_data["error"] = f"Weather API request failed: {e}"
    except ValueError as e: # Handles JSON decoding errors
        weather_data["error"] = f"Error parsing Weather JSON response: {e}"

    return weather_data

@app.route('/weather_by_coords', methods=['POST'])
def weather_by_coords_route():
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return jsonify({"error": "API Key for weather service is not configured."}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request: No JSON payload."}), 400

    lat = data.get('lat')
    lon = data.get('lon')

    if lat is None or lon is None:
        return jsonify({"error": "Missing latitude or longitude in request."}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return jsonify({"error": "Latitude and longitude must be valid numbers."}), 400

    weather_result = get_weather_by_coords(lat, lon, api_key)
    return jsonify(weather_result)

if __name__ == '__main__':
    app.run(debug=True)