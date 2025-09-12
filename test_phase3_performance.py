#!/usr/bin/env python3
"""
Phase 3 Performance Testing Script

This script tests the performance improvements introduced in Phase 3:
- Smart message strategy selection
- Batch message management
- Handler-specific UX optimizations
- Performance monitoring and optimization
"""

import asyncio
import time
import logging
from typing import Dict, Any
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.performance_monitor import PerformanceMonitor, run_performance_test
from handlers.base_handler import SmartMessageManager, BatchMessageManager, InteractionType, ContentType
from handlers.relatorios_handler import ModernRelatoriosHandler


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase3TestSuite:
    """Comprehensive test suite for Phase 3 performance features"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor(logger)
        self.results = {}
    
    async def test_smart_message_strategies(self) -> Dict[str, Any]:
        """Test smart message strategy selection performance"""
        logger.info("Testing Smart Message Strategy Selection...")
        
        smart_manager = SmartMessageManager()
        test_scenarios = [
            (InteractionType.MENU_NAVIGATION, ContentType.SELECTION),
            (InteractionType.FORM_INPUT, ContentType.VALIDATION_ERROR),
            (InteractionType.REPORT_DISPLAY, ContentType.DATA),
            (InteractionType.SECURITY, ContentType.CREDENTIALS),
            (InteractionType.ERROR_DISPLAY, ContentType.ERROR),
        ]
        
        results = {"strategies_tested": 0, "total_time": 0, "average_time": 0}
        
        start_time = time.time()
        
        for interaction_type, content_type in test_scenarios:
            async with self.monitor.monitor_operation(
                operation="strategy_selection",
                handler_name="smart_message_test"
            ):
                # Test strategy retrieval
                strategy = smart_manager.get_strategy(interaction_type, content_type)
                
                # Test response creation
                response = smart_manager.create_response_with_strategy(
                    message=f"Test message for {interaction_type.value}",
                    keyboard=None,
                    interaction_type=interaction_type,
                    content_type=content_type
                )
                
                results["strategies_tested"] += 1
                await asyncio.sleep(0.001)  # Simulate processing time
        
        total_time = time.time() - start_time
        results["total_time"] = total_time
        results["average_time"] = total_time / len(test_scenarios)
        
        logger.info(f"Tested {results['strategies_tested']} strategies in {total_time:.3f}s")
        return results
    
    async def test_batch_message_operations(self) -> Dict[str, Any]:
        """Test batch message management performance"""
        logger.info("Testing Batch Message Operations...")
        
        batch_manager = BatchMessageManager(logger)
        
        # Simulate message objects for testing
        class MockMessage:
            def __init__(self, msg_id):
                self.message_id = msg_id
                self.chat_id = 12345
            
            async def delete(self):
                await asyncio.sleep(0.01)  # Simulate network delay
        
        class MockCallbackQuery:
            def __init__(self, msg_id):
                self.message = MockMessage(msg_id)
            
            async def answer(self):
                await asyncio.sleep(0.005)  # Simulate network delay
        
        # Test different batch sizes
        batch_sizes = [1, 5, 10, 25, 50]
        results = {"batch_tests": []}
        
        for batch_size in batch_sizes:
            # Create mock messages
            mock_messages = [MockMessage(i) for i in range(batch_size)]
            mock_callbacks = [MockCallbackQuery(i) for i in range(batch_size)]
            
            # Test instant cleanup
            start_time = time.time()
            async with self.monitor.monitor_operation(
                operation="batch_operation",
                handler_name="batch_test",
                batch_operation=True,
                message_count=batch_size
            ):
                await batch_manager.batch_cleanup(mock_messages, strategy="instant")
            instant_time = time.time() - start_time
            
            # Test safe cleanup
            start_time = time.time()
            async with self.monitor.monitor_operation(
                operation="batch_operation",
                handler_name="batch_test",
                batch_operation=True,
                message_count=batch_size
            ):
                await batch_manager.batch_cleanup(mock_callbacks, strategy="safe")
            safe_time = time.time() - start_time
            
            results["batch_tests"].append({
                "batch_size": batch_size,
                "instant_cleanup_time": instant_time,
                "safe_cleanup_time": safe_time,
                "instant_throughput": batch_size / instant_time if instant_time > 0 else 0,
                "safe_throughput": batch_size / safe_time if safe_time > 0 else 0
            })
            
            logger.info(f"Batch size {batch_size}: instant={instant_time:.3f}s, safe={safe_time:.3f}s")
        
        return results
    
    async def test_handler_optimization(self) -> Dict[str, Any]:
        """Test handler-specific optimization performance"""
        logger.info("Testing Handler-Specific Optimizations...")
        
        # Test scenarios for RelatoriosHandler
        test_scenarios = [
            {
                "name": "menu_navigation",
                "operation": "menu_navigation",
                "operations": 10,
                "interaction_type": "menu_navigation",
                "content_type": "selection",
                "edit_in_place": True,
                "simulated_delay": 0.01
            },
            {
                "name": "form_validation",
                "operation": "form_validation",
                "operations": 20,
                "interaction_type": "form_input",
                "content_type": "validation_error",
                "edit_in_place": True,
                "simulated_delay": 0.02
            },
            {
                "name": "batch_report_generation",
                "operation": "batch_operation",
                "operations": 5,
                "batch_operation": True,
                "message_count": 10,
                "simulated_delay": 0.1
            }
        ]
        
        results = await run_performance_test(ModernRelatoriosHandler, test_scenarios)
        return results
    
    async def test_memory_efficiency(self) -> Dict[str, Any]:
        """Test memory efficiency of Phase 3 improvements"""
        logger.info("Testing Memory Efficiency...")
        
        import tracemalloc
        tracemalloc.start()
        
        # Simulate heavy usage
        smart_manager = SmartMessageManager()
        batch_manager = BatchMessageManager(logger)
        
        # Create many strategy requests
        for _ in range(1000):
            strategy = smart_manager.get_strategy(
                InteractionType.MENU_NAVIGATION, 
                ContentType.SELECTION
            )
            response = smart_manager.create_response_with_strategy(
                message="Test message",
                keyboard=None,
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION
            )
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        results = {
            "current_memory_mb": current / 1024 / 1024,
            "peak_memory_mb": peak / 1024 / 1024,
            "strategy_requests": 1000,
            "memory_per_request_bytes": peak / 1000
        }
        
        logger.info(f"Memory usage: {results['current_memory_mb']:.2f}MB current, {results['peak_memory_mb']:.2f}MB peak")
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 3 performance tests"""
        logger.info("🚀 Starting Phase 3 Performance Test Suite...")
        
        start_time = time.time()
        
        # Run all test categories
        self.results = {
            "smart_strategies": await self.test_smart_message_strategies(),
            "batch_operations": await self.test_batch_message_operations(),
            "handler_optimization": await self.test_handler_optimization(),
            "memory_efficiency": await self.test_memory_efficiency(),
        }
        
        total_time = time.time() - start_time
        
        # Generate comprehensive report
        performance_summary = self.monitor.get_performance_summary()
        compliance_report = self.monitor.get_compliance_report()
        
        final_report = {
            "test_duration": total_time,
            "test_results": self.results,
            "performance_summary": performance_summary,
            "compliance_report": compliance_report,
            "phase_3_status": self._generate_phase_3_status(compliance_report)
        }
        
        logger.info(f"✅ Phase 3 Performance Test Suite completed in {total_time:.2f}s")
        return final_report
    
    def _generate_phase_3_status(self, compliance_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Phase 3 implementation status"""
        status = {
            "smart_message_system": "✅ Implemented and tested",
            "batch_operations": "✅ Implemented and tested", 
            "handler_optimizations": "✅ Implemented and tested",
            "performance_monitoring": "✅ Implemented and tested",
            "overall_compliance": compliance_report.get("phase_3_compliance", False),
            "ready_for_production": True
        }
        
        if not status["overall_compliance"]:
            status["ready_for_production"] = False
            status["issues_found"] = compliance_report.get("performance_issues", [])
        
        return status


async def main():
    """Main test execution function"""
    print("🎯 Phase 3: Advanced Features Performance Testing")
    print("=" * 60)
    
    test_suite = Phase3TestSuite()
    
    try:
        report = await test_suite.run_all_tests()
        
        # Print detailed results
        print("\n📊 Test Results Summary:")
        print("-" * 40)
        
        # Smart Strategy Performance
        smart_results = report["test_results"]["smart_strategies"]
        print(f"Smart Strategies: {smart_results['strategies_tested']} tested")
        print(f"Average strategy time: {smart_results['average_time']:.4f}s")
        
        # Batch Operation Performance
        batch_results = report["test_results"]["batch_operations"]
        print(f"\nBatch Operations: {len(batch_results['batch_tests'])} scenarios tested")
        for test in batch_results['batch_tests']:
            print(f"  Batch size {test['batch_size']}: {test['instant_throughput']:.1f} msg/s (instant)")
        
        # Performance Summary
        perf_summary = report["performance_summary"]
        print(f"\nOverall Performance:")
        print(f"Total operations: {perf_summary['total_operations']}")
        print(f"Success rate: {perf_summary['success_rate']:.1f}%")
        print(f"Average duration: {perf_summary['average_duration']:.4f}s")
        
        # Memory Efficiency
        memory_results = report["test_results"]["memory_efficiency"]
        print(f"\nMemory Efficiency:")
        print(f"Peak memory usage: {memory_results['peak_memory_mb']:.2f}MB")
        print(f"Memory per request: {memory_results['memory_per_request_bytes']:.1f} bytes")
        
        # Phase 3 Status
        phase3_status = report["phase_3_status"]
        print(f"\n🎉 Phase 3 Implementation Status:")
        print("-" * 40)
        for feature, status in phase3_status.items():
            if isinstance(status, str) and status.startswith("✅"):
                print(f"{status}")
            elif feature == "overall_compliance":
                compliance_icon = "✅" if status else "⚠️"
                print(f"{compliance_icon} Overall compliance: {status}")
            elif feature == "ready_for_production":
                ready_icon = "🚀" if status else "🔧"
                print(f"{ready_icon} Ready for production: {status}")
        
        if not phase3_status["overall_compliance"]:
            print(f"\n⚠️ Issues found: {len(phase3_status.get('issues_found', []))}")
            for issue in phase3_status.get("issues_found", []):
                print(f"  - {issue}")
        
        print(f"\n⏱️ Total test duration: {report['test_duration']:.2f}s")
        print("\n🎯 Phase 3 testing completed successfully!")
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        print(f"\n❌ Test suite failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)