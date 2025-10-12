"""
Advanced analytics service for expedition performance metrics and insights.
Provides comprehensive analytics, reporting, and visualization data for expeditions.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import statistics

from services.base_service import BaseService, ServiceError
from core.interfaces import IExpeditionService
from models.expedition import ExpeditionStatus, PaymentStatus


class AnalyticsService(BaseService):
    """
    Advanced analytics service for expedition performance analysis.
    Provides comprehensive metrics, trends, and business insights.
    """

    def __init__(self, expedition_service: IExpeditionService):
        super().__init__()
        self.expedition_service = expedition_service

    def get_expedition_performance_metrics(self, expedition_id: int) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics for a specific expedition.

        Args:
            expedition_id: Expedition identifier

        Returns:
            Dictionary with detailed performance metrics
        """
        try:
            expedition = self.expedition_service.get_expedition_by_id(expedition_id)
            if not expedition:
                return {}

            # Get basic expedition data
            items = self.expedition_service.get_expedition_items(expedition_id)
            consumptions = self.expedition_service.get_expedition_consumptions(expedition_id)

            # Calculate time metrics
            now = datetime.now()
            duration = now - expedition.created_at if expedition.created_at else timedelta(0)
            time_to_deadline = expedition.deadline - now if expedition.deadline else None
            is_overdue = time_to_deadline and time_to_deadline.total_seconds() < 0

            # Calculate completion metrics
            total_items = len(items)
            total_required_quantity = sum(item.required_quantity for item in items)
            total_consumed_quantity = sum(consumption.quantity_consumed for consumption in consumptions)

            item_completion_rate = (len(set(c.expedition_item_id for c in consumptions)) / total_items * 100) if total_items > 0 else 0
            quantity_completion_rate = (total_consumed_quantity / total_required_quantity * 100) if total_required_quantity > 0 else 0

            # Calculate financial metrics
            total_value = sum(consumption.total_cost for consumption in consumptions)
            paid_value = sum(consumption.total_cost for consumption in consumptions if consumption.payment_status == PaymentStatus.PAID.value)
            pending_value = total_value - paid_value

            # Calculate consumer metrics
            unique_consumers = len(set(c.consumer_name for c in consumptions))
            consumption_frequency = defaultdict(int)
            consumer_spending = defaultdict(Decimal)

            for consumption in consumptions:
                consumption_frequency[consumption.consumer_name] += 1
                consumer_spending[consumption.consumer_name] += consumption.total_cost

            # Calculate efficiency metrics
            avg_consumption_value = total_value / len(consumptions) if consumptions else 0
            avg_daily_progress = quantity_completion_rate / max(duration.days, 1) if duration.days > 0 else 0

            # Performance scoring (0-100)
            completion_score = (item_completion_rate + quantity_completion_rate) / 2
            timeliness_score = self._calculate_timeliness_score(expedition, duration, time_to_deadline)
            payment_score = (paid_value / total_value * 100) if total_value > 0 else 100
            engagement_score = min(unique_consumers * 10, 100)  # Max 100 for 10+ consumers

            overall_performance_score = (completion_score + timeliness_score + payment_score + engagement_score) / 4

            return {
                "expedition_id": expedition_id,
                "expedition_name": expedition.name,
                "status": expedition.status,
                "created_at": expedition.created_at.isoformat() if expedition.created_at else None,
                "deadline": expedition.deadline.isoformat() if expedition.deadline else None,
                "duration_days": duration.days,
                "is_overdue": is_overdue,
                "time_to_deadline_hours": time_to_deadline.total_seconds() / 3600 if time_to_deadline else None,

                "completion_metrics": {
                    "total_items": total_items,
                    "completed_items": len(set(c.expedition_item_id for c in consumptions)),
                    "item_completion_rate": round(item_completion_rate, 2),
                    "total_required_quantity": total_required_quantity,
                    "total_consumed_quantity": total_consumed_quantity,
                    "quantity_completion_rate": round(quantity_completion_rate, 2),
                    "avg_daily_progress": round(avg_daily_progress, 2)
                },

                "financial_metrics": {
                    "total_value": float(total_value),
                    "paid_value": float(paid_value),
                    "pending_value": float(pending_value),
                    "payment_completion_rate": round((paid_value / total_value * 100) if total_value > 0 else 0, 2),
                    "avg_consumption_value": float(avg_consumption_value)
                },

                "consumer_metrics": {
                    "unique_consumers": unique_consumers,
                    "total_consumptions": len(consumptions),
                    "avg_consumptions_per_consumer": round(len(consumptions) / unique_consumers, 2) if unique_consumers > 0 else 0,
                    "top_consumers": self._get_top_consumers(consumer_spending, consumption_frequency)[:5]
                },

                "performance_scores": {
                    "completion_score": round(completion_score, 2),
                    "timeliness_score": round(timeliness_score, 2),
                    "payment_score": round(payment_score, 2),
                    "engagement_score": round(engagement_score, 2),
                    "overall_performance_score": round(overall_performance_score, 2)
                },

                "efficiency_metrics": {
                    "consumption_velocity": round(len(consumptions) / max(duration.days, 1), 2),
                    "revenue_velocity": float(total_value / max(duration.days, 1)),
                    "consumer_acquisition_rate": round(unique_consumers / max(duration.days, 1), 2)
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get performance metrics for expedition {expedition_id}: {e}", exc_info=True)
            return {}

    def get_timeline_visualization_data(self, expedition_id: int, granularity: str = "daily") -> Dict[str, Any]:
        """
        Get timeline visualization data for an expedition.

        Args:
            expedition_id: Expedition identifier
            granularity: Time granularity ("hourly", "daily", "weekly")

        Returns:
            Timeline data for visualization
        """
        try:
            expedition = self.expedition_service.get_expedition_by_id(expedition_id)
            if not expedition:
                return {}

            consumptions = self.expedition_service.get_expedition_consumptions(expedition_id)
            if not consumptions:
                return {"timeline": [], "summary": {}}

            # Sort consumptions by time
            sorted_consumptions = sorted(consumptions, key=lambda c: c.consumed_at or datetime.min)

            # Generate time buckets
            start_time = expedition.created_at
            end_time = max((c.consumed_at for c in sorted_consumptions if c.consumed_at), default=datetime.now())

            time_buckets = self._generate_time_buckets(start_time, end_time, granularity)

            # Aggregate data by time bucket
            timeline_data = []
            cumulative_quantity = 0
            cumulative_value = 0
            cumulative_consumers = set()

            for bucket_start, bucket_end in time_buckets:
                bucket_consumptions = [
                    c for c in sorted_consumptions
                    if c.consumed_at and bucket_start <= c.consumed_at < bucket_end
                ]

                bucket_quantity = sum(c.quantity_consumed for c in bucket_consumptions)
                bucket_value = sum(c.total_cost for c in bucket_consumptions)
                bucket_consumers = set(c.consumer_name for c in bucket_consumptions)

                cumulative_quantity += bucket_quantity
                cumulative_value += bucket_value
                cumulative_consumers.update(bucket_consumers)

                timeline_data.append({
                    "period_start": bucket_start.isoformat(),
                    "period_end": bucket_end.isoformat(),
                    "period_label": self._format_period_label(bucket_start, granularity),
                    "consumptions_count": len(bucket_consumptions),
                    "quantity_consumed": bucket_quantity,
                    "value_consumed": float(bucket_value),
                    "unique_consumers": len(bucket_consumers),
                    "cumulative_quantity": cumulative_quantity,
                    "cumulative_value": float(cumulative_value),
                    "cumulative_consumers": len(cumulative_consumers)
                })

            return {
                "expedition_id": expedition_id,
                "granularity": granularity,
                "timeline": timeline_data,
                "summary": {
                    "total_periods": len(timeline_data),
                    "active_periods": len([t for t in timeline_data if t["consumptions_count"] > 0]),
                    "peak_consumption_period": max(timeline_data, key=lambda x: x["quantity_consumed"])["period_label"] if timeline_data else None,
                    "peak_value_period": max(timeline_data, key=lambda x: x["value_consumed"])["period_label"] if timeline_data else None
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get timeline data for expedition {expedition_id}: {e}", exc_info=True)
            return {}

    def calculate_profit_loss_analysis(self, expedition_id: int) -> Dict[str, Any]:
        """
        Calculate detailed profit/loss analysis for an expedition.

        Args:
            expedition_id: Expedition identifier

        Returns:
            Profit/loss analysis with cost breakdowns
        """
        try:
            expedition = self.expedition_service.get_expedition_by_id(expedition_id)
            if not expedition:
                return {}

            items = self.expedition_service.get_expedition_items(expedition_id)
            consumptions = self.expedition_service.get_expedition_consumptions(expedition_id)

            # Calculate revenue metrics
            total_revenue = sum(c.total_cost for c in consumptions)
            collected_revenue = sum(c.total_cost for c in consumptions if c.payment_status == PaymentStatus.PAID.value)
            pending_revenue = total_revenue - collected_revenue

            # Calculate costs (from inventory costs where available)
            total_cost = Decimal('0')
            cost_breakdown = []

            for item in items:
                # Get product cost information
                try:
                    product_query = """
                        SELECT p.nome, AVG(e.custo) as avg_cost
                        FROM Produtos p
                        LEFT JOIN Estoque e ON p.id = e.produto_id
                        WHERE p.id = %s
                        GROUP BY p.id, p.nome
                    """
                    product_result = self._execute_query(product_query, (item.product_id,), fetch_one=True)

                    if product_result:
                        product_name, avg_cost = product_result
                        avg_cost = Decimal(str(avg_cost)) if avg_cost else Decimal('0')

                        consumed_quantity = sum(
                            c.quantity_consumed for c in consumptions
                            if c.expedition_item_id == item.id
                        )

                        item_cost = avg_cost * consumed_quantity
                        total_cost += item_cost

                        cost_breakdown.append({
                            "product_name": product_name,
                            "consumed_quantity": consumed_quantity,
                            "unit_cost": float(avg_cost),
                            "total_cost": float(item_cost)
                        })

                except Exception as e:
                    self.logger.warning(f"Could not calculate cost for item {item.id}: {e}")

            # Calculate profit metrics
            gross_profit = collected_revenue - total_cost
            potential_profit = total_revenue - total_cost
            profit_margin = (gross_profit / collected_revenue * 100) if collected_revenue > 0 else 0
            potential_margin = (potential_profit / total_revenue * 100) if total_revenue > 0 else 0

            # ROI calculations
            roi = (gross_profit / total_cost * 100) if total_cost > 0 else 0
            potential_roi = (potential_profit / total_cost * 100) if total_cost > 0 else 0

            return {
                "expedition_id": expedition_id,
                "expedition_name": expedition.name,
                "analysis_date": datetime.now().isoformat(),

                "revenue_analysis": {
                    "total_revenue": float(total_revenue),
                    "collected_revenue": float(collected_revenue),
                    "pending_revenue": float(pending_revenue),
                    "collection_rate": round((collected_revenue / total_revenue * 100) if total_revenue > 0 else 0, 2)
                },

                "cost_analysis": {
                    "total_cost": float(total_cost),
                    "cost_breakdown": cost_breakdown,
                    "avg_cost_per_consumption": float(total_cost / len(consumptions)) if consumptions else 0
                },

                "profit_analysis": {
                    "gross_profit": float(gross_profit),
                    "potential_profit": float(potential_profit),
                    "profit_margin": round(profit_margin, 2),
                    "potential_margin": round(potential_margin, 2),
                    "roi": round(roi, 2),
                    "potential_roi": round(potential_roi, 2)
                },

                "financial_health": {
                    "break_even_point": float(total_cost),
                    "break_even_achieved": collected_revenue >= total_cost,
                    "profitability_status": self._get_profitability_status(gross_profit, potential_profit),
                    "risk_assessment": self._assess_financial_risk(collected_revenue, total_cost, pending_revenue)
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate profit/loss for expedition {expedition_id}: {e}", exc_info=True)
            return {}

    def get_comparative_analytics(self, expedition_ids: List[int]) -> Dict[str, Any]:
        """
        Get comparative analytics across multiple expeditions.

        Args:
            expedition_ids: List of expedition identifiers

        Returns:
            Comparative analysis data
        """
        try:
            expedition_data = []

            for exp_id in expedition_ids:
                metrics = self.get_expedition_performance_metrics(exp_id)
                if metrics:
                    expedition_data.append(metrics)

            if not expedition_data:
                return {}

            # Calculate comparative metrics
            performance_scores = [exp["performance_scores"]["overall_performance_score"] for exp in expedition_data]
            completion_rates = [exp["completion_metrics"]["quantity_completion_rate"] for exp in expedition_data]
            revenue_values = [exp["financial_metrics"]["total_value"] for exp in expedition_data]
            duration_days = [exp["duration_days"] for exp in expedition_data]

            return {
                "expeditions_compared": len(expedition_data),
                "comparison_date": datetime.now().isoformat(),

                "performance_comparison": {
                    "avg_performance_score": round(statistics.mean(performance_scores), 2),
                    "best_performing": max(expedition_data, key=lambda x: x["performance_scores"]["overall_performance_score"]),
                    "worst_performing": min(expedition_data, key=lambda x: x["performance_scores"]["overall_performance_score"]),
                    "performance_std_dev": round(statistics.stdev(performance_scores) if len(performance_scores) > 1 else 0, 2)
                },

                "completion_comparison": {
                    "avg_completion_rate": round(statistics.mean(completion_rates), 2),
                    "completion_std_dev": round(statistics.stdev(completion_rates) if len(completion_rates) > 1 else 0, 2),
                    "fastest_completion": min(expedition_data, key=lambda x: x["duration_days"]) if expedition_data else None
                },

                "financial_comparison": {
                    "total_revenue": sum(revenue_values),
                    "avg_revenue": round(statistics.mean(revenue_values), 2),
                    "revenue_std_dev": round(statistics.stdev(revenue_values) if len(revenue_values) > 1 else 0, 2),
                    "highest_revenue": max(expedition_data, key=lambda x: x["financial_metrics"]["total_value"]),
                    "most_efficient": min(expedition_data, key=lambda x: x["duration_days"] / max(x["financial_metrics"]["total_value"], 1))
                },

                "expedition_rankings": self._rank_expeditions(expedition_data)
            }

        except Exception as e:
            self.logger.error(f"Failed to generate comparative analytics: {e}", exc_info=True)
            return {}

    def _calculate_timeliness_score(self, expedition, duration: timedelta, time_to_deadline: Optional[timedelta]) -> float:
        """Calculate timeliness performance score (0-100)."""
        if not expedition.deadline:
            return 100  # No deadline = perfect timeliness

        if not time_to_deadline:
            return 50  # Unknown deadline status

        if time_to_deadline.total_seconds() > 0:
            # Still on time - score based on how much time is left
            total_duration = expedition.deadline - expedition.created_at
            progress = duration.total_seconds() / total_duration.total_seconds()
            return max(100 - (progress * 50), 50)  # 50-100 score range
        else:
            # Overdue - score based on how overdue
            overdue_hours = abs(time_to_deadline.total_seconds()) / 3600
            return max(50 - overdue_hours, 0)  # Decreasing score for overdue

    def _get_top_consumers(self, consumer_spending: Dict[str, Decimal], consumption_frequency: Dict[str, int]) -> List[Dict[str, Any]]:
        """Get top consumers ranked by spending and frequency."""
        consumer_data = []

        for consumer in consumer_spending.keys():
            consumer_data.append({
                "consumer_name": consumer,
                "total_spent": float(consumer_spending[consumer]),
                "consumption_count": consumption_frequency[consumer],
                "avg_consumption_value": float(consumer_spending[consumer] / consumption_frequency[consumer])
            })

        return sorted(consumer_data, key=lambda x: x["total_spent"], reverse=True)

    def _generate_time_buckets(self, start_time: datetime, end_time: datetime, granularity: str) -> List[Tuple[datetime, datetime]]:
        """Generate time buckets for timeline analysis."""
        buckets = []
        current_time = start_time

        if granularity == "hourly":
            delta = timedelta(hours=1)
        elif granularity == "daily":
            delta = timedelta(days=1)
        elif granularity == "weekly":
            delta = timedelta(weeks=1)
        else:
            delta = timedelta(days=1)

        while current_time < end_time:
            bucket_end = min(current_time + delta, end_time)
            buckets.append((current_time, bucket_end))
            current_time = bucket_end

        return buckets

    def _format_period_label(self, period_start: datetime, granularity: str) -> str:
        """Format period label for display."""
        if granularity == "hourly":
            return period_start.strftime("%Y-%m-%d %H:00")
        elif granularity == "daily":
            return period_start.strftime("%Y-%m-%d")
        elif granularity == "weekly":
            return f"Week of {period_start.strftime('%Y-%m-%d')}"
        else:
            return period_start.strftime("%Y-%m-%d")

    def _get_profitability_status(self, gross_profit: Decimal, potential_profit: Decimal) -> str:
        """Determine profitability status."""
        if gross_profit > 0:
            return "profitable"
        elif potential_profit > 0:
            return "potentially_profitable"
        elif gross_profit == 0:
            return "break_even"
        else:
            return "loss_making"

    def _assess_financial_risk(self, collected_revenue: Decimal, total_cost: Decimal, pending_revenue: Decimal) -> str:
        """Assess financial risk level."""
        if collected_revenue >= total_cost:
            return "low"
        elif collected_revenue + pending_revenue >= total_cost:
            return "medium"
        else:
            return "high"

    def _rank_expeditions(self, expedition_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rank expeditions across multiple criteria."""
        ranked_data = {
            "by_performance": sorted(expedition_data, key=lambda x: x["performance_scores"]["overall_performance_score"], reverse=True),
            "by_revenue": sorted(expedition_data, key=lambda x: x["financial_metrics"]["total_value"], reverse=True),
            "by_completion": sorted(expedition_data, key=lambda x: x["completion_metrics"]["quantity_completion_rate"], reverse=True),
            "by_efficiency": sorted(expedition_data, key=lambda x: x["efficiency_metrics"]["revenue_velocity"], reverse=True)
        }

        # Add ranking positions
        for category, rankings in ranked_data.items():
            for i, exp in enumerate(rankings):
                exp[f"{category}_rank"] = i + 1

        return ranked_data