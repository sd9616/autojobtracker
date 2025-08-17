from selenium.webdriver.support import expected_conditions as EC
from handshake_agent import HandshakeJobAgent
from dotenv import dotenv_values
from logger import logger
from cryptography.fernet import Fernet

if __name__ == "__main__":
    # Generate encryption key for this session    
    # Get env variables
    config = dotenv_values(".env") 
    
    
    # Initialize agent
    agent = HandshakeJobAgent(config
    )
    
    # Run agent with search keywords
    search_keywords = ["software engineer", "data scientist", "intern"]
    agent.run_agent(search_keywords=search_keywords)
    