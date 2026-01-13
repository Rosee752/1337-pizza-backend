from unittest.mock import MagicMock
import pytest
from fastapi import HTTPException
from app.api.v1.services.stock_service import validate_and_reduce_ingredients


def test_validate_and_reduce_ingredients_success():
    mock_db = MagicMock()

    # Mock Pizza Type
    mock_pt = MagicMock()
    mock_pt.dough_id = 1
    mock_pt.sauce_id = 2

    # Mock Topping in PizzaType
    mock_topping_assoc = MagicMock()
    mock_topping_assoc.topping_id = 3
    mock_topping_assoc.quantity = 2
    mock_pt.toppings = [mock_topping_assoc]

    # Mock DB returns
    mock_dough = MagicMock()
    mock_dough.stock = 10

    mock_sauce = MagicMock()
    mock_sauce.stock = 5

    mock_topping = MagicMock()
    mock_topping.stock = 20

    # Setup Side Effects for DB Queries
    def query_side_effect(model):
        query_mock = MagicMock()
        first_mock = query_mock.filter.return_value.with_for_update.return_value.first

        if "Dough" in str(model):
            first_mock.return_value = mock_dough
        elif "Sauce" in str(model):
            first_mock.return_value = mock_sauce
        elif "Topping" in str(model):
            first_mock.return_value = mock_topping
        return query_mock

    mock_db.query.side_effect = query_side_effect

    # Execute
    validate_and_reduce_ingredients(mock_pt, mock_db)

    # Assert Reductions
    assert mock_dough.stock == 9
    assert mock_sauce.stock == 4
    assert mock_topping.stock == 18  # 20 - 2
    mock_db.commit.assert_called_once()


def test_validate_and_reduce_ingredients_no_sauce_stock():
    mock_db = MagicMock()
    mock_pt = MagicMock()
    mock_pt.dough_id = 1
    mock_pt.sauce_id = 2
    mock_pt.toppings = []

    mock_dough = MagicMock()
    mock_dough.stock = 10

    mock_sauce = MagicMock()
    mock_sauce.stock = 0  # Empty

    def query_side_effect(model):
        query_mock = MagicMock()
        first_mock = query_mock.filter.return_value.with_for_update.return_value.first
        if "Dough" in str(model):
            first_mock.return_value = mock_dough
        elif "Sauce" in str(model):
            first_mock.return_value = mock_sauce
        return query_mock

    mock_db.query.side_effect = query_side_effect

    with pytest.raises(HTTPException) as exc:
        validate_and_reduce_ingredients(mock_pt, mock_db)

    assert exc.value.status_code == 409
    assert "Sauce" in exc.value.detail


# ... keep existing tests ...

def test_increase_stock_of_ingredients_success():
    mock_db = MagicMock()

    # Mock Pizza Type
    mock_pt = MagicMock()
    mock_pt.dough_id = 1
    mock_pt.sauce_id = 2

    mock_topping_assoc = MagicMock()
    mock_topping_assoc.topping_id = 3
    mock_topping_assoc.quantity = 2
    mock_pt.toppings = [mock_topping_assoc]

    # Mock DB returns
    mock_dough = MagicMock()
    mock_dough.stock = 10
    mock_sauce = MagicMock()
    mock_sauce.stock = 5
    mock_topping = MagicMock()
    mock_topping.stock = 20

    def query_side_effect(model):
        query_mock = MagicMock()
        first_mock = query_mock.filter.return_value.with_for_update.return_value.first
        if "Dough" in str(model):
            first_mock.return_value = mock_dough
        elif "Sauce" in str(model):
            first_mock.return_value = mock_sauce
        elif "Topping" in str(model):
            first_mock.return_value = mock_topping
        return query_mock

    mock_db.query.side_effect = query_side_effect

    # Import the function inside the test or at top
    from app.api.v1.services.stock_service import increase_stock_of_ingredients

    # Execute
    increase_stock_of_ingredients(mock_pt, mock_db)

    # Assert Increases
    assert mock_dough.stock == 11
    assert mock_sauce.stock == 6
    assert mock_topping.stock == 22
    mock_db.commit.assert_called_once()
