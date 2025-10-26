"""
Load testing utility for expedition system performance validation.
Tests concurrent operations and system stability under load.
"""

import asyncio
import concurrent.futures
import logging
import random
import statistics
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from threading import Lock

from core.modern_service_container import get_expedition_service, get_export_service, get_brambler_service
from models.expedition import ExpeditionCreateRequest, ExpeditionItemRequest, ItemConsumptionRequest, ExpeditionStatus


class LoadTestResults:
    """Container for load test results and statistics."""

    def __init__(self):
        self.start_time = time.time()
        self.end_time = None
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self._lock = Lock()

    def add_result(self, success: bool, response_time: float, error: Optional[str] = None):
        """Add a test result."""
        with self._lock:
            self.total_operations += 1
            if success:
                self.successful_operations += 1
            else:
                self.failed_operations += 1
                if error:
                    self.errors.append(error)
            self.response_times.append(response_time)

    def finalize(self):
        """Finalize the test results."""
        self.end_time = time.time()

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary statistics."""
        if not self.response_times:
            return {"error": "No response times recorded"}

        duration = (self.end_time or time.time()) - self.start_time

        return {
            "duration_seconds": round(duration, 2),
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "success_rate": round((self.successful_operations / self.total_operations * 100), 2) if self.total_operations > 0 else 0,
            "operations_per_second": round(self.total_operations / duration, 2) if duration > 0 else 0,
            "response_time_stats": {
                "min_ms": round(min(self.response_times) * 1000, 2),
                "max_ms": round(max(self.response_times) * 1000, 2),
                "avg_ms": round(statistics.mean(self.response_times) * 1000, 2),
                "median_ms": round(statistics.median(self.response_times) * 1000, 2),
                "p95_ms": round(self._percentile(self.response_times, 95) * 1000, 2),
                "p99_ms": round(self._percentile(self.response_times, 99) * 1000, 2)
            },
            "error_summary": self._get_error_summary()
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile from sorted data."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * percentile / 100
        floor_k = int(k)
        ceil_k = floor_k + 1
        if ceil_k >= len(sorted_data):
            return sorted_data[-1]
        return sorted_data[floor_k] + (k - floor_k) * (sorted_data[ceil_k] - sorted_data[floor_k])

    def _get_error_summary(self) -> Dict[str, int]:
        """Get summary of errors by type."""
        error_counts = {}
        for error in self.errors:
            error_type = type(error).__name__ if hasattr(error, '__name__') else str(error)[:50]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        return error_counts


class ExpeditionLoadTester:
    """Load tester for expedition system operations."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.results = LoadTestResults()

    def _generate_test_expedition(self, index: int) -> ExpeditionCreateRequest:
        """Generate a test expedition request."""
        return ExpeditionCreateRequest(
            name=f"Load Test Expedition #{index}",
            owner_chat_id=random.randint(1000000, 9999999),
            deadline=datetime.now() + timedelta(days=random.randint(1, 30))
        )

    def _generate_test_consumption(self, expedition_item_id: int) -> ItemConsumptionRequest:
        """Generate a test consumption request."""
        return ItemConsumptionRequest(
            expedition_item_id=expedition_item_id,
            consumer_name=f"TestUser{random.randint(1, 100)}",
            pirate_name=f"Captain{random.randint(1, 100)}",
            quantity_consumed=random.randint(1, 5),
            unit_price=round(random.uniform(1.0, 50.0), 2)
        )

    def _execute_operation(self, operation_name: str, operation_func) -> None:
        """Execute a single operation and record results."""
        start_time = time.time()
        success = False
        error = None

        try:
            result = operation_func()
            success = result is not None
        except Exception as e:
            error = str(e)
            self.logger.debug(f"Operation {operation_name} failed: {e}")

        response_time = time.time() - start_time
        self.results.add_result(success, response_time, error)

    def test_expedition_creation(self, num_expeditions: int = 100) -> Dict[str, Any]:
        """Test concurrent expedition creation."""
        self.logger.info(f"Testing creation of {num_expeditions} expeditions...")

        expedition_service = get_expedition_service()

        def create_expedition(index: int):
            request = self._generate_test_expedition(index)
            return expedition_service.create_expedition(request)

        # Use ThreadPoolExecutor for concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(lambda i=i: self._execute_operation(f"create_expedition_{i}", lambda: create_expedition(i)))
                for i in range(num_expeditions)
            ]

            # Wait for all operations to complete
            concurrent.futures.wait(futures)

        return self.results.get_summary()

    def test_expedition_queries(self, num_queries: int = 500) -> Dict[str, Any]:
        """Test concurrent expedition queries."""
        self.logger.info(f"Testing {num_queries} concurrent queries...")

        expedition_service = get_expedition_service()

        query_functions = [
            lambda: expedition_service.get_all_expeditions(),
            lambda: expedition_service.get_active_expeditions(),
            lambda: expedition_service.get_overdue_expeditions(),
            lambda: expedition_service.get_expedition_dashboard_summary()
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for i in range(num_queries):
                query_func = random.choice(query_functions)
                future = executor.submit(
                    lambda f=query_func: self._execute_operation(f"query_{i}", f)
                )
                futures.append(future)

            # Wait for all operations to complete
            concurrent.futures.wait(futures)

        return self.results.get_summary()

    def test_export_operations(self, num_exports: int = 50) -> Dict[str, Any]:
        """Test concurrent export operations."""
        self.logger.info(f"Testing {num_exports} concurrent export operations...")

        export_service = get_export_service()

        export_functions = [
            lambda: export_service.export_expedition_data(),
            lambda: export_service.export_pirate_activity_report(),
            lambda: export_service.export_profit_loss_report()
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(num_exports):
                export_func = random.choice(export_functions)
                future = executor.submit(
                    lambda f=export_func: self._execute_operation(f"export_{i}", f)
                )
                futures.append(future)

            # Wait for all operations to complete
            concurrent.futures.wait(futures)

        return self.results.get_summary()

    def test_search_operations(self, num_searches: int = 200) -> Dict[str, Any]:
        """Test concurrent search operations."""
        self.logger.info(f"Testing {num_searches} concurrent search operations...")

        export_service = get_export_service()

        search_terms = ["test", "expedition", "load", "pirate", "captain"]
        statuses = ["active", "completed", "cancelled", None]

        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = []
            for i in range(num_searches):
                search_query = random.choice(search_terms) if random.random() > 0.3 else None
                status_filter = random.choice(statuses)

                future = executor.submit(
                    lambda sq=search_query, sf=status_filter: self._execute_operation(
                        f"search_{i}",
                        lambda: export_service.search_expeditions(
                            search_query=sq,
                            status_filter=sf,
                            limit=random.randint(10, 100)
                        )
                    )
                )
                futures.append(future)

            # Wait for all operations to complete
            concurrent.futures.wait(futures)

        return self.results.get_summary()

    def run_comprehensive_load_test(self) -> Dict[str, Any]:
        """Run a comprehensive load test covering all major operations."""
        self.logger.info("Starting comprehensive load test...")

        # Reset results for comprehensive test
        self.results = LoadTestResults()

        test_phases = [
            ("Expedition Creation", lambda: self.test_expedition_creation(50)),
            ("Query Operations", lambda: self.test_expedition_queries(200)),
            ("Search Operations", lambda: self.test_search_operations(100)),
            ("Export Operations", lambda: self.test_export_operations(25))
        ]

        phase_results = {}

        for phase_name, test_func in test_phases:
            self.logger.info(f"Running {phase_name} phase...")
            phase_start = time.time()

            # Reset results for this phase
            phase_results_obj = LoadTestResults()
            original_results = self.results
            self.results = phase_results_obj

            try:
                test_func()
                phase_results_obj.finalize()
                phase_results[phase_name] = phase_results_obj.get_summary()
            except Exception as e:
                self.logger.error(f"Phase {phase_name} failed: {e}")
                phase_results[phase_name] = {"error": str(e)}

            # Merge results back
            original_results.total_operations += phase_results_obj.total_operations
            original_results.successful_operations += phase_results_obj.successful_operations
            original_results.failed_operations += phase_results_obj.failed_operations
            original_results.response_times.extend(phase_results_obj.response_times)
            original_results.errors.extend(phase_results_obj.errors)
            self.results = original_results

            phase_duration = time.time() - phase_start
            self.logger.info(f"Phase {phase_name} completed in {phase_duration:.2f}s")

        self.results.finalize()

        return {
            "overall_summary": self.results.get_summary(),
            "phase_results": phase_results,
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on test results."""
        recommendations = []
        summary = self.results.get_summary()

        if summary.get("success_rate", 0) < 95:
            recommendations.append("Success rate is below 95% - investigate error causes and improve error handling")

        if summary.get("operations_per_second", 0) < 50:
            recommendations.append("Operations per second is low - consider connection pool tuning or query optimization")

        response_stats = summary.get("response_time_stats", {})
        if response_stats.get("p95_ms", 0) > 2000:
            recommendations.append("95th percentile response time is over 2 seconds - optimize slow queries")

        if response_stats.get("avg_ms", 0) > 500:
            recommendations.append("Average response time is over 500ms - consider caching frequently accessed data")

        if len(self.results.errors) > 10:
            recommendations.append("High error count detected - review error patterns and improve resilience")

        if not recommendations:
            recommendations.append("Performance looks good! System is handling load well.")

        return recommendations


def run_load_test():
    """Run the load test and print results."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    tester = ExpeditionLoadTester()

    print("🚀 Starting Expedition System Load Test")
    print("=" * 60)

    results = tester.run_comprehensive_load_test()

    print("\n📊 LOAD TEST RESULTS")
    print("=" * 60)

    # Overall summary
    overall = results["overall_summary"]
    print(f"Total Duration: {overall['duration_seconds']}s")
    print(f"Total Operations: {overall['total_operations']}")
    print(f"Success Rate: {overall['success_rate']}%")
    print(f"Operations/Second: {overall['operations_per_second']}")

    # Response time statistics
    response_stats = overall["response_time_stats"]
    print(f"\nResponse Times:")
    print(f"  Average: {response_stats['avg_ms']}ms")
    print(f"  95th percentile: {response_stats['p95_ms']}ms")
    print(f"  99th percentile: {response_stats['p99_ms']}ms")

    # Phase results
    print(f"\nPhase Breakdown:")
    for phase, phase_data in results["phase_results"].items():
        if "error" not in phase_data:
            print(f"  {phase}: {phase_data['successful_operations']}/{phase_data['total_operations']} success, {phase_data['response_time_stats']['avg_ms']:.1f}ms avg")
        else:
            print(f"  {phase}: FAILED - {phase_data['error']}")

    # Recommendations
    print(f"\n💡 Recommendations:")
    for i, recommendation in enumerate(results["recommendations"], 1):
        print(f"  {i}. {recommendation}")

    print("\n✅ Load test completed!")


if __name__ == "__main__":
    run_load_test()