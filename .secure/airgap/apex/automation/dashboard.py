#!/usr/bin/env python3
"""
Apex Trading System - Web Dashboard
Phase 5: Real-time monitoring dashboard
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


class DashboardGenerator:
    """Generates HTML dashboard for trading system"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.output_dir = self.config.get("output_dir", "apex/dashboard")
        self.refresh_interval = self.config.get("refresh_seconds", 30)
    
    def generate(self, data: Dict) -> str:
        """Generate complete dashboard HTML"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apex Trading Dashboard</title>
    <meta http-equiv="refresh" content="{self.refresh_interval}">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e1a;
            color: #e0e6ed;
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
            padding: 20px 30px;
            border-bottom: 1px solid #30363d;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .header h1 {{
            font-size: 24px;
            color: #58a6ff;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .header .status {{
            display: flex;
            gap: 20px;
            align-items: center;
        }}
        
        .status-badge {{
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .status-badge.online {{
            background: #238636;
            color: white;
        }}
        
        .status-badge.offline {{
            background: #da3633;
            color: white;
        }}
        
        .container {{
            padding: 20px 30px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
        }}
        
        .card h3 {{
            font-size: 14px;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .metric {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #21262d;
        }}
        
        .metric:last-child {{
            border-bottom: none;
        }}
        
        .metric-label {{
            color: #8b949e;
            font-size: 14px;
        }}
        
        .metric-value {{
            font-size: 16px;
            font-weight: 600;
            font-family: 'SF Mono', Monaco, monospace;
        }}
        
        .metric-value.positive {{
            color: #3fb950;
        }}
        
        .metric-value.negative {{
            color: #f85149;
        }}
        
        .metric-value.neutral {{
            color: #e0e6ed;
        }}
        
        .large-metric {{
            font-size: 32px;
            font-weight: 700;
            margin: 10px 0;
        }}
        
        .chart-container {{
            height: 200px;
            background: #0d1117;
            border-radius: 8px;
            margin-top: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #8b949e;
            font-size: 14px;
        }}
        
        .positions-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        .positions-table th,
        .positions-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #21262d;
        }}
        
        .positions-table th {{
            color: #8b949e;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .positions-table tr:hover {{
            background: #1c2128;
        }}
        
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        
        .badge.long {{
            background: #23863633;
            color: #3fb950;
        }}
        
        .badge.short {{
            background: #da363333;
            color: #f85149;
        }}
        
        .alerts-list {{
            max-height: 300px;
            overflow-y: auto;
        }}
        
        .alert-item {{
            padding: 12px;
            border-left: 3px solid;
            margin-bottom: 8px;
            background: #0d1117;
            border-radius: 0 8px 8px 0;
        }}
        
        .alert-item.critical {{
            border-color: #f85149;
        }}
        
        .alert-item.high {{
            border-color: #f0883e;
        }}
        
        .alert-item.medium {{
            border-color: #d29922;
        }}
        
        .alert-item.low {{
            border-color: #58a6ff;
        }}
        
        .alert-time {{
            font-size: 11px;
            color: #8b949e;
        }}
        
        .alert-title {{
            font-weight: 600;
            margin: 4px 0;
        }}
        
        .alert-message {{
            font-size: 13px;
            color: #8b949e;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #8b949e;
            font-size: 12px;
            border-top: 1px solid #30363d;
            margin-top: 30px;
        }}
        
        .strategies-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}
        
        .strategy-item {{
            background: #0d1117;
            padding: 12px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .strategy-name {{
            font-size: 13px;
        }}
        
        .strategy-status {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}
        
        .strategy-status.active {{
            background: #3fb950;
            box-shadow: 0 0 8px #3fb950;
        }}
        
        .strategy-status.inactive {{
            background: #8b949e;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 Apex Trading System</h1>
        <div class="status">
            <span class="status-badge online">● Online</span>
            <span>Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
        </div>
    </div>
    
    <div class="container">
        <!-- Performance Overview -->
        <div class="grid">
            <div class="card">
                <h3>💰 Daily P&L</h3>
                <div class="large-metric {self._get_pnl_class(data.get('daily_pnl', 0))}">
                    {self._format_currency(data.get('daily_pnl', 0))}
                </div>
                <div class="metric">
                    <span class="metric-label">Win Rate</span>
                    <span class="metric-value">{data.get('win_rate', 0):.1f}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Trades</span>
                    <span class="metric-value">{data.get('total_trades', 0)}</span>
                </div>
            </div>
            
            <div class="card">
                <h3>📊 Portfolio Value</h3>
                <div class="large-metric neutral">
                    {self._format_currency(data.get('portfolio_value', 10000))}
                </div>
                <div class="metric">
                    <span class="metric-label">Available Cash</span>
                    <span class="metric-value">{self._format_currency(data.get('cash', 10000))}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Positions Value</span>
                    <span class="metric-value">{self._format_currency(data.get('positions_value', 0))}</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🎯 Active Strategies</h3>
                <div class="strategies-grid">
                    {self._render_strategies(data.get('strategies', {}))}
                </div>
            </div>
        </div>
        
        <!-- Positions -->
        <div class="card">
            <h3>📋 Open Positions</h3>
            {self._render_positions(data.get('positions', []))}
        </div>
        
        <!-- Recent Alerts -->
        <div class="card">
            <h3>🔔 Recent Alerts</h3>
            <div class="alerts-list">
                {self._render_alerts(data.get('alerts', []))}
            </div>
        </div>
        
        <!-- System Status -->
        <div class="grid" style="margin-top: 30px;">
            <div class="card">
                <h3>🔌 Exchange Connections</h3>
                {self._render_exchanges(data.get('exchanges', {}))}
            </div>
            
            <div class="card">
                <h3>⏱️ Scheduled Tasks</h3>
                {self._render_tasks(data.get('tasks', {}))}
            </div>
        </div>
    </div>
    
    <div class="footer">
        Apex Trading System v1.0 | Phase 5 Complete | Auto-refresh every {self.refresh_interval}s
    </div>
</body>
</html>"""
        
        return html
    
    def _get_pnl_class(self, pnl: float) -> str:
        if pnl > 0:
            return "positive"
        elif pnl < 0:
            return "negative"
        return "neutral"
    
    def _format_currency(self, value: float) -> str:
        if value is None:
            return "$0.00"
        sign = "+" if value > 0 else ""
        return f"{sign}${value:,.2f}"
    
    def _render_strategies(self, strategies: Dict) -> str:
        if not strategies:
            strategies = {
                "Breakout": True,
                "Mean Reversion": False,
                "Trend Following": True,
                "ML Strategy": True,
                "Ensemble": True
            }
        
        html = ""
        for name, active in strategies.items():
            status_class = "active" if active else "inactive"
            html += f"""
                    <div class="strategy-item">
                        <span class="strategy-name">{name}</span>
                        <span class="strategy-status {status_class}"></span>
                    </div>"""
        return html
    
    def _render_positions(self, positions: List[Dict]) -> str:
        if not positions:
            return '<p style="color: #8b949e; padding: 20px;">No open positions</p>'
        
        html = """
                <table class="positions-table">
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Side</th>
                            <th>Size</th>
                            <th>Entry Price</th>
                            <th>Current Price</th>
                            <th>P&L</th>
                            <th>P&L %</th>
                        </tr>
                    </thead>
                    <tbody>"""
        
        for pos in positions:
            pnl_class = self._get_pnl_class(pos.get('pnl', 0))
            side_class = "long" if pos.get('side') == 'long' else "short"
            
            html += f"""
                        <tr>
                            <td><strong>{pos.get('symbol', 'N/A')}</strong></td>
                            <td><span class="badge {side_class}">{pos.get('side', 'N/A')}</span></td>
                            <td>{pos.get('size', 0):.4f}</td>
                            <td>${pos.get('entry_price', 0):,.2f}</td>
                            <td>${pos.get('current_price', 0):,.2f}</td>
                            <td class="{pnl_class}">${pos.get('pnl', 0):,.2f}</td>
                            <td class="{pnl_class}">{pos.get('pnl_percent', 0):.2f}%</td>
                        </tr>"""
        
        html += """
                    </tbody>
                </table>"""
        return html
    
    def _render_alerts(self, alerts: List[Dict]) -> str:
        if not alerts:
            return '<p style="color: #8b949e; padding: 20px;">No recent alerts</p>'
        
        html = ""
        for alert in alerts[:10]:  # Show last 10
            priority = alert.get('priority', 'low')
            html += f"""
                    <div class="alert-item {priority}">
                        <div class="alert-time">{alert.get('time', 'N/A')}</div>
                        <div class="alert-title">{alert.get('title', 'Alert')}</div>
                        <div class="alert-message">{alert.get('message', '')}</div>
                    </div>"""
        return html
    
    def _render_exchanges(self, exchanges: Dict) -> str:
        if not exchanges:
            exchanges = {
                "Binance": {"connected": True, "latency_ms": 45},
                "Coinbase": {"connected": False, "latency_ms": None},
                "Kraken": {"connected": True, "latency_ms": 120}
            }
        
        html = ""
        for name, status in exchanges.items():
            connected = status.get('connected', False)
            status_text = "Connected" if connected else "Disconnected"
            status_class = "positive" if connected else "negative"
            latency = status.get('latency_ms', '-')
            
            html += f"""
                    <div class="metric">
                        <span class="metric-label">{name}</span>
                        <span class="metric-value {status_class}">{status_text} ({latency}ms)</span>
                    </div>"""
        return html
    
    def _render_tasks(self, tasks: Dict) -> str:
        if not tasks:
            tasks = {
                "Price Monitor": {"status": "running", "last_run": "2 min ago"},
                "Signal Scanner": {"status": "running", "last_run": "5 min ago"},
                "P&L Report": {"status": "scheduled", "next_run": "23:00"}
            }
        
        html = ""
        for name, task in tasks.items():
            status = task.get('status', 'unknown')
            last_run = task.get('last_run', '-')
            next_run = task.get('next_run', '-')
            
            status_class = "positive" if status == "running" else "neutral"
            time_info = f"Last: {last_run}" if last_run != '-' else f"Next: {next_run}"
            
            html += f"""
                    <div class="metric">
                        <span class="metric-label">{name}</span>
                        <span class="metric-value {status_class}">{status.title()} ({time_info})</span>
                    </div>"""
        return html
    
    def save(self, data: Dict, filename: str = "index.html"):
        """Generate and save dashboard to file"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        html = self.generate(data)
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(html)
        
        return filepath


class DashboardServer:
    """Simple HTTP server for dashboard (optional)"""
    
    def __init__(self, generator: DashboardGenerator, port: int = 8080):
        self.generator = generator
        self.port = port
        self.data: Dict = {}
    
    def update_data(self, data: Dict):
        """Update dashboard data"""
        self.data.update(data)
        self.generator.save(self.data)
    
    def start(self):
        """Start the dashboard server"""
        import http.server
        import socketserver
        
        os.chdir(self.generator.output_dir)
        
        handler = http.server.SimpleHTTPRequestHandler
        
        with socketserver.TCPServer(("", self.port), handler) as httpd:
            print(f"Dashboard server running at http://localhost:{self.port}")
            httpd.serve_forever()


# Export
__all__ = ['DashboardGenerator', 'DashboardServer']