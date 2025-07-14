import os
from flask import Flask, request
from dotenv import load_dotenv
import requests # Import the requests library for making HTTP calls

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Africa's Talking Credentials (for later SMS/Voice integration) ---
# These are loaded from your .env file.
# Ensure your .env file has:
# AT_USERNAME="your_africas_talking_username"
# AT_API_KEY="your_africas_talking_api_key"
AT_USERNAME = os.getenv("AT_USERNAME")
AT_API_KEY = os.getenv("AT_API_KEY")

# --- OpenWeatherMap API Key ---
# This is loaded from your .env file.
# Ensure your .env file has:
# OPENWEATHER_API_KEY="YOUR_OPENWEATHERMAP_API_KEY"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Basic checks to ensure credentials are loaded
if not AT_USERNAME or not AT_API_KEY:
    print("WARNING: Africa's Talking credentials (AT_USERNAME, AT_API_KEY) not found in environment or .env file.")
    print("Please ensure your .env file is correctly set up.")

if not OPENWEATHER_API_KEY:
    print("WARNING: OpenWeatherMap API key (OPENWEATHER_API_KEY) not found in environment or .env file.")
    print("Weather forecast functionality may not work.")


# --- Session State Storage ---
# This dictionary will temporarily store the state of each USSD session.
# In a production environment, you would use a persistent database (like Firestore)
# for session management. For a hackathon, in-memory is acceptable.
session_states = {}


# --- Helper Function to Get Weather Forecast ---
def get_weather_forecast(city_name):
    """
    Fetches weather forecast for a given city using OpenWeatherMap API.
    """
    if not OPENWEATHER_API_KEY:
        return "END Weather service not available. API key missing."

    # OpenWeatherMap API endpoint for current weather
    # Using f-string for easy URL construction
    # units=metric for Celsius temperature
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}&units=metric"

    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        # Extract relevant weather information
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
        city_display_name = data['name'] # OpenWeatherMap returns the official city name

        return f"END Weather in {city_display_name}: {weather_description.capitalize()}, {temperature}°C."

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return "END City not found. Please check spelling and try again."
        else:
            print(f"HTTP error occurred: {http_err} - Status Code: {response.status_code}")
            return "END Error fetching weather data. Please try again later."
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
        return "END Network error. Please check your internet connection."
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
        return "END Request timed out. Please try again."
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred during API request: {req_err}")
        return "END An unexpected error occurred. Please try again."
    except KeyError as key_err:
        print(f"Key error in weather data: {key_err}. Response data: {data}")
        return "END Weather data format error. Please try again."
    except Exception as e:
        print(f"An unexpected error occurred in get_weather_forecast: {e}")
        return "END An unknown error occurred. Please try again."


# --- USSD Callback Endpoint ---
@app.route('/', methods=['POST', 'GET'])
def ussd_callback():
    # Initialize response_text for each request
    response_text = ""

    # Read the variables sent by Africa's Talking
    session_id = request.values.get("sessionId", None)
    service_code = request.values.get("serviceCode", None)
    phone_number = request.values.get("phoneNumber", None)
    text = request.values.get("text", "").strip() # User input from the USSD session

    # Determine the current state of the session
    current_state = session_states.get(session_id, None)

    # --- USSD Logic ---
    # This is where you define the flow of your USSD menu
    if text == '':
        # This is the first request, show the main menu
        response_text = "CON Welcome to MkulimaMkononi! \n"
        response_text += "1. Get Agri-Tips \n"
        response_text += "2. Weather Forecast \n"
        response_text += "3. My Account"

    elif text == '1':
        # User selected 'Get Agri-Tips'
        response_text = "CON Select crop for tips: \n"
        response_text += "1. Maize \n"
        response_text += "2. Beans \n"
        response_text += "3. Coffee"

    elif text == '1*1':
        # User selected 'Get Agri-Tips' -> 'Maize'
        response_text = "END Maize Tip: Ensure proper spacing for optimal growth. Look out for Fall Armyworm during early stages."

    elif text == '1*2':
        # User selected 'Get Agri-Tips' -> 'Beans'
        response_text = "END Beans Tip: Plant disease-resistant varieties. Provide support for climbing beans."

    elif text == '1*3':
        # User selected 'Get Agri-Tips' -> 'Coffee'
        response_text = "END Coffee Tip: Prune regularly for better yield. Monitor for Coffee Berry Disease."

    elif text == '2':
        # User selected 'Weather Forecast'
        response_text = "CON Please enter your town or city name (e.g., Nairobi):"
        # Store the session state to indicate we are now awaiting a city name
        session_states[session_id] = 'awaiting_city_name'

    # --- Handle City Name Input for Weather Forecast ---
    elif current_state == 'awaiting_city_name':
        city_name = text.split('*')[-1].strip() # The user's input is the city name
        print(f"DEBUG: Attempting to fetch weather for city: '{city_name}'")
        response_text = get_weather_forecast(city_name)
        # After getting weather, end the session and clear the state
        if session_id in session_states:
            del session_states[session_id]
   
    elif text == '3':
        # User selected 'My Account'
        response_text = "CON My Account: \n"
        response_text += "1. View Phone Number \n"
        response_text += "2. Change Crop Preference"

    elif text == '3*1':
        # User selected 'My Account' -> 'View Phone Number'
        response_text = "END Your registered phone number is: " + phone_number

    elif text == '3*2':
        # User selected 'My Account' -> 'Change Crop Preference'
        # This would lead to another menu to select new crop.
        # For now, we'll just end the session.
        response_text = "END Feature under development. Please contact support to change preferences."

    else:
        # Handle invalid input or unexpected paths
        response_text = "END Invalid selection. Please try again."

    # Return the response to Africa's Talking
    return response_text

# --- Run the Flask Application ---
if __name__ == '__main__':
    # Get port from environment variable, or default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    print(f"MkulimaMkononi USSD app running on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=True) # debug=True for development
