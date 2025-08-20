from google_api import create_service

client_secret_file = 'client_secret.json'
API_SERVICE_NAME = 'gmail'
API_VERSION = 'v1'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
service = create_service(client_secret_file, API_SERVICE_NAME, API_VERSION, SCOPES)