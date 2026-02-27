#!/usr/bin/env python3
"""
Apex Trading System - Cron Scheduler Integration
Phase 5: Integration with OpenClaw cron system for automated trading
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ApexCronScheduler:
    """
    Manages scheduled trading tasks using OpenClaw's cron system.
    Creates and manages cron jobs for automated trading operations.
    """
    
    def __init__(self, config_path: str = "apex/config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.schedules_file = "apex/logs/schedules.json"
        self._ensure_schedules_file()
    
    def _load_config(self) -> Dict:
        """Load Apex configuration"""
        if Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _ensure_schedules_file(self):
        """Ensure schedules tracking file exists"""
        Path(self.schedules_file).parent.mkdir(parents=True, exist_ok=True)
        if not Path(self.schedules_file).exists():
            with open(self.schedules_file, 'w') as f:
                json.dump({"schedules": []}, f, indent=2)
    
    def _load_schedules(self) -> List[Dict]:
        """Load existing schedules"""
        with open(self.schedules_file, 'r') as f:
            return json.load(f).get("schedules", [])
    
    def _save_schedules(self, schedules: List[Dict]):
        """Save schedules to file"""
        with open(self.schedules_file, 'w') as f:
            json.dump({"schedules": schedules, "updated": datetime.now().isoformat()}, 
                     f, indent=2)
    
    def create_backtest_schedule(self, name: str, strategy: str, 
                                  schedule: str, symbol: str = "BTC/USDT",
                                  days: int = 30, capital: float = 10000) -> Dict:
        """
        Create a scheduled backtest task.
        
        Args:
            name: Schedule name
            strategy: Strategy to run (breakout, mean_reversion, etc.)
            schedule: Cron expression (e.g., "0 9 * * *" for 9am daily)
            symbol: Trading pair
            days: Backtest period in days
            capital: Initial capital
        """
        task = {
            "name": name,
            "type": "backtest",
            "strategy": strategy,
            "symbol": symbol,
            "days": days,
            "capital": capital,
            "schedule": schedule,
            "created": datetime.now().isoformat(),
            "enabled": True
        }
        
        schedules = self._load_schedules()
        schedules.append(task)
        self._save_schedules(schedules)
        
        return task
    
    def create_paper_schedule(self, name: str, strategy: str,
                               interval_minutes: int = 15,
                               symbol: str = "BTC/USDT",
                               timeframe: str = "1h") -> Dict:
        """
        Create a scheduled paper trading task.
        
        Args:
            name: Schedule name
            strategy: Strategy to run
            interval_minutes: Check interval in minutes
            symbol: Trading pair
            timeframe: Candle timeframe
        """
        task = {
            "name": name,
            "type": "paper",
            "strategy": strategy,
            "symbol": symbol,
            "timeframe": timeframe,
            "interval_minutes": interval_minutes,
            "created": datetime.now().isoformat(),
            "enabled": True
        }
        
        schedules = self._load_schedules()
        schedules.append(task)
        self._save_schedules(schedules)
        
        return task
    
    def create_alert_schedule(self, name: str, alert_type: str,
                               schedule: str, params: Dict = None) -> Dict:
        """
        Create a scheduled alert/monitoring task.
        
        Args:
            name: Schedule name
            alert_type: Type of alert (price, signal, portfolio)
            schedule: Cron expression
            params: Additional parameters
        """
        task = {
            "name": name,
            "type": "alert",
            "alert_type": alert_type,
            "schedule": schedule,
            "params": params or {},
            "created": datetime.now().isoformat(),
            "enabled": True
        }
        
        schedules = self._load_schedules()
        schedules.append(task)
        self._save_schedules(schedules)
        
        return task
    
    def list_schedules(self) -> List[Dict]:
        """List all scheduled tasks"""
        return self._load_schedules()
    
    def remove_schedule(self, name: str) -> bool:
        """Remove a scheduled task by name"""
        schedules = self._load_schedules()
        original_count = len(schedules)
        schedules = [s for s in schedules if s["name"] != name]
        
        if len(schedules) < original_count:
            self._save_schedules(schedules)
            return True
        return False
    
    def enable_schedule(self, name: str, enabled: bool = True) -> bool:
        """Enable or disable a schedule"""
        schedules = self._load_schedules()
        for s in schedules:
            if s["name"] == name:
                s["enabled"] = enabled
                self._save_schedules(schedules)
                return True
        return False
    
    def generate_cron_command(self, task: Dict) -> str:
        """Generate the Python command for a scheduled task"""
        task_type = task.get("type")
        
        if task_type == "backtest":
            return (
                f"python apex/main.py backtest "
                f"--strategy {task['strategy']} "
                f"--symbol {task['symbol']} "
                f"--days {task['days']} "
                f"--capital {task['capital']}"
            )
        
        elif task_type == "paper":
            return (
                f"python apex/main.py paper "
                f"--strategy {task['strategy']} "
                f"--symbol {task['symbol']} "
                f"--timeframe {task['timeframe']}"
            )
        
        elif task_type == "alert":
            # Custom alert command
            return f"python apex/automation/run_alert.py --type {task['alert_type']}"
        
        return ""
    
    def export_to_openclaw_format(self) -> List[Dict]:
        """
        Export schedules in OpenClaw cron format.
        Returns list of job definitions ready for cron.add
        """
        schedules = self._load_schedules()
        jobs = []
        
        for s in schedules:
            if not s.get("enabled", True):
                continue
            
            schedule_expr = s.get("schedule", "*/15 * * * *")
            
            job = {
                "name": f"apex-{s['name']}",
                "schedule": {
                    "kind": "cron",
                    "expr": schedule_expr,
                    "tz": "America/Sao_Paulo"  # Rhuam's timezone
                },
                "payload": {
                    "kind": "agentTurn",
                    "message": f"Run Apex {s['type']} task: {s['name']}. "
                               f"Execute: {self.generate_cron_command(s)}",
                    "model": "kimi-coding/k2p5"
                },
                "sessionTarget": "isolated",
                "enabled": True,
                "notify": True
            }
            jobs.append(job)
        
        return jobs


def main():
    """CLI for cron scheduler management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Apex Cron Scheduler')
    subparsers = parser.add_subparsers(dest='command')
    
    # List command
    subparsers.add_parser('list', help='List all schedules')
    
    # Add backtest command
    backtest_parser = subparsers.add_parser('add-backtest', help='Add backtest schedule')
    backtest_parser.add_argument('--name', required=True, help='Schedule name')
    backtest_parser.add_argument('--strategy', required=True, help='Strategy name')
    backtest_parser.add_argument('--schedule', required=True, help='Cron expression')
    backtest_parser.add_argument('--symbol', default='BTC/USDT', help='Trading pair')
    backtest_parser.add_argument('--days', type=int, default=30, help='Backtest days')
    backtest_parser.add_argument('--capital', type=float, default=10000, help='Capital')
    
    # Add paper command
    paper_parser = subparsers.add_parser('add-paper', help='Add paper trading schedule')
    paper_parser.add_argument('--name', required=True, help='Schedule name')
    paper_parser.add_argument('--strategy', required=True, help='Strategy name')
    paper_parser.add_argument('--interval', type=int, default=15, help='Interval minutes')
    paper_parser.add_argument('--symbol', default='BTC/USDT', help='Trading pair')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove schedule')
    remove_parser.add_argument('name', help='Schedule name')
    
    # Export command
    subparsers.add_parser('export', help='Export to OpenClaw format')
    
    args = parser.parse_args()
    
    scheduler = ApexCronScheduler()
    
    if args.command == 'list':
        schedules = scheduler.list_schedules()
        print(f"\n{'='*60}")
        print("APEX SCHEDULED TASKS")
        print('='*60)
        for s in schedules:
            status = "✅" if s.get("enabled", True) else "❌"
            print(f"{status} {s['name']} ({s['type']})")
            print(f"   Strategy: {s.get('strategy', 'N/A')}")
            print(f"   Schedule: {s.get('schedule', 'N/A')}")
            print()
    
    elif args.command == 'add-backtest':
        task = scheduler.create_backtest_schedule(
            name=args.name,
            strategy=args.strategy,
            schedule=args.schedule,
            symbol=args.symbol,
            days=args.days,
            capital=args.capital
        )
        print(f"✅ Created backtest schedule: {task['name']}")
    
    elif args.command == 'add-paper':
        task = scheduler.create_paper_schedule(
            name=args.name,
            strategy=args.strategy,
            interval_minutes=args.interval,
            symbol=args.symbol
        )
        print(f"✅ Created paper trading schedule: {task['name']}")
    
    elif args.command == 'remove':
        if scheduler.remove_schedule(args.name):
            print(f"✅ Removed schedule: {args.name}")
        else:
            print(f"❌ Schedule not found: {args.name}")
    
    elif args.command == 'export':
        jobs = scheduler.export_to_openclaw_format()
        print(json.dumps(jobs, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
