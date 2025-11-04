"""
WebSocket service for real-time expedition updates and notifications.
Handles real-time communication for expedition progress, alerts, and completion notifications.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import json
import threading
from flask_socketio import SocketIO, emit, join_room, leave_room
from services.base_service import BaseService, ServiceError
from core.interfaces import IWebSocketService
from models.expedition import ExpeditionStatus


class WebSocketService(BaseService, IWebSocketService):
    """WebSocket service for real-time expedition updates."""

    def __init__(self, socketio: Optional[SocketIO] = None):
        super().__init__()
        self.socketio = socketio
        self._subscribers: Dict[int, Set[int]] = {}  # expedition_id -> set of user_ids
        self._user_sessions: Dict[int, str] = {}  # user_id -> session_id
        self._lock = threading.Lock()
        self._alert_thresholds = {
            'critical': timedelta(hours=1),
            'urgent': timedelta(hours=6),
            'warning': timedelta(days=1),
            'info': timedelta(days=3)
        }

    def set_socketio(self, socketio: SocketIO):
        """Set the SocketIO instance."""
        self.socketio = socketio

    def broadcast_expedition_progress(self, expedition_id: int, progress_data: Dict[str, Any]) -> bool:
        """Broadcast expedition progress updates to connected clients."""
        try:
            if not self.socketio:
                self.logger.warning("SocketIO not initialized, cannot broadcast progress")
                return False

            # Get expedition details for context
            expedition_query = """
                SELECT name, status, created_at, deadline, owner_user_id
                FROM expeditions
                WHERE id = %s
            """
            expedition = self._execute_query(expedition_query, (expedition_id,), fetch_one=True)

            if not expedition:
                self.logger.error(f"Expedition {expedition_id} not found for progress broadcast")
                return False

            expedition_name, status, created_at, deadline, owner_user_id = expedition

            # Prepare progress message
            progress_message = {
                'type': 'expedition_progress',
                'expedition_id': expedition_id,
                'expedition_name': expedition_name,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'data': progress_data
            }

            # Broadcast to expedition room
            room_name = f"expedition_{expedition_id}"
            self.socketio.emit('expedition_progress', progress_message, room=room_name)

            # Also send to owner directly
            owner_room = f"user_{owner_user_id}"
            self.socketio.emit('expedition_progress', progress_message, room=owner_room)

            self._log_operation("broadcast_expedition_progress",
                              expedition_id=expedition_id,
                              subscribers=len(self._subscribers.get(expedition_id, set())))

            return True

        except Exception as e:
            self.logger.error(f"Failed to broadcast expedition progress: {e}", exc_info=True)
            return False

    def send_deadline_alert(self, expedition_id: int, alert_type: str, alert_data: Dict[str, Any]) -> bool:
        """Send deadline alert notifications."""
        try:
            if not self.socketio:
                self.logger.warning("SocketIO not initialized, cannot send deadline alert")
                return False

            # Get expedition details
            expedition_query = """
                SELECT name, deadline, owner_user_id
                FROM expeditions
                WHERE id = %s
            """
            expedition = self._execute_query(expedition_query, (expedition_id,), fetch_one=True)

            if not expedition:
                self.logger.error(f"Expedition {expedition_id} not found for deadline alert")
                return False

            expedition_name, deadline, owner_user_id = expedition

            # Calculate time remaining
            time_remaining = deadline - datetime.now() if deadline else None

            # Prepare alert message
            alert_message = {
                'type': 'deadline_alert',
                'alert_type': alert_type,
                'expedition_id': expedition_id,
                'expedition_name': expedition_name,
                'deadline': deadline.isoformat() if deadline else None,
                'time_remaining_hours': time_remaining.total_seconds() / 3600 if time_remaining else None,
                'timestamp': datetime.now().isoformat(),
                'data': alert_data
            }

            # Send to expedition room
            room_name = f"expedition_{expedition_id}"
            self.socketio.emit('deadline_alert', alert_message, room=room_name)

            # Send priority alert to owner
            owner_room = f"user_{owner_user_id}"
            self.socketio.emit('priority_alert', alert_message, room=owner_room)

            self._log_operation("send_deadline_alert",
                              expedition_id=expedition_id,
                              alert_type=alert_type,
                              owner_user_id=owner_user_id)

            return True

        except Exception as e:
            self.logger.error(f"Failed to send deadline alert: {e}", exc_info=True)
            return False

    def notify_expedition_completion(self, expedition_id: int, completion_data: Dict[str, Any]) -> bool:
        """Notify about expedition completion."""
        try:
            if not self.socketio:
                self.logger.warning("SocketIO not initialized, cannot send completion notification")
                return False

            # Get expedition details and completion stats
            expedition_query = """
                SELECT e.name, e.status, e.created_at, e.deadline, e.owner_user_id,
                       COUNT(ei.id) as total_items,
                       COUNT(ea.id) as consumed_items
                FROM expeditions e
                LEFT JOIN expedition_items ei ON e.id = ei.expedition_id
                LEFT JOIN expedition_assignments ea ON ei.id = ea.expedition_item_id
                WHERE e.id = %s
                GROUP BY e.id, e.name, e.status, e.created_at, e.deadline, e.owner_user_id
            """
            expedition_data = self._execute_query(expedition_query, (expedition_id,), fetch_one=True)

            if not expedition_data:
                self.logger.error(f"Expedition {expedition_id} not found for completion notification")
                return False

            (expedition_name, status, created_at, deadline, owner_user_id,
             total_items, consumed_items) = expedition_data

            # Calculate completion metrics
            completion_rate = (consumed_items / total_items * 100) if total_items > 0 else 0
            duration = datetime.now() - created_at if created_at else None

            # Prepare completion message
            completion_message = {
                'type': 'expedition_completion',
                'expedition_id': expedition_id,
                'expedition_name': expedition_name,
                'status': status,
                'completion_rate': round(completion_rate, 2),
                'total_items': total_items,
                'consumed_items': consumed_items,
                'duration_hours': duration.total_seconds() / 3600 if duration else None,
                'completed_on_time': deadline is None or datetime.now() <= deadline,
                'timestamp': datetime.now().isoformat(),
                'data': completion_data
            }

            # Broadcast completion to all subscribers
            room_name = f"expedition_{expedition_id}"
            self.socketio.emit('expedition_completed', completion_message, room=room_name)

            # Send special notification to owner
            owner_room = f"user_{owner_user_id}"
            self.socketio.emit('expedition_completed', completion_message, room=owner_room)

            # Clean up subscribers for completed expedition
            with self._lock:
                if expedition_id in self._subscribers:
                    del self._subscribers[expedition_id]

            self._log_operation("notify_expedition_completion",
                              expedition_id=expedition_id,
                              completion_rate=completion_rate,
                              owner_user_id=owner_user_id)

            return True

        except Exception as e:
            self.logger.error(f"Failed to send completion notification: {e}", exc_info=True)
            return False

    def subscribe_to_expedition(self, user_id: int, expedition_id: int) -> bool:
        """Subscribe user to expedition updates."""
        try:
            with self._lock:
                if expedition_id not in self._subscribers:
                    self._subscribers[expedition_id] = set()
                self._subscribers[expedition_id].add(user_id)

            # Join user to expedition room if session exists
            if self.socketio and user_id in self._user_sessions:
                room_name = f"expedition_{expedition_id}"
                # Note: join_room requires session context, this would be called from socket event

            self._log_operation("subscribe_to_expedition",
                              user_id=user_id,
                              expedition_id=expedition_id)

            return True

        except Exception as e:
            self.logger.error(f"Failed to subscribe user to expedition: {e}", exc_info=True)
            return False

    def unsubscribe_from_expedition(self, user_id: int, expedition_id: int) -> bool:
        """Unsubscribe user from expedition updates."""
        try:
            with self._lock:
                if expedition_id in self._subscribers:
                    self._subscribers[expedition_id].discard(user_id)
                    if not self._subscribers[expedition_id]:
                        del self._subscribers[expedition_id]

            # Leave expedition room if session exists
            if self.socketio and user_id in self._user_sessions:
                room_name = f"expedition_{expedition_id}"
                # Note: leave_room requires session context

            self._log_operation("unsubscribe_from_expedition",
                              user_id=user_id,
                              expedition_id=expedition_id)

            return True

        except Exception as e:
            self.logger.error(f"Failed to unsubscribe user from expedition: {e}", exc_info=True)
            return False

    def get_active_subscribers(self, expedition_id: int) -> List[int]:
        """Get list of active subscribers for an expedition."""
        with self._lock:
            return list(self._subscribers.get(expedition_id, set()))

    def broadcast_system_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Broadcast system-wide alerts."""
        try:
            if not self.socketio:
                self.logger.warning("SocketIO not initialized, cannot broadcast system alert")
                return False

            # Prepare system alert message
            alert_message = {
                'type': 'system_alert',
                'timestamp': datetime.now().isoformat(),
                'data': alert_data
            }

            # Broadcast to all connected clients
            self.socketio.emit('system_alert', alert_message, broadcast=True)

            self._log_operation("broadcast_system_alert", alert_type=alert_data.get('type', 'unknown'))

            return True

        except Exception as e:
            self.logger.error(f"Failed to broadcast system alert: {e}", exc_info=True)
            return False

    def check_deadline_alerts(self) -> int:
        """Check all expeditions for deadline alerts and send notifications."""
        alerts_sent = 0

        try:
            # Get all active expeditions with deadlines
            query = """
                SELECT id, name, deadline, owner_user_id
                FROM expeditions
                WHERE status IN ('active', 'in_progress')
                AND deadline IS NOT NULL
            """
            expeditions = self._execute_query(query, fetch_all=True)

            if not expeditions:
                return 0

            current_time = datetime.now()

            for expedition_id, name, deadline, owner_user_id in expeditions:
                time_remaining = deadline - current_time

                # Determine alert type based on time remaining
                alert_type = None
                if time_remaining <= self._alert_thresholds['critical']:
                    alert_type = 'critical'
                elif time_remaining <= self._alert_thresholds['urgent']:
                    alert_type = 'urgent'
                elif time_remaining <= self._alert_thresholds['warning']:
                    alert_type = 'warning'
                elif time_remaining <= self._alert_thresholds['info']:
                    alert_type = 'info'

                if alert_type:
                    alert_data = {
                        'message': f"Expedition '{name}' deadline approaching",
                        'time_remaining': str(time_remaining),
                        'hours_remaining': time_remaining.total_seconds() / 3600
                    }

                    if self.send_deadline_alert(expedition_id, alert_type, alert_data):
                        alerts_sent += 1

            if alerts_sent > 0:
                self._log_operation("check_deadline_alerts", alerts_sent=alerts_sent)

            return alerts_sent

        except Exception as e:
            self.logger.error(f"Failed to check deadline alerts: {e}", exc_info=True)
            return 0

    def get_expedition_metrics(self, expedition_id: int) -> Dict[str, Any]:
        """Get real-time metrics for an expedition."""
        try:
            # Get comprehensive expedition metrics
            metrics_query = """
                SELECT
                    e.name,
                    e.status,
                    e.created_at,
                    e.deadline,
                    COUNT(DISTINCT ei.id) as total_items,
                    COUNT(DISTINCT ea.id) as consumed_items,
                    COUNT(DISTINCT ep.original_name) as unique_consumers,
                    SUM(CASE WHEN ea.payment_status = 'paid' THEN ea.total_cost ELSE 0 END) as paid_amount,
                    SUM(CASE WHEN ea.payment_status = 'pending' THEN ea.total_cost ELSE 0 END) as pending_amount
                FROM expeditions e
                LEFT JOIN expedition_items ei ON e.id = ei.expedition_id
                LEFT JOIN expedition_assignments ea ON ei.id = ea.expedition_item_id
                LEFT JOIN expedition_pirates ep ON ea.pirate_id = ep.id
                WHERE e.id = %s
                GROUP BY e.id, e.name, e.status, e.created_at, e.deadline
            """

            metrics_data = self._execute_query(metrics_query, (expedition_id,), fetch_one=True)

            if not metrics_data:
                return {}

            (name, status, created_at, deadline, total_items, consumed_items,
             unique_consumers, paid_amount, pending_amount) = metrics_data

            # Calculate derived metrics
            completion_rate = (consumed_items / total_items * 100) if total_items > 0 else 0
            total_revenue = (paid_amount or 0) + (pending_amount or 0)

            current_time = datetime.now()
            duration = current_time - created_at if created_at else timedelta(0)
            time_remaining = deadline - current_time if deadline else None

            return {
                'expedition_id': expedition_id,
                'name': name,
                'status': status,
                'completion_rate': round(completion_rate, 2),
                'total_items': total_items or 0,
                'consumed_items': consumed_items or 0,
                'unique_consumers': unique_consumers or 0,
                'total_revenue': float(total_revenue) if total_revenue else 0.0,
                'paid_amount': float(paid_amount) if paid_amount else 0.0,
                'pending_amount': float(pending_amount) if pending_amount else 0.0,
                'duration_hours': duration.total_seconds() / 3600,
                'time_remaining_hours': time_remaining.total_seconds() / 3600 if time_remaining else None,
                'is_overdue': time_remaining.total_seconds() < 0 if time_remaining else False,
                'active_subscribers': len(self.get_active_subscribers(expedition_id))
            }

        except Exception as e:
            self.logger.error(f"Failed to get expedition metrics: {e}", exc_info=True)
            return {}