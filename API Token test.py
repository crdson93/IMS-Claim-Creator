import requests

# Prompt the user to enter the initial access token
initial_token = '8RfGAA0rhPQr6K6P6hBNsEHBESXiyZpCN5wkd'

# Use the initial access token to make the API request
url = "https://api.smartsheet.com/2.0/sheets"
headers = {"Authorization": f"Bearer {initial_token}"}
response = requests.get(url, headers=headers)

# Check if the response status code indicates an authentication error (401)
if response.status_code == 401:
    print("Invalid initial API access token. Please enter a new token.")
    new_token = input("Enter the new API access token: ")

    # Retry the API request with the new access token
    headers["Authorization"] = f"Bearer {new_token}"
    response = requests.get(url, headers=headers)

# Use the response data as needed
data = response.json()
