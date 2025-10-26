import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Optional, List, Dict, Any

from services.base_repository import BaseRepository
from services.base_service import ServiceError, ValidationError, NotFoundError


class MockModel:
    """Mock model class for testing BaseRepository"""

    def __init__(self, id: int, name: str, value: str = None):
        self.id = id
        self.name = name
        self.value = value

    @classmethod
    def from_db_row(cls, row):
        """Create model from database row"""
        if not row:
            return None
        return cls(id=row[0], name=row[1], value=row[2] if len(row) > 2 else None)


class TestBaseRepository:
    """Test suite for BaseRepository class"""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository for testing"""
        with patch('services.base_repository.get_db_manager'):
            repo = BaseRepository("test_table", MockModel, "id")
            repo._column_mappings = ["id", "name", "value"]
            return repo

    def test_init(self, mock_repository):
        """Test repository initialization"""
        assert mock_repository.table_name == "test_table"
        assert mock_repository.model_class == MockModel
        assert mock_repository.primary_key == "id"
        assert mock_repository._column_mappings == ["id", "name", "value"]

    def test_build_select_query_basic(self, mock_repository):
        """Test basic SELECT query building"""
        query = mock_repository._build_select_query()
        expected = "SELECT id, name, value FROM test_table"
        assert query == expected

    def test_build_select_query_with_where(self, mock_repository):
        """Test SELECT query with WHERE clause"""
        query = mock_repository._build_select_query(where_clause="id = %s")
        expected = "SELECT id, name, value FROM test_table WHERE id = %s"
        assert query == expected

    def test_build_select_query_with_order_by(self, mock_repository):
        """Test SELECT query with ORDER BY clause"""
        query = mock_repository._build_select_query(order_by="name ASC")
        expected = "SELECT id, name, value FROM test_table ORDER BY name ASC"
        assert query == expected

    def test_build_select_query_with_limit(self, mock_repository):
        """Test SELECT query with LIMIT clause"""
        query = mock_repository._build_select_query(limit=10)
        expected = "SELECT id, name, value FROM test_table LIMIT 10"
        assert query == expected

    def test_build_select_query_complete(self, mock_repository):
        """Test SELECT query with all clauses"""
        query = mock_repository._build_select_query(
            columns=["id", "name"],
            where_clause="active = %s",
            order_by="name DESC",
            limit=5
        )
        expected = "SELECT id, name FROM test_table WHERE active = %s ORDER BY name DESC LIMIT 5"
        assert query == expected

    def test_get_by_id_success(self, mock_repository):
        """Test successful get_by_id operation"""
        mock_repository._execute_query = Mock(return_value=(1, "test_name", "test_value"))

        result = mock_repository.get_by_id(1)

        assert result is not None
        assert result.id == 1
        assert result.name == "test_name"
        assert result.value == "test_value"

        mock_repository._execute_query.assert_called_once_with(
            "SELECT id, name, value FROM test_table WHERE id = %s",
            (1,),
            fetch_one=True
        )

    def test_get_by_id_not_found(self, mock_repository):
        """Test get_by_id when entity not found"""
        mock_repository._execute_query = Mock(return_value=None)

        result = mock_repository.get_by_id(999)

        assert result is None

    def test_get_all_success(self, mock_repository):
        """Test successful get_all operation"""
        mock_rows = [
            (1, "item1", "value1"),
            (2, "item2", "value2"),
            (3, "item3", "value3")
        ]
        mock_repository._execute_query = Mock(return_value=mock_rows)
        mock_repository._log_operation = Mock()

        result = mock_repository.get_all()

        assert len(result) == 3
        assert result[0].id == 1
        assert result[1].name == "item2"
        assert result[2].value == "value3"

        mock_repository._log_operation.assert_called_once_with("get_all_test_table", count=3)

    def test_get_all_with_order_and_limit(self, mock_repository):
        """Test get_all with order by and limit"""
        mock_repository._execute_query = Mock(return_value=[(1, "item1", "value1")])
        mock_repository._log_operation = Mock()

        result = mock_repository.get_all(order_by="name ASC", limit=5)

        mock_repository._execute_query.assert_called_once_with(
            "SELECT id, name, value FROM test_table ORDER BY name ASC LIMIT 5",
            fetch_all=True
        )

    def test_get_by_field_success(self, mock_repository):
        """Test successful get_by_field operation"""
        mock_rows = [
            (1, "test_name", "search_value"),
            (2, "test_name2", "search_value")
        ]
        mock_repository._execute_query = Mock(return_value=mock_rows)

        result = mock_repository.get_by_field("value", "search_value")

        assert len(result) == 2
        assert result[0].value == "search_value"
        assert result[1].value == "search_value"

        mock_repository._execute_query.assert_called_once_with(
            "SELECT id, name, value FROM test_table WHERE value = %s",
            ("search_value",),
            fetch_all=True
        )

    def test_get_one_by_field_success(self, mock_repository):
        """Test successful get_one_by_field operation"""
        mock_repository.get_by_field = Mock(return_value=[MockModel(1, "test", "value")])

        result = mock_repository.get_one_by_field("name", "test")

        assert result is not None
        assert result.name == "test"
        mock_repository.get_by_field.assert_called_once_with("name", "test", limit=1)

    def test_get_one_by_field_not_found(self, mock_repository):
        """Test get_one_by_field when no results"""
        mock_repository.get_by_field = Mock(return_value=[])

        result = mock_repository.get_one_by_field("name", "nonexistent")

        assert result is None

    def test_exists_true(self, mock_repository):
        """Test exists when entity exists"""
        mock_repository._execute_query = Mock(return_value=(1,))

        result = mock_repository.exists("name", "test_name")

        assert result is True
        mock_repository._execute_query.assert_called_once_with(
            "SELECT 1 FROM test_table WHERE name = %s LIMIT 1",
            ("test_name",),
            fetch_one=True
        )

    def test_exists_false(self, mock_repository):
        """Test exists when entity does not exist"""
        mock_repository._execute_query = Mock(return_value=None)

        result = mock_repository.exists("name", "nonexistent")

        assert result is False

    def test_exists_with_exclude(self, mock_repository):
        """Test exists with exclude_id parameter"""
        mock_repository._execute_query = Mock(return_value=None)

        result = mock_repository.exists("name", "test_name", exclude_id=1)

        assert result is False
        mock_repository._execute_query.assert_called_once_with(
            "SELECT 1 FROM test_table WHERE name = %s AND id != %s LIMIT 1",
            ("test_name", 1),
            fetch_one=True
        )

    def test_count_all(self, mock_repository):
        """Test count without filters"""
        mock_repository._execute_query = Mock(return_value=(5,))

        result = mock_repository.count()

        assert result == 5
        mock_repository._execute_query.assert_called_once_with(
            "SELECT COUNT(*) FROM test_table",
            (),
            fetch_one=True
        )

    def test_count_with_filter(self, mock_repository):
        """Test count with WHERE clause"""
        mock_repository._execute_query = Mock(return_value=(3,))

        result = mock_repository.count("active = %s", ("Y",))

        assert result == 3
        mock_repository._execute_query.assert_called_once_with(
            "SELECT COUNT(*) FROM test_table WHERE active = %s",
            ("Y",),
            fetch_one=True
        )

    def test_create_success(self, mock_repository):
        """Test successful create operation"""
        mock_repository._execute_query = Mock(return_value=(1, "new_item", "new_value"))
        mock_repository._log_operation = Mock()

        data = {"name": "new_item", "value": "new_value"}
        result = mock_repository.create(data)

        assert result is not None
        assert result.name == "new_item"
        assert result.value == "new_value"

        expected_query = "INSERT INTO test_table (name, value) VALUES (%s, %s) RETURNING id, name, value"
        mock_repository._execute_query.assert_called_once_with(
            expected_query,
            ("new_item", "new_value"),
            fetch_one=True
        )
        mock_repository._log_operation.assert_called_once()

    def test_create_empty_data(self, mock_repository):
        """Test create with empty data raises ValidationError"""
        with pytest.raises(ValidationError, match="No data provided for creation"):
            mock_repository.create({})

    def test_update_success(self, mock_repository):
        """Test successful update operation"""
        mock_repository.exists = Mock(return_value=True)
        mock_repository._execute_query = Mock(return_value=(1, "updated_item", "updated_value"))
        mock_repository._log_operation = Mock()

        data = {"name": "updated_item", "value": "updated_value"}
        result = mock_repository.update(1, data)

        assert result is not None
        assert result.name == "updated_item"
        assert result.value == "updated_value"

        expected_query = "UPDATE test_table SET name = %s, value = %s WHERE id = %s RETURNING id, name, value"
        mock_repository._execute_query.assert_called_once_with(
            expected_query,
            ("updated_item", "updated_value", 1),
            fetch_one=True
        )

    def test_update_not_found(self, mock_repository):
        """Test update when entity doesn't exist"""
        mock_repository.exists = Mock(return_value=False)

        with pytest.raises(NotFoundError, match="test_table with id=999 not found"):
            mock_repository.update(999, {"name": "updated"})

    def test_update_empty_data(self, mock_repository):
        """Test update with empty data raises ValidationError"""
        with pytest.raises(ValidationError, match="No data provided for update"):
            mock_repository.update(1, {})

    def test_delete_success(self, mock_repository):
        """Test successful delete operation"""
        mock_repository.exists = Mock(return_value=True)
        mock_repository._execute_query = Mock(return_value=1)
        mock_repository._log_operation = Mock()

        result = mock_repository.delete(1)

        assert result is True
        mock_repository._execute_query.assert_called_once_with(
            "DELETE FROM test_table WHERE id = %s",
            (1,)
        )
        mock_repository._log_operation.assert_called_once_with("delete_test_table", entity_id=1)

    def test_delete_not_found(self, mock_repository):
        """Test delete when entity doesn't exist"""
        mock_repository.exists = Mock(return_value=False)

        with pytest.raises(NotFoundError, match="test_table with id=999 not found"):
            mock_repository.delete(999)

    def test_delete_by_field_success(self, mock_repository):
        """Test successful delete_by_field operation"""
        mock_repository._execute_query = Mock(return_value=3)
        mock_repository._log_operation = Mock()

        result = mock_repository.delete_by_field("status", "inactive")

        assert result == 3
        mock_repository._execute_query.assert_called_once_with(
            "DELETE FROM test_table WHERE status = %s",
            ("inactive",)
        )
        mock_repository._log_operation.assert_called_once_with(
            "delete_by_field_test_table",
            field="status",
            value="inactive",
            count=3
        )

    def test_execute_custom_query(self, mock_repository):
        """Test execute_custom_query operation"""
        mock_repository._execute_query = Mock(return_value=[(1, "test")])
        mock_repository._log_operation = Mock()

        query = "SELECT id, name FROM test_table WHERE custom_field = %s"
        result = mock_repository.execute_custom_query(query, ("value",), fetch_all=True)

        assert result == [(1, "test")]
        mock_repository._execute_query.assert_called_once_with(
            query,
            ("value",),
            False,
            True
        )
        mock_repository._log_operation.assert_called_once_with(
            "custom_query_test_table",
            query_type="SELECT"
        )


class TestBaseRepositoryIntegration:
    """Integration tests for BaseRepository with more realistic scenarios"""

    @pytest.fixture
    def user_repository(self):
        """Create repository for Users table"""
        with patch('services.base_repository.get_db_manager'):
            repo = BaseRepository("Usuarios", MockModel, "id")
            repo._column_mappings = ["id", "username", "nivel"]
            return repo

    def test_user_crud_workflow(self, user_repository):
        """Test complete CRUD workflow for user entity"""
        # Mock database operations
        user_repository._execute_query = Mock()
        user_repository._log_operation = Mock()

        # Test create
        user_repository._execute_query.return_value = (1, "testuser", "admin")
        user = user_repository.create({"username": "testuser", "nivel": "admin"})
        assert user.name == "testuser"  # MockModel maps username to name

        # Test read
        user_repository._execute_query.return_value = (1, "testuser", "admin")
        user = user_repository.get_by_id(1)
        assert user.id == 1

        # Test update
        user_repository.exists = Mock(return_value=True)
        user_repository._execute_query.return_value = (1, "testuser", "owner")
        updated_user = user_repository.update(1, {"nivel": "owner"})
        assert updated_user.value == "owner"  # MockModel maps nivel to value

        # Test delete
        user_repository.exists = Mock(return_value=True)
        user_repository._execute_query.return_value = 1
        result = user_repository.delete(1)
        assert result is True

    def test_bulk_operations(self, user_repository):
        """Test bulk operations and filtering"""
        # Mock get_all
        mock_users = [
            (1, "user1", "admin"),
            (2, "user2", "user"),
            (3, "user3", "admin")
        ]
        user_repository._execute_query = Mock(return_value=mock_users)
        user_repository._log_operation = Mock()

        users = user_repository.get_all(order_by="username ASC")
        assert len(users) == 3

        # Test filter by field
        admin_users = [(1, "user1", "admin"), (3, "user3", "admin")]
        user_repository._execute_query.return_value = admin_users
        admins = user_repository.get_by_field("nivel", "admin")
        assert len(admins) == 2

        # Test count
        user_repository._execute_query.return_value = (2,)
        count = user_repository.count("nivel = %s", ("admin",))
        assert count == 2