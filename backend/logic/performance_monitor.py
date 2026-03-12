"""
Performance Monitoring and Optimization System
Enterprise-grade monitoring with real-time metrics, optimization, and alerting
"""

import json
import os
import logging
import time
import threading
import psutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import queue

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemResource:
    """System resource usage"""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_usage_percent: float
    network_io: Dict[str, int] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Alert:
    """Performance alert"""
    severity: str  # "info", "warning", "critical"
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


class MetricsCollector:
    """Collects and aggregates performance metrics"""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.metrics = defaultdict(lambda: deque(maxlen=max_history))
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.timers = defaultdict(list)
        self.histograms = defaultdict(lambda: deque(maxlen=1000))
        self.lock = threading.Lock()
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            self.counters[name] += value
            metric = PerformanceMetric(
                name=name,
                value=self.counters[name],
                unit="count",
                timestamp=datetime.now(),
                tags=tags or {}
            )
            self.metrics[name].append(metric)
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric"""
        with self.lock:
            self.gauges[name] = value
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit="gauge",
                timestamp=datetime.now(),
                tags=tags or {}
            )
            self.metrics[name].append(metric)
    
    def record_timer(self, name: str, duration: float, tags: Dict[str, str] = None):
        """Record a timer metric"""
        with self.lock:
            self.timers[name].append(duration)
            
            # Keep only recent values
            if len(self.timers[name]) > 1000:
                self.timers[name] = self.timers[name][-1000:]
            
            metric = PerformanceMetric(
                name=name,
                value=duration,
                unit="seconds",
                timestamp=datetime.now(),
                tags=tags or {}
            )
            self.metrics[name].append(metric)
            
            # Update histogram
            self.histograms[name].append(duration)
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram metric"""
        with self.lock:
            self.histograms[name].append(value)
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit="histogram",
                timestamp=datetime.now(),
                tags=tags or {}
            )
            self.metrics[name].append(metric)
    
    def get_metric_summary(self, name: str, minutes: int = 5) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        with self.lock:
            if name not in self.metrics:
                return {}
            
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            recent_metrics = [
                m for m in self.metrics[name] 
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {}
            
            values = [m.value for m in recent_metrics]
            
            summary = {
                "name": name,
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": np.mean(values),
                "median": np.median(values),
                "std": np.std(values),
                "p95": np.percentile(values, 95),
                "p99": np.percentile(values, 99),
                "unit": recent_metrics[0].unit,
                "latest": recent_metrics[-1].value,
                "latest_timestamp": recent_metrics[-1].timestamp.isoformat()
            }
            
            return summary
    
    def get_all_summaries(self, minutes: int = 5) -> Dict[str, Dict[str, Any]]:
        """Get summaries for all metrics"""
        summaries = {}
        
        with self.lock:
            for name in self.metrics:
                summary = self.get_metric_summary(name, minutes)
                if summary:
                    summaries[name] = summary
        
        return summaries


class ResourceMonitor:
    """Monitor system resources"""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.running = False
        self.thread = None
        self.resources = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    def start(self):
        """Start resource monitoring"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Resource monitoring started")
    
    def stop(self):
        """Stop resource monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                resource = self._collect_resources()
                
                with self.lock:
                    self.resources.append(resource)
                
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                time.sleep(self.interval)
    
    def _collect_resources(self) -> SystemResource:
        """Collect current system resources"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_mb = memory.used / 1024 / 1024
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        
        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        return SystemResource(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_mb=memory_mb,
            disk_usage_percent=disk_usage_percent,
            network_io=network_io
        )
    
    def get_current_resources(self) -> Optional[SystemResource]:
        """Get current resource usage"""
        with self.lock:
            if self.resources:
                return self.resources[-1]
        return None
    
    def get_resource_history(self, minutes: int = 5) -> List[SystemResource]:
        """Get resource usage history"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            return [
                r for r in self.resources 
                if r.timestamp >= cutoff_time
            ]
    
    def get_resource_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """Get resource usage summary"""
        history = self.get_resource_history(minutes)
        
        if not history:
            return {}
        
        cpu_values = [r.cpu_percent for r in history]
        memory_values = [r.memory_percent for r in history]
        disk_values = [r.disk_usage_percent for r in history]
        
        return {
            "cpu": {
                "current": cpu_values[-1] if cpu_values else 0,
                "mean": np.mean(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
                "min": min(cpu_values) if cpu_values else 0
            },
            "memory": {
                "current": memory_values[-1] if memory_values else 0,
                "mean": np.mean(memory_values) if memory_values else 0,
                "max": max(memory_values) if memory_values else 0,
                "min": min(memory_values) if memory_values else 0,
                "current_mb": history[-1].memory_mb if history else 0
            },
            "disk": {
                "current": disk_values[-1] if disk_values else 0,
                "mean": np.mean(disk_values) if disk_values else 0
            },
            "samples": len(history)
        }


class AlertManager:
    """Manage performance alerts"""
    
    def __init__(self):
        self.alerts = deque(maxlen=1000)
        self.rules = {}
        self.handlers = []
        self.lock = threading.Lock()
    
    def add_rule(self, name: str, metric_name: str, threshold: float, 
                 operator: str = "gt", severity: str = "warning", 
                 duration_minutes: int = 5):
        """Add an alert rule"""
        self.rules[name] = {
            "metric_name": metric_name,
            "threshold": threshold,
            "operator": operator,
            "severity": severity,
            "duration_minutes": duration_minutes,
            "triggered_time": None
        }
    
    def add_handler(self, handler: Callable[[Alert], None]):
        """Add alert handler"""
        self.handlers.append(handler)
    
    def check_alerts(self, metrics_collector: MetricsCollector):
        """Check metrics against alert rules"""
        current_time = datetime.now()
        
        for rule_name, rule in self.rules.items():
            metric_name = rule["metric_name"]
            
            # Get latest metric value
            summary = metrics_collector.get_metric_summary(metric_name, minutes=1)
            if not summary:
                continue
            
            current_value = summary["latest"]
            threshold = rule["threshold"]
            operator = rule["operator"]
            
            # Check if alert condition is met
            triggered = False
            if operator == "gt" and current_value > threshold:
                triggered = True
            elif operator == "lt" and current_value < threshold:
                triggered = True
            elif operator == "eq" and current_value == threshold:
                triggered = True
            elif operator == "ne" and current_value != threshold:
                triggered = True
            
            if triggered:
                if rule["triggered_time"] is None:
                    # First time triggered
                    rule["triggered_time"] = current_time
                elif (current_time - rule["triggered_time"]).total_seconds() >= rule["duration_minutes"] * 60:
                    # Alert should fire
                    self._fire_alert(rule_name, rule, current_value)
                    rule["triggered_time"] = None  # Reset to avoid repeated alerts
            else:
                rule["triggered_time"] = None  # Reset if condition no longer met
    
    def _fire_alert(self, rule_name: str, rule: Dict[str, Any], current_value: float):
        """Fire an alert"""
        alert = Alert(
            severity=rule["severity"],
            message=f"Alert: {rule_name} - {rule['metric_name']} is {current_value:.2f} (threshold: {rule['threshold']})",
            metric_name=rule["metric_name"],
            current_value=current_value,
            threshold=rule["threshold"]
        )
        
        with self.lock:
            self.alerts.append(alert)
        
        # Call handlers
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
        
        logger.warning(f"Alert fired: {alert.message}")
    
    def get_active_alerts(self, hours: int = 24) -> List[Alert]:
        """Get active alerts"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            return [a for a in self.alerts if a.timestamp >= cutoff_time and not a.resolved]


class PerformanceOptimizer:
    """Optimize system performance based on metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.optimization_rules = []
        self.optimization_history = deque(maxlen=100)
    
    def add_optimization_rule(self, name: str, condition: Callable[[Dict[str, Any]], bool], 
                            action: Callable[[], None], description: str):
        """Add optimization rule"""
        self.optimization_rules.append({
            "name": name,
            "condition": condition,
            "action": action,
            "description": description,
            "last_triggered": None
        })
    
    def check_optimizations(self):
        """Check and apply optimizations"""
        summaries = self.metrics.get_all_summaries(minutes=5)
        
        for rule in self.optimization_rules:
            try:
                if rule["condition"](summaries):
                    if (rule["last_triggered"] is None or 
                        (datetime.now() - rule["last_triggered"]).total_seconds() > 300):  # 5 min cooldown
                        
                        rule["action"]()
                        rule["last_triggered"] = datetime.now()
                        
                        self.optimization_history.append({
                            "name": rule["name"],
                            "description": rule["description"],
                            "timestamp": datetime.now()
                        })
                        
                        logger.info(f"Optimization applied: {rule['name']}")
                        
            except Exception as e:
                logger.error(f"Optimization rule error ({rule['name']}): {e}")


class PerformanceMonitor:
    """Main performance monitoring system"""
    
    def __init__(self, data_dir: str, config: Dict[str, Any] = None):
        self.data_dir = data_dir
        self.config = config or {}
        
        # Initialize components
        self.metrics_collector = MetricsCollector(
            max_history=self.config.get("max_history", 10000)
        )
        self.resource_monitor = ResourceMonitor(
            interval=self.config.get("resource_interval", 1.0)
        )
        self.alert_manager = AlertManager()
        self.optimizer = PerformanceOptimizer(self.metrics_collector)
        
        # Database for persistence
        self.db_path = os.path.join(data_dir, "performance_monitor.db")
        self._init_database()
        
        # Monitoring state
        self.running = False
        self.monitor_thread = None
        
        # Setup default alert rules
        self._setup_default_alerts()
        
        # Setup default optimization rules
        self._setup_default_optimizations()
        
        logger.info("PerformanceMonitor initialized")
    
    def _init_database(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                value REAL,
                unit TEXT,
                timestamp DATETIME,
                tags TEXT,
                metadata TEXT
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                severity TEXT,
                message TEXT,
                metric_name TEXT,
                current_value REAL,
                threshold REAL,
                timestamp DATETIME,
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Optimization history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                timestamp DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _setup_default_alerts(self):
        """Setup default alert rules"""
        # CPU usage alert
        self.alert_manager.add_rule(
            name="high_cpu",
            metric_name="cpu_usage",
            threshold=80.0,
            operator="gt",
            severity="warning",
            duration_minutes=5
        )
        
        # Memory usage alert
        self.alert_manager.add_rule(
            name="high_memory",
            metric_name="memory_usage",
            threshold=85.0,
            operator="gt",
            severity="critical",
            duration_minutes=3
        )
        
        # Response time alert
        self.alert_manager.add_rule(
            name="slow_response",
            metric_name="question_generation_time",
            threshold=2.0,
            operator="gt",
            severity="warning",
            duration_minutes=2
        )
        
        # Error rate alert
        self.alert_manager.add_rule(
            name="high_error_rate",
            metric_name="error_rate",
            threshold=0.05,
            operator="gt",
            severity="critical",
            duration_minutes=1
        )
    
    def _setup_default_optimizations(self):
        """Setup default optimization rules"""
        # Clear cache if memory is high
        def clear_cache_condition(summaries):
            memory_summary = summaries.get("memory_usage", {})
            return memory_summary.get("current", 0) > 85.0
        
        def clear_cache_action():
            # This would clear various caches
            logger.info("Clearing caches due to high memory usage")
        
        self.optimizer.add_optimization_rule(
            name="clear_cache",
            condition=clear_cache_condition,
            action=clear_cache_action,
            description="Clear caches when memory usage is high"
        )
        
        # Reduce batch size if response time is high
        def reduce_batch_condition(summaries):
            response_summary = summaries.get("question_generation_time", {})
            return response_summary.get("mean", 0) > 1.5
        
        def reduce_batch_action():
            # This would reduce batch sizes for processing
            logger.info("Reducing batch sizes due to high response time")
        
        self.optimizer.add_optimization_rule(
            name="reduce_batch_size",
            condition=reduce_batch_condition,
            action=reduce_batch_action,
            description="Reduce batch sizes when response time is high"
        )
    
    def start(self):
        """Start performance monitoring"""
        if self.running:
            return
        
        self.running = True
        self.resource_monitor.start()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Performance monitoring started")
    
    def stop(self):
        """Stop performance monitoring"""
        self.running = False
        
        if self.resource_monitor:
            self.resource_monitor.stop()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect system resources
                resources = self.resource_monitor.get_current_resources()
                if resources:
                    self.metrics_collector.set_gauge("cpu_usage", resources.cpu_percent)
                    self.metrics_collector.set_gauge("memory_usage", resources.memory_percent)
                    self.metrics_collector.set_gauge("memory_mb", resources.memory_mb)
                    self.metrics_collector.set_gauge("disk_usage", resources.disk_usage_percent)
                
                # Check alerts
                self.alert_manager.check_alerts(self.metrics_collector)
                
                # Check optimizations
                self.optimizer.check_optimizations()
                
                # Persist metrics periodically
                if int(time.time()) % 60 == 0:  # Every minute
                    self._persist_metrics()
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(5)
    
    def _persist_metrics(self):
        """Persist metrics to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Persist recent metrics
            cutoff_time = datetime.now() - timedelta(minutes=5)
            
            for metric_name, metric_deque in self.metrics_collector.metrics.items():
                for metric in metric_deque:
                    if metric.timestamp >= cutoff_time:
                        cursor.execute('''
                            INSERT INTO metrics (name, value, unit, timestamp, tags, metadata)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            metric.name,
                            metric.value,
                            metric.unit,
                            metric.timestamp,
                            json.dumps(metric.tags),
                            json.dumps(metric.metadata)
                        ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to persist metrics: {e}")
    
    def record_question_generation(self, duration: float, success: bool, 
                                 question_source: str = "unknown"):
        """Record question generation metrics"""
        self.metrics_collector.record_timer("question_generation_time", duration, 
                                           {"source": question_source})
        
        if success:
            self.metrics_collector.increment_counter("questions_generated", 1.0,
                                                   {"source": question_source})
        else:
            self.metrics_collector.increment_counter("question_errors", 1.0,
                                                   {"source": question_source})
    
    def record_inference(self, duration: float, success: bool, 
                       candidates_count: int):
        """Record inference metrics"""
        self.metrics_collector.record_timer("inference_time", duration,
                                           {"candidates": str(candidates_count)})
        
        if success:
            self.metrics_collector.increment_counter("successful_inferences", 1.0)
        else:
            self.metrics_collector.increment_counter("failed_inferences", 1.0)
        
        self.metrics_collector.set_gauge("candidates_count", candidates_count)
    
    def record_learning(self, duration: float, songs_learned: int, 
                      quality_score: float):
        """Record learning metrics"""
        self.metrics_collector.record_timer("learning_time", duration)
        self.metrics_collector.increment_counter("songs_learned", songs_learned)
        self.metrics_collector.set_gauge("learning_quality", quality_score)
    
    def get_performance_report(self, minutes: int = 60) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        # Get metric summaries
        metric_summaries = self.metrics_collector.get_all_summaries(minutes)
        
        # Get resource summary
        resource_summary = self.resource_monitor.get_resource_summary(minutes)
        
        # Get active alerts
        active_alerts = self.alert_manager.get_active_alerts(hours=24)
        
        # Get optimization history
        recent_optimizations = [
            opt for opt in self.optimizer.optimization_history
            if (datetime.now() - opt["timestamp"]).total_seconds() <= minutes * 60
        ]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "period_minutes": minutes,
            "metrics": metric_summaries,
            "resources": resource_summary,
            "alerts": {
                "active_count": len(active_alerts),
                "active": [
                    {
                        "severity": alert.severity,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in active_alerts[-10:]  # Last 10 alerts
                ]
            },
            "optimizations": {
                "recent_count": len(recent_optimizations),
                "recent": [
                    {
                        "name": opt["name"],
                        "description": opt["description"],
                        "timestamp": opt["timestamp"].isoformat()
                    }
                    for opt in recent_optimizations[-5:]  # Last 5 optimizations
                ]
            },
            "system_health": self._calculate_system_health(metric_summaries, resource_summary)
        }
    
    def _calculate_system_health(self, metrics: Dict[str, Any], 
                               resources: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall system health score"""
        health_score = 100.0
        issues = []
        
        # Check CPU usage
        cpu_usage = resources.get("cpu", {}).get("current", 0)
        if cpu_usage > 90:
            health_score -= 20
            issues.append("Very high CPU usage")
        elif cpu_usage > 70:
            health_score -= 10
            issues.append("High CPU usage")
        
        # Check memory usage
        memory_usage = resources.get("memory", {}).get("current", 0)
        if memory_usage > 90:
            health_score -= 20
            issues.append("Very high memory usage")
        elif memory_usage > 80:
            health_score -= 10
            issues.append("High memory usage")
        
        # Check response times
        response_time = metrics.get("question_generation_time", {}).get("mean", 0)
        if response_time > 2.0:
            health_score -= 15
            issues.append("Slow response times")
        elif response_time > 1.0:
            health_score -= 5
            issues.append("Moderate response times")
        
        # Check error rates
        error_rate = 0.0
        total_requests = metrics.get("questions_generated", {}).get("count", 0)
        total_errors = metrics.get("question_errors", {}).get("count", 0)
        
        if total_requests > 0:
            error_rate = total_errors / total_requests
        
        if error_rate > 0.1:
            health_score -= 25
            issues.append("High error rate")
        elif error_rate > 0.05:
            health_score -= 10
            issues.append("Moderate error rate")
        
        # Determine health status
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 75:
            status = "good"
        elif health_score >= 60:
            status = "fair"
        elif health_score >= 40:
            status = "poor"
        else:
            status = "critical"
        
        return {
            "score": max(0, health_score),
            "status": status,
            "issues": issues
        }


# Global performance monitor instance
_global_monitor = None


def get_performance_monitor(data_dir: str = None) -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _global_monitor
    
    if _global_monitor is None:
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        _global_monitor = PerformanceMonitor(data_dir)
        _global_monitor.start()
    
    return _global_monitor


def record_performance(metric_type: str, **kwargs):
    """Convenience function to record performance metrics"""
    monitor = get_performance_monitor()
    
    if metric_type == "question_generation":
        monitor.record_question_generation(**kwargs)
    elif metric_type == "inference":
        monitor.record_inference(**kwargs)
    elif metric_type == "learning":
        monitor.record_learning(**kwargs)
    else:
        logger.warning(f"Unknown metric type: {metric_type}")


if __name__ == "__main__":
    # Test performance monitoring
    logging.basicConfig(level=logging.INFO)
    
    monitor = get_performance_monitor()
    
    # Simulate some metrics
    for i in range(10):
        record_performance("question_generation", 
                         duration=0.1 + (i % 3) * 0.05, 
                         success=i % 4 != 0,
                         question_source="graph")
        
        record_performance("inference",
                         duration=0.05 + (i % 2) * 0.02,
                         success=True,
                         candidates_count=10 + i)
        
        time.sleep(0.1)
    
    # Generate report
    report = monitor.get_performance_report(minutes=5)
    print(json.dumps(report, indent=2, default=str))
    
    monitor.stop()
