import os 
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase 
from email import encoders
from googleapiclient.errors import HttpError
from google_api import create_service
from logger import logger


class GmailAPI: 
    def __init__(self): 
        self.client_file =  'client_secret.json'
        self.API_SERVICE_NAME = 'gmail'
        self.API_VERSION = 'v1'
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly'] 
    
        # Initialize service 
        self.service = self.init_gmail_service(self.client_file, api_name=self.API_SERVICE_NAME, api_version=self.API_VERSION, scopes=self.SCOPES)
        
    def init_gmail_service(self, client_file, api_name, api_version, scopes): 
        return create_service(client_file, api_name, api_version, scopes)
    
    def find_emails(self, sender: str):
        print("\n=============== Find Emails: start ===============")
        request = (
            self.service.users()
            .messages()
            .list(userId="me", q=f"from:{sender}", maxResults=200)
        )

        result = self._execute_request(request)
        try:
            messages = result["messages"]
            print(f"Retrieved messages matching the '{sender}' query: {messages}")
        except KeyError:
            print(f"No messages found for the sender '{sender}'")
            messasges = []

        print("=============== Find Emails: end ===============")

        return messages
    
    # def get_email(self, email_id: str):
    #     print("\n=============== Get Email: start ===============")

    #     request = self.service.users().messages().get(userId="me", id=email_id)
    #     result = self._execute_request(request)
    #     content = result["payload"]["parts"][0]["body"]["data"]
    #     content = content.replace("-", "+").replace("_", "/")
    #     decoded = base64.b64decode(content).decode("utf-8")

    #     print(f"Retrieved email with email_id={email_id}: {result}")
    #     print("=============== Get Email: end ===============")

    #     return decoded
		
    def get_all_emails(self): 
        request = (self.service.users().messages().list(userId="me", q="is:unread", labelIds=["INBOX"]))
        
        try: 
            results = self._execute_request(request)
            
            messages = results.get("messages", [])
            
            if not messages: 
                print("No messages found.")
                return 
        
            print("Messages:")
            for message in messages: 
                print(f'Message ID: {message["id"]}')
                msg_request = (
                    self.service.users().messages().get(userId="me", id=message["id"])
                )   
                msg = self._execute_request(msg_request)
                
                print(f'    Subject: {msg["snippet"]}')      
        except HttpError as error: 
            logger.error(f"HTTP Error occurred while fetching emails {error}")   
        # try: 
        #     messages = results.get("messages", [])
        # try: 
    @staticmethod
    def _execute_request(request):
        try:
            return request.execute()
        except HttpError as e:
            print(f"An error occurred: {e}")
            raise RuntimeError(e)
        
def main(): 
    client = GmailAPI() 
    client.get_all_emails()
    # sender="kaushal.dalal@gmail.com"
    # emails = client.find_emails(sender)
    # email_ids = [email["id"] for email in emails]
    # contents = [client.get_email(email_id) for email_id in email_ids]
    
    # print(f"Content of the emails matching sender '{sender}':")
    # for content in contents:
    #     print(content.title)
    #     print()
if __name__ == "__main__": 
    main()