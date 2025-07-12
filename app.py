import os
from flask import Flask, request
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Africa's Talking Credentials (for later SMS/Voice integration) ---
# For now, we are just setting them up.
# Ensure these are in your .env file:
# AT_USERNAME="your_africas_talking_username"
# AT_API_KEY="your_africas_talking_api_key"
AT_USERNAME = os.getenv("AT_USERNAME")
AT_API_KEY = os.getenv("AT_API_KEY")

# Basic check to ensure credentials are loaded
if not AT_USERNAME or not AT_API_KEY:
    print("WARNING: Africa's Talking credentials (AT_USERNAME, AT_API_KEY) not found in environment or .env file.")
    print("Please ensure your .env file is correctly set up.")
    # In a real app, you might want to exit or raise an error here.

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
        # For a real app, you'd integrate with a weather API here.
        # For hackathon MVP, we can provide a sample or simple logic.
        response_text = "END Weather for Ruiru: Sunny with scattered clouds, 28°C. Good conditions for fieldwork."

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