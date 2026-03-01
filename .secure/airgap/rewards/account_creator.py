#!/usr/bin/env python3
"""
Microsoft Rewards Account Creator
Using available free phone number services
"""

import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Free SMS services to try
SMS_SERVICES = [
    "https://receive-smss.com",
    "https://sms24.me",
    "https://esimplus.me",
    "https://pvapins.com"
]

def get_free_number():
    """Attempt to get free phone number from services"""
    # This requires browser automation to select number
    # Will implement with Selenium
    pass

def create_outlook_account(email, password, phone):
    """Create Outlook account with phone verification"""
    driver = webdriver.Chrome()
    try:
        # Go to Outlook signup
        driver.get("https://signup.live.com")
        time.sleep(3)
        
        # Fill email
        email_field = driver.find_element(By.ID, "MemberName")
        email_field.send_keys(email)
        driver.find_element(By.ID, "iSignupAction").click()
        time.sleep(2)
        
        # Fill password
        pass_field = driver.find_element(By.ID, "Password")
        pass_field.send_keys(password)
        driver.find_element(By.ID, "iSignupAction").click()
        time.sleep(2)
        
        # Fill name
        first_name = driver.find_element(By.ID, "FirstName")
        first_name.send_keys("User")
        last_name = driver.find_element(By.ID, "LastName")
        last_name.send_keys(str(random.randint(1000,9999)))
        driver.find_element(By.ID, "iSignupAction").click()
        time.sleep(2)
        
        # Birth date
        # ... fill date fields ...
        driver.find_element(By.ID, "iSignupAction").click()
        time.sleep(2)
        
        # Phone verification
        phone_field = driver.find_element(By.ID, "PhoneCountry")
        # Select country
        phone_input = driver.find_element(By.ID, "PhoneNumber")
        phone_input.send_keys(phone)
        driver.find_element(By.ID, "iSignupAction").click()
        
        # Wait for SMS
        time.sleep(30)
        
        # Get SMS code from service
        code = get_sms_code(phone)
        
        # Enter code
        code_field = driver.find_element(By.ID, "VerificationCode")
        code_field.send_keys(code)
        driver.find_element(By.ID, "iSignupAction").click()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        driver.quit()

def get_sms_code(phone):
    """Retrieve SMS code from free service"""
    # Implementation depends on service
    # Need to scrape website or use API
    pass

if __name__ == "__main__":
    # Create 5 accounts
    for i in range(5):
        email = f"rewardsuser{i}{random.randint(1000,9999)}@outlook.com"
        password = f"Pass{random.randint(100000,999999)}!"
        
        print(f"Creating account {i+1}: {email}")
        # create_outlook_account(email, password, phone)
        
        time.sleep(random.uniform(60, 120))
