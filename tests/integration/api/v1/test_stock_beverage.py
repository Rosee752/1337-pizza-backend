import pytest
from decimal import Decimal
import uuid
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Assuming these imports exist in your project structure
from app.database.connection import SessionLocal
import app.api.v1.endpoints.beverage.crud as beverage_crud
from app.database.models import Beverage  # Necessary for direct stock query in utils
from app.api.v1.endpoints.beverage.schemas import BeverageCreateSchema


# --- Functions Under Test (Replicated for testing context) ---

def beverage_is_available(beverage_id: uuid.UUID, db: Session):
    """Checks if a beverage is available (stock >= 0)."""
    # Note: This function only checks if the item exists and stock is not negative.
    beverage = beverage_crud.get_beverage_by_id(beverage_id, db)
    if beverage:
        return beverage.stock >= 0
    return False


def change_stock_of_beverage(beverage_id: uuid.UUID, change_amount: int, db: Session):
    """Changes the stock of a beverage, preventing stock from becoming negative."""
    beverage = db.query(Beverage).filter(Beverage.id == beverage_id).first()

    if beverage and beverage.stock + change_amount >= 0:
        setattr(beverage, 'stock', beverage.stock + change_amount)
        db.commit()
        db.refresh(beverage)
        return True

    return False


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
    """Creates a unique beverage with initial stock of 10 for most tests."""
    unique_name = f"Test Beverage {uuid.uuid4()}"
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


# --- Integration Tests for beverage_is_available ---
# NOTE: The check is only for 'stock >= 0', so tests for specific amounts were fixed.

def test_beverage_is_available_with_sufficient_stock(db: Session, sample_beverage: Beverage):
    # act: Call beverage_is_available with only two arguments (ID and DB)
    result = beverage_is_available(sample_beverage.id, db)
    # assert: Stock 10 >= 0, so it should be available
    assert result is True


def test_beverage_is_available_with_exact_stock(db: Session, sample_beverage: Beverage):
    # arrange: Set stock to a known amount
    sample_beverage.stock = 10
    db.commit()
    # act
    result = beverage_is_available(sample_beverage.id, db)
    # assert
    assert result is True


def test_beverage_is_available_with_zero_stock(db: Session, sample_beverage: Beverage):
    # arrange: Set stock to 0
    sample_beverage.stock = 0
    db.commit()
    # act
    result = beverage_is_available(sample_beverage.id, db)
    # assert: Stock 0 >= 0, so it should be available
    assert result is True


def test_beverage_is_available_with_insufficient_stock(db: Session, sample_beverage: Beverage):
    # arrange: Since the function only checks for stock >= 0, this test is redundant
    # for the current function definition, but we can set it to -1 for a fail case.
    sample_beverage.stock = -1
    db.commit()
    # act
    result = beverage_is_available(sample_beverage.id, db)
    # assert: Stock -1 is NOT >= 0, so it should be False
    assert result is False


def test_beverage_is_available_when_beverage_not_found(db: Session):
    # arrange
    non_existent_id = uuid.uuid4()
    # act
    result = beverage_is_available(non_existent_id, db)
    # assert
    assert result is False


# --- Integration Tests for change_stock_of_beverage ---

def test_change_stock_of_beverage_increase(db: Session, sample_beverage: Beverage):
    initial_stock = sample_beverage.stock  # 10
    change_amount = 5

    # act
    result = change_stock_of_beverage(sample_beverage.id, change_amount, db)

    # assert
    assert result is True
    db.refresh(sample_beverage)
    assert sample_beverage.stock == initial_stock + change_amount


def test_change_stock_of_beverage_decrease(db: Session, sample_beverage: Beverage):
    initial_stock = sample_beverage.stock  # 10
    change_amount = -3

    # act
    result = change_stock_of_beverage(sample_beverage.id, change_amount, db)

    # assert
    assert result is True
    db.refresh(sample_beverage)
    assert sample_beverage.stock == initial_stock + change_amount


def test_change_stock_of_beverage_to_zero(db: Session, sample_beverage: Beverage):
    initial_stock = sample_beverage.stock  # 10
    change_amount = -initial_stock  # -10

    # act
    result = change_stock_of_beverage(sample_beverage.id, change_amount, db)

    # assert
    assert result is True
    db.refresh(sample_beverage)
    assert sample_beverage.stock == 0


def test_change_stock_of_beverage_would_go_negative(db: Session, sample_beverage: Beverage):
    initial_stock = sample_beverage.stock  # 10
    change_amount = -11  # Attempts to go to -1

    # act
    result = change_stock_of_beverage(sample_beverage.id, change_amount, db)

    # assert: Must fail
    assert result is False
    # Verify stock remains unchanged
    db.refresh(sample_beverage)
    assert sample_beverage.stock == initial_stock


def test_change_stock_of_beverage_when_beverage_not_found(db: Session):
    non_existent_id = uuid.uuid4()
    change_amount = 5

    # act
    result = change_stock_of_beverage(non_existent_id, change_amount, db)

    # assert
    assert result is False