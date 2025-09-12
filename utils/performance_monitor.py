"""
Performance monitoring and optimization utilities for Phase 3 UX compliance.

This module provides tools to measure and optimize message handling performance,
focusing on the new smart message system and batch operations.
"""

import time
import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from functools import wraps
from contextlib import asynccontextmanager
from telegram import Update
from telegram.ext import ContextTypes


@dataclass
class PerformanceMetric:
    """Performance metric data container"""
    operation: str
    duration: float
    timestamp: float
    handler_name: str
    interaction_type: Optional[str] = None
    content_type: Optional[str] = None
    message_count: int = 1
    edit_in_place: bool = False
    batch_operation: bool = False
    success: bool = True
    error_message: Optional[str] = None


class PerformanceMonitor:
    """Advanced performance monitoring for Phase 3 UX compliance"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.metrics: List[PerformanceMetric] = []
        self.thresholds = {
            "message_send": 1.0,      # 1 second for message sending
            "message_edit": 0.1,      # 100ms for message editing
            "batch_operation": 2.0,   # 2 seconds for batch operations
            "menu_navigation": 0.05,  # 50ms for menu updates
            "form_validation": 0.5,   # 500ms for form validation
        }
        self.optimization_suggestions: List[str] = []
    
    @asynccontextmanager
    async def monitor_operation(self, operation: str, handler_name: str, **kwargs):
        """Context manager for monitoring operation performance"""
        start_time = time.time()
        metric = PerformanceMetric(
            operation=operation,
            duration=0.0,
            timestamp=start_time,
            handler_name=handler_name,
            **kwargs
        )
        
        try:
            yield metric
            metric.success = True
        except Exception as e:
            metric.success = False
            metric.error_message = str(e)
            self.logger.error(f"Performance monitoring error in {operation}: {e}")
            raise
        finally:
            metric.duration = time.time() - start_time
            self.metrics.append(metric)
            await self._analyze_performance(metric)
    
    async def _analyze_performance(self, metric: PerformanceMetric):
        """Analyze performance and generate optimization suggestions"""
        threshold = self.thresholds.get(metric.operation, 1.0)
        
        if metric.duration > threshold:
            suggestion = await self._generate_optimization_suggestion(metric)
            if suggestion:
                self.optimization_suggestions.append(suggestion)
                self.logger.warning(f"Performance issue detected: {suggestion}")
    
    async def _generate_optimization_suggestion(self, metric: PerformanceMetric) -> Optional[str]:
        """Generate specific optimization suggestions based on performance data"""
        if metric.operation == "message_edit" and metric.duration > 0.1:
            return f"Edit-in-place operation in {metric.handler_name} took {metric.duration:.2f}s. Consider optimizing keyboard generation or message content."
        
        elif metric.operation == "batch_operation" and metric.duration > 2.0:
            return f"Batch operation in {metric.handler_name} took {metric.duration:.2f}s for {metric.message_count} messages. Consider parallelization or chunking."
        
        elif metric.operation == "menu_navigation" and metric.duration > 0.05:
            return f"Menu navigation in {metric.handler_name} took {metric.duration:.2f}s. Check for unnecessary database calls or complex keyboard generation."
        
        elif metric.operation == "message_send" and metric.duration > 1.0:
            return f"Message sending in {metric.handler_name} took {metric.duration:.2f}s. Check network conditions or message complexity."
        
        return None
    
    def performance_decorator(self, operation: str, handler_name: str = "unknown"):
        """Decorator for monitoring function performance"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                async with self.monitor_operation(operation, handler_name) as metric:
                    result = await func(*args, **kwargs)
                    return result
            return wrapper
        return decorator
    
    def get_performance_summary(self, handler_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary statistics"""
        filtered_metrics = self.metrics
        if handler_name:
            filtered_metrics = [m for m in self.metrics if m.handler_name == handler_name]
        
        if not filtered_metrics:
            return {"total_operations": 0}
        
        # Calculate statistics
        successful_metrics = [m for m in filtered_metrics if m.success]
        failed_metrics = [m for m in filtered_metrics if not m.success]
        
        durations = [m.duration for m in successful_metrics]
        
        summary = {
            "total_operations": len(filtered_metrics),
            "successful_operations": len(successful_metrics),
            "failed_operations": len(failed_metrics),
            "success_rate": len(successful_metrics) / len(filtered_metrics) * 100,
            "average_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "optimization_suggestions": self.optimization_suggestions[-5:],  # Last 5 suggestions
        }
        
        # Performance by operation type
        operations = {}
        for metric in successful_metrics:
            op = metric.operation
            if op not in operations:
                operations[op] = {"count": 0, "total_duration": 0, "avg_duration": 0}
            operations[op]["count"] += 1
            operations[op]["total_duration"] += metric.duration
        
        for op, data in operations.items():
            data["avg_duration"] = data["total_duration"] / data["count"]
        
        summary["operations"] = operations
        
        # UX compliance metrics
        edit_in_place_metrics = [m for m in successful_metrics if m.edit_in_place]
        batch_metrics = [m for m in successful_metrics if m.batch_operation]
        
        summary["ux_compliance"] = {
            "edit_in_place_operations": len(edit_in_place_metrics),
            "edit_in_place_avg_duration": sum(m.duration for m in edit_in_place_metrics) / len(edit_in_place_metrics) if edit_in_place_metrics else 0,
            "batch_operations": len(batch_metrics),
            "batch_avg_duration": sum(m.duration for m in batch_metrics) / len(batch_metrics) if batch_metrics else 0,
        }
        
        return summary
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate Phase 3 UX compliance report"""
        report = {
            "phase_3_compliance": True,
            "performance_issues": [],
            "optimization_opportunities": [],
            "recommendations": []
        }
        
        # Check edit-in-place performance
        edit_metrics = [m for m in self.metrics if m.edit_in_place and m.success]
        if edit_metrics:
            avg_edit_time = sum(m.duration for m in edit_metrics) / len(edit_metrics)
            if avg_edit_time > 0.1:
                report["performance_issues"].append(f"Edit-in-place operations averaging {avg_edit_time:.2f}s (target: <0.1s)")
                report["phase_3_compliance"] = False
        
        # Check batch operation efficiency
        batch_metrics = [m for m in self.metrics if m.batch_operation and m.success]
        if batch_metrics:
            avg_batch_time = sum(m.duration for m in batch_metrics) / len(batch_metrics)
            avg_message_count = sum(m.message_count for m in batch_metrics) / len(batch_metrics)
            efficiency = avg_message_count / avg_batch_time if avg_batch_time > 0 else 0
            
            if efficiency < 5:  # Less than 5 messages per second
                report["performance_issues"].append(f"Batch operations processing {efficiency:.1f} messages/second (target: >5 msg/s)")
                report["phase_3_compliance"] = False
        
        # Generate recommendations
        if not report["performance_issues"]:
            report["recommendations"].append("✅ All Phase 3 performance targets met!")
        else:
            report["recommendations"].extend([
                "🔧 Consider implementing async parallelization for batch operations",
                "⚡ Cache frequently generated keyboards and messages",
                "📊 Monitor database query performance in handlers",
                "🎯 Use smart message strategies consistently across all handlers"
            ])
        
        return report
    
    def clear_metrics(self):
        """Clear collected metrics (useful for testing)"""
        self.metrics.clear()
        self.optimization_suggestions.clear()


# Global performance monitor instance
_global_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return _global_monitor


def monitor_handler_performance(operation: str, handler_name: str = "unknown"):
    """Decorator for monitoring handler performance"""
    return _global_monitor.performance_decorator(operation, handler_name)


async def run_performance_test(handler_class, test_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run performance tests on a handler with various scenarios"""
    monitor = PerformanceMonitor()
    handler = handler_class()
    results = []
    
    for scenario in test_scenarios:
        scenario_name = scenario.get("name", "unnamed")
        operation_count = scenario.get("operations", 1)
        
        # Simulate the scenario
        start_time = time.time()
        
        for i in range(operation_count):
            async with monitor.monitor_operation(
                operation=scenario.get("operation", "test"),
                handler_name=handler.name,
                interaction_type=scenario.get("interaction_type"),
                content_type=scenario.get("content_type"),
                edit_in_place=scenario.get("edit_in_place", False),
                batch_operation=scenario.get("batch_operation", False)
            ) as metric:
                # Simulate operation delay
                await asyncio.sleep(scenario.get("simulated_delay", 0.01))
                metric.message_count = scenario.get("message_count", 1)
        
        scenario_duration = time.time() - start_time
        results.append({
            "scenario": scenario_name,
            "duration": scenario_duration,
            "operations": operation_count,
            "throughput": operation_count / scenario_duration
        })
    
    return {
        "test_results": results,
        "performance_summary": monitor.get_performance_summary(),
        "compliance_report": monitor.get_compliance_report()
    }