#!/usr/bin/env python3
"""
Microsoft Rewards Automation - Small Scale Test
For Rhuam - Money Making Operation
"""

import time
import random
import json
import os
from datetime import datetime

# Configuration
CONFIG = {
    "accounts": [],  # Will be populated
    "daily_points_target": 300,
    "search_count_pc": 30,
    "search_count_mobile": 20,
    "delay_min": 2,
    "delay_max": 5,
}

# Search queries for automation
SEARCH_QUERIES = [
    "weather today", "news", "sports", "recipes", "movies",
    "stock market", "bitcoin price", "technology", "science",
    "history", "geography", "math calculator", "translate",
    "maps", "flights", "hotels", "restaurants", "shopping",
    "youtube", "facebook", "twitter", "instagram", "linkedin",
    "amazon", "ebay", "walmart", "target", "best buy",
    "cnn", "bbc", "fox news", "msnbc", "reuters",
    "nba", "nfl", "mlb", "nhl", "soccer",
    "iphone", "samsung", "google", "microsoft", "apple",
    "tesla", "spacex", "elon musk", "jeff bezos", "bill gates",
]

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def random_delay():
    """Random delay between actions"""
    delay = random.uniform(CONFIG["delay_min"], CONFIG["delay_max"])
    time.sleep(delay)

def simulate_search(query):
    """Simulate a Bing search"""
    log(f"Searching: {query}")
    random_delay()
    log(f"Search complete: {query}")
    return True

def run_daily_tasks(account):
    """Run daily tasks for one account"""
    log(f"Starting daily tasks for account: {account['email']}")
    
    points_earned = 0
    
    # PC searches
    log(f"Running {CONFIG['search_count_pc']} PC searches...")
    for i in range(CONFIG["search_count_pc"]):
        query = random.choice(SEARCH_QUERIES)
        if simulate_search(query):
            points_earned += 5  # Approximate points per search
        
        # Random break every 10 searches
        if i % 10 == 0 and i > 0:
            log("Taking a break...")
            time.sleep(random.uniform(10, 30))
    
    # Mobile searches (simulated)
    log(f"Running {CONFIG['search_count_mobile']} mobile searches...")
    for i in range(CONFIG["search_count_mobile"]):
        query = random.choice(SEARCH_QUERIES)
        if simulate_search(query + " mobile"):
            points_earned += 5
    
    # Daily quiz (simulated)
    log("Completing daily quiz...")
    random_delay()
    points_earned += 30
    
    # Daily poll (simulated)
    log("Completing daily poll...")
    random_delay()
    points_earned += 10
    
    log(f"Daily tasks complete. Points earned: ~{points_earned}")
    return points_earned

def main():
    """Main function"""
    log("Microsoft Rewards Automation - Starting")
    log("Mode: SIMULATION (no real browser)")
    
    # Load accounts
    accounts_file = "accounts.json"
    if os.path.exists(accounts_file):
        with open(accounts_file, 'r') as f:
            CONFIG["accounts"] = json.load(f)
    else:
        log("No accounts file found. Creating template...")
        CONFIG["accounts"] = [
            {"email": "account1@example.com", "password": "", "referral": None},
        ]
        with open(accounts_file, 'w') as f:
            json.dump(CONFIG["accounts"], f, indent=2)
        log(f"Template created: {accounts_file}")
        log("Edit the file with real account credentials")
        return
    
    # Run for each account
    total_points = 0
    for account in CONFIG["accounts"]:
        if not account.get("email") or "example.com" in account["email"]:
            log(f"Skipping template account: {account.get('email', 'unknown')}")
            continue
        
        points = run_daily_tasks(account)
        total_points += points
        
        # Delay between accounts
        if account != CONFIG["accounts"][-1]:
            log("Switching to next account...")
            time.sleep(random.uniform(60, 120))
    
    log(f"All accounts complete. Total points: ~{total_points}")
    log(f"Estimated value: ~${total_points / 1000:.2f}")

if __name__ == "__main__":
    main()
