import os 
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build 
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from logger import logger
import traceback

def create_service(client_secret_file, api_name, api_version, *scopes, prefix=''): 
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scopes for scopes in scopes[0]]
    
    logger.info(f"Scopes {scopes}")
    creds = None
    working_dir = os.getcwd()
    logger.info(f"{working_dir}")
    token_dir = 'token files'
    token_file = f'token_{API_SERVICE_NAME}_{API_VERSION}{prefix}.json'
    
    # Check if token dir exists 
    if not os.path.exists(os.path.join(working_dir, token_dir)): 
        os.mkdir(os.path.join(working_dir, token_dir))
        
    if os.path.exists(os.path.join(working_dir, token_dir, token_file)): 
        creds = Credentials.from_authorized_user_file(os.path.join(working_dir, token_dir, token_file), SCOPES)
        
    if not creds or not creds.valid: 
        if creds and creds.expired and creds.refresh_token: 
            creds.refresh(Request())
        else: 
            logger.info("Installed App Flow")
            logger.info(f"scopes {SCOPES}")
            logger.info(f"client_secret_file {CLIENT_SECRET_FILE}, type {type(CLIENT_SECRET_FILE)}")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(os.path.join(working_dir, token_dir, token_file), 'w') as token: 
            token.write(creds.to_json())

    try: 
        service = build(API_SERVICE_NAME, API_VERSION, credentials=creds, static_discovery=False)
        logger.info(f"{API_SERVICE_NAME} {API_VERSION} service created successfully")

        return service
    except Exception as e: 
        print(e)
        logger.error(f'failed to create service instance for {API_SERVICE_NAME}')
        os.remove(os.path.join(working_dir, token_dir, token_file))
        return None
