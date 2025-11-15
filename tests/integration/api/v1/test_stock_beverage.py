import pytest
from decimal import Decimal
import uuid
from sqlalchemy.orm import Session

# --- Assuming these imports exist in your project structure ---
from app.database.connection import SessionLocal
import app.api.v1.endpoints.beverage.crud as beverage_crud
from app.api.v1.endpoints.beverage.schemas import BeverageCreateSchema
from app.database.models import Beverage  # Necessary for direct stock query in utils

# --- THIS IS THE CRITICAL IMPORT ---
# Import the functions from their correct file location
from app.api.v1.endpoints.order.stock_logic.stock_beverage_crud import (
    beverage_is_available,
    change_stock_of_beverage
)


# --- Pytest Fixtures ---

@pytest.fixture(scope='module')
def db():
    """Provides a database session for the tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_beverage(db: Session):
    """
    Creates a unique beverage with initial stock of 10 for each test.
    This fixture ensures each test runs in isolation.
    """
    unique_name = f'Test Beverage {uuid.uuid4()}'
    initial_stock = 10

    beverage_data = BeverageCreateSchema(
        name=unique_name,
        price=Decimal('2.50'),
        description='Test description',
        stock=initial_stock
    )

    db_beverage = beverage_crud.create_beverage(beverage_data, db)

    yield db_beverage

    # Cleanup: Delete the beverage after the test is complete
    beverage_crud.delete_beverage_by_id(db_beverage.id, db)


# --- Tests for beverage_is_available ---

def test_beverage_is_available_with_sufficient_stock(db: Session, sample_beverage: Beverage):
    """Covers: if beverage: True, return beverage.stock >= 0: True"""
    # arrange: sample_beverage.stock is 10
    # act
    result = beverage_is_available(sample_beverage.id, db)
    # assert
    assert result is True


def test_beverage_is_available_with_zero_stock(db: Session, sample_beverage: Beverage):
    """Covers: if beverage: True, return beverage.stock >= 0: True"""
    # arrange: Set stock to 0
    sample_beverage.stock = 0
    db.commit()
    # act
    result = beverage_is_available(sample_beverage.id, db)
    # assert: Stock 0 >= 0 is True
    assert result is True


def test_beverage_is_available_with_negative_stock(db: Session, sample_beverage: Beverage):
    """Covers: if beverage: True, return beverage.stock >= 0: False"""
    # arrange: Set stock to -1
    sample_beverage.stock = -1
    db.commit()
    # act
    result = beverage_is_available(sample_beverage.id, db)
    # assert: Stock -1 >= 0 is False
    assert result is False


def test_beverage_is_available_when_beverage_not_found(db: Session):
    """Covers: if beverage: False"""
    # arrange
    non_existent_id = uuid.uuid4()
    # act
    result = beverage_is_available(non_existent_id, db)
    # assert
    assert result is False


# --- Tests for change_stock_of_beverage ---

def test_change_stock_of_beverage_increase(db: Session, sample_beverage: Beverage):
    """CoV1ERS: if beverage: True, and beverage.stock + change_amount >= 0: True"""
    initial_stock = sample_beverage.stock  # 10
    change_amount = 5

    # act
    result = change_stock_of_beverage(sample_beverage.id, change_amount, db)

    # assert
    assert result is True
    db.refresh(sample_beverage)
    assert sample_beverage.stock == initial_stock + change_amount  # 15


def test_change_stock_of_beverage_decrease(db: Session, sample_beverage: Beverage):
    """Covers: if beverage: True, and beverage.stock + change_amount >= 0: True"""
    initial_stock = sample_beverage.stock  # 10
    change_amount = -3

    # act
    result = change_stock_of_beverage(sample_beverage.id, change_amount, db)

    # assert
    assert result is True
    db.refresh(sample_beverage)
    assert sample_beverage.stock == initial_stock + change_amount  # 7


def test_change_stock_of_beverage_to_zero(db: Session, sample_beverage: Beverage):
    """Covers: if beverage: True, and beverage.stock + change_amount >= 0: True"""
    initial_stock = sample_beverage.stock  # 10
    change_amount = -initial_stock  # -10

    # act
    result = change_stock_of_beverage(sample_beverage.id, change_amount, db)

    # assert
    assert result is True
    db.refresh(sample_beverage)
    assert sample_beverage.stock == 0


def test_change_stock_of_beverage_would_go_negative(db: Session, sample_beverage: Beverage):
    """Covers: if beverage: True, and beverage.stock + change_amount >= 0: False"""
    initial_stock = sample_beverage.stock  # 10
    change_amount = -11  # Attempts to go to -1

    # act
    result = change_stock_of_beverage(sample_beverage.id, change_amount, db)

    # assert: Must fail
    assert result is False
    # Verify stock remains unchanged
    db.refresh(sample_beverage)
    assert sample_beverage.stock == initial_stock  # 10


def test_change_stock_of_beverage_when_beverage_not_found(db: Session):
    """Covers: if beverage: False"""
    non_existent_id = uuid.uuid4()
    change_amount = 5

    # act
    result = change_stock_of_beverage(non_existent_id, change_amount, db)

    # assert
    assert result is False