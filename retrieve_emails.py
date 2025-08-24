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
    
    def find_emails_by_user(self, sender: str):
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
        
    def get_raw_emails(self, max_results=100): 
        
        all_messages = []
        next_page_token = None
        
        try: 
            while True: 
                
                # Get all unread messages
                request = (self.service.users().messages().list(
                    userId="me", 
                    q="is:unread -category:promotions",
                    labelIds=["INBOX", "UNREAD"], 
                    maxResults=min(500, max_results - len(all_messages) if max_results else 500),
                    pageToken=next_page_token))
            
                results = self._execute_request(request)
                
                messages = results.get("messages", [])
                
                all_messages.extend(messages)
                
                next_page_token = results.get('nextPageToken')
                    
                if not next_page_token or (max_results and len(all_messages) >= max_results): 
                    break 
                
        except HttpError as error: 
            logger.error(f"HTTP Error occurred while fetching emails {error}")   
            return 
        
        return all_messages[:max_results] if max_results else all_messages
    
    def get_email_detail(self, msg_id): 
        try: 
            # message = self.service.users().messages().get(userId='me', id=msg_id, format='full').execute() 
            message = self._execute_request(self.service.users().messages().get(userId='me', id=msg_id, format='full'))
            payload = message['payload']
            headers = payload.get('headers', [])

            subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), None)

            if not subject: 
                subject = message.get('subject', 'No subject')
                
            sender = next((header['value'] for header in headers if header['name'] == 'From'), 'No sender')
            recipients = next((header['value'] for header in headers if header['name'] == 'To'), 'No recipients')
            snippet = message.get('snippet', 'No snippet')
            has_attachments = any(part.get('filename') for part in payload.get('parts', []) if part.get('filename'))
            date = next((header['value'] for header in headers if header['name'] == 'Date'), 'No date')
            star = message.get('labelIds', []).count('STARRED') > 0 
            label = ', '.join(message.get('labelIds', []))
            
            body = self._extract_body(payload)
            
        except HttpError as error: 
            logger.error(f"HTTP Error occurred while fetching email details")   
            return 
        
        return {
            'subject': subject, 
            'message_id': msg_id, 
            'sender': sender, 
            'recipients': recipients, 
            'body': body, 
            'snippet': snippet, 
            'has_attachments': has_attachments, 
            'date': date, 
            'star': star, 
            'label': label
        }
        
    def get_email_details(self, messages): 
        email_infos = []
        logger.info(f"Retrieving Info for {len(messages)} emails")
        for message in messages: 
            details = self.get_email_detail(message['id'])
            if details: 
                email_infos.append(details)
                logger.debug(f"Subject: {details['subject']}")
                # print(f"From: {details['sender']}")
                # print(f"Recipients: {details['recipients']}")
                # print(f"Body: {details['body'][:100]}...")
                # print(f"Snipped: {details['snippet']}")
                # print(f"Has Attachment: {details['has_attachments']}")
                # print(f"Date: {details['date']}")
                # print(f"Star: {details['star']}")
                # print(f"Label: {details['label']}")
                # print("-" * 50)
                
        logger.info(f"Retrieved Email Info for {len(email_infos)} emails")
        return email_infos
        
    def print_emails(self, messages): 
        # messages = [message for message in messages if "CATEGORY_PROMOTIONS" not in message["label"] ]
        # logger.info(f"Messages after filtering out promotions {len(messages)}")
        for message in messages: 
            details = self.get_a_emails_details(message['id'])
            if details: 
                print(f"Subject: {details['subject']}")
                print(f"From: {details['sender']}")
                print(f"Recipients: {details['recipients']}")
                print(f"Body: {details['body'][:100]}...")
                print(f"Snipped: {details['snippet']}")
                print(f"Has Attachment: {details['has_attachments']}")
                print(f"Date: {details['date']}")
                print(f"Star: {details['star']}")
                print(f"Label: {details['label']}")
                print("-" * 50)
    
    def get_emails(self): 
        messages = self.get_raw_emails()
        emails = self.get_email_details(messages)
            
        return emails
    
    def _extract_body(self, payload): 
        body = '<Text body not available>'
        if 'parts' in payload: 
            for part in payload['parts']: 
                if part['mimeType'] == 'multipart/alternative': 
                    for subpart in part['parts']: 
                        if subpart['mimeType'] == 'text/plain' and 'data' in subpart['body']: 
                            body = base64.urlsafe_b64decode(subpart['body']['data']).decode('utf-8')
                            break 
                elif part['mimeType'] == 'text/plain' and 'data' in part['body']: 
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break 
        elif 'body' in payload and 'data' in payload['body']: 
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            
        return body
    
    @staticmethod
    def _execute_request(request):
        try:
            return request.execute()
        except HttpError as e:
            print(f"An error occurred: {e}")
            raise RuntimeError(e)
        
def main(): 
    client = GmailAPI() 
    email = client.get_emails()
    # messages = client.get_raw_emails()
    # email_details = client.get_emails_details(messages)
    
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