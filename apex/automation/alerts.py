#!/usr/bin/env python3
"""
Apex Trading System - Automation & Monitoring Module
Phase 5: Cron scheduling, alerts, and dashboard
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertType(Enum):
    PRICE = "price"
    SIGNAL = "signal"
    POSITION = "position"
    RISK = "risk"
    SYSTEM = "system"
    ERROR = "error"


class AlertPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Trading alert notification"""
    alert_type: AlertType
    priority: AlertPriority
    title: str
    message: str
    symbol: Optional[str] = None
    timestamp: datetime = None
    data: Dict = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.data is None:
            self.data = {}
    
    def to_dict(self) -> Dict:
        return {
            "alert_type": self.alert_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }


class AlertChannel:
    """Base class for alert channels"""
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
    
    async def send(self, alert: Alert) -> bool:
        """Send alert through this channel"""
        raise NotImplementedError
    
    def format_message(self, alert: Alert) -> str:
        """Format alert for this channel"""
        emoji_map = {
            AlertPriority.LOW: "ℹ️",
            AlertPriority.MEDIUM: "⚠️",
            AlertPriority.HIGH: "🔴",
            AlertPriority.CRITICAL: "🚨"
        }
        
        emoji = emoji_map.get(alert.priority, "📢")
        symbol_str = f" [{alert.symbol}]" if alert.symbol else ""
        
        return f"""{emoji} **{alert.title}**{symbol_str}

{alert.message}

Priority: {alert.priority.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"""


class TelegramChannel(AlertChannel):
    """Telegram bot alert channel"""
    
    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True):
        super().__init__("telegram", enabled)
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send(self, alert: Alert) -> bool:
        if not self.enabled:
            return False
        
        try:
            import aiohttp
            
            message = self.format_message(alert)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Telegram alert sent: {alert.title}")
                        return True
                    else:
                        logger.error(f"Telegram API error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False


class DiscordChannel(AlertChannel):
    """Discord webhook alert channel"""
    
    def __init__(self, webhook_url: str, enabled: bool = True):
        super().__init__("discord", enabled)
        self.webhook_url = webhook_url
    
    async def send(self, alert: Alert) -> bool:
        if not self.enabled:
            return False
        
        try:
            import aiohttp
            
            color_map = {
                AlertPriority.LOW: 3447003,      # Blue
                AlertPriority.MEDIUM: 16776960,  # Yellow
                AlertPriority.HIGH: 15158332,    # Red
                AlertPriority.CRITICAL: 16711680 # Dark Red
            }
            
            embed = {
                "title": alert.title,
                "description": alert.message,
                "color": color_map.get(alert.priority, 3447003),
                "timestamp": alert.timestamp.isoformat(),
                "fields": []
            }
            
            if alert.symbol:
                embed["fields"].append({
                    "name": "Symbol",
                    "value": alert.symbol,
                    "inline": True
                })
            
            embed["fields"].append({
                "name": "Priority",
                "value": alert.priority.value.upper(),
                "inline": True
            })
            
            payload = {
                "embeds": [embed]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info(f"Discord alert sent: {alert.title}")
                        return True
                    else:
                        logger.error(f"Discord API error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False


class ConsoleChannel(AlertChannel):
    """Console/log alert channel (always works)"""
    
    def __init__(self, enabled: bool = True):
        super().__init__("console", enabled)
    
    async def send(self, alert: Alert) -> bool:
        color_map = {
            AlertPriority.LOW: "\033[94m",     # Blue
            AlertPriority.MEDIUM: "\033[93m",  # Yellow
            AlertPriority.HIGH: "\033[91m",    # Red
            AlertPriority.CRITICAL: "\033[91m\033[1m"  # Bold Red
        }
        reset = "\033[0m"
        
        color = color_map.get(alert.priority, "")
        symbol_str = f" [{alert.symbol}]" if alert.symbol else ""
        
        print(f"\n{color}{'='*60}{reset}")
        print(f"{color}🚨 ALERT: {alert.title}{symbol_str}{reset}")
        print(f"{color}{'='*60}{reset}")
        print(f"{alert.message}")
        print(f"Priority: {alert.priority.value.upper()}")
        print(f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        return True


class AlertManager:
    """Manages all alert channels and routing"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.channels: List[AlertChannel] = []
        self.alert_history: List[Alert] = []
        self.max_history = 1000
        
        self._setup_channels()
    
    def _setup_channels(self):
        """Initialize alert channels from config"""
        # Console channel (always add)
        self.channels.append(ConsoleChannel(enabled=True))
        
        # Telegram
        telegram_config = self.config.get("telegram", {})
        if telegram_config.get("enabled"):
            self.channels.append(TelegramChannel(
                bot_token=telegram_config.get("bot_token", ""),
                chat_id=telegram_config.get("chat_id", ""),
                enabled=True
            ))
        
        # Discord
        discord_config = self.config.get("discord", {})
        if discord_config.get("enabled"):
            self.channels.append(DiscordChannel(
                webhook_url=discord_config.get("webhook_url", ""),
                enabled=True
            ))
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to all enabled channels"""
        self.alert_history.append(alert)
        
        # Trim history
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
        
        results = []
        for channel in self.channels:
            try:
                result = await channel.send(alert)
                results.append(result)
            except Exception as e:
                logger.error(f"Channel {channel.name} failed: {e}")
                results.append(False)
        
        return any(results)
    
    def send_alert_sync(self, alert: Alert) -> bool:
        """Synchronous wrapper for sending alerts"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.send_alert(alert))
        except RuntimeError:
            # No event loop running
            return asyncio.run(self.send_alert(alert))
    
    # Convenience methods for common alerts
    def signal_alert(self, symbol: str, signal_type: str, price: float, confidence: float = None):
        """Alert for trading signal"""
        msg = f"Signal: {signal_type}\nPrice: ${price:,.2f}"
        if confidence:
            msg += f"\nConfidence: {confidence:.1%}"
        
        alert = Alert(
            alert_type=AlertType.SIGNAL,
            priority=AlertPriority.HIGH,
            title=f"Trading Signal: {signal_type}",
            message=msg,
            symbol=symbol,
            data={"signal_type": signal_type, "price": price, "confidence": confidence}
        )
        return self.send_alert_sync(alert)
    
    def position_alert(self, symbol: str, action: str, size: float, price: float, pnl: float = None):
        """Alert for position changes"""
        msg = f"Action: {action}\nSize: {size}\nPrice: ${price:,.2f}"
        if pnl is not None:
            emoji = "🟢" if pnl >= 0 else "🔴"
            msg += f"\nP&L: {emoji} ${pnl:,.2f}"
        
        alert = Alert(
            alert_type=AlertType.POSITION,
            priority=AlertPriority.MEDIUM,
            title=f"Position {action}: {symbol}",
            message=msg,
            symbol=symbol,
            data={"action": action, "size": size, "price": price, "pnl": pnl}
        )
        return self.send_alert_sync(alert)
    
    def risk_alert(self, title: str, message: str, symbol: str = None):
        """Alert for risk events"""
        alert = Alert(
            alert_type=AlertType.RISK,
            priority=AlertPriority.HIGH,
            title=title,
            message=message,
            symbol=symbol
        )
        return self.send_alert_sync(alert)
    
    def price_alert(self, symbol: str, price: float, condition: str):
        """Alert for price thresholds"""
        alert = Alert(
            alert_type=AlertType.PRICE,
            priority=AlertPriority.MEDIUM,
            title=f"Price Alert: {symbol}",
            message=f"Price ${price:,.2f} triggered condition: {condition}",
            symbol=symbol,
            data={"price": price, "condition": condition}
        )
        return self.send_alert_sync(alert)
    
    def system_alert(self, title: str, message: str, priority: AlertPriority = AlertPriority.LOW):
        """Alert for system events"""
        alert = Alert(
            alert_type=AlertType.SYSTEM,
            priority=priority,
            title=title,
            message=message
        )
        return self.send_alert_sync(alert)
    
    def error_alert(self, title: str, message: str, error_details: str = None):
        """Alert for errors"""
        full_msg = message
        if error_details:
            full_msg += f"\n\nDetails: {error_details}"
        
        alert = Alert(
            alert_type=AlertType.ERROR,
            priority=AlertPriority.CRITICAL,
            title=title,
            message=full_msg
        )
        return self.send_alert_sync(alert)


class ScheduledTask:
    """Represents a scheduled trading task"""
    
    def __init__(self, name: str, schedule: str, task_type: str, 
                 params: Dict = None, enabled: bool = True):
        self.name = name
        self.schedule = schedule  # Cron expression or "every_X_min"
        self.task_type = task_type
        self.params = params or {}
        self.enabled = enabled
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "schedule": self.schedule,
            "task_type": self.task_type,
            "params": self.params,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count
        }


class Scheduler:
    """Task scheduler for automated trading"""
    
    def __init__(self, alert_manager: AlertManager = None):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.alert_manager = alert_manager
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: Dict[str, Callable] = {}
    
    def register_callback(self, task_type: str, callback: Callable):
        """Register a handler for a task type"""
        self._callbacks[task_type] = callback
    
    def add_task(self, task: ScheduledTask) -> bool:
        """Add a scheduled task"""
        self.tasks[task.name] = task
        self._calculate_next_run(task)
        logger.info(f"Added scheduled task: {task.name}")
        return True
    
    def remove_task(self, name: str) -> bool:
        """Remove a scheduled task"""
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"Removed scheduled task: {name}")
            return True
        return False
    
    def _calculate_next_run(self, task: ScheduledTask):
        """Calculate next run time for a task"""
        now = datetime.now()
        
        if task.schedule.startswith("every_"):
            # Parse "every_X_min" or "every_X_hour"
            parts = task.schedule.split("_")
            if len(parts) >= 3:
                value = int(parts[1])
                unit = parts[2]
                
                if unit.startswith("min"):
                    delta = timedelta(minutes=value)
                elif unit.startswith("hour"):
                    delta = timedelta(hours=value)
                else:
                    delta = timedelta(minutes=15)  # Default
                
                if task.last_run:
                    task.next_run = task.last_run + delta
                else:
                    task.next_run = now + timedelta(seconds=10)  # First run soon
        else:
            # For now, treat unknown schedules as 15 min intervals
            task.next_run = now + timedelta(minutes=15)
    
    def _should_run(self, task: ScheduledTask) -> bool:
        """Check if task should run now"""
        if not task.enabled:
            return False
        if task.next_run is None:
            return False
        return datetime.now() >= task.next_run
    
    def _execute_task(self, task: ScheduledTask):
        """Execute a task"""
        logger.info(f"Executing task: {task.name}")
        
        try:
            callback = self._callbacks.get(task.task_type)
            if callback:
                callback(task.params)
                task.run_count += 1
                
                if self.alert_manager:
                    self.alert_manager.system_alert(
                        f"Task Completed: {task.name}",
                        f"Task type: {task.task_type}\nRun count: {task.run_count}",
                        AlertPriority.LOW
                    )
            else:
                logger.warning(f"No callback registered for task type: {task.task_type}")
                
        except Exception as e:
            logger.error(f"Task {task.name} failed: {e}")
            task.error_count += 1
            
            if self.alert_manager:
                self.alert_manager.error_alert(
                    f"Task Failed: {task.name}",
                    f"Task type: {task.task_type}",
                    str(e)
                )
        
        task.last_run = datetime.now()
        self._calculate_next_run(task)
    
    def _run_loop(self):
        """Main scheduler loop"""
        logger.info("Scheduler started")
        
        while self.running:
            for task in self.tasks.values():
                if self._should_run(task):
                    self._execute_task(task)
            
            time.sleep(10)  # Check every 10 seconds
        
        logger.info("Scheduler stopped")
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        if self.alert_manager:
            self.alert_manager.system_alert(
                "Scheduler Started",
                f"Active tasks: {len(self.tasks)}",
                AlertPriority.LOW
            )
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def get_status(self) -> Dict:
        """Get scheduler status"""
        return {
            "running": self.running,
            "task_count": len(self.tasks),
            "tasks": {name: task.to_dict() for name, task in self.tasks.items()}
        }


class PerformanceMonitor:
    """Monitors trading performance metrics"""
    
    def __init__(self, alert_manager: AlertManager = None):
        self.alert_manager = alert_manager
        self.daily_stats = {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "pnl": 0.0,
            "volume": 0.0
        }
        self.last_reset = datetime.now().date()
        self.price_cache: Dict[str, List[Dict]] = {}  # symbol -> price history
    
    def record_trade(self, symbol: str, side: str, size: float, 
                     price: float, pnl: float = None):
        """Record a trade for statistics"""
        self._check_reset()
        
        self.daily_stats["trades"] += 1
        self.daily_stats["volume"] += size * price
        
        if pnl is not None:
            self.daily_stats["pnl"] += pnl
            if pnl >= 0:
                self.daily_stats["wins"] += 1
            else:
                self.daily_stats["losses"] += 1
    
    def _check_reset(self):
        """Reset daily stats if it's a new day"""
        today = datetime.now().date()
        if today != self.last_reset:
            # Send summary before reset
            if self.alert_manager:
                self._send_daily_summary()
            
            self.daily_stats = {
                "trades": 0,
                "wins": 0,
                "losses": 0,
                "pnl": 0.0,
                "volume": 0.0
            }
            self.last_reset = today
    
    def _send_daily_summary(self):
        """Send daily performance summary"""
        stats = self.daily_stats
        win_rate = (stats["wins"] / stats["trades"] * 100) if stats["trades"] > 0 else 0
        
        pnl_emoji = "🟢" if stats["pnl"] >= 0 else "🔴"
        
        message = f"""Daily Trading Summary ({self.last_reset})

Trades: {stats['trades']}
Wins: {stats['wins']} | Losses: {stats['losses']}
Win Rate: {win_rate:.1f}%

P&L: {pnl_emoji} ${stats['pnl']:,.2f}
Volume: ${stats['volume']:,.2f}"""
        
        self.alert_manager.system_alert(
            "Daily Performance Summary",
            message,
            AlertPriority.LOW
        )
    
    def update_price(self, symbol: str, price: float):
        """Update price cache for monitoring"""
        if symbol not in self.price_cache:
            self.price_cache[symbol] = []
        
        self.price_cache[symbol].append({
            "price": price,
            "time": datetime.now()
        })
        
        # Keep last 1000 prices
        if len(self.price_cache[symbol]) > 1000:
            self.price_cache[symbol] = self.price_cache[symbol][-1000:]
    
    def get_stats(self) -> Dict:
        """Get current performance stats"""
        self._check_reset()
        
        stats = self.daily_stats.copy()
        stats["win_rate"] = (stats["wins"] / stats["trades"] * 100) if stats["trades"] > 0 else 0
        stats["date"] = self.last_reset.isoformat()
        
        return stats


# Export all classes
__all__ = [
    'AlertType', 'AlertPriority', 'Alert',
    'AlertChannel', 'TelegramChannel', 'DiscordChannel', 'ConsoleChannel',
    'AlertManager', 'ScheduledTask', 'Scheduler', 'PerformanceMonitor'
]