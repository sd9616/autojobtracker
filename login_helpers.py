import pickle
import os 
from cryptography.fernet import Fernet
from logger import logger
import json
# Helper Functions
def save_cookies(driver, filename):
    # f = Fernet(key)
    # plain_text_cookies = driver.get_cookies()
    # bytes_cookies = plain_text_cookies.encode()
    # encrypted_cookies = f.encrypt(bytes_cookies)
    with open(filename, 'wb') as filehandler:
        # pickle.dump(encrypted_cookies, filehandler)
        pickle.dump(driver.get_cookies(), filehandler)

def load_cookies(driver, filename, url):
    # logger.info("in load cookies")
    if not os.path.exists(filename):
        logger.error(f"Cookies (f{filename}) file does not exist")
    driver.get(url)
    # f = Fernet(key)
    
    with open(filename, 'rb') as cookiesfile:
        # cookies = json.loads(f.decrypt(cookiesfile.read()).decode())
        # cookies = json.dumps(f.decrypt(cookiesfile.read()).decode())
        # logger.info("Loading Cookies")
        cookies = pickle.load(cookiesfile)
        for cookie in cookies:
            driver.add_cookie(cookie)