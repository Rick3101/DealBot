"""
Modern Flask application using the new service container architecture.
This replaces app.py with proper dependency injection and configuration management.
"""

import os
import logging
import nest_asyncio
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from telegram import Update

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables

# Import new configuration and service system
from core.config import get_config, configure_logging, print_config_summary
from core.modern_service_container import initialize_services, health_check_services, get_service_diagnostics
from database import initialize_database
from database.schema import initialize_schema
from core.bot_manager import BotManager
from core.handler_registry import configure_handlers


class BotApplication:
    """
    Main application class that manages the bot lifecycle and services.
    Encapsulates Flask app, services, and bot management.
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self.flask_app = None
        self.socketio = None
        self.bot_manager = None
        self.services_initialized = False
        
        # Configure logging first
        configure_logging()
        self.logger.info("BotApplication initializing...")
        
        # Print configuration summary
        print_config_summary()
        
        # Validate configuration
        config_errors = self.config.validate()
        if config_errors:
            self.logger.error(f"Configuration errors: {config_errors}")
            raise ValueError(f"Invalid configuration: {', '.join(config_errors)}")
    
    def initialize_services(self):
        """Initialize all application services."""
        if self.services_initialized:
            return
        
        self.logger.info("Initializing services...")
        
        try:
            # Initialize database connection pool
            initialize_database(database_url=self.config.database.url)
            self.logger.info("Database connection pool initialized")
            
            # Initialize database schema (tables, indexes, default data)
            initialize_schema()
            self.logger.info("Database schema initialized")
            
            # Initialize modern service container
            service_config = {
                'environment': self.config.environment.value,
                'debug': self.config.debug,
                'database': self.config.database.to_dict() if hasattr(self.config.database, 'to_dict') else {}
            }
            
            initialize_services(service_config)
            self.logger.info("Service container initialized")
            
            # Verify services health
            health = health_check_services()
            if not health.get('container', {}).get('healthy', False):
                self.logger.warning("Some services are not healthy:")
                for service, status in health.get('services', {}).items():
                    if isinstance(status, dict):
                        if not status.get('healthy', False):
                            self.logger.warning(f"  - {service}: {status.get('message', 'Unknown error')}")
                    else:
                        # Handle case where status is a bool
                        if not status:
                            self.logger.warning(f"  - {service}: Not healthy")
            
            self.services_initialized = True
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}", exc_info=True)
            raise
    
    def create_flask_app(self) -> Flask:
        """Create and configure Flask application."""
        if self.flask_app is not None:
            return self.flask_app
        
        self.logger.info("Creating Flask application...")
        
        # Create Flask app
        app = Flask(__name__)
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'expedition-websocket-key')

        # Enable CORS for all routes - using after_request for better compatibility
        @app.after_request
        def after_request(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,X-Chat-ID,X-Telegram-Init-Data')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
            return response

        self.logger.info("CORS enabled with after_request handler")

        # Initialize SocketIO with threading async mode for Windows compatibility
        self.socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode='threading',
            logger=True,
            engineio_logger=True,
            ping_timeout=60,
            ping_interval=25
        )

        # Apply nest_asyncio for async compatibility
        nest_asyncio.apply()

        # Configure routes and WebSocket events
        self._configure_routes(app)
        self._configure_websocket_events()

        # Set SocketIO instance in WebSocket service
        try:
            from core.modern_service_container import get_websocket_service
            websocket_service = get_websocket_service()
            websocket_service.set_socketio(self.socketio)
            self.logger.info("SocketIO connected to WebSocket service")
        except Exception as e:
            self.logger.warning(f"Failed to connect SocketIO to WebSocket service: {e}")

        self.flask_app = app
        self.logger.info("Flask application created with SocketIO")
        
        return app
    
    def initialize_bot(self):
        """Initialize the Telegram bot manager."""
        if self.bot_manager is not None:
            return
        
        self.logger.info("Initializing bot manager...")
        
        try:
            webhook_url = f"{self.config.telegram.webhook_url}/{self.config.telegram.bot_token}"
            
            self.bot_manager = BotManager(
                self.config.telegram.bot_token, 
                webhook_url
            )
            
            # Configure handlers using the service container
            self.bot_manager.set_handler_configurator(configure_handlers)
            
            self.logger.info(f"Bot manager initialized with webhook URL: {webhook_url}")
            self.logger.info("Webhook has been set up and is ready to receive updates")
            self.logger.info(f"Bot manager instance ID: {id(self.bot_manager)}")
            
            # Start worker thread immediately - async initialization will happen in worker
            self.bot_manager.start_worker()
            self.logger.info("Bot manager worker started - initialization will complete async")
            
            # Wait for bot initialization to complete properly
            import time
            max_wait = 35  # Maximum 35 seconds (longer than bot manager timeout of 25s)
            wait_time = 0
            
            while not self.bot_manager.is_ready and wait_time < max_wait:
                time.sleep(0.5)
                wait_time += 0.5
                self.logger.debug(f"Waiting for bot initialization... {wait_time}s")
            
            if self.bot_manager.is_ready:
                self.logger.info(f"Bot ready after {wait_time}s - Bot manager ID: {id(self.bot_manager)}")
            else:
                self.logger.error(f"Bot failed to initialize within {max_wait}s")
                raise RuntimeError("Bot initialization timeout")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {e}", exc_info=True)
            raise
    
    def _configure_routes(self, app: Flask):
        """Configure Flask routes."""
        
        
        @app.route(f"/{self.config.telegram.bot_token}", methods=["POST"])
        def webhook():
            """Handle incoming telegram webhooks."""
            self.logger.info("=== WEBHOOK REQUEST RECEIVED ===")
            try:
                if not self.bot_manager:
                    self.logger.warning("Bot manager not initialized, rejecting webhook")
                    return jsonify({"error": "Bot manager not initialized"}), 503
                
                # Force debug the bot manager state
                self.logger.info(f"Webhook - Bot manager instance ID: {id(self.bot_manager)}")
                self.logger.info(f"Webhook - Bot manager exists: {self.bot_manager is not None}")
                if self.bot_manager:
                    self.logger.info(f"Webhook - Bot manager ready: {self.bot_manager.is_ready}")
                    self.logger.info(f"Webhook - App bot exists: {self.bot_manager.app_bot is not None}")
                    if self.bot_manager.app_bot:
                        self.logger.info(f"Webhook - Bot exists: {self.bot_manager.app_bot.bot is not None}")
                    self.logger.info(f"Webhook - Initialized: {self.bot_manager._is_initialized}")
                    self.logger.info(f"Webhook - Worker alive: {self.bot_manager.worker_thread and self.bot_manager.worker_thread.is_alive()}")
                
                if not self.bot_manager.is_ready:
                    # Log detailed status for debugging
                    self.logger.warning(f"Bot manager object id: {id(self.bot_manager)}")
                    self.logger.warning(f"Bot manager app_bot: {self.bot_manager.app_bot is not None}")
                    self.logger.warning(f"Bot manager initialized: {self.bot_manager._is_initialized}")
                    status = self.bot_manager.get_health_status()
                    self.logger.warning(f"Bot not ready, rejecting webhook. Status: {status}")
                    return jsonify({"error": "Bot not ready", "status": status}), 503

                # Parse telegram update
                update_data = request.get_json(force=True)
                if not update_data:
                    return jsonify({"error": "No data"}), 400
                    
                update = Update.de_json(update_data, self.bot_manager.app_bot.bot)
                
                # Queue update for processing
                self.logger.info(f"Queuing update: {update.update_id}")
                if self.bot_manager.queue_update(update):
                    self.logger.info(f"Update {update.update_id} queued successfully")
                    return jsonify({"status": "ok"}), 200
                else:
                    self.logger.warning(f"Failed to queue update {update.update_id} - queue full")
                    return jsonify({"error": "Queue full"}), 503
                    
            except Exception as e:
                self.logger.error(f"Webhook error: {e}", exc_info=True)
                return jsonify({"error": "Internal server error"}), 500
        
        @app.route("/")
        def health():
            """Simple health check."""
            return jsonify({
                "status": "healthy",
                "message": "Bot online",
                "version": os.getenv("RENDER_GIT_COMMIT", "local")[:8] if os.getenv("RENDER_GIT_COMMIT") else "local"
            })
        
        @app.route("/test", methods=["GET", "POST"])
        def test_endpoint():
            """Test endpoint to verify Flask is working."""
            self.logger.info(f"Test endpoint hit: {request.method}")
            return jsonify({"message": "Flask is working", "method": request.method})
        
        @app.route("/health")
        def health_detailed():
            """Detailed health check with full system status."""
            try:
                # Get service diagnostics
                diagnostics = get_service_diagnostics()

                # Bot health
                bot_status = {}
                if self.bot_manager:
                    bot_status = self.bot_manager.get_health_status()
                else:
                    bot_status = {"bot_ready": False, "error": "Bot manager not initialized"}

                # Database connection pool health
                db_pool_status = {}
                pool_warnings = []
                try:
                    from database import get_db_manager
                    db_manager = get_db_manager()
                    pool_status = db_manager.get_pool_status()
                    db_pool_status = pool_status

                    # Check pool utilization
                    used = pool_status.get('used_connections', 0)
                    max_conn = pool_status.get('max_connections', 1)
                    utilization = (used / max_conn * 100) if max_conn > 0 else 0

                    if utilization > 80:
                        pool_warnings.append(f"High connection pool utilization: {utilization:.1f}%")

                    db_pool_status['utilization_percent'] = round(utilization, 1)
                    db_pool_status['healthy'] = utilization < 90

                except Exception as pool_error:
                    db_pool_status = {"error": str(pool_error), "healthy": False}
                    pool_warnings.append(f"Connection pool check failed: {pool_error}")

                # Overall status
                services_healthy = diagnostics.get('health', {}).get('container', {}).get('healthy', False)
                bot_healthy = bot_status.get("bot_ready", False)
                pool_healthy = db_pool_status.get('healthy', True)
                overall_healthy = services_healthy and bot_healthy and pool_healthy

                response = {
                    "status": "healthy" if overall_healthy else "degraded",
                    "timestamp": __import__('datetime').datetime.now().isoformat(),
                    "services": diagnostics,
                    "bot": bot_status,
                    "database_pool": db_pool_status,
                    "warnings": pool_warnings,
                    "config": {
                        "environment": self.config.environment.value,
                        "debug": self.config.debug,
                        "webhook_enabled": self.config.telegram.use_webhook
                    },
                    "version": os.getenv("RENDER_GIT_COMMIT", "local")[:8] if os.getenv("RENDER_GIT_COMMIT") else "local"
                }

                return jsonify(response), 200 if overall_healthy else 503

            except Exception as e:
                self.logger.error(f"Health check failed: {e}", exc_info=True)
                return jsonify({
                    "status": "error",
                    "error": str(e),
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                }), 503
        
        @app.route("/services")
        def services_info():
            """Get detailed service information."""
            try:
                diagnostics = get_service_diagnostics()
                return jsonify(diagnostics)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @app.route("/config")
        def config_info():
            """Get configuration information (sensitive data hidden)."""
            try:
                return jsonify(self.config.to_dict())
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # ===== MINI APP STATIC FILES SERVING =====

        @app.route("/webapp")
        @app.route("/webapp/")
        def serve_webapp():
            """Serve the Mini App index.html."""
            try:
                import os
                webapp_dir = os.path.join(os.path.dirname(__file__), 'webapp', 'dist')
                index_path = os.path.join(webapp_dir, 'index.html')

                if os.path.exists(index_path):
                    from flask import send_file
                    return send_file(index_path)
                else:
                    return jsonify({
                        "error": "Mini App not built",
                        "message": "Run 'cd webapp && npm run build' to build the Mini App"
                    }), 404
            except Exception as e:
                return jsonify({"error": f"Failed to serve Mini App: {str(e)}"}), 500

        @app.route("/webapp/<path:filename>")
        def serve_webapp_assets(filename):
            """Serve Mini App static assets."""
            try:
                import os
                from flask import send_from_directory

                webapp_dir = os.path.join(os.path.dirname(__file__), 'webapp', 'dist')

                if os.path.exists(webapp_dir):
                    return send_from_directory(webapp_dir, filename)
                else:
                    return jsonify({
                        "error": "Mini App not built",
                        "message": "Run 'cd webapp && npm run build' to build the Mini App"
                    }), 404
            except Exception as e:
                return jsonify({"error": f"Failed to serve asset: {str(e)}"}), 500
        
        
        @app.route("/api/dashboard")
        def api_dashboard():
            """API endpoint for dashboard data."""
            try:
                from core.modern_service_container import get_product_service, get_user_service, get_sales_service
                from database import get_database_manager
                
                # Get services
                product_service = get_product_service()
                user_service = get_user_service(None)
                sales_service = get_sales_service()
                db_manager = get_database_manager()
                
                # Get stats from database
                with db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        # Count products
                        cur.execute("SELECT COUNT(*) FROM Produtos")
                        total_products = cur.fetchone()[0]
                        
                        # Count sales
                        cur.execute("SELECT COUNT(*) FROM Vendas")
                        total_sales = cur.fetchone()[0]
                        
                        # Count users
                        cur.execute("SELECT COUNT(*) FROM Usuarios")
                        total_users = cur.fetchone()[0]
                        
                        # Calculate total revenue
                        cur.execute("SELECT COALESCE(SUM(preco_total), 0) FROM Vendas")
                        total_revenue = float(cur.fetchone()[0] or 0)
                
                return jsonify({
                    "products": total_products,
                    "sales": total_sales,
                    "users": total_users,
                    "revenue": f"R$ {total_revenue:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                })
            except Exception as e:
                self.logger.error(f"Dashboard API error: {e}")
                return jsonify({"error": "Erro ao carregar dados"}), 500
        
        @app.route("/api/products")
        def api_products():
            """API endpoint for products data."""
            try:
                from core.modern_service_container import get_product_service

                product_service = get_product_service()
                products_with_stock = product_service.get_products_with_stock()

                products = []
                for item in products_with_stock:
                    product = item.product
                    products.append({
                        "id": product.id,
                        "name": product.nome,
                        "emoji": product.emoji or "",
                        "price": float(item.average_price),
                        "stock": item.total_quantity,
                        "status": "Ativo" if item.total_quantity > 0 else "Inativo"
                    })

                return jsonify({"products": products})
            except Exception as e:
                self.logger.error(f"Products API error: {e}", exc_info=True)
                return jsonify({"error": "Erro ao carregar produtos"}), 500
        
        @app.route("/api/sales")
        def api_sales():
            """API endpoint for sales data."""
            try:
                from database import get_database_manager
                
                db_manager = get_database_manager()
                
                with db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT v.id, v.data_venda, v.comprador_nome, v.preco_total,
                                   CASE WHEN p.valor_pago >= v.preco_total THEN 'Pago' ELSE 'Pendente' END as status,
                                   STRING_AGG(pr.emoji || ' ' || pr.nome, ', ') as produtos
                            FROM Vendas v
                            LEFT JOIN Pagamentos p ON v.comprador_nome = p.usuario_nome
                            LEFT JOIN ItensVenda iv ON v.id = iv.venda_id
                            LEFT JOIN Produtos pr ON iv.produto_id = pr.id
                            GROUP BY v.id, v.data_venda, v.comprador_nome, v.preco_total, p.valor_pago
                            ORDER BY v.data_venda DESC
                            LIMIT 50
                        """)
                        
                        sales = []
                        for row in cur.fetchall():
                            sales.append({
                                "id": row[0],
                                "date": row[1].strftime("%d/%m %H:%M") if row[1] else "",
                                "customer": row[2],
                                "total": f"R$ {row[3]:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                                "status": row[4],
                                "products": row[5] or "N/A"
                            })
                
                return jsonify({"sales": sales})
            except Exception as e:
                self.logger.error(f"Sales API error: {e}")
                return jsonify({"error": "Erro ao carregar vendas"}), 500
        
        @app.route("/api/users")
        def api_users():
            """API endpoint for users data."""
            try:
                from database import get_database_manager

                db_manager = get_database_manager()

                with db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT u.username, u.nivel,
                                   COALESCE(SUM(v.preco_total), 0) as total_compras,
                                   MAX(v.data_venda) as ultimo_acesso
                            FROM Usuarios u
                            LEFT JOIN Vendas v ON u.username = v.comprador_nome
                            GROUP BY u.username, u.nivel
                            ORDER BY total_compras DESC
                        """)

                        users = []
                        for row in cur.fetchall():
                            users.append({
                                "username": row[0],
                                "level": row[1].capitalize() if row[1] else "User",
                                "total_purchases": f"R$ {row[2]:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                                "last_access": row[3].strftime("%d/%m %H:%M") if row[3] else "Nunca",
                                "status": "Ativo"
                            })

                return jsonify({"users": users})
            except Exception as e:
                self.logger.error(f"Users API error: {e}")
                return jsonify({"error": "Erro ao carregar usuários"}), 500

        @app.route("/api/buyers")
        def api_buyers():
            """API endpoint for getting unique buyer names from sales."""
            try:
                from database import get_database_manager

                db_manager = get_database_manager()

                with db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT DISTINCT comprador
                            FROM Vendas
                            WHERE comprador IS NOT NULL
                            ORDER BY comprador
                        """)

                        buyers = [{"name": row[0]} for row in cur.fetchall()]

                return jsonify({"buyers": buyers})
            except Exception as e:
                import traceback
                self.logger.error(f"Buyers API error: {e}\n{traceback.format_exc()}")
                return jsonify({"error": "Erro ao carregar compradores", "detail": str(e)}), 500

        # ===== EXPEDITION API ENDPOINTS =====

        @app.route("/api/expeditions", methods=["GET", "POST"])
        def api_expeditions():
            """API endpoint for expedition management."""
            try:
                from core.modern_service_container import get_expedition_service, get_user_service
                from models.expedition import ExpeditionCreateRequest

                expedition_service = get_expedition_service()
                user_service = get_user_service(None)

                if request.method == "GET":
                    # Check authentication - require owner permission for full list
                    chat_id = request.headers.get('X-Chat-ID')
                    if not chat_id:
                        return jsonify({"error": "Authentication required"}), 401

                    try:
                        chat_id = int(chat_id)
                        user_level = user_service.get_user_permission_level(chat_id)
                        if not user_level:
                            return jsonify({"error": "User not authenticated"}), 401
                    except (ValueError, TypeError):
                        return jsonify({"error": "Invalid chat ID"}), 400

                    # Get expeditions based on permission level
                    if user_level.value in ['owner', 'admin']:
                        expeditions = expedition_service.get_all_expeditions()
                    else:
                        expeditions = expedition_service.get_expeditions_by_owner(chat_id)

                    # Convert to response format
                    expeditions_data = []
                    for exp in expeditions:
                        expeditions_data.append({
                            "id": exp.id,
                            "name": exp.name,
                            "owner_chat_id": exp.owner_chat_id,
                            "status": exp.status.value,
                            "deadline": exp.deadline.isoformat() if exp.deadline else None,
                            "created_at": exp.created_at.isoformat() if exp.created_at else None,
                            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None
                        })

                    return jsonify({"expeditions": expeditions_data})

                elif request.method == "POST":
                    # Create new expedition - require owner permission
                    chat_id = request.headers.get('X-Chat-ID')
                    if not chat_id:
                        return jsonify({"error": "Authentication required"}), 401

                    try:
                        chat_id = int(chat_id)
                        user_level = user_service.get_user_permission_level(chat_id)
                        if not user_level or user_level.value != 'owner':
                            return jsonify({"error": "Owner permission required"}), 403
                    except (ValueError, TypeError):
                        return jsonify({"error": "Invalid chat ID"}), 400

                    # Parse request data
                    data = request.get_json()
                    if not data:
                        return jsonify({"error": "Request body required"}), 400

                    # Validate required fields
                    if not data.get('name'):
                        return jsonify({"error": "Expedition name is required"}), 400

                    # Create expedition request
                    deadline = None
                    if data.get('deadline'):
                        try:
                            deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
                        except ValueError:
                            return jsonify({"error": "Invalid deadline format"}), 400

                    create_request = ExpeditionCreateRequest(
                        name=data['name'],
                        owner_chat_id=chat_id,
                        deadline=deadline
                    )

                    # Create expedition
                    expedition = expedition_service.create_expedition(create_request)

                    return jsonify({
                        "id": expedition.id,
                        "name": expedition.name,
                        "owner_chat_id": expedition.owner_chat_id,
                        "status": expedition.status.value,
                        "deadline": expedition.deadline.isoformat() if expedition.deadline else None,
                        "created_at": expedition.created_at.isoformat() if expedition.created_at else None
                    }), 201

            except Exception as e:
                self.logger.error(f"Expeditions API error: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @app.route("/api/expeditions/<int:expedition_id>", methods=["GET", "PUT", "DELETE"])
        def api_expedition_by_id(expedition_id: int):
            """API endpoint for individual expedition management."""
            try:
                from core.modern_service_container import get_expedition_service, get_user_service
                from models.expedition import ExpeditionStatus

                expedition_service = get_expedition_service()
                user_service = get_user_service(None)

                # Check authentication
                chat_id = request.headers.get('X-Chat-ID')
                if not chat_id:
                    return jsonify({"error": "Authentication required"}), 401

                try:
                    chat_id = int(chat_id)
                    user_level = user_service.get_user_permission_level(chat_id)
                    if not user_level:
                        return jsonify({"error": "User not authenticated"}), 401
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid chat ID"}), 400

                # Get expedition
                expedition = expedition_service.get_expedition_by_id(expedition_id)
                if not expedition:
                    return jsonify({"error": "Expedition not found"}), 404

                # Check ownership or admin/owner permission
                is_owner = expedition.owner_chat_id == chat_id
                is_privileged = user_level.value in ['owner', 'admin']

                if not (is_owner or is_privileged):
                    return jsonify({"error": "Access denied"}), 403

                if request.method == "GET":
                    # Get detailed expedition response
                    expedition_response = expedition_service.get_expedition_response(expedition_id)
                    if not expedition_response:
                        return jsonify({"error": "Expedition details not available"}), 500

                    return jsonify({
                        "id": expedition_response.expedition.id,
                        "name": expedition_response.expedition.name,
                        "owner_chat_id": expedition_response.expedition.owner_chat_id,
                        "status": expedition_response.expedition.status.value,
                        "deadline": expedition_response.expedition.deadline.isoformat() if expedition_response.expedition.deadline else None,
                        "created_at": expedition_response.expedition.created_at.isoformat() if expedition_response.expedition.created_at else None,
                        "completed_at": expedition_response.expedition.completed_at.isoformat() if expedition_response.expedition.completed_at else None,
                        "items": [
                            {
                                "id": item.id,
                                "product_id": item.produto_id,  # Fixed: model uses 'produto_id' not 'product_id'
                                "product_name": item.product_name,
                                "product_emoji": item.product_emoji,
                                "quantity": item.quantity_needed,
                                "quantity_needed": item.quantity_needed,
                                "consumed": item.quantity_consumed,
                                "available": max(0, item.quantity_needed - item.quantity_consumed),
                                "unit_price": float(item.unit_price),
                                "price": float(item.unit_price),
                                "added_at": item.added_at.isoformat() if item.added_at else None
                            } for item in expedition_response.items
                        ],
                        "consumptions": [
                            {
                                "id": consumption.id,
                                "consumer_name": consumption.consumer_name,
                                "product_name": consumption.product_name,
                                "quantity": consumption.quantity,
                                "unit_price": float(consumption.unit_price),
                                "total_price": float(consumption.total_price),
                                "amount_paid": float(consumption.amount_paid),
                                "payment_status": consumption.payment_status.value,
                                "consumed_at": consumption.consumed_at.isoformat() if consumption.consumed_at else None
                            } for consumption in expedition_response.consumptions
                        ],
                        "progress": {
                            "total_items": expedition_response.total_items,
                            "consumed_items": expedition_response.consumed_items,
                            "remaining_items": expedition_response.remaining_items,
                            "completion_percentage": expedition_response.completion_percentage,
                            "total_value": float(expedition_response.total_value),
                            "consumed_value": float(expedition_response.consumed_value),
                            "remaining_value": float(expedition_response.remaining_value)
                        }
                    })

                elif request.method == "PUT":
                    # Update expedition - only owner can update
                    if not is_owner and user_level.value != 'owner':
                        return jsonify({"error": "Only expedition owner or system owner can update"}), 403

                    data = request.get_json()
                    if not data:
                        return jsonify({"error": "Request body required"}), 400

                    # Update status if provided
                    if 'status' in data:
                        try:
                            new_status = ExpeditionStatus.from_string(data['status'])
                            expedition_service.update_expedition_status(expedition_id, new_status)
                        except ValueError:
                            return jsonify({"error": "Invalid status"}), 400

                    # Get updated expedition
                    updated_expedition = expedition_service.get_expedition_by_id(expedition_id)
                    return jsonify({
                        "id": updated_expedition.id,
                        "name": updated_expedition.name,
                        "owner_chat_id": updated_expedition.owner_chat_id,
                        "status": updated_expedition.status.value,
                        "deadline": updated_expedition.deadline.isoformat() if updated_expedition.deadline else None,
                        "created_at": updated_expedition.created_at.isoformat() if updated_expedition.created_at else None,
                        "completed_at": updated_expedition.completed_at.isoformat() if updated_expedition.completed_at else None
                    })

                elif request.method == "DELETE":
                    # Delete expedition - only owner can delete
                    if not is_owner and user_level.value != 'owner':
                        return jsonify({"error": "Only expedition owner or system owner can delete"}), 403

                    success = expedition_service.delete_expedition(expedition_id)
                    if success:
                        return jsonify({"message": "Expedition deleted successfully"})
                    else:
                        return jsonify({"error": "Failed to delete expedition"}), 500

            except Exception as e:
                self.logger.error(f"Expedition API error: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @app.route("/api/expeditions/<int:expedition_id>/items", methods=["GET", "POST"])
        def api_expedition_items(expedition_id: int):
            """API endpoint for expedition items management."""
            try:
                from core.modern_service_container import get_expedition_service, get_user_service, get_product_service
                from models.expedition import ExpeditionItemRequest

                expedition_service = get_expedition_service()
                user_service = get_user_service(None)
                product_service = get_product_service()

                # Check authentication
                chat_id = request.headers.get('X-Chat-ID')
                if not chat_id:
                    return jsonify({"error": "Authentication required"}), 401

                try:
                    chat_id = int(chat_id)
                    user_level = user_service.get_user_permission_level(chat_id)
                    if not user_level:
                        return jsonify({"error": "User not authenticated"}), 401
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid chat ID"}), 400

                # Get expedition and check access
                expedition = expedition_service.get_expedition_by_id(expedition_id)
                if not expedition:
                    return jsonify({"error": "Expedition not found"}), 404

                is_owner = expedition.owner_chat_id == chat_id
                is_privileged = user_level.value in ['owner', 'admin']

                if not (is_owner or is_privileged):
                    return jsonify({"error": "Access denied"}), 403

                if request.method == "GET":
                    # Get expedition items with product details
                    items = expedition_service.get_expedition_items(expedition_id)
                    items_data = []
                    for item in items:
                        # Get product details
                        product = product_service.get_product_by_id(item.produto_id)
                        if product:
                            items_data.append({
                                "id": item.id,
                                "product_id": item.produto_id,
                                "product_name": product.nome,
                                "product_emoji": product.emoji or '',
                                "quantity": item.quantity_required,
                                "quantity_needed": item.quantity_required,
                                "consumed": item.quantity_consumed,
                                "available": max(0, item.quantity_required - item.quantity_consumed),
                                "unit_price": float(product.preco),
                                "price": float(product.preco),
                                "added_at": item.created_at.isoformat() if item.created_at else None
                            })

                    return jsonify({"items": items_data})

                elif request.method == "POST":
                    # Add items to expedition - only owner can add items
                    if not is_owner and user_level.value != 'owner':
                        return jsonify({"error": "Only expedition owner or system owner can add items"}), 403

                    data = request.get_json()
                    if not data:
                        return jsonify({"error": "Request body required"}), 400

                    items_data = data.get('items', [])
                    if not items_data:
                        return jsonify({"error": "Items list required"}), 400

                    # Validate and create item requests
                    item_requests = []
                    for item_data in items_data:
                        if not all(key in item_data for key in ['product_id', 'quantity']):
                            return jsonify({"error": "Each item must have product_id and quantity"}), 400

                        # Validate product exists
                        product = product_service.get_product_by_id(item_data['product_id'])
                        if not product:
                            return jsonify({"error": f"Product {item_data['product_id']} not found"}), 400

                        try:
                            quantity = int(item_data['quantity'])
                            if quantity <= 0:
                                return jsonify({"error": "Quantity must be positive"}), 400
                        except (ValueError, TypeError):
                            return jsonify({"error": "Invalid quantity"}), 400

                        # Parse optional unit_cost
                        unit_cost = None
                        if 'unit_cost' in item_data and item_data['unit_cost'] is not None:
                            try:
                                unit_cost = float(item_data['unit_cost'])
                                if unit_cost < 0:
                                    return jsonify({"error": "Unit cost cannot be negative"}), 400
                            except (ValueError, TypeError):
                                return jsonify({"error": "Invalid unit cost"}), 400

                        item_requests.append(ExpeditionItemRequest(
                            expedition_id=expedition_id,
                            produto_id=item_data['product_id'],
                            quantity_required=quantity,
                            unit_cost=unit_cost
                        ))

                    # Add items to expedition
                    created_items = expedition_service.add_items_to_expedition(expedition_id, item_requests)

                    items_data = []
                    for item in created_items:
                        # Get product details
                        product = product_service.get_product_by_id(item.produto_id)
                        if product:
                            items_data.append({
                                "id": item.id,
                                "product_id": item.produto_id,
                                "product_name": product.nome,
                                "product_emoji": product.emoji or '',
                                "quantity": item.quantity_required,
                                "quantity_needed": item.quantity_required,
                                "consumed": item.quantity_consumed,
                                "available": max(0, item.quantity_required - item.quantity_consumed),
                                "unit_price": float(product.preco) if hasattr(product, 'preco') else 0.0,
                                "price": float(product.preco) if hasattr(product, 'preco') else 0.0,
                                "added_at": item.created_at.isoformat() if item.created_at else None
                            })

                    return jsonify({"items": items_data}), 201

            except Exception as e:
                self.logger.error(f"Expedition items API error: {e}", exc_info=True)
                return jsonify({"error": str(e)}), 500

        @app.route("/api/expeditions/<int:expedition_id>/consume", methods=["POST"])
        def api_expedition_consume(expedition_id: int):
            """API endpoint for expedition item consumption."""
            print(f"[CONSUME DEBUG] Endpoint hit for expedition {expedition_id}")
            print(f"[CONSUME DEBUG] Request data: {request.get_json()}")
            try:
                from core.modern_service_container import get_expedition_service, get_user_service
                from models.expedition import ItemConsumptionRequest
                from services.base_service import ValidationError, NotFoundError

                expedition_service = get_expedition_service()
                user_service = get_user_service(None)

                # Check authentication - require admin+ permission
                chat_id = request.headers.get('X-Chat-ID')
                if not chat_id:
                    return jsonify({"error": "Authentication required"}), 401

                try:
                    chat_id = int(chat_id)
                    user_level = user_service.get_user_permission_level(chat_id)
                    if not user_level or user_level.value not in ['owner', 'admin']:
                        return jsonify({"error": "Admin permission required"}), 403
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid chat ID"}), 400

                # Get consumer name from user
                user = user_service.get_user_by_chat_id(chat_id)
                if not user:
                    return jsonify({"error": "User not found"}), 404

                # Get expedition and validate
                expedition = expedition_service.get_expedition_by_id(expedition_id)
                if not expedition:
                    return jsonify({"error": "Expedition not found"}), 404

                # Parse request data
                data = request.get_json()
                if not data:
                    return jsonify({"error": "Request body required"}), 400

                # Validate required fields
                required_fields = ['product_id', 'quantity', 'pirate_name', 'price']
                if not all(field in data for field in required_fields):
                    return jsonify({"error": "product_id, quantity, pirate_name, and price are required"}), 400

                try:
                    product_id = int(data['product_id'])
                    quantity = int(data['quantity'])
                    pirate_name = str(data['pirate_name']).strip()
                    price = float(data['price'])

                    if quantity <= 0:
                        return jsonify({"error": "Quantity must be positive"}), 400
                    if price <= 0:
                        return jsonify({"error": "Price must be positive"}), 400
                    if not pirate_name:
                        return jsonify({"error": "Pirate name is required"}), 400

                except (ValueError, TypeError) as e:
                    return jsonify({"error": f"Invalid input: {str(e)}"}), 400

                # Get expedition item ID from product ID using expedition service
                from decimal import Decimal

                # Find the expedition item for this product
                expedition_items = expedition_service.get_expedition_items(expedition_id)
                print(f"[CONSUME DEBUG] Found {len(expedition_items)} items in expedition {expedition_id}")
                for item in expedition_items:
                    print(f"[CONSUME DEBUG] Item: id={item.id}, produto_id={item.produto_id}, qty_required={item.quantity_required}")

                expedition_item = None
                for item in expedition_items:
                    if item.produto_id == product_id:
                        expedition_item = item
                        break

                if not expedition_item:
                    print(f"[CONSUME DEBUG] Product {product_id} not found in expedition {expedition_id}. Available products: {[item.produto_id for item in expedition_items]}")
                    return jsonify({
                        "error": "Product not found in expedition",
                        "detail": f"Product {product_id} is not part of expedition {expedition_id}",
                        "available_products": [item.produto_id for item in expedition_items]
                    }), 404

                # Get original name from pirate name
                from core.modern_service_container import get_brambler_service
                brambler_service = get_brambler_service()

                # Get pirate names for this expedition
                pirate_names_list = brambler_service.get_expedition_pirate_names(expedition_id)

                # Find the original name for this pirate
                consumer_name = pirate_name  # Default to pirate name
                for pn in pirate_names_list:
                    if pn.pirate_name == pirate_name and pn.original_name:
                        consumer_name = pn.original_name
                        break

                # Create consumption request with all parameters
                consumption_request = ItemConsumptionRequest(
                    expedition_item_id=expedition_item.id,
                    consumer_name=consumer_name,
                    pirate_name=pirate_name,
                    quantity_consumed=quantity,
                    unit_price=Decimal(str(price))
                )

                # Record consumption (will create vendas and process FIFO)
                consumption = expedition_service.consume_item(consumption_request)

                return jsonify({
                    "id": consumption.id,
                    "expedition_id": consumption.expedition_id,
                    "pirate_name": consumption.pirate_name,
                    "expedition_item_id": consumption.item_id,
                    "quantity": consumption.quantity,
                    "unit_price": float(consumption.unit_price),
                    "total_price": float(consumption.assignment_amount),
                    "assignment_status": consumption.assignment_status.value,
                    "consumed_at": consumption.consumed_date.isoformat() if consumption.consumed_date else None
                }), 201

            except ValidationError as e:
                self.logger.warning(f"Validation error in consume: {e}")
                return jsonify({"error": str(e)}), 400
            except NotFoundError as e:
                self.logger.warning(f"Not found error in consume: {e}")
                return jsonify({"error": str(e)}), 404
            except Exception as e:
                self.logger.error(f"Expedition consume API error: {e}", exc_info=True)
                return jsonify({"error": str(e)}), 500

        @app.route("/api/brambler/generate/<int:expedition_id>", methods=["POST"])
        def api_brambler_generate(expedition_id: int):
            """API endpoint for generating pirate names for expedition."""
            try:
                from core.modern_service_container import get_expedition_service, get_brambler_service

                expedition_service = get_expedition_service()
                brambler_service = get_brambler_service()

                # Get expedition
                expedition = expedition_service.get_expedition_by_id(expedition_id)
                if not expedition:
                    return jsonify({"error": "Expedition not found"}), 404

                # Parse request data
                data = request.get_json()
                if not data:
                    return jsonify({"error": "Request body required"}), 400

                original_names = data.get('original_names', [])
                if not original_names or not isinstance(original_names, list):
                    return jsonify({"error": "original_names list is required"}), 400

                # Generate pirate names
                pirate_names = brambler_service.generate_pirate_names(expedition_id, original_names)

                pirate_names_data = []
                for pirate_name in pirate_names:
                    pirate_names_data.append({
                        "id": pirate_name.id,
                        "expedition_id": pirate_name.expedition_id,
                        "original_name": pirate_name.original_name,
                        "pirate_name": pirate_name.pirate_name,
                        "created_at": pirate_name.created_at.isoformat() if pirate_name.created_at else None
                    })

                return jsonify({"pirate_names": pirate_names_data}), 201

            except Exception as e:
                import traceback
                self.logger.error(f"Brambler generate API error: {e}\n{traceback.format_exc()}")
                return jsonify({"error": "Internal server error", "detail": str(e)}), 500

        @app.route("/api/brambler/decrypt/<int:expedition_id>", methods=["POST"])
        def api_brambler_decrypt(expedition_id: int):
            """API endpoint for decrypting pirate names (owner access only)."""
            try:
                from core.modern_service_container import get_expedition_service, get_brambler_service, get_user_service

                expedition_service = get_expedition_service()
                brambler_service = get_brambler_service()
                user_service = get_user_service(None)

                # Check authentication - require owner permission
                chat_id = request.headers.get('X-Chat-ID')
                if not chat_id:
                    return jsonify({"error": "Authentication required"}), 401

                try:
                    chat_id = int(chat_id)
                    user_level = user_service.get_user_permission_level(chat_id)
                    if not user_level or user_level.value != 'owner':
                        return jsonify({"error": "Owner permission required"}), 403
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid chat ID"}), 400

                # Get expedition and validate ownership
                expedition = expedition_service.get_expedition_by_id(expedition_id)
                if not expedition:
                    return jsonify({"error": "Expedition not found"}), 404

                if expedition.owner_chat_id != chat_id:
                    return jsonify({"error": "Only expedition owner can decrypt pirate names"}), 403

                # Parse request data
                data = request.get_json()
                if not data:
                    return jsonify({"error": "Request body required"}), 400

                encrypted_mapping = data.get('encrypted_mapping')
                owner_key = data.get('owner_key')

                if not encrypted_mapping or not owner_key:
                    return jsonify({"error": "encrypted_mapping and owner_key are required"}), 400

                # Decrypt name mapping
                decrypted_mapping = brambler_service.decrypt_name_mapping(expedition_id, encrypted_mapping, owner_key)

                if decrypted_mapping is None:
                    return jsonify({"error": "Failed to decrypt mapping - invalid key or data"}), 400

                return jsonify({"decrypted_mapping": decrypted_mapping})

            except Exception as e:
                self.logger.error(f"Brambler decrypt API error: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @app.route("/api/brambler/names/<int:expedition_id>", methods=["GET"])
        def api_brambler_names(expedition_id: int):
            """API endpoint for getting pirate names for an expedition."""
            try:
                from core.modern_service_container import get_expedition_service, get_user_service

                expedition_service = get_expedition_service()
                user_service = get_user_service(None)

                # Check authentication
                chat_id = request.headers.get('X-Chat-ID')
                if not chat_id:
                    return jsonify({"error": "Authentication required"}), 401

                try:
                    chat_id = int(chat_id)
                    user_level = user_service.get_user_permission_level(chat_id)
                    if not user_level:
                        return jsonify({"error": "User not authenticated"}), 401
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid chat ID"}), 400

                # Get expedition and validate access
                expedition = expedition_service.get_expedition_by_id(expedition_id)
                if not expedition:
                    return jsonify({"error": "Expedition not found"}), 404

                is_owner = expedition.owner_chat_id == chat_id
                is_privileged = user_level.value in ['owner', 'admin']

                if not (is_owner or is_privileged):
                    return jsonify({"error": "Access denied"}), 403

                # Get all pirate names and stats in a SINGLE optimized query
                from database import get_database_manager
                db_manager = get_database_manager()

                pirate_names_data = []
                with db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        # Single bulk query with all data
                        cur.execute("""
                            SELECT
                                ep.id,
                                ep.expedition_id,
                                ep.pirate_name,
                                ep.original_name,
                                ep.joined_at,
                                COALESCE(COUNT(DISTINCT ea.id), 0) as total_items,
                                COALESCE(SUM(ea.consumed_quantity), 0) as items_consumed,
                                COALESCE(SUM(ea.total_cost), 0) as total_spent,
                                COALESCE(SUM(CASE WHEN epm.payment_status = 'completed'
                                    THEN epm.payment_amount ELSE 0 END), 0) as total_paid
                            FROM expedition_pirates ep
                            LEFT JOIN expedition_assignments ea ON ea.pirate_id = ep.id
                            LEFT JOIN expedition_payments epm ON epm.pirate_id = ep.id
                            WHERE ep.expedition_id = %s
                            GROUP BY ep.id, ep.expedition_id, ep.pirate_name, ep.original_name, ep.joined_at
                            ORDER BY ep.joined_at DESC
                        """, (expedition_id,))

                        results = cur.fetchall()

                        # Only show original names to expedition owner or system owner
                        show_original = is_owner or user_level.value == 'owner'

                        for row in results:
                            (pirate_id, exp_id, pirate_name, original_name, joined_at,
                             total_items, items_consumed, total_spent, total_paid) = row

                            debt = float(total_spent or 0) - float(total_paid or 0)

                            # Get recent items for this pirate (last 3 consumptions)
                            cur.execute("""
                                SELECT
                                    p.nome,
                                    p.emoji,
                                    ea.consumed_quantity,
                                    ea.completed_at
                                FROM expedition_assignments ea
                                JOIN expedition_items ei ON ea.expedition_item_id = ei.id
                                JOIN produtos p ON ei.produto_id = p.id
                                WHERE ea.pirate_id = %s
                                ORDER BY ea.completed_at DESC
                                LIMIT 3
                            """, (pirate_id,))

                            recent_items_rows = cur.fetchall()
                            recent_items = []
                            for item_row in recent_items_rows:
                                product_name, product_emoji, quantity, consumed_at = item_row
                                recent_items.append({
                                    "name": product_name,
                                    "emoji": product_emoji or "",
                                    "quantity": quantity,
                                    "consumed_at": consumed_at.isoformat() if consumed_at else None
                                })

                            pirate_names_data.append({
                                "id": pirate_id,
                                "expedition_id": exp_id,
                                "original_name": original_name if show_original else None,
                                "pirate_name": pirate_name,
                                "created_at": joined_at.isoformat() if joined_at else None,
                                "stats": {
                                    "total_items": int(total_items or 0),
                                    "items_consumed": int(items_consumed or 0),
                                    "total_spent": float(total_spent or 0),
                                    "total_paid": float(total_paid or 0),
                                    "debt": debt
                                },
                                "recent_items": recent_items
                            })

                return jsonify({"pirate_names": pirate_names_data})

            except Exception as e:
                self.logger.error(f"Brambler names API error: {e}")
                return jsonify({"error": "Internal server error"}), 500

        # ===== EXPEDITION DASHBOARD AND REPORTING ENDPOINTS =====

        @app.route("/api/dashboard/timeline", methods=["GET"])
        def api_dashboard_timeline():
            """API endpoint for expedition timeline data for dashboard."""
            try:
                from core.modern_service_container import get_expedition_service, get_user_service

                expedition_service = get_expedition_service()
                user_service = get_user_service(None)

                # Check authentication - require admin+ permission
                chat_id = request.headers.get('X-Chat-ID')
                if not chat_id:
                    return jsonify({"error": "Authentication required"}), 401

                try:
                    chat_id = int(chat_id)
                    user_level = user_service.get_user_permission_level(chat_id)
                    if not user_level or user_level.value not in ['owner', 'admin']:
                        return jsonify({"error": "Admin permission required"}), 403
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid chat ID"}), 400

                # Get all expedition data in a single optimized query
                expedition_data_map = expedition_service.get_all_expedition_responses_bulk()

                # Prepare timeline data
                timeline_data = []
                stats = {
                    "total_expeditions": 0,
                    "active_expeditions": 0,
                    "completed_expeditions": 0,
                    "overdue_expeditions": 0
                }

                current_time = datetime.now()

                for expedition_id, exp_data in expedition_data_map.items():
                    # Determine if overdue
                    deadline = None
                    if exp_data.get('deadline'):
                        from datetime import datetime as dt
                        deadline = dt.fromisoformat(exp_data['deadline'])

                    is_overdue = (
                        deadline and
                        deadline < current_time and
                        exp_data['status'] == 'active'
                    )

                    timeline_entry = {
                        "id": exp_data['id'],
                        "name": exp_data['name'],
                        "owner_chat_id": exp_data['owner_chat_id'],
                        "status": exp_data['status'],
                        "deadline": exp_data['deadline'],
                        "created_at": exp_data['created_at'],
                        "completed_at": exp_data['completed_at'],
                        "is_overdue": is_overdue,
                        "progress": {
                            "completion_percentage": exp_data['completion_percentage'],
                            "total_items": exp_data['total_items'],
                            "consumed_items": exp_data['total_quantity_consumed'],
                            "remaining_items": exp_data['total_quantity_needed'] - exp_data['total_quantity_consumed'],
                            "total_value": exp_data['total_value'],
                            "consumed_value": exp_data['consumed_value'],
                            "remaining_value": exp_data['remaining_value']
                        }
                    }
                    timeline_data.append(timeline_entry)

                    # Update stats
                    stats["total_expeditions"] += 1
                    if exp_data['status'] == 'active':
                        stats["active_expeditions"] += 1
                        if is_overdue:
                            stats["overdue_expeditions"] += 1
                    elif exp_data['status'] == 'completed':
                        stats["completed_expeditions"] += 1

                # Sort by creation date (newest first)
                timeline_data.sort(key=lambda x: x['created_at'] or '', reverse=True)

                return jsonify({
                    "timeline": timeline_data,
                    "stats": stats
                })

            except Exception as e:
                self.logger.error(f"Dashboard timeline API error: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @app.route("/api/dashboard/overdue", methods=["GET"])
        def api_dashboard_overdue():
            """API endpoint for overdue expeditions monitoring."""
            try:
                from core.modern_service_container import get_expedition_service, get_user_service

                expedition_service = get_expedition_service()
                user_service = get_user_service(None)

                # Check authentication - require admin+ permission
                chat_id = request.headers.get('X-Chat-ID')
                if not chat_id:
                    return jsonify({"error": "Authentication required"}), 401

                try:
                    chat_id = int(chat_id)
                    user_level = user_service.get_user_permission_level(chat_id)
                    if not user_level or user_level.value not in ['owner', 'admin']:
                        return jsonify({"error": "Admin permission required"}), 403
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid chat ID"}), 400

                # Get overdue expeditions
                overdue_expeditions = expedition_service.get_overdue_expeditions()

                current_time = datetime.now()
                overdue_data = []

                for expedition in overdue_expeditions:
                    # Calculate how overdue
                    days_overdue = 0
                    alert_level = "info"

                    if expedition.deadline:
                        days_overdue = (current_time - expedition.deadline).days
                        if days_overdue > 7:
                            alert_level = "critical"
                        elif days_overdue > 3:
                            alert_level = "urgent"
                        elif days_overdue > 1:
                            alert_level = "warning"

                    # Get expedition progress
                    expedition_response = expedition_service.get_expedition_response(expedition.id)

                    overdue_entry = {
                        "id": expedition.id,
                        "name": expedition.name,
                        "owner_chat_id": expedition.owner_chat_id,
                        "deadline": expedition.deadline.isoformat() if expedition.deadline else None,
                        "days_overdue": days_overdue,
                        "alert_level": alert_level,
                        "progress": {
                            "completion_percentage": expedition_response.completion_percentage if expedition_response else 0,
                            "total_items": expedition_response.total_items if expedition_response else 0,
                            "remaining_items": expedition_response.remaining_items if expedition_response else 0,
                            "total_value": float(expedition_response.total_value) if expedition_response else 0.0,
                            "remaining_value": float(expedition_response.remaining_value) if expedition_response else 0.0
                        }
                    }
                    overdue_data.append(overdue_entry)

                # Sort by days overdue (most overdue first)
                overdue_data.sort(key=lambda x: x['days_overdue'], reverse=True)

                return jsonify({
                    "overdue_expeditions": overdue_data,
                    "total_overdue": len(overdue_data)
                })

            except Exception as e:
                self.logger.error(f"Dashboard overdue API error: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @app.route("/api/dashboard/analytics", methods=["GET"])
        def api_dashboard_analytics():
            """API endpoint for expedition analytics and statistics."""
            try:
                from core.modern_service_container import get_expedition_service, get_user_service
                from decimal import Decimal

                expedition_service = get_expedition_service()
                user_service = get_user_service(None)

                # Check authentication - require admin+ permission
                chat_id = request.headers.get('X-Chat-ID')
                if not chat_id:
                    return jsonify({"error": "Authentication required"}), 401

                try:
                    chat_id = int(chat_id)
                    user_level = user_service.get_user_permission_level(chat_id)
                    if not user_level or user_level.value not in ['owner', 'admin']:
                        return jsonify({"error": "Admin permission required"}), 403
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid chat ID"}), 400

                # Get all expedition data in a single optimized query
                expedition_data_map = expedition_service.get_all_expedition_responses_bulk()

                # Initialize analytics data
                analytics = {
                    "overview": {
                        "total_expeditions": len(expedition_data_map),
                        "active_expeditions": 0,
                        "completed_expeditions": 0,
                        "cancelled_expeditions": 0,
                        "overdue_expeditions": 0
                    },
                    "value_analysis": {
                        "total_expedition_value": 0.0,
                        "completed_expedition_value": 0.0,
                        "active_expedition_value": 0.0,
                        "consumed_value": 0.0,
                        "pending_value": 0.0
                    },
                    "progress_analysis": {
                        "average_completion_rate": 0.0,
                        "expeditions_by_progress": {
                            "0-25%": 0,
                            "25-50%": 0,
                            "50-75%": 0,
                            "75-100%": 0,
                            "completed": 0
                        }
                    },
                    "timeline_analysis": {
                        "expeditions_created_this_week": 0,
                        "expeditions_created_this_month": 0,
                        "expeditions_completed_this_week": 0,
                        "expeditions_completed_this_month": 0
                    }
                }

                current_time = datetime.now()
                week_ago = current_time - timedelta(days=7)
                month_ago = current_time - timedelta(days=30)

                total_completion_percentage = 0.0
                expeditions_with_progress = 0

                for expedition_id, exp_data in expedition_data_map.items():
                    # Status analysis
                    if exp_data['status'] == 'active':
                        analytics["overview"]["active_expeditions"] += 1
                        analytics["value_analysis"]["active_expedition_value"] += exp_data['total_value']
                    elif exp_data['status'] == 'completed':
                        analytics["overview"]["completed_expeditions"] += 1
                        analytics["value_analysis"]["completed_expedition_value"] += exp_data['total_value']
                    elif exp_data['status'] == 'cancelled':
                        analytics["overview"]["cancelled_expeditions"] += 1

                    # Overdue check
                    deadline = None
                    if exp_data.get('deadline'):
                        from datetime import datetime as dt
                        deadline = dt.fromisoformat(exp_data['deadline'])
                    if deadline and deadline < current_time and exp_data['status'] == 'active':
                        analytics["overview"]["overdue_expeditions"] += 1

                    # Value analysis
                    analytics["value_analysis"]["total_expedition_value"] += exp_data['total_value']
                    analytics["value_analysis"]["consumed_value"] += exp_data['consumed_value']
                    analytics["value_analysis"]["pending_value"] += exp_data['remaining_value']

                    # Progress analysis
                    completion_rate = exp_data['completion_percentage']
                    total_completion_percentage += completion_rate
                    expeditions_with_progress += 1

                    if exp_data['status'] == 'completed':
                        analytics["progress_analysis"]["expeditions_by_progress"]["completed"] += 1
                    elif completion_rate >= 75:
                        analytics["progress_analysis"]["expeditions_by_progress"]["75-100%"] += 1
                    elif completion_rate >= 50:
                        analytics["progress_analysis"]["expeditions_by_progress"]["50-75%"] += 1
                    elif completion_rate >= 25:
                        analytics["progress_analysis"]["expeditions_by_progress"]["25-50%"] += 1
                    else:
                        analytics["progress_analysis"]["expeditions_by_progress"]["0-25%"] += 1

                    # Timeline analysis
                    created_at = None
                    completed_at = None
                    if exp_data.get('created_at'):
                        from datetime import datetime as dt
                        created_at = dt.fromisoformat(exp_data['created_at'])
                    if exp_data.get('completed_at'):
                        from datetime import datetime as dt
                        completed_at = dt.fromisoformat(exp_data['completed_at'])

                    if created_at:
                        if created_at >= week_ago:
                            analytics["timeline_analysis"]["expeditions_created_this_week"] += 1
                        if created_at >= month_ago:
                            analytics["timeline_analysis"]["expeditions_created_this_month"] += 1

                    if completed_at:
                        if completed_at >= week_ago:
                            analytics["timeline_analysis"]["expeditions_completed_this_week"] += 1
                        if completed_at >= month_ago:
                            analytics["timeline_analysis"]["expeditions_completed_this_month"] += 1

                # Calculate average completion rate
                if expeditions_with_progress > 0:
                    analytics["progress_analysis"]["average_completion_rate"] = total_completion_percentage / expeditions_with_progress

                return jsonify(analytics)

            except Exception as e:
                self.logger.error(f"Dashboard analytics API error: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @app.route("/api/expeditions/consumptions", methods=["GET"])
        def api_expedition_consumptions():
            """API endpoint for expedition consumptions with filtering."""
            try:
                from core.modern_service_container import get_expedition_service, get_user_service

                expedition_service = get_expedition_service()
                user_service = get_user_service(None)

                # Check authentication - require admin+ permission
                chat_id = request.headers.get('X-Chat-ID')
                if not chat_id:
                    return jsonify({"error": "Authentication required"}), 401

                try:
                    chat_id = int(chat_id)
                    user_level = user_service.get_user_permission_level(chat_id)
                    if not user_level or user_level.value not in ['owner', 'admin']:
                        return jsonify({"error": "Admin permission required"}), 403
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid chat ID"}), 400

                # Parse query parameters
                consumer_name = request.args.get('consumer_name')
                payment_status = request.args.get('payment_status')  # 'pending', 'paid', 'partial'

                # Get unpaid consumptions if payment_status is pending
                if payment_status == 'pending':
                    consumptions = expedition_service.get_unpaid_consumptions(consumer_name)
                    consumptions_data = []
                    for consumption in consumptions:
                        consumptions_data.append({
                            "id": consumption.id,
                            "expedition_id": consumption.expedition_id,
                            "expedition_name": consumption.expedition_name,
                            "consumer_name": consumption.consumer_name,
                            "product_name": consumption.product_name,
                            "quantity": consumption.quantity,
                            "unit_price": float(consumption.unit_price),
                            "total_price": float(consumption.total_price),
                            "payment_status": consumption.payment_status.value,
                            "consumed_at": consumption.consumed_at.isoformat() if consumption.consumed_at else None
                        })
                    return jsonify({"consumptions": consumptions_data})

                # For other cases, get user consumptions if specified
                if consumer_name:
                    consumptions = expedition_service.get_user_consumptions(consumer_name)
                    consumptions_data = []
                    for consumption in consumptions:
                        consumptions_data.append({
                            "id": consumption.id,
                            "expedition_id": consumption.expedition_id,
                            "consumer_name": consumption.consumer_name,
                            "product_id": consumption.product_id,
                            "quantity": consumption.quantity,
                            "unit_price": float(consumption.unit_price),
                            "total_price": float(consumption.total_price),
                            "payment_status": consumption.payment_status.value,
                            "consumed_at": consumption.consumed_at.isoformat() if consumption.consumed_at else None
                        })
                    return jsonify({"consumptions": consumptions_data})

                # If no specific filters, return recent consumptions from all expeditions
                all_expeditions = expedition_service.get_active_expeditions()
                all_consumptions = []

                for expedition in all_expeditions[:10]:  # Limit to 10 most recent expeditions
                    expedition_consumptions = expedition_service.get_expedition_consumptions(expedition.id)
                    all_consumptions.extend(expedition_consumptions)

                # Sort by consumed_at (most recent first)
                all_consumptions.sort(key=lambda x: x.consumed_at or datetime.min, reverse=True)

                consumptions_data = []
                for consumption in all_consumptions[:50]:  # Limit to 50 most recent
                    consumptions_data.append({
                        "id": consumption.id,
                        "expedition_id": consumption.expedition_id,
                        "consumer_name": consumption.consumer_name,
                        "product_id": consumption.product_id,
                        "quantity": consumption.quantity,
                        "unit_price": float(consumption.unit_price),
                        "total_price": float(consumption.total_price),
                        "payment_status": consumption.payment_status.value,
                        "consumed_at": consumption.consumed_at.isoformat() if consumption.consumed_at else None
                    })

                return jsonify({"consumptions": consumptions_data})

            except Exception as e:
                self.logger.error(f"Expedition consumptions API error: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @app.route("/api/expeditions/consumptions/<int:consumption_id>/pay", methods=["POST"])
        def api_pay_consumption(consumption_id):
            """API endpoint to pay for a consumption (full or partial payment)."""
            try:
                from core.modern_service_container import get_expedition_service, get_user_service
                from decimal import Decimal
                from services.base_service import NotFoundError, ValidationError

                expedition_service = get_expedition_service()
                user_service = get_user_service(None)

                # Check authentication - require admin+ permission
                chat_id = request.headers.get('X-Chat-ID')
                if not chat_id:
                    return jsonify({"error": "Authentication required"}), 401

                try:
                    chat_id = int(chat_id)
                    user_level = user_service.get_user_permission_level(chat_id)
                    if not user_level or user_level.value not in ['owner', 'admin']:
                        return jsonify({"error": "Admin permission required"}), 403
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid chat ID"}), 400

                # Parse request body
                data = request.get_json()
                if not data or 'amount' not in data:
                    return jsonify({"error": "Payment amount is required"}), 400

                try:
                    amount = Decimal(str(data['amount']))
                except (ValueError, TypeError):
                    return jsonify({"error": "Invalid payment amount"}), 400

                # Process payment - consumption_id is actually assignment_id in our architecture
                updated_assignment = expedition_service.pay_assignment(consumption_id, amount)

                # Invalidate expedition cache to ensure fresh data
                from utils.query_cache import get_query_cache
                cache = get_query_cache()
                cache_key = f"expedition_details_{updated_assignment.expedition_id}"
                cache.invalidate(cache_key)

                # Get the updated payment info from database
                from database import get_database_manager
                db_manager = get_database_manager()

                with db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        # Query to get full assignment with payment info
                        cur.execute("""
                            SELECT ea.id, ea.expedition_id, ea.expedition_item_id,
                                   ep.original_name, ep.pirate_name,
                                   ea.consumed_quantity, ea.unit_price, ea.total_cost,
                                   COALESCE(SUM(ep2.payment_amount), 0) as amount_paid,
                                   ea.payment_status, ea.completed_at
                            FROM expedition_assignments ea
                            JOIN expedition_pirates ep ON ea.pirate_id = ep.id
                            LEFT JOIN expedition_payments ep2 ON ep2.assignment_id = ea.id
                                AND ep2.payment_status = 'completed'
                            WHERE ea.id = %s
                            GROUP BY ea.id, ep.id, ep.original_name, ep.pirate_name
                        """, (consumption_id,))

                        result = cur.fetchone()
                        if not result:
                            return jsonify({"error": "Failed to retrieve updated payment info"}), 500

                        (a_id, expedition_id, expedition_item_id, original_name, pirate_name,
                         consumed_qty, unit_price, total_cost, amount_paid, payment_status, completed_at) = result

                # Return formatted response
                consumption_data = {
                    "id": a_id,
                    "expedition_id": expedition_id,
                    "expedition_item_id": expedition_item_id,
                    "consumer_name": original_name,
                    "pirate_name": pirate_name,
                    "quantity": consumed_qty,
                    "unit_price": float(unit_price),
                    "total_price": float(total_cost),
                    "amount_paid": float(amount_paid),
                    "payment_status": payment_status,
                    "consumed_at": completed_at.isoformat() if completed_at else None
                }

                return jsonify(consumption_data), 200

            except NotFoundError as e:
                return jsonify({"error": str(e)}), 404
            except ValidationError as e:
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                self.logger.error(f"Pay consumption API error: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @app.route("/api/expeditions/export", methods=["GET"])
        def export_expedition_data():
            """Export expedition data to CSV."""
            try:
                # Get authentication level
                auth_level = self._get_user_auth_level(request)
                if not auth_level or auth_level not in ['admin', 'owner']:
                    return jsonify({"error": "Admin or owner access required"}), 401

                # Get export service
                from core.modern_service_container import get_export_service
                export_service = get_export_service()

                # Parse query parameters
                expedition_id = request.args.get('expedition_id', type=int)
                status_filter = request.args.get('status')
                date_from_str = request.args.get('date_from')
                date_to_str = request.args.get('date_to')

                date_from = None
                date_to = None
                if date_from_str:
                    try:
                        date_from = datetime.fromisoformat(date_from_str.replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({"error": "Invalid date_from format. Use ISO format."}), 400

                if date_to_str:
                    try:
                        date_to = datetime.fromisoformat(date_to_str.replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({"error": "Invalid date_to format. Use ISO format."}), 400

                # Generate export
                filepath = export_service.export_expedition_data(
                    expedition_id=expedition_id,
                    status_filter=status_filter,
                    date_from=date_from,
                    date_to=date_to
                )

                filename = os.path.basename(filepath)
                return jsonify({
                    "success": True,
                    "message": "Export completed successfully",
                    "file_path": filepath,
                    "filename": filename,
                    "download_url": f"/api/exports/download/{filename}"
                })

            except Exception as e:
                self.logger.error(f"Export expedition data API error: {e}")
                return jsonify({"error": f"Export failed: {str(e)}"}), 500

        @app.route("/api/expeditions/reports/pirate-activity", methods=["GET"])
        def export_pirate_activity_report():
            """Export pirate activity report."""
            try:
                # Get authentication level
                auth_level = self._get_user_auth_level(request)
                if not auth_level or auth_level not in ['admin', 'owner']:
                    return jsonify({"error": "Admin or owner access required"}), 401

                # Get export service
                from core.modern_service_container import get_export_service
                export_service = get_export_service()

                # Parse query parameters
                expedition_id = request.args.get('expedition_id', type=int)
                anonymized = request.args.get('anonymized', 'true').lower() == 'true'
                date_from_str = request.args.get('date_from')
                date_to_str = request.args.get('date_to')

                date_from = None
                date_to = None
                if date_from_str:
                    try:
                        date_from = datetime.fromisoformat(date_from_str.replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({"error": "Invalid date_from format. Use ISO format."}), 400

                if date_to_str:
                    try:
                        date_to = datetime.fromisoformat(date_to_str.replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({"error": "Invalid date_to format. Use ISO format."}), 400

                # Generate export
                filepath = export_service.export_pirate_activity_report(
                    expedition_id=expedition_id,
                    anonymized=anonymized,
                    date_from=date_from,
                    date_to=date_to
                )

                filename = os.path.basename(filepath)
                return jsonify({
                    "success": True,
                    "message": "Pirate activity report completed successfully",
                    "file_path": filepath,
                    "filename": filename,
                    "download_url": f"/api/exports/download/{filename}"
                })

            except Exception as e:
                self.logger.error(f"Export pirate activity report API error: {e}")
                return jsonify({"error": f"Report generation failed: {str(e)}"}), 500

        @app.route("/api/expeditions/reports/profit-loss", methods=["GET"])
        def export_profit_loss_report():
            """Export profit/loss report."""
            try:
                # Get authentication level
                auth_level = self._get_user_auth_level(request)
                if not auth_level or auth_level not in ['admin', 'owner']:
                    return jsonify({"error": "Admin or owner access required"}), 401

                # Get export service
                from core.modern_service_container import get_export_service
                export_service = get_export_service()

                # Parse query parameters
                expedition_id = request.args.get('expedition_id', type=int)
                date_from_str = request.args.get('date_from')
                date_to_str = request.args.get('date_to')

                date_from = None
                date_to = None
                if date_from_str:
                    try:
                        date_from = datetime.fromisoformat(date_from_str.replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({"error": "Invalid date_from format. Use ISO format."}), 400

                if date_to_str:
                    try:
                        date_to = datetime.fromisoformat(date_to_str.replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({"error": "Invalid date_to format. Use ISO format."}), 400

                # Generate export
                filepath = export_service.export_profit_loss_report(
                    expedition_id=expedition_id,
                    date_from=date_from,
                    date_to=date_to
                )

                filename = os.path.basename(filepath)
                return jsonify({
                    "success": True,
                    "message": "Profit/loss report completed successfully",
                    "file_path": filepath,
                    "filename": filename,
                    "download_url": f"/api/exports/download/{filename}"
                })

            except Exception as e:
                self.logger.error(f"Export profit/loss report API error: {e}")
                return jsonify({"error": f"Report generation failed: {str(e)}"}), 500

        @app.route("/api/expeditions/search", methods=["GET"])
        def search_expeditions():
            """Search expeditions with advanced filtering."""
            try:
                # Get authentication level
                auth_level = self._get_user_auth_level(request)
                if not auth_level:
                    return jsonify({"error": "Authentication required"}), 401

                # Get export service
                from core.modern_service_container import get_export_service
                export_service = get_export_service()

                # Parse query parameters
                search_query = request.args.get('q')
                status_filter = request.args.get('status')
                owner_chat_id = request.args.get('owner_chat_id', type=int)
                date_from_str = request.args.get('date_from')
                date_to_str = request.args.get('date_to')
                sort_by = request.args.get('sort_by', 'created_at')
                sort_order = request.args.get('sort_order', 'DESC')
                limit = request.args.get('limit', 50, type=int)
                offset = request.args.get('offset', 0, type=int)

                # Validate limit
                if limit > 1000:
                    limit = 1000

                date_from = None
                date_to = None
                if date_from_str:
                    try:
                        date_from = datetime.fromisoformat(date_from_str.replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({"error": "Invalid date_from format. Use ISO format."}), 400

                if date_to_str:
                    try:
                        date_to = datetime.fromisoformat(date_to_str.replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({"error": "Invalid date_to format. Use ISO format."}), 400

                # Perform search
                results, total_count = export_service.search_expeditions(
                    search_query=search_query,
                    status_filter=status_filter,
                    owner_chat_id=owner_chat_id,
                    date_from=date_from,
                    date_to=date_to,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    limit=limit,
                    offset=offset
                )

                return jsonify({
                    "results": results,
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                })

            except Exception as e:
                self.logger.error(f"Search expeditions API error: {e}")
                return jsonify({"error": f"Search failed: {str(e)}"}), 500

        @app.route("/api/exports/download/<filename>", methods=["GET"])
        def download_export_file(filename):
            """Download exported file."""
            try:
                # Get authentication level
                auth_level = self._get_user_auth_level(request)
                if not auth_level or auth_level not in ['admin', 'owner']:
                    return jsonify({"error": "Admin or owner access required"}), 401

                # Security check - only allow specific patterns
                import re
                if not re.match(r'^(expedition_export_|pirate_activity_|profit_loss_report_)\d{8}_\d{6}\.csv$', filename):
                    return jsonify({"error": "Invalid file requested"}), 400

                # Get file path
                import tempfile
                filepath = os.path.join(tempfile.gettempdir(), filename)

                if not os.path.exists(filepath):
                    return jsonify({"error": "File not found"}), 404

                # Return file
                from flask import send_file
                return send_file(filepath, as_attachment=True, download_name=filename)

            except Exception as e:
                self.logger.error(f"Download export file API error: {e}")
                return jsonify({"error": f"Download failed: {str(e)}"}), 500

    def _configure_websocket_events(self):
        """Configure WebSocket event handlers."""
        if not self.socketio:
            return

        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            self.logger.info(f"Client connected: {request.sid}")
            emit('connected', {'message': 'Connected to expedition updates'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            self.logger.info(f"Client disconnected: {request.sid}")

        @self.socketio.on('join_expedition')
        def handle_join_expedition(data):
            """Handle client joining expedition room."""
            try:
                expedition_id = data.get('expedition_id')
                user_id = data.get('user_id')

                if not expedition_id or not user_id:
                    emit('error', {'message': 'Missing expedition_id or user_id'})
                    return

                room_name = f"expedition_{expedition_id}"
                join_room(room_name)

                # Subscribe user to expedition updates
                from core.modern_service_container import get_websocket_service
                websocket_service = get_websocket_service()
                websocket_service.subscribe_to_expedition(user_id, expedition_id)

                self.logger.info(f"User {user_id} joined expedition {expedition_id} room")
                emit('joined', {'expedition_id': expedition_id, 'room': room_name})

            except Exception as e:
                self.logger.error(f"Join expedition error: {e}")
                emit('error', {'message': 'Failed to join expedition'})

        @self.socketio.on('leave_expedition')
        def handle_leave_expedition(data):
            """Handle client leaving expedition room."""
            try:
                expedition_id = data.get('expedition_id')
                user_id = data.get('user_id')

                if not expedition_id or not user_id:
                    emit('error', {'message': 'Missing expedition_id or user_id'})
                    return

                room_name = f"expedition_{expedition_id}"
                leave_room(room_name)

                # Unsubscribe user from expedition updates
                from core.modern_service_container import get_websocket_service
                websocket_service = get_websocket_service()
                websocket_service.unsubscribe_from_expedition(user_id, expedition_id)

                self.logger.info(f"User {user_id} left expedition {expedition_id} room")
                emit('left', {'expedition_id': expedition_id})

            except Exception as e:
                self.logger.error(f"Leave expedition error: {e}")
                emit('error', {'message': 'Failed to leave expedition'})

        @self.socketio.on('get_expedition_metrics')
        def handle_get_expedition_metrics(data):
            """Handle request for expedition metrics."""
            try:
                expedition_id = data.get('expedition_id')

                if not expedition_id:
                    emit('error', {'message': 'Missing expedition_id'})
                    return

                from core.modern_service_container import get_websocket_service
                websocket_service = get_websocket_service()
                metrics = websocket_service.get_expedition_metrics(expedition_id)

                emit('expedition_metrics', metrics)

            except Exception as e:
                self.logger.error(f"Get expedition metrics error: {e}")
                emit('error', {'message': 'Failed to get expedition metrics'})

        @self.socketio.on('join_user_room')
        def handle_join_user_room(data):
            """Handle user joining their personal notification room."""
            try:
                user_id = data.get('user_id')

                if not user_id:
                    emit('error', {'message': 'Missing user_id'})
                    return

                room_name = f"user_{user_id}"
                join_room(room_name)

                self.logger.info(f"User {user_id} joined personal notification room")
                emit('joined_user_room', {'user_id': user_id, 'room': room_name})

            except Exception as e:
                self.logger.error(f"Join user room error: {e}")
                emit('error', {'message': 'Failed to join user room'})

    def run(self):
        """Run the complete application."""
        try:
            # Initialize services
            self.logger.info(">> STEP 1: Initializing services")
            self.initialize_services()
            
            # Create Flask app
            self.logger.info(">> STEP 2: Creating Flask app")
            app = self.create_flask_app()
            
            # Initialize bot
            self.logger.info(">> STEP 3: Initializing bot")
            self.initialize_bot()
            
            # Register cleanup
            import atexit
            self.logger.info(">> STEP 4: Starting Flask")
            atexit.register(self.cleanup)
            
            # Handle signals
            import signal
            def signal_handler(signum, frame):
                self.logger.info(f"Received signal {signum}, shutting down gracefully...")
                self.cleanup()
                exit(0)
            
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            
            # Start Flask app with SocketIO
            self.logger.info(f"Starting Flask app with SocketIO on {self.config.host}:{self.config.port}")
            if self.socketio:
                self.socketio.run(
                    app,
                    host=self.config.host,
                    port=self.config.port,
                    debug=False,  # FORCE OFF
                    use_reloader=False  # 🔥 CRITICAL: disables restart
                )
            else:
                # Fallback to regular Flask if SocketIO failed to initialize
                app.run(
                    host=self.config.host,
                    port=self.config.port,
                    debug=False,  # FORCE OFF
                    use_reloader=False  # 🔥 CRITICAL: disables restart
                )
            
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            self.cleanup()
        except Exception as e:
            self.logger.error(f"Application error: {e}", exc_info=True)
            self.cleanup()
            raise
    
    def cleanup(self):
        """Clean shutdown for all services."""
        self.logger.info("Performing cleanup...")
        
        try:
            # Shutdown bot manager
            if self.bot_manager:
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.bot_manager.shutdown())
                    self.logger.info("Bot manager shutdown complete")
                except Exception as e:
                    self.logger.error(f"Bot shutdown error: {e}")
        except Exception as e:
            self.logger.error(f"Error during bot cleanup: {e}")
        
        try:
            # Dispose services
            from core.modern_service_container import get_service_registry
            registry = get_service_registry()
            registry.dispose()
            self.logger.info("Services disposed")
        except Exception as e:
            self.logger.error(f"Error disposing services: {e}")
        
        try:
            # Close database connections
            from database import close_database
            close_database()
            self.logger.info("Database connections closed")
        except Exception as e:
            self.logger.error(f"Database shutdown error: {e}")
        
        self.logger.info("Cleanup completed")


def create_app() -> Flask:
    """
    Factory function to create Flask app.
    Useful for testing and external integrations.
    """
    bot_app = BotApplication()
    bot_app.initialize_services()
    bot_app.initialize_bot()
    return bot_app.create_flask_app()


if __name__ == "__main__":
    # Create and run the application
    bot_application = BotApplication()
    bot_application.run()