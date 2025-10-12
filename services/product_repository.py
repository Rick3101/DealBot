from typing import Optional, List
from services.base_repository import BaseRepository
from models.product import Product, StockItem


class ProductRepository(BaseRepository):
    """
    Repository for product-specific database operations.
    Extends BaseRepository with product-specific functionality.
    """

    def __init__(self):
        super().__init__(
            table_name="Produtos",
            model_class=Product,
            primary_key="id"
        )

    def _get_default_columns(self) -> List[str]:
        """Override to specify product table columns."""
        return ["id", "nome", "emoji", "media_file_id"]

    def get_by_name(self, name: str) -> Optional[Product]:
        """
        Get product by name.

        Args:
            name: Product name to search for

        Returns:
            Product object if found, None otherwise
        """
        return self.get_one_by_field("nome", name)

    def name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if product name exists.

        Args:
            name: Product name to check
            exclude_id: Product ID to exclude from check (for updates)

        Returns:
            True if name exists, False otherwise
        """
        return self.exists("nome", name, exclude_id)

    def get_products_with_stock(self) -> List[dict]:
        """
        Get all products with their current stock information.

        Returns:
            List of dictionaries with product and stock information
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
                    products_with_stock.append({
                        'product': product,
                        'total_quantity': int(stock_data[0]),
                        'average_cost': float(stock_data[1]),
                        'average_price': float(stock_data[2]),
                        'total_value': float(stock_data[3])
                    })

        return products_with_stock


class StockRepository(BaseRepository):
    """
    Repository for stock-specific database operations.
    Handles inventory management for products.
    """

    def __init__(self):
        super().__init__(
            table_name="Estoque",
            model_class=StockItem,
            primary_key="id"
        )

    def _get_default_columns(self) -> List[str]:
        """Override to specify stock table columns."""
        return ["id", "produto_id", "quantidade", "preco", "custo", "data_adicao"]

    def get_by_product_id(self, product_id: int) -> List[StockItem]:
        """
        Get all stock items for a product in FIFO order.

        Args:
            product_id: Product ID

        Returns:
            List of stock items ordered by addition date (FIFO)
        """
        return self.get_by_field("produto_id", product_id, order_by="data_adicao ASC")

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

    def consume_fifo(self, product_id: int, quantity: int) -> List[StockItem]:
        """
        Consume stock using FIFO method with optimized SQL.

        Args:
            product_id: Product ID
            quantity: Quantity to consume

        Returns:
            List of stock items that were consumed (for audit trail)
        """
        from services.base_service import ValidationError, ServiceError

        # Check available quantity
        available = self.get_available_quantity(product_id)
        if available < quantity:
            raise ValidationError(f"Insufficient stock. Available: {available}, Requested: {quantity}")

        try:
            # Use SQL CTE to consume stock in a single query operation
            # This is much faster than N+1 queries
            consume_query = """
            WITH stock_to_consume AS (
                SELECT id, produto_id, quantidade, preco as valor, custo, data_adicao as data,
                       SUM(quantidade) OVER (ORDER BY data_adicao, id) as running_total
                FROM Estoque
                WHERE produto_id = %s
                ORDER BY data_adicao, id
            ),
            items_affected AS (
                SELECT id, produto_id, quantidade, valor, custo, data,
                       CASE
                           WHEN running_total - quantidade >= %s THEN 0
                           WHEN running_total <= %s THEN quantidade
                           ELSE running_total - %s
                       END as consumed_qty
                FROM stock_to_consume
                WHERE running_total > running_total - quantidade
                  AND running_total - quantidade < %s
            )
            SELECT id, produto_id, consumed_qty, quantidade, valor, custo, data
            FROM items_affected
            WHERE consumed_qty > 0
            ORDER BY data, id
            """

            consumed_rows = self._execute_query(
                consume_query,
                (product_id, quantity, quantity, quantity, quantity),
                fetch_all=True
            )

            if not consumed_rows:
                raise ServiceError("No stock items found to consume")

            consumed_items = []

            # Process consumed items: delete fully consumed, update partially consumed
            for row in consumed_rows:
                stock_id, produto_id, consumed_qty, original_qty, valor, custo, data = row

                consumed_item = StockItem(
                    id=stock_id,
                    produto_id=produto_id,
                    quantidade=int(consumed_qty),
                    valor=valor,
                    custo=custo,
                    data=data
                )
                consumed_items.append(consumed_item)

                if consumed_qty >= original_qty:
                    # Fully consumed - delete
                    self.delete(stock_id)
                else:
                    # Partially consumed - update
                    new_quantity = original_qty - consumed_qty
                    self.update(stock_id, {"quantidade": int(new_quantity)})

            self._log_operation("stock_consumed_fifo", product_id=product_id, quantity=quantity)
            return consumed_items

        except Exception as e:
            self.logger.error(f"Error consuming stock for product {product_id}: {e}")
            raise ServiceError(f"Failed to consume stock: {str(e)}")

    def add_stock(self, product_id: int, quantity: int, price: float, cost: float) -> StockItem:
        """
        Add stock for a product.

        Args:
            product_id: Product ID
            quantity: Quantity to add
            price: Sale price
            cost: Cost price

        Returns:
            Created stock item
        """
        data = {
            "produto_id": product_id,
            "quantidade": quantity,
            "preco": price,
            "custo": cost
        }

        return self.create(data)