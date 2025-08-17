#!/usr/bin/env python3
# logger.py
import logging
import sys

# Configure root logger
logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  
        logging.FileHandler("app.log", mode="a") 
    ]
)

# Create a logger object you can import everywhere
logger = logging.getLogger("autojobtracker")
