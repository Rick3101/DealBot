from typing import Optional, List
from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError, DuplicateError
from models.product import Product, CreateProductRequest, UpdateProductRequest, StockItem, AddStockRequest, ProductWithStock
from utils.input_sanitizer import InputSanitizer
from core.interfaces import IProductService


class ProductService(BaseService, IProductService):
    """
    Service layer for product management.
    Handles product CRUD operations and inventory management.
    """
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Get product by ID.
        
        Args:
            product_id: Product ID to search for
            
        Returns:
            Product object if found, None otherwise
        """
        query = "SELECT id, nome, emoji, media_file_id FROM Produtos WHERE id = %s"
        row = self._execute_query(query, (product_id,), fetch_one=True)
        
        return Product.from_db_row(row) if row else None
    
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
            query = "SELECT id, nome, emoji, media_file_id FROM Produtos WHERE nome = %s"
            row = self._execute_query(query, (name,), fetch_one=True)
            
            return Product.from_db_row(row) if row else None
            
        except Exception as e:
            self.logger.error(f"Error getting product by name {name}: {e}")
            return None
    
    def get_all_products(self) -> List[Product]:
        """
        Get all products.
        
        Returns:
            List of all products
        """
        query = "SELECT id, nome, emoji, media_file_id FROM Produtos ORDER BY nome"
        rows = self._execute_query(query, fetch_all=True)
        
        products = []
        if rows:
            for row in rows:
                product = Product.from_db_row(row)
                if product:
                    products.append(product)
        
        self._log_operation("products_listed", count=len(products))
        return products
    
    def get_products_with_stock(self) -> List[ProductWithStock]:
        """
        Get all products with their current stock information.
        
        Returns:
            List of products with stock information
        """
        query = """
            SELECT 
                p.id, p.nome, p.emoji, p.media_file_id,
                COALESCE(SUM(e.quantidade), 0) as total_quantity,
                COALESCE(AVG(e.custo), 0) as avg_cost,
                COALESCE(AVG(e.preco), 0) as avg_price,
                COALESCE(SUM(e.quantidade * e.preco), 0) as total_value
            FROM Produtos p
            LEFT JOIN Estoque e ON p.id = e.produto_id
            GROUP BY p.id, p.nome, p.emoji, p.media_file_id
            ORDER BY p.nome
        """
        
        rows = self._execute_query(query, fetch_all=True)
        
        products_with_stock = []
        if rows:
            for row in rows:
                product_data = row[:4]  # First 4 columns are product data
                stock_data = row[4:]    # Last 4 columns are stock data
                
                product = Product.from_db_row(product_data)
                if product:
                    product_with_stock = ProductWithStock(
                        product=product,
                        total_quantity=int(stock_data[0]),
                        average_cost=float(stock_data[1]),
                        average_price=float(stock_data[2]),
                        total_value=float(stock_data[3])
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
        # Validate request
        errors = request.validate()
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")
        
        # Sanitize inputs
        try:
            nome = InputSanitizer.sanitize_product_name(request.nome)
            emoji = InputSanitizer.sanitize_emoji(request.emoji) if request.emoji else None
        except ValueError as e:
            raise ValidationError(f"Input validation failed: {str(e)}")
        
        # Check if product name already exists
        if self.product_name_exists(nome):
            raise DuplicateError(f"Product '{nome}' already exists")
        
        # Create product
        query = """
            INSERT INTO Produtos (nome, emoji, media_file_id) 
            VALUES (%s, %s, %s) 
            RETURNING id, nome, emoji, media_file_id
        """
        
        try:
            row = self._execute_query(
                query, 
                (nome, emoji, request.media_file_id), 
                fetch_one=True
            )
            
            if not row:
                raise ServiceError("Failed to create product - no row returned")
            
            product = Product.from_db_row(row)
            self._log_operation("product_created", nome=nome, product_id=product.id)
            return product
            
        except Exception as e:
            self.logger.error(f"Error creating product {nome}: {e}")
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
        existing_product = self.get_product_by_id(request.product_id)
        if not existing_product:
            raise NotFoundError(f"Product with ID {request.product_id} not found")
        
        # Build update query dynamically
        updates = []
        params = []
        
        if request.nome is not None:
            try:
                nome = InputSanitizer.sanitize_product_name(request.nome)
                # Check for duplicate name (excluding current product)
                if self.product_name_exists(nome, exclude_product_id=request.product_id):
                    raise DuplicateError(f"Product '{nome}' already exists")
                updates.append("nome = %s")
                params.append(nome)
            except ValueError as e:
                raise ValidationError(f"Invalid product name: {str(e)}")
        
        if request.emoji is not None:
            try:
                emoji = InputSanitizer.sanitize_emoji(request.emoji) if request.emoji else None
                updates.append("emoji = %s")
                params.append(emoji)
            except ValueError as e:
                raise ValidationError(f"Invalid emoji: {str(e)}")
        
        if request.media_file_id is not None:
            updates.append("media_file_id = %s")
            params.append(request.media_file_id)
        
        # Execute update
        params.append(request.product_id)  # Add product_id for WHERE clause
        query = f"""
            UPDATE Produtos 
            SET {', '.join(updates)} 
            WHERE id = %s 
            RETURNING id, nome, emoji, media_file_id
        """
        
        try:
            row = self._execute_query(query, tuple(params), fetch_one=True)
            
            if not row:
                raise ServiceError("Failed to update product - no row returned")
            
            product = Product.from_db_row(row)
            self._log_operation("product_updated", product_id=request.product_id, updates=len(updates))
            return product
            
        except Exception as e:
            self.logger.error(f"Error updating product {request.product_id}: {e}")
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
        # Check if product exists
        if not self.get_product_by_id(product_id):
            raise NotFoundError(f"Product with ID {product_id} not found")
        
        # Delete product (stock items will be deleted automatically due to FK constraint)
        query = "DELETE FROM Produtos WHERE id = %s"
        rows_affected = self._execute_query(query, (product_id,))
        
        if rows_affected > 0:
            self._log_operation("product_deleted", product_id=product_id)
            return True
        
        return False
    
    def product_name_exists(self, name: str, exclude_product_id: Optional[int] = None) -> bool:
        """
        Check if product name already exists.
        
        Args:
            name: Product name to check
            exclude_product_id: Product ID to exclude from check (for updates)
            
        Returns:
            True if name exists, False otherwise
        """
        if exclude_product_id:
            query = "SELECT 1 FROM Produtos WHERE nome = %s AND id != %s"
            params = (name, exclude_product_id)
        else:
            query = "SELECT 1 FROM Produtos WHERE nome = %s"
            params = (name,)
        
        row = self._execute_query(query, params, fetch_one=True)
        return row is not None
    
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
        if not self.get_product_by_id(request.produto_id):
            raise NotFoundError(f"Product with ID {request.produto_id} not found")
        
        # Add stock
        query = """
            INSERT INTO Estoque (produto_id, quantidade, preco, custo) 
            VALUES (%s, %s, %s, %s) 
            RETURNING id, produto_id, quantidade, preco, custo, data_adicao
        """
        
        try:
            row = self._execute_query(
                query, 
                (request.produto_id, request.quantidade, request.valor, request.custo), 
                fetch_one=True
            )
            
            if not row:
                raise ServiceError("Failed to add stock - no row returned")
            
            stock_item = StockItem.from_db_row(row)
            self._log_operation(
                "stock_added", 
                produto_id=request.produto_id, 
                quantidade=request.quantidade,
                valor=request.valor
            )
            return stock_item
            
        except Exception as e:
            self.logger.error(f"Error adding stock for product {request.produto_id}: {e}")
            raise ServiceError(f"Failed to add stock: {str(e)}")
    
    def get_product_stock(self, product_id: int) -> List[StockItem]:
        """
        Get all stock items for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            List of stock items
        """
        query = """
            SELECT id, produto_id, quantidade, preco, custo, data_adicao 
            FROM Estoque 
            WHERE produto_id = %s 
            ORDER BY data_adicao ASC
        """
        
        rows = self._execute_query(query, (product_id,), fetch_all=True)
        
        stock_items = []
        if rows:
            for row in rows:
                stock_item = StockItem.from_db_row(row)
                if stock_item:
                    stock_items.append(stock_item)
        
        return stock_items
    
    def get_available_quantity(self, product_id: int) -> int:
        """
        Get total available quantity for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            Total available quantity
        """
        query = "SELECT COALESCE(SUM(quantidade), 0) FROM Estoque WHERE produto_id = %s"
        row = self._execute_query(query, (product_id,), fetch_one=True)
        
        return int(row[0]) if row else 0
    
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
        available = self.get_available_quantity(product_id)
        if available < quantity:
            raise ValidationError(f"Insufficient stock. Available: {available}, Requested: {quantity}")
        
        # Get stock items in FIFO order
        stock_items = self.get_product_stock(product_id)
        
        consumed_items = []
        remaining_to_consume = quantity
        
        try:
            for stock_item in stock_items:
                if remaining_to_consume <= 0:
                    break
                
                if stock_item.quantidade <= remaining_to_consume:
                    # Consume entire stock item
                    consumed_quantity = stock_item.quantidade
                    remaining_to_consume -= consumed_quantity
                    
                    # Delete stock item
                    delete_query = "DELETE FROM Estoque WHERE id = %s"
                    self._execute_query(delete_query, (stock_item.id,))
                    
                    consumed_items.append(stock_item)
                    
                else:
                    # Partially consume stock item
                    consumed_quantity = remaining_to_consume
                    new_quantity = stock_item.quantidade - consumed_quantity
                    remaining_to_consume = 0
                    
                    # Update stock item quantity
                    update_query = "UPDATE Estoque SET quantidade = %s WHERE id = %s"
                    self._execute_query(update_query, (new_quantity, stock_item.id))
                    
                    # Create consumed item record
                    consumed_item = StockItem(
                        id=stock_item.id,
                        produto_id=stock_item.produto_id,
                        quantidade=consumed_quantity,
                        valor=stock_item.valor,
                        custo=stock_item.custo,
                        data=stock_item.data
                    )
                    consumed_items.append(consumed_item)
            
            self._log_operation("stock_consumed", product_id=product_id, quantity=quantity)
            return consumed_items
            
        except Exception as e:
            self.logger.error(f"Error consuming stock for product {product_id}: {e}")
            raise ServiceError(f"Failed to consume stock: {str(e)}")