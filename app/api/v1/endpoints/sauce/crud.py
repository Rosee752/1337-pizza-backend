import pytest
from app.api.v1.endpoints.sauce import crud
from app.schemas.sauce import SauceCreateSchema  # Adjust import path as needed


# --- Tests for check_sauce_availability ---

def test_check_sauce_availability_success(db):
    """Test that availability returns True when stock is positive."""
    # 1. Create a sauce with stock
    sauce_in = SauceCreateSchema(name="Spicy Marinara", stock=10)
    created_sauce = crud.create_sauce(db=db, schema=sauce_in)

    # 2. Check availability
    is_available = crud.check_sauce_availability(db=db, sauce_id=created_sauce.id)

    assert is_available is True


def test_check_sauce_availability_no_stock(db):
    """Test that availability returns False when stock is 0."""
    sauce_in = SauceCreateSchema(name="Empty Marinara", stock=0)
    created_sauce = crud.create_sauce(db=db, schema=sauce_in)

    is_available = crud.check_sauce_availability(db=db, sauce_id=created_sauce.id)

    assert is_available is False


def test_check_sauce_availability_not_found(db):
    """Test that availability returns False for non-existent ID."""
    import uuid
    random_id = uuid.uuid4()

    is_available = crud.check_sauce_availability(db=db, sauce_id=random_id)

    assert is_available is False


# --- Tests for change_stock_of_sauce ---

def test_change_stock_add_amount(db):
    """Test adding stock to an existing sauce."""
    sauce_in = SauceCreateSchema(name="Stock Sauce", stock=10)
    created_sauce = crud.create_sauce(db=db, schema=sauce_in)

    # Add 5 to stock
    result = crud.change_stock_of_sauce(db=db, sauce_id=created_sauce.id, amount=5)

    # Refresh to check DB
    db.refresh(created_sauce)

    assert result is True
    assert created_sauce.stock == 15


def test_change_stock_reduce_valid(db):
    """Test reducing stock (valid amount)."""
    sauce_in = SauceCreateSchema(name="Reduce Sauce", stock=10)
    created_sauce = crud.create_sauce(db=db, schema=sauce_in)

    # Remove 3
    result = crud.change_stock_of_sauce(db=db, sauce_id=created_sauce.id, amount=-3)

    db.refresh(created_sauce)

    assert result is True
    assert created_sauce.stock == 7


def test_change_stock_reduce_invalid(db):
    """Test that stock cannot go below zero."""
    sauce_in = SauceCreateSchema(name="Low Stock Sauce", stock=5)
    created_sauce = crud.create_sauce(db=db, schema=sauce_in)

    # Try to remove 10 (should fail because 5 - 10 < 0)
    result = crud.change_stock_of_sauce(db=db, sauce_id=created_sauce.id, amount=-10)

    db.refresh(created_sauce)

    assert result is False
    assert created_sauce.stock == 5  # Stock should remain unchanged


def test_change_stock_not_found(db):
    """Test changing stock for a non-existent sauce."""
    import uuid
    random_id = uuid.uuid4()

    result = crud.change_stock_of_sauce(db=db, sauce_id=random_id, amount=5)

    assert result is False