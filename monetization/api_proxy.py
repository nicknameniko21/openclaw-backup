#!/usr/bin/env python3
"""
Kimi API Proxy Service
Monetize unused API quota
"""

import json
import time
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Rate limiting and pricing
PRICING = {
    "basic": 0.001,  # $0.001 per 1K tokens
    "premium": 0.002,  # $0.002 per 1K tokens with priority
}

# Track usage
usage_log = []

def log_request(client, tokens, cost):
    usage_log.append({
        "timestamp": datetime.now().isoformat(),
        "client": client,
        "tokens": tokens,
        "cost": cost
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Proxy to Kimi API with monetization"""
    data = request.json
    client_key = request.headers.get('X-Client-Key')
    
    if not client_key:
        return jsonify({"error": "Client key required"}), 401
    
    # Calculate cost
    estimated_tokens = len(str(data)) // 4
    cost = (estimated_tokens / 1000) * PRICING["basic"]
    
    # Log for billing
    log_request(client_key, estimated_tokens, cost)
    
    # Return mock response for now
    return jsonify({
        "response": "API call logged. Cost: ${:.4f}".format(cost),
        "tokens": estimated_tokens,
        "cost": cost,
        "status": "success"
    })

@app.route('/api/usage', methods=['GET'])
def get_usage():
    """Get usage statistics"""
    client = request.args.get('client')
    
    if client:
        client_usage = [u for u in usage_log if u['client'] == client]
        total_cost = sum(u['cost'] for u in client_usage)
        return jsonify({
            "client": client,
            "total_calls": len(client_usage),
            "total_cost": total_cost,
            "usage": client_usage
        })
    
    return jsonify({
        "total_calls": len(usage_log),
        "total_revenue": sum(u['cost'] for u in usage_log),
        "clients": list(set(u['client'] for u in usage_log))
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)
