#!/usr/bin/env python3
"""
Kimi API Proxy Service
Monetize unused API quota
"""

import json
import time
import secrets
from datetime import datetime
from collections import defaultdict
from flask import Flask, request, jsonify

app = Flask(__name__)

# Security: API keys storage (in production use database)
api_keys = {}
usage_tracker = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0.0})

# Rate limiting
rate_limits = defaultdict(lambda: {"count": 0, "reset_time": time.time() + 60})

# Pricing
PRICING = {
    "basic": 0.001,    # $0.001 per 1K tokens
    "premium": 0.002,  # $0.002 per 1K tokens
}

# Credits system
credits = defaultdict(float)

def generate_api_key():
    """Generate secure API key"""
    return secrets.token_urlsafe(32)

def check_rate_limit(client_key):
    """Check if client exceeded rate limit"""
    now = time.time()
    if now > rate_limits[client_key]["reset_time"]:
        rate_limits[client_key] = {"count": 0, "reset_time": now + 60}
    
    rate_limits[client_key]["count"] += 1
    return rate_limits[client_key]["count"] <= 100  # 100 req/min

def authenticate():
    """Authenticate request"""
    client_key = request.headers.get('X-API-Key')
    if not client_key or client_key not in api_keys:
        return None
    return client_key

def charge_client(client_key, cost):
    """Charge client credits"""
    if credits[client_key] >= cost:
        credits[client_key] -= cost
        return True
    return False

@app.route('/api/register', methods=['POST'])
def register():
    """Register new client and get API key"""
    data = request.json
    client_name = data.get('name', 'anonymous')
    
    # Generate API key
    api_key = generate_api_key()
    api_keys[api_key] = {
        "name": client_name,
        "created": datetime.now().isoformat(),
        "tier": "basic"
    }
    
    # Give $5 free credits
    credits[api_key] = 5.0
    
    return jsonify({
        "api_key": api_key,
        "credits": 5.0,
        "message": "Registration successful. $5 free credits added."
    })

@app.route('/api/add-credits', methods=['POST'])
def add_credits():
    """Add credits (payment processing)"""
    data = request.json
    api_key = data.get('api_key')
    amount = data.get('amount', 0)
    
    if api_key not in api_keys:
        return jsonify({"error": "Invalid API key"}), 401
    
    # In production: process payment here
    credits[api_key] += amount
    
    return jsonify({
        "credits_added": amount,
        "total_credits": credits[api_key]
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Proxy to Kimi API with monetization"""
    # Authenticate
    client_key = authenticate()
    if not client_key:
        return jsonify({"error": "Authentication required"}), 401
    
    # Rate limiting
    if not check_rate_limit(client_key):
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    data = request.json
    
    # Calculate cost
    estimated_tokens = len(str(data)) // 4
    cost = (estimated_tokens / 1000) * PRICING["basic"]
    
    # Check credits
    if not charge_client(client_key, cost):
        return jsonify({"error": "Insufficient credits"}), 402
    
    # Track usage
    usage_tracker[client_key]["calls"] += 1
    usage_tracker[client_key]["tokens"] += estimated_tokens
    usage_tracker[client_key]["cost"] += cost
    
    # Return response
    return jsonify({
        "response": "API call processed",
        "tokens": estimated_tokens,
        "cost": cost,
        "remaining_credits": credits[client_key],
        "status": "success"
    })

@app.route('/api/usage', methods=['GET'])
def get_usage():
    """Get usage statistics"""
    client_key = authenticate()
    if not client_key:
        return jsonify({"error": "Authentication required"}), 401
    
    return jsonify({
        "client": api_keys.get(client_key, {}).get("name"),
        "total_calls": usage_tracker[client_key]["calls"],
        "total_tokens": usage_tracker[client_key]["tokens"],
        "total_cost": usage_tracker[client_key]["cost"],
        "remaining_credits": credits[client_key]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)
