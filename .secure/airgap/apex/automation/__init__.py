# Automation module initialization
"""
Apex Trading System - Automation Module
Phase 5: Cron scheduling, alerts, and dashboard
"""

from .alerts import (
    AlertType, AlertPriority, Alert,
    AlertChannel, TelegramChannel, DiscordChannel, ConsoleChannel,
    AlertManager, ScheduledTask, Scheduler, PerformanceMonitor
)

from .dashboard import DashboardGenerator, DashboardServer

__all__ = [
    'AlertType', 'AlertPriority', 'Alert',
    'AlertChannel', 'TelegramChannel', 'DiscordChannel', 'ConsoleChannel',
    'AlertManager', 'ScheduledTask', 'Scheduler', 'PerformanceMonitor',
    'DashboardGenerator', 'DashboardServer'
]