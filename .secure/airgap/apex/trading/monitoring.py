"""
Monitoring and Alerting System
Real-time monitoring and notifications for the Apex trading system.
"""

import logging
import json
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import time


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged,
            'metadata': self.metadata
        }


@dataclass
class Metric:
    """Metric data point"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict = field(default_factory=dict)


class AlertManager:
    """
    Manages alerts and notifications for the trading system.
    
    Features:
    - Alert generation and storage
    - Threshold-based alerts
    - Notification channels (console, file, webhook)
    - Alert acknowledgment
    """
    
    def __init__(self, storage_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.storage_path = storage_path
        self.handlers: List[Callable] = []
        
        # Thresholds
        self.thresholds: Dict[str, Dict] = {}
        
        # Alert counters
        self.alert_counts: Dict[AlertLevel, int] = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 0,
            AlertLevel.ERROR: 0,
            AlertLevel.CRITICAL: 0
        }
        
        if storage_path:
            self._load_alerts()
    
    def add_handler(self, handler: Callable):
        """Add an alert handler callback"""
        self.handlers.append(handler)
    
    def create_alert(self, level: AlertLevel, title: str, message: str,
                    metadata: Dict = None) -> Alert:
        """Create and dispatch a new alert"""
        alert_id = f"alert_{datetime.now().timestamp()}"
        
        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            metadata=metadata or {}
        )
        
        self.alerts.append(alert)
        self.alert_counts[level] += 1
        
        # Log the alert
        log_message = f"[{level.value.upper()}] {title}: {message}"
        if level == AlertLevel.CRITICAL:
            self.logger.critical(log_message)
        elif level == AlertLevel.ERROR:
            self.logger.error(log_message)
        elif level == AlertLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Dispatch to handlers
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler error: {e}")
        
        self._save_alerts()
        return alert
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                self._save_alerts()
                return True
        return False
    
    def clear_alert(self, alert_id: str) -> bool:
        """Clear/resolve an alert"""
        for i, alert in enumerate(self.alerts):
            if alert.id == alert_id:
                self.alert_history.append(alert)
                self.alerts.pop(i)
                self._save_alerts()
                return True
        return False
    
    def set_threshold(self, metric_name: str, warning: float = None,
                     critical: float = None, operator: str = 'greater'):
        """
        Set alert thresholds for a metric.
        
        Args:
            metric_name: Name of the metric
            warning: Warning threshold
            critical: Critical threshold
            operator: 'greater' or 'less' - whether to alert when metric is above or below threshold
        """
        self.thresholds[metric_name] = {
            'warning': warning,
            'critical': critical,
            'operator': operator
        }
    
    def check_threshold(self, metric_name: str, value: float) -> Optional[AlertLevel]:
        """Check if a metric value crosses any thresholds"""
        if metric_name not in self.thresholds:
            return None
        
        threshold = self.thresholds[metric_name]
        operator = threshold.get('operator', 'greater')
        
        if operator == 'greater':
            if threshold.get('critical') and value >= threshold['critical']:
                return AlertLevel.CRITICAL
            if threshold.get('warning') and value >= threshold['warning']:
                return AlertLevel.WARNING
        else:  # less
            if threshold.get('critical') and value <= threshold['critical']:
                return AlertLevel.CRITICAL
            if threshold.get('warning') and value <= threshold['warning']:
                return AlertLevel.WARNING
        
        return None
    
    def get_active_alerts(self, level: AlertLevel = None) -> List[Alert]:
        """Get active (unacknowledged) alerts"""
        alerts = [a for a in self.alerts if not a.acknowledged]
        if level:
            alerts = [a for a in alerts if a.level == level]
        return alerts
    
    def get_alert_summary(self) -> Dict:
        """Get summary of current alerts"""
        return {
            'active': len(self.get_active_alerts()),
            'total': len(self.alerts),
            'history': len(self.alert_history),
            'counts': {level.value: count for level, count in self.alert_counts.items()},
            'by_level': {
                'critical': len(self.get_active_alerts(AlertLevel.CRITICAL)),
                'error': len(self.get_active_alerts(AlertLevel.ERROR)),
                'warning': len(self.get_active_alerts(AlertLevel.WARNING)),
                'info': len(self.get_active_alerts(AlertLevel.INFO))
            }
        }
    
    def _save_alerts(self):
        """Save alerts to file"""
        if not self.storage_path:
            return
        
        try:
            data = {
                'active': [a.to_dict() for a in self.alerts],
                'history': [a.to_dict() for a in self.alert_history[-100:]]  # Keep last 100
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving alerts: {e}")
    
    def _load_alerts(self):
        """Load alerts from file"""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Note: In production, you'd properly reconstruct Alert objects
            self.logger.info(f"Loaded {len(data.get('active', []))} active alerts")
        except Exception as e:
            self.logger.error(f"Error loading alerts: {e}")


class MetricsCollector:
    """
    Collects and stores trading metrics.
    """
    
    def __init__(self, max_history: int = 10000):
        self.metrics: List[Metric] = []
        self.max_history = max_history
        self._lock = threading.Lock()
    
    def record(self, name: str, value: float, labels: Dict = None):
        """Record a metric"""
        with self._lock:
            metric = Metric(
                name=name,
                value=value,
                labels=labels or {}
            )
            self.metrics.append(metric)
            
            # Trim old metrics
            if len(self.metrics) > self.max_history:
                self.metrics = self.metrics[-self.max_history:]
    
    def get_latest(self, name: str) -> Optional[Metric]:
        """Get the latest value for a metric"""
        for metric in reversed(self.metrics):
            if metric.name == name:
                return metric
        return None
    
    def get_range(self, name: str, minutes: int = 60) -> List[Metric]:
        """Get metric values for the last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self.metrics if m.name == name and m.timestamp >= cutoff]
    
    def get_average(self, name: str, minutes: int = 60) -> Optional[float]:
        """Get average value for a metric over time period"""
        values = [m.value for m in self.get_range(name, minutes)]
        return sum(values) / len(values) if values else None
    
    def get_statistics(self) -> Dict:
        """Get statistics for all metrics"""
        stats = {}
        metric_names = set(m.name for m in self.metrics)
        
        for name in metric_names:
            values = [m.value for m in self.metrics if m.name == name]
            if values:
                stats[name] = {
                    'count': len(values),
                    'latest': values[-1],
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values)
                }
        
        return stats


class SystemMonitor:
    """
    Monitors system health and trading performance.
    """
    
    def __init__(self, alert_manager: AlertManager, metrics_collector: MetricsCollector):
        self.alert_manager = alert_manager
        self.metrics = metrics_collector
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._monitor_thread = None
        
        # Default thresholds
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self):
        """Setup default monitoring thresholds"""
        # Daily loss limit
        self.alert_manager.set_threshold('daily_loss_pct', warning=0.03, critical=0.05)
        
        # Drawdown
        self.alert_manager.set_threshold('drawdown_pct', warning=0.1, critical=0.2)
        
        # Position count
        self.alert_manager.set_threshold('open_positions', warning=5, critical=10)
        
        # API latency
        self.alert_manager.set_threshold('api_latency_ms', warning=1000, critical=5000)
    
    def start(self):
        """Start monitoring loop"""
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        self.logger.info("System monitor started")
    
    def stop(self):
        """Stop monitoring loop"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("System monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                self._check_metrics()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                time.sleep(60)
    
    def _check_metrics(self):
        """Check all metrics against thresholds"""
        stats = self.metrics.get_statistics()
        
        for name, data in stats.items():
            level = self.alert_manager.check_threshold(name, data['latest'])
            if level:
                self.alert_manager.create_alert(
                    level=level,
                    title=f"{name} Threshold Alert",
                    message=f"{name} is at {data['latest']:.4f}",
                    metadata={'metric': name, 'value': data['latest']}
                )
    
    def record_trade(self, symbol: str, side: str, amount: float, price: float, pnl: float = 0):
        """Record a trade execution"""
        self.metrics.record('trade_executed', 1, {'symbol': symbol, 'side': side})
        self.metrics.record('trade_volume', amount * price, {'symbol': symbol})
        if pnl != 0:
            self.metrics.record('trade_pnl', pnl, {'symbol': symbol})
    
    def record_position(self, symbol: str, size: float, unrealized_pnl: float):
        """Record position update"""
        self.metrics.record('position_size', size, {'symbol': symbol})
        self.metrics.record('unrealized_pnl', unrealized_pnl, {'symbol': symbol})
    
    def get_health_status(self) -> Dict:
        """Get overall system health status"""
        alert_summary = self.alert_manager.get_alert_summary()
        metrics_stats = self.metrics.get_statistics()
        
        # Determine health level
        if alert_summary['by_level']['critical'] > 0:
            health = 'critical'
        elif alert_summary['by_level']['error'] > 0:
            health = 'error'
        elif alert_summary['by_level']['warning'] > 0:
            health = 'warning'
        else:
            health = 'healthy'
        
        return {
            'status': health,
            'alerts': alert_summary,
            'metrics': metrics_stats,
            'timestamp': datetime.now().isoformat()
        }
