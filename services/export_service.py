"""
Export service implementation for generating CSV exports and reports.
Extends BaseService for database operations and error handling.
"""

import csv
import logging
import os
import tempfile
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from io import StringIO

from services.base_service import BaseService, ServiceError, ValidationError
from models.expedition import ExpeditionStatus, PaymentStatus


class ExportService(BaseService):
    """
    Service for generating exports and reports from expedition data.
    Provides CSV export functionality with filtering and search capabilities.
    """

    def __init__(self):
        super().__init__()
        self.temp_dir = tempfile.gettempdir()

    def export_expedition_data(self, expedition_id: Optional[int] = None,
                             status_filter: Optional[str] = None,
                             date_from: Optional[datetime] = None,
                             date_to: Optional[datetime] = None) -> str:
        """
        Export expedition data to CSV format.

        Args:
            expedition_id: Specific expedition to export (optional)
            status_filter: Filter by expedition status (optional)
            date_from: Filter expeditions created after this date (optional)
            date_to: Filter expeditions created before this date (optional)

        Returns:
            File path to the generated CSV file
        """
        self._log_operation("ExportExpeditionData",
                          expedition_id=expedition_id,
                          status_filter=status_filter)

        # Build query based on filters
        where_conditions = []
        params = []

        # Optimized query using CTEs for better performance
        base_query = """
            WITH expedition_stats AS (
                SELECT
                    e.id, e.name, e.owner_chat_id, e.status, e.deadline,
                    e.created_at, e.completed_at
                FROM expeditions e
            ),
            item_stats AS (
                SELECT
                    ei.expedition_id,
                    COUNT(ei.id) as total_items,
                    COALESCE(SUM(ei.quantity_required), 0) as total_required_quantity,
                    COALESCE(SUM(ei.quantity_consumed), 0) as total_consumed_quantity
                FROM expedition_items ei
                GROUP BY ei.expedition_id
            ),
            consumption_stats AS (
                SELECT
                    ea.expedition_id,
                    COUNT(ea.id) as total_consumptions,
                    COALESCE(SUM(ea.total_cost), 0) as total_consumption_value,
                    COALESCE(SUM(CASE WHEN ea.payment_status = %s THEN ea.total_cost ELSE 0 END), 0) as total_paid_value
                FROM expedition_assignments ea
                GROUP BY ea.expedition_id
            )
            SELECT
                e.id, e.name, e.owner_chat_id, e.status, e.deadline,
                e.created_at, e.completed_at,
                COALESCE(i.total_items, 0) as total_items,
                COALESCE(i.total_required_quantity, 0) as total_required_quantity,
                COALESCE(i.total_consumed_quantity, 0) as total_consumed_quantity,
                COALESCE(c.total_consumptions, 0) as total_consumptions,
                COALESCE(c.total_consumption_value, 0) as total_consumption_value,
                COALESCE(c.total_paid_value, 0) as total_paid_value
            FROM expedition_stats e
            LEFT JOIN item_stats i ON e.id = i.expedition_id
            LEFT JOIN consumption_stats c ON e.id = c.expedition_id
        """
        params.append(PaymentStatus.PAID.value)

        # Build where conditions for the main expedition_stats CTE
        expedition_where_conditions = []

        if expedition_id:
            expedition_where_conditions.append("e.id = %s")
            params.append(expedition_id)

        if status_filter:
            expedition_where_conditions.append("e.status = %s")
            params.append(status_filter)

        if date_from:
            expedition_where_conditions.append("e.created_at >= %s")
            params.append(date_from)

        if date_to:
            expedition_where_conditions.append("e.created_at <= %s")
            params.append(date_to)

        # Apply where conditions to the expedition_stats CTE
        if expedition_where_conditions:
            base_query = base_query.replace(
                "FROM expeditions e",
                f"FROM expeditions e WHERE {' AND '.join(expedition_where_conditions)}"
            )

        base_query += """
            ORDER BY e.created_at DESC
        """

        results = self._execute_query(base_query, tuple(params), fetch_all=True)

        # Generate CSV file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"expedition_export_{timestamp}.csv"
        filepath = os.path.join(self.temp_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow([
                'Expedition ID', 'Name', 'Owner Chat ID', 'Status', 'Deadline',
                'Created At', 'Completed At', 'Total Items', 'Required Quantity',
                'Consumed Quantity', 'Total Consumptions', 'Total Value',
                'Paid Value', 'Unpaid Value', 'Completion Percentage',
                'Payment Percentage', 'Is Overdue'
            ])

            # Write data
            for row in results or []:
                (exp_id, name, owner_chat_id, status, deadline, created_at, completed_at,
                 total_items, total_required_qty, total_consumed_qty, total_consumptions,
                 total_value, paid_value) = row

                unpaid_value = total_value - paid_value
                completion_pct = (total_consumed_qty / total_required_qty * 100) if total_required_qty > 0 else 0
                payment_pct = (paid_value / total_value * 100) if total_value > 0 else 0
                is_overdue = deadline and deadline < datetime.now() if status == ExpeditionStatus.ACTIVE.value else False

                writer.writerow([
                    exp_id, name, owner_chat_id, status,
                    deadline.strftime("%Y-%m-%d %H:%M") if deadline else '',
                    created_at.strftime("%Y-%m-%d %H:%M"),
                    completed_at.strftime("%Y-%m-%d %H:%M") if completed_at else '',
                    total_items, total_required_qty, total_consumed_qty,
                    total_consumptions, f"{total_value:.2f}", f"{paid_value:.2f}",
                    f"{unpaid_value:.2f}", f"{completion_pct:.1f}%", f"{payment_pct:.1f}%",
                    'Yes' if is_overdue else 'No'
                ])

        self.logger.info(f"Exported expedition data to {filepath}")
        return filepath

    def export_pirate_activity_report(self, expedition_id: Optional[int] = None,
                                    anonymized: bool = True,
                                    date_from: Optional[datetime] = None,
                                    date_to: Optional[datetime] = None) -> str:
        """
        Export pirate activity report (anonymized by default).

        Args:
            expedition_id: Specific expedition (optional)
            anonymized: Use pirate names instead of real names
            date_from: Filter consumptions after this date (optional)
            date_to: Filter consumptions before this date (optional)

        Returns:
            File path to the generated CSV file
        """
        self._log_operation("ExportPirateActivityReport",
                          expedition_id=expedition_id,
                          anonymized=anonymized)

        # Build query
        where_conditions = []
        params = []

        base_query = """
            SELECT ea.id, ea.expedition_id, e.name as expedition_name,
                   ep.original_name as consumer_name, ep.pirate_name, ea.consumed_quantity,
                   ea.unit_price, ea.total_cost, ea.payment_status, ea.assigned_at,
                   p.nome as product_name, ei.quantity_required
            FROM expedition_assignments ea
            JOIN expeditions e ON ea.expedition_id = e.id
            JOIN expedition_pirates ep ON ea.pirate_id = ep.id
            JOIN expedition_items ei ON ea.expedition_item_id = ei.id
            JOIN produtos p ON ei.produto_id = p.id
        """

        if expedition_id:
            where_conditions.append("ea.expedition_id = %s")
            params.append(expedition_id)

        if date_from:
            where_conditions.append("ea.assigned_at >= %s")
            params.append(date_from)

        if date_to:
            where_conditions.append("ea.assigned_at <= %s")
            params.append(date_to)

        if where_conditions:
            base_query += " WHERE " + " AND ".join(where_conditions)

        base_query += " ORDER BY ea.assigned_at DESC"

        results = self._execute_query(base_query, tuple(params), fetch_all=True)

        # Generate CSV file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pirate_activity_{'anonymous' if anonymized else 'detailed'}_{timestamp}.csv"
        filepath = os.path.join(self.temp_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            header = ['Consumption ID', 'Expedition ID', 'Expedition Name']
            if anonymized:
                header.extend(['Pirate Name', 'Quantity Consumed', 'Unit Price', 'Total Cost'])
            else:
                header.extend(['Consumer Name', 'Pirate Name', 'Quantity Consumed', 'Unit Price', 'Total Cost'])

            header.extend(['Payment Status', 'Consumed At', 'Product Name', 'Item Required Quantity'])
            writer.writerow(header)

            # Write data
            for row in results or []:
                (consumption_id, exp_id, exp_name, consumer_name, pirate_name,
                 quantity_consumed, unit_price, total_cost, payment_status, consumed_at,
                 product_name, quantity_required) = row

                data_row = [consumption_id, exp_id, exp_name]
                if anonymized:
                    data_row.extend([pirate_name, quantity_consumed, f"{unit_price:.2f}", f"{total_cost:.2f}"])
                else:
                    data_row.extend([consumer_name, pirate_name, quantity_consumed, f"{unit_price:.2f}", f"{total_cost:.2f}"])

                data_row.extend([
                    payment_status,
                    consumed_at.strftime("%Y-%m-%d %H:%M"),
                    product_name,
                    quantity_required
                ])
                writer.writerow(data_row)

        self.logger.info(f"Exported pirate activity report to {filepath}")
        return filepath

    def export_profit_loss_report(self, expedition_id: Optional[int] = None,
                                date_from: Optional[datetime] = None,
                                date_to: Optional[datetime] = None) -> str:
        """
        Export profit/loss report for expeditions.

        Args:
            expedition_id: Specific expedition (optional)
            date_from: Filter expeditions created after this date (optional)
            date_to: Filter expeditions created before this date (optional)

        Returns:
            File path to the generated CSV file
        """
        self._log_operation("ExportProfitLossReport", expedition_id=expedition_id)

        # Get expedition financial data with cost information
        where_conditions = []
        params = []

        # Optimized profit/loss query with CTEs
        base_query = """
            WITH expedition_base AS (
                SELECT id, name, created_at, status
                FROM expeditions e
            ),
            consumption_metrics AS (
                SELECT
                    ea.expedition_id,
                    COUNT(ea.id) as total_consumptions,
                    COALESCE(SUM(ea.consumed_quantity), 0) as total_quantity_sold,
                    COALESCE(SUM(ea.total_cost), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN ea.payment_status = %s THEN ea.total_cost ELSE 0 END), 0) as total_collected,
                    COALESCE(AVG(ea.unit_price), 0) as avg_selling_price
                FROM expedition_assignments ea
                GROUP BY ea.expedition_id
            ),
            cost_metrics AS (
                SELECT
                    v.expedition_id,
                    COALESCE(SUM(iv.quantidade * es.custo_unitario), 0) as total_cost_of_goods_sold
                FROM vendas v
                INNER JOIN itens_venda iv ON v.id = iv.venda_id
                INNER JOIN estoque es ON iv.estoque_id = es.id
                WHERE v.expedition_id IS NOT NULL
                GROUP BY v.expedition_id
            )
            SELECT
                e.id, e.name, e.created_at, e.status,
                COALESCE(c.total_consumptions, 0) as total_consumptions,
                COALESCE(c.total_quantity_sold, 0) as total_quantity_sold,
                COALESCE(c.total_revenue, 0) as total_revenue,
                COALESCE(c.total_collected, 0) as total_collected,
                COALESCE(c.avg_selling_price, 0) as avg_selling_price,
                COALESCE(cogs.total_cost_of_goods_sold, 0) as total_cost_of_goods_sold
            FROM expedition_base e
            LEFT JOIN consumption_metrics c ON e.id = c.expedition_id
            LEFT JOIN cost_metrics cogs ON e.id = cogs.expedition_id
        """
        params.append(PaymentStatus.PAID.value)

        if expedition_id:
            where_conditions.append("e.id = %s")
            params.append(expedition_id)

        if date_from:
            where_conditions.append("e.created_at >= %s")
            params.append(date_from)

        if date_to:
            where_conditions.append("e.created_at <= %s")
            params.append(date_to)

        if where_conditions:
            base_query += " WHERE " + " AND ".join(where_conditions)

        base_query += """
            GROUP BY e.id, e.name, e.created_at, e.status
            ORDER BY e.created_at DESC
        """

        results = self._execute_query(base_query, tuple(params), fetch_all=True)

        # Generate CSV file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"profit_loss_report_{timestamp}.csv"
        filepath = os.path.join(self.temp_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow([
                'Expedition ID', 'Name', 'Created At', 'Status',
                'Total Consumptions', 'Quantity Sold', 'Total Revenue',
                'Total Collected', 'Outstanding Debt', 'Avg Selling Price',
                'Cost of Goods Sold', 'Gross Profit', 'Gross Margin %',
                'Collection Rate %'
            ])

            total_revenue_sum = 0
            total_profit_sum = 0
            total_collected_sum = 0

            # Write data
            for row in results or []:
                (exp_id, name, created_at, status, total_consumptions,
                 quantity_sold, total_revenue, total_collected, avg_price, cogs) = row

                outstanding_debt = total_revenue - total_collected
                gross_profit = total_revenue - cogs
                gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
                collection_rate = (total_collected / total_revenue * 100) if total_revenue > 0 else 0

                writer.writerow([
                    exp_id, name, created_at.strftime("%Y-%m-%d"), status,
                    total_consumptions, quantity_sold, f"{total_revenue:.2f}",
                    f"{total_collected:.2f}", f"{outstanding_debt:.2f}", f"{avg_price:.2f}",
                    f"{cogs:.2f}", f"{gross_profit:.2f}", f"{gross_margin:.1f}%",
                    f"{collection_rate:.1f}%"
                ])

                total_revenue_sum += total_revenue
                total_profit_sum += gross_profit
                total_collected_sum += total_collected

            # Write summary row
            if results:
                writer.writerow([])  # Empty row
                writer.writerow([
                    'TOTAL', 'Summary', '', '',
                    sum(row[4] for row in results), sum(row[5] for row in results),
                    f"{total_revenue_sum:.2f}", f"{total_collected_sum:.2f}",
                    f"{total_revenue_sum - total_collected_sum:.2f}", '',
                    '', f"{total_profit_sum:.2f}",
                    f"{total_profit_sum / total_revenue_sum * 100:.1f}%" if total_revenue_sum > 0 else '0%',
                    f"{total_collected_sum / total_revenue_sum * 100:.1f}%" if total_revenue_sum > 0 else '0%'
                ])

        self.logger.info(f"Exported profit/loss report to {filepath}")
        return filepath

    def search_expeditions(self, search_query: Optional[str] = None,
                          status_filter: Optional[str] = None,
                          owner_chat_id: Optional[int] = None,
                          date_from: Optional[datetime] = None,
                          date_to: Optional[datetime] = None,
                          sort_by: str = "created_at",
                          sort_order: str = "DESC",
                          limit: int = 100,
                          offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search expeditions with advanced filtering and sorting.

        Args:
            search_query: Search in expedition name (optional)
            status_filter: Filter by status (optional)
            owner_chat_id: Filter by owner (optional)
            date_from: Created after this date (optional)
            date_to: Created before this date (optional)
            sort_by: Column to sort by
            sort_order: ASC or DESC
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            Tuple of (results list, total count)
        """
        self._log_operation("SearchExpeditions",
                          search_query=search_query,
                          status_filter=status_filter)

        # Validate sort parameters
        valid_sort_columns = ['id', 'name', 'created_at', 'deadline', 'status']
        if sort_by not in valid_sort_columns:
            sort_by = 'created_at'

        if sort_order.upper() not in ['ASC', 'DESC']:
            sort_order = 'DESC'

        # Build base query
        where_conditions = []
        params = []

        base_query = """
            SELECT e.id, e.name, e.owner_chat_id, e.status, e.deadline,
                   e.created_at, e.completed_at,
                   COUNT(ei.id) as total_items,
                   COALESCE(SUM(ei.quantity_required), 0) as total_required_quantity,
                   COALESCE(SUM(ei.quantity_consumed), 0) as total_consumed_quantity
            FROM expeditions e
            LEFT JOIN expedition_items ei ON e.id = ei.expedition_id
        """

        # Add search conditions
        if search_query:
            where_conditions.append("e.name ILIKE %s")
            params.append(f"%{search_query}%")

        if status_filter:
            where_conditions.append("e.status = %s")
            params.append(status_filter)

        if owner_chat_id:
            where_conditions.append("e.owner_chat_id = %s")
            params.append(owner_chat_id)

        if date_from:
            where_conditions.append("e.created_at >= %s")
            params.append(date_from)

        if date_to:
            where_conditions.append("e.created_at <= %s")
            params.append(date_to)

        if where_conditions:
            base_query += " WHERE " + " AND ".join(where_conditions)

        base_query += f"""
            GROUP BY e.id, e.name, e.owner_chat_id, e.status, e.deadline, e.created_at, e.completed_at
            ORDER BY e.{sort_by} {sort_order}
            LIMIT %s OFFSET %s
        """

        params.extend([limit, offset])

        # Execute search query
        results = self._execute_query(base_query, tuple(params), fetch_all=True)

        # Get total count for pagination
        count_query = """
            SELECT COUNT(DISTINCT e.id)
            FROM expeditions e
        """

        if where_conditions:
            count_query += " WHERE " + " AND ".join(where_conditions[:-2])  # Remove limit/offset params

        total_count = self._execute_query(count_query, tuple(params[:-2]), fetch_one=True)[0] if where_conditions else 0

        # Format results
        formatted_results = []
        for row in results or []:
            (exp_id, name, owner_chat_id, status, deadline, created_at, completed_at,
             total_items, total_required_qty, total_consumed_qty) = row

            completion_pct = (total_consumed_qty / total_required_qty * 100) if total_required_qty > 0 else 0
            is_overdue = deadline and deadline < datetime.now() if status == ExpeditionStatus.ACTIVE.value else False

            formatted_results.append({
                'id': exp_id,
                'name': name,
                'owner_chat_id': owner_chat_id,
                'status': status,
                'deadline': deadline.isoformat() if deadline else None,
                'created_at': created_at.isoformat(),
                'completed_at': completed_at.isoformat() if completed_at else None,
                'total_items': total_items,
                'total_required_quantity': total_required_qty,
                'total_consumed_quantity': total_consumed_qty,
                'completion_percentage': round(completion_pct, 1),
                'is_overdue': is_overdue
            })

        return formatted_results, total_count

    def cleanup_export_files(self, older_than_hours: int = 24) -> int:
        """
        Clean up old export files from temp directory.

        Args:
            older_than_hours: Delete files older than this many hours

        Returns:
            Number of files deleted
        """
        self._log_operation("CleanupExportFiles", older_than_hours=older_than_hours)

        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        deleted_count = 0

        try:
            for filename in os.listdir(self.temp_dir):
                if filename.startswith(('expedition_export_', 'pirate_activity_', 'profit_loss_report_')):
                    filepath = os.path.join(self.temp_dir, filename)
                    file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))

                    if file_modified < cutoff_time:
                        os.remove(filepath)
                        deleted_count += 1
                        self.logger.debug(f"Deleted old export file: {filename}")

        except Exception as e:
            self.logger.error(f"Error cleaning up export files: {e}")

        self.logger.info(f"Cleaned up {deleted_count} old export files")
        return deleted_count

    def generate_expedition_summary_report(self, expedition_ids: List[int]) -> str:
        """
        Generate a comprehensive summary report for multiple expeditions.

        Args:
            expedition_ids: List of expedition IDs to include

        Returns:
            File path to the generated summary report
        """
        if not expedition_ids:
            raise ValidationError("No expedition IDs provided")

        self._log_operation("GenerateExpeditionSummaryReport",
                          expedition_count=len(expedition_ids))

        # Get expedition details
        placeholders = ','.join(['%s'] * len(expedition_ids))

        query = f"""
            SELECT e.id, e.name, e.owner_chat_id, e.status, e.deadline,
                   e.created_at, e.completed_at,
                   COUNT(DISTINCT ei.id) as total_items,
                   COUNT(DISTINCT ea.id) as total_consumptions,
                   COUNT(DISTINCT ep.original_name) as unique_consumers,
                   COALESCE(SUM(ei.quantity_required), 0) as total_required_quantity,
                   COALESCE(SUM(ei.quantity_consumed), 0) as total_consumed_quantity,
                   COALESCE(SUM(ea.total_cost), 0) as total_revenue,
                   COALESCE(SUM(CASE WHEN ea.payment_status = %s THEN ea.total_cost ELSE 0 END), 0) as total_collected
            FROM expeditions e
            LEFT JOIN expedition_items ei ON e.id = ei.expedition_id
            LEFT JOIN expedition_assignments ea ON e.id = ea.expedition_id
            LEFT JOIN expedition_pirates ep ON ea.pirate_id = ep.id
            WHERE e.id IN ({placeholders})
            GROUP BY e.id, e.name, e.owner_chat_id, e.status, e.deadline, e.created_at, e.completed_at
            ORDER BY e.created_at DESC
        """

        params = [PaymentStatus.PAID.value] + expedition_ids
        results = self._execute_query(query, tuple(params), fetch_all=True)

        # Generate comprehensive report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"expedition_summary_report_{timestamp}.csv"
        filepath = os.path.join(self.temp_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow([
                'Expedition ID', 'Name', 'Owner Chat ID', 'Status',
                'Created At', 'Completed At', 'Deadline',
                'Total Items', 'Total Consumptions', 'Unique Consumers',
                'Required Quantity', 'Consumed Quantity', 'Completion %',
                'Total Revenue', 'Total Collected', 'Outstanding Debt',
                'Collection Rate %', 'Days Active', 'Is Overdue'
            ])

            # Aggregate statistics
            total_revenue_all = 0
            total_collected_all = 0
            total_expeditions = len(results or [])

            # Write data
            for row in results or []:
                (exp_id, name, owner_chat_id, status, deadline, created_at, completed_at,
                 total_items, total_consumptions, unique_consumers, total_required_qty,
                 total_consumed_qty, total_revenue, total_collected) = row

                completion_pct = (total_consumed_qty / total_required_qty * 100) if total_required_qty > 0 else 0
                outstanding_debt = total_revenue - total_collected
                collection_rate = (total_collected / total_revenue * 100) if total_revenue > 0 else 0

                # Calculate days active
                end_date = completed_at or datetime.now()
                days_active = (end_date - created_at).days

                is_overdue = deadline and deadline < datetime.now() if status == ExpeditionStatus.ACTIVE.value else False

                writer.writerow([
                    exp_id, name, owner_chat_id, status,
                    created_at.strftime("%Y-%m-%d"),
                    completed_at.strftime("%Y-%m-%d") if completed_at else '',
                    deadline.strftime("%Y-%m-%d") if deadline else '',
                    total_items, total_consumptions, unique_consumers,
                    total_required_qty, total_consumed_qty, f"{completion_pct:.1f}%",
                    f"{total_revenue:.2f}", f"{total_collected:.2f}", f"{outstanding_debt:.2f}",
                    f"{collection_rate:.1f}%", days_active, 'Yes' if is_overdue else 'No'
                ])

                total_revenue_all += total_revenue
                total_collected_all += total_collected

            # Write summary statistics
            if results:
                writer.writerow([])  # Empty row
                writer.writerow(['SUMMARY STATISTICS'])
                writer.writerow(['Total Expeditions', total_expeditions])
                writer.writerow(['Total Revenue', f"{total_revenue_all:.2f}"])
                writer.writerow(['Total Collected', f"{total_collected_all:.2f}"])
                writer.writerow(['Total Outstanding', f"{total_revenue_all - total_collected_all:.2f}"])
                writer.writerow(['Overall Collection Rate', f"{total_collected_all / total_revenue_all * 100:.1f}%" if total_revenue_all > 0 else '0%'])

        self.logger.info(f"Generated expedition summary report: {filepath}")
        return filepath