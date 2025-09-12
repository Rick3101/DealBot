import asyncio
import logging
import threading
from queue import Queue
from typing import Optional
from telegram import Update
from telegram.ext import Application, ContextTypes
from telegram.request import HTTPXRequest
from core.modern_service_container import get_service_registry


class BotManager:
    """
    Clean bot management for Render deployment with nest_asyncio.
    Handles bot initialization, webhook setup, and update processing.
    """
    
    def __init__(self, token: str, webhook_url: str):
        self.token = token
        self.webhook_url = webhook_url
        self.app_bot: Optional[Application] = None
        self.update_queue = Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)
        self._is_initialized = False
        # Services are now managed globally by modern service container
        
    @property
    def is_ready(self) -> bool:
        """Check if bot is ready to process updates."""
        ready = (self.app_bot is not None and 
                self.app_bot.bot is not None and 
                self._is_initialized)
        if not ready:
            self.logger.debug(f"Bot not ready - app_bot: {self.app_bot is not None}, "
                            f"bot: {self.app_bot.bot is not None if self.app_bot else False}, "
                            f"initialized: {self._is_initialized}")
        return ready
    
    def start_worker(self):
        """Start the update processing worker thread."""
        if self.worker_thread and self.worker_thread.is_alive():
            self.logger.info("Worker thread already running")
            return
            
        self.worker_thread = threading.Thread(
            target=self._run_worker, 
            daemon=True, 
            name="BotUpdateWorker"
        )
        self.worker_thread.start()
        self.logger.info("Bot worker thread started")
    
    def _run_worker(self):
        """Run the async worker in a new event loop."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._worker_loop())
        except Exception as e:
            self.logger.error(f"Worker thread crashed: {e}", exc_info=True)
            raise
    
    async def _worker_loop(self):
        """Main worker loop that processes updates."""
        try:
            await self._initialize_bot()
            await self._start_processing_loop()
        except Exception as e:
            self.logger.error(f"Worker loop error: {e}", exc_info=True)
            raise
    
    async def _initialize_bot(self):
        """Initialize the telegram bot application."""
        if self.app_bot is not None:
            self.logger.info("Bot already initialized")
            return
            
        self.logger.info("Initializing bot application...")
        
        # Create bot application with timeouts
        request_conf = HTTPXRequest(
            connect_timeout=10, 
            read_timeout=10, 
            write_timeout=10
        )
        
        self.app_bot = Application.builder().token(self.token).request(request_conf).build()
        
        # Register error handler
        self.app_bot.add_error_handler(self._error_handler)
        
        # Inject services into application
        # Modern service container uses global registry - no injection needed
        
        # Register all handlers (will be set from outside)
        self._register_handlers()
        
        # Initialize and set webhook
        await self.app_bot.initialize()
        self.logger.info(f"Setting webhook URL: {self.webhook_url}")
        
        try:
            await self.app_bot.bot.set_webhook(url=self.webhook_url)
            self.logger.info("Webhook set successfully")
            
            # Verify webhook was set
            webhook_info = await self.app_bot.bot.get_webhook_info()
            self.logger.info(f"Webhook info: URL={webhook_info.url}, pending_updates={webhook_info.pending_update_count}")
            
        except Exception as webhook_error:
            self.logger.error(f"Failed to set webhook: {webhook_error}")
            raise
            
        if not self.webhook_url:
            await self.app_bot.start()     

        self._is_initialized = True
        self.logger.info(f"Bot application initialized and webhook set. Bot ready: {self.is_ready}")
    
    def _register_handlers(self):
        """Register all telegram handlers. Override this method to add handlers."""
        # This will be set from app.py to avoid circular imports
        if hasattr(self, '_handler_configurator'):
            self._handler_configurator(self.app_bot)
        else:
            self.logger.warning("No handler configurator set")
    
    def set_handler_configurator(self, configurator_func):
        """Set the function that will configure handlers."""
        self._handler_configurator = configurator_func
    
    async def _start_processing_loop(self):
        """Start the main update processing loop."""
        self.logger.info("Starting update processing loop...")
        
        while True:
            try:
                # Get update from queue with timeout to avoid blocking indefinitely
                try:
                    update = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: self.update_queue.get(timeout=1)  # 1 second timeout
                    )
                    # Process the update
                    await self._process_update(update)
                except:
                    # Timeout or empty queue - just continue the loop
                    await asyncio.sleep(0.1)  # Small sleep to prevent busy waiting
                    continue
                
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}", exc_info=True)
                # Continue processing other updates
                await asyncio.sleep(0.1)
                continue
    
    async def _process_update(self, update: Update):
        """Process a single telegram update."""
        try:
            if not self.is_ready:
                self.logger.warning("Bot not ready, skipping update")
                return
                
            await self.app_bot.process_update(update)
            
        except Exception as e:
            self.logger.error(
                f"Error processing update {update.update_id}: {e}", 
                exc_info=True
            )
    
    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Global error handler for telegram bot."""
        error_details = f"Error type: {type(context.error).__name__}, Message: {str(context.error)}"
        self.logger.error(
            f"Telegram bot error: {error_details}", 
            exc_info=context.error
        )
        
        # Log update details for debugging
        if isinstance(update, Update):
            self.logger.error(f"Update details: {update}")
        
        # Try to send error message to user if possible
        if isinstance(update, Update) and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Ocorreu um erro inesperado. Tente novamente."
                )
            except Exception as send_error:
                self.logger.error(f"Failed to send error message: {send_error}")
    
    def queue_update(self, update: Update) -> bool:
        """Queue an update for processing."""
        if not self.is_ready:
            self.logger.warning("Bot not ready, rejecting update")
            return False
            
        try:
            self.update_queue.put(update, timeout=1)  # Don't block forever
            return True
        except Exception as e:
            self.logger.error(f"Failed to queue update: {e}")
            return False
    
    async def shutdown(self):
        """Gracefully shutdown the bot."""
        self.logger.info("Shutting down bot...")
        
        try:
            if self.app_bot:
                await self.app_bot.stop()
                await self.app_bot.shutdown()
                self.logger.info("Bot application shut down")
        except Exception as e:
            self.logger.error(f"Error during bot shutdown: {e}")
        
        self._is_initialized = False
        self.app_bot = None
    
    def get_health_status(self) -> dict:
        """Get health status for monitoring."""
        services_health = get_service_registry().health_check()
        
        return {
            "bot_ready": self.is_ready,
            "worker_alive": self.worker_thread and self.worker_thread.is_alive(),
            "queue_size": self.update_queue.qsize(),
            "initialized": self._is_initialized,
            "services": services_health
        }