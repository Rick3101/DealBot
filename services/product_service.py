from typing import Optional, List
from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError, DuplicateError
from services.product_repository import ProductRepository, StockRepository
from services.validation_service import ValidationService
from models.product import Product, CreateProductRequest, UpdateProductRequest, StockItem, AddStockRequest, ProductWithStock
from utils.input_sanitizer import InputSanitizer
from core.interfaces import IProductService


class ProductService(BaseService, IProductService):
    """
    Service layer for product management.
    Handles product CRUD operations and inventory management.
    Uses repository pattern for data access and unified validation.
    """

    def __init__(self):
        super().__init__()
        self._product_repository = ProductRepository()
        self._stock_repository = StockRepository()
        self._validation_service = ValidationService()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Get product by ID.

        Args:
            product_id: Product ID to search for

        Returns:
            Product object if found, None otherwise
        """
        return self._product_repository.get_by_id(product_id)
    
    def get_product_by_name(self, name: str) -> Optional[Product]:
        """
        Get product by name.

        Args:
            name: Product name to search for

        Returns:
            Product object if found, None otherwise
        """
        try:
            name = InputSanitizer.sanitize_product_name(name)
            return self._product_repository.get_by_name(name)
        except Exception as e:
            self.logger.error(f"Error getting product by name {name}: {e}")
            return None
    
    def get_all_products(self) -> List[Product]:
        """
        Get all products.

        Returns:
            List of all products
        """
        products = self._product_repository.get_all(order_by="nome")
        self._log_operation("products_listed", count=len(products))
        return products
    
    def get_products_with_stock(self) -> List[ProductWithStock]:
        """
        Get all products with their current stock information.

        Returns:
            List of products with stock information
        """
        products_with_stock_data = self._product_repository.get_products_with_stock()

        products_with_stock = []
        for data in products_with_stock_data:
            product_with_stock = ProductWithStock(
                product=data['product'],
                total_quantity=data['total_quantity'],
                average_cost=data['average_cost'],
                average_price=data['average_price'],
                total_value=data['total_value']
            )
            products_with_stock.append(product_with_stock)

        return products_with_stock
    
    def create_product(self, request: CreateProductRequest) -> Product:
        """
        Create a new product.

        Args:
            request: Product creation request

        Returns:
            Created product object

        Raises:
            ValidationError: If request is invalid
            DuplicateError: If product name already exists
        """
        # Validate request using ValidationService
        errors = self._validation_service.validate_create_request(request, "product")
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")

        # Sanitize inputs
        try:
            nome = InputSanitizer.sanitize_product_name(request.nome)
            emoji = InputSanitizer.sanitize_emoji(request.emoji) if request.emoji else None
        except ValueError as e:
            raise ValidationError(f"Input validation failed: {str(e)}")

        # Check business rules
        business_errors = self._validation_service.validate_business_rules("product", {"nome": nome})
        if business_errors:
            raise DuplicateError(business_errors[0])  # First error is likely duplicate

        # Create product using repository
        try:
            data = {
                "nome": nome,
                "emoji": emoji,
                "media_file_id": request.media_file_id
            }

            product = self._product_repository.create(data)
            if not product:
                raise ServiceError("Failed to create product - no product returned")

            self._log_operation("product_created", nome=nome, product_id=product.id)
            return product

        except Exception as e:
            self.logger.error(f"Error creating product {nome}: {e}")
            if isinstance(e, (ValidationError, DuplicateError)):
                raise
            raise ServiceError(f"Failed to create product: {str(e)}")
    
    def update_product(self, request: UpdateProductRequest) -> Product:
        """
        Update an existing product.

        Args:
            request: Product update request

        Returns:
            Updated product object

        Raises:
            NotFoundError: If product doesn't exist
            ValidationError: If request is invalid
        """
        if not request.has_updates():
            raise ValidationError("No updates provided")

        # Check if product exists
        existing_product = self._product_repository.get_by_id(request.product_id)
        if not existing_product:
            raise NotFoundError(f"Product with ID {request.product_id} not found")

        # Validate request using ValidationService
        errors = self._validation_service.validate_update_request(request, existing_product)
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")

        # Build update data
        update_data = {}

        if request.nome is not None:
            try:
                nome = InputSanitizer.sanitize_product_name(request.nome)
                # Check business rules for duplicate name
                business_errors = self._validation_service.validate_business_rules(
                    "product", {"nome": nome, "exclude_id": request.product_id}
                )
                if business_errors:
                    raise DuplicateError(business_errors[0])
                update_data["nome"] = nome
            except ValueError as e:
                raise ValidationError(f"Invalid product name: {str(e)}")

        if request.emoji is not None:
            try:
                emoji = InputSanitizer.sanitize_emoji(request.emoji) if request.emoji else None
                update_data["emoji"] = emoji
            except ValueError as e:
                raise ValidationError(f"Invalid emoji: {str(e)}")

        if request.media_file_id is not None:
            update_data["media_file_id"] = request.media_file_id

        # Execute update using repository
        try:
            product = self._product_repository.update(request.product_id, update_data)
            if not product:
                raise ServiceError("Failed to update product - no product returned")

            self._log_operation("product_updated", product_id=request.product_id, updates=len(update_data))
            return product

        except Exception as e:
            self.logger.error(f"Error updating product {request.product_id}: {e}")
            if isinstance(e, (ValidationError, DuplicateError, NotFoundError)):
                raise
            raise ServiceError(f"Failed to update product: {str(e)}")
    
    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product.
        Note: This will also delete associated stock items due to foreign key constraints.

        Args:
            product_id: ID of product to delete

        Returns:
            True if deleted successfully

        Raises:
            NotFoundError: If product doesn't exist
        """
        # Delete using repository (includes existence check)
        success = self._product_repository.delete(product_id)

        if success:
            self._log_operation("product_deleted", product_id=product_id)

        return success
    
    def product_name_exists(self, name: str, exclude_product_id: Optional[int] = None) -> bool:
        """
        Check if product name already exists.

        Args:
            name: Product name to check
            exclude_product_id: Product ID to exclude from check (for updates)

        Returns:
            True if name exists, False otherwise
        """
        return self._product_repository.name_exists(name, exclude_product_id)
    
    def add_stock(self, request: AddStockRequest) -> StockItem:
        """
        Add stock for a product.

        Args:
            request: Add stock request

        Returns:
            Created stock item

        Raises:
            ValidationError: If request is invalid
            NotFoundError: If product doesn't exist
        """
        # Validate request
        errors = request.validate()
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")

        # Check if product exists
        if not self._product_repository.get_by_id(request.produto_id):
            raise NotFoundError(f"Product with ID {request.produto_id} not found")

        # Add stock using repository
        try:
            stock_item = self._stock_repository.add_stock(
                request.produto_id,
                request.quantidade,
                request.valor,
                request.custo
            )

            self._log_operation(
                "stock_added",
                produto_id=request.produto_id,
                quantidade=request.quantidade,
                valor=request.valor
            )
            return stock_item

        except Exception as e:
            self.logger.error(f"Error adding stock for product {request.produto_id}: {e}")
            if isinstance(e, (ValidationError, NotFoundError)):
                raise
            raise ServiceError(f"Failed to add stock: {str(e)}")
    
    def get_product_stock(self, product_id: int) -> List[StockItem]:
        """
        Get all stock items for a product.

        Args:
            product_id: Product ID

        Returns:
            List of stock items
        """
        return self._stock_repository.get_by_product_id(product_id)
    
    def get_available_quantity(self, product_id: int) -> int:
        """
        Get total available quantity for a product.

        Args:
            product_id: Product ID

        Returns:
            Total available quantity
        """
        return self._stock_repository.get_available_quantity(product_id)
    
    def consume_stock(self, product_id: int, quantity: int) -> List[StockItem]:
        """
        Consume stock using FIFO method.

        Args:
            product_id: Product ID
            quantity: Quantity to consume

        Returns:
            List of stock items that were consumed (for audit trail)

        Raises:
            ValidationError: If insufficient stock
        """
        try:
            consumed_items = self._stock_repository.consume_fifo(product_id, quantity)
            self._log_operation("stock_consumed", product_id=product_id, quantity=quantity)
            return consumed_items

        except Exception as e:
            self.logger.error(f"Error consuming stock for product {product_id}: {e}")
            if isinstance(e, ValidationError):
                raise
            raise ServiceError(f"Failed to consume stock: {str(e)}")