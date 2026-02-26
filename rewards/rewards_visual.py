#!/usr/bin/env python3
"""
Microsoft Rewards Automation with Screenshots
For Rhuam - Visual monitoring
"""

import time
import random
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Screenshot directory
SCREENSHOT_DIR = "/root/.openclaw/workspace/rewards/screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def take_screenshot(driver, name):
    """Take screenshot and save"""
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"{SCREENSHOT_DIR}/{name}_{timestamp}.png"
    driver.save_screenshot(filename)
    log(f"Screenshot saved: {filename}")
    return filename

def setup_driver():
    """Setup Chrome driver with options"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Headless for now (no display)
    chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def bing_search(driver, query):
    """Perform Bing search"""
    log(f"Searching: {query}")
    driver.get("https://www.bing.com")
    time.sleep(2)
    
    # Take screenshot
    take_screenshot(driver, "bing_homepage")
    
    # Find search box
    try:
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)
        
        # Take screenshot of results
        take_screenshot(driver, f"search_{query.replace(' ', '_')[:20]}")
        
        log(f"Search complete: {query}")
        return True
    except Exception as e:
        log(f"Search failed: {e}")
        take_screenshot(driver, "error_search")
        return False

def run_rewards_session():
    """Run one rewards session"""
    log("Starting Microsoft Rewards session")
    
    driver = setup_driver()
    
    try:
        # Test searches
        searches = [
            "weather today",
            "news headlines", 
            "stock market",
            "bitcoin price",
            "technology news"
        ]
        
        for query in searches:
            bing_search(driver, query)
            time.sleep(random.uniform(5, 10))
        
        log("Session complete")
        
    except Exception as e:
        log(f"Session error: {e}")
        take_screenshot(driver, "error_session")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    run_rewards_session()
