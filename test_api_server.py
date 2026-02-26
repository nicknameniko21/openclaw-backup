#!/usr/bin/env python3
"""
OpenAI-Compatible API Endpoint for Rowboat
Test server to connect Rowboat to Kimi Claw
"""

import json
import http.server
import socketserver
import subprocess
import os
from datetime import datetime

PORT = 8081
API_KEY = "rhuam-test-key-2026"

class OpenAIHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {format % args}")
    
    def do_POST(self):
        # Accept any authorization (for testing)
        auth_header = self.headers.get('Authorization', '')
        # Log what we received for debugging
        print(f"[AUTH] Received: {auth_header}")
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            messages = data.get('messages', [])
            model = data.get('model', 'kimi-coding/k2p5')
            
            # Get last user message
            user_message = ""
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_message = msg.get('content', '')
                    break
            
            print(f"[REQUEST] Model: {model}, Message: {user_message[:100]}...")
            
            # Create response (OpenAI-compatible format)
            response = {
                "id": f"chatcmpl-{datetime.now().timestamp()}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"[Kimi Claw Test Response] Received: {user_message}\n\nI am connected via OpenAI-compatible API. Ready to work."
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": 20,
                    "total_tokens": len(user_message.split()) + 20
                }
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
            print(f"[RESPONSE] Sent successfully")
            
        except Exception as e:
            print(f"[ERROR] {e}")
            self.send_error(500, str(e))
    
    def do_GET(self):
        # Health check
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "kimi-claw-test"}).encode())
        else:
            self.send_error(404)

if __name__ == "__main__":
    print(f"Starting Kimi Claw Test API on port {PORT}")
    print(f"API Key: {API_KEY}")
    print(f"Health check: http://localhost:{PORT}/health")
    print(f"Chat endpoint: http://localhost:{PORT}/v1/chat/completions")
    print("\nReady for Rowboat connection test...")
    
    with socketserver.TCPServer(("0.0.0.0", PORT), OpenAIHandler) as httpd:
        httpd.serve_forever()
