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


# --- Functions Under Test (Copying the logic provided by the user) ---

def beverage_is_available(beverage_id: uuid.UUID, db: Session):
    """Checks if a beverage is available (stock >= 0)."""
    beverage = beverage_crud.get_beverage_by_id(beverage_id, db)
    if beverage:
        # Note: The requirement is for stock >= 0
        return beverage.stock >= 0
    return False


def change_stock_of_beverage(beverage_id: uuid.UUID, change_amount: int, db: Session):
    """Changes the stock of a beverage, preventing stock from becoming negative."""
    # Get Beverage using direct query as per provided logic
    beverage = db.query(Beverage).filter(Beverage.id == beverage_id).first()

    # Check if Beverage exists and if Stock is not getting smaller than zero
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
def setup_beverage(db: Session):
    """Creates a unique beverage for testing and ensures cleanup."""
    unique_name = f"Test Beverage {uuid.uuid4()}"
    initial_stock = 5

    beverage_data = BeverageCreateSchema(
        name=unique_name,
        price=Decimal('4.50'),
        description='Refreshing test drink',
        stock=initial_stock
    )

    db_beverage = beverage_crud.create_beverage(beverage_data, db)
    created_id = db_beverage.id

    # Yield the ID to the test function
    yield created_id, initial_stock

    # Cleanup: Delete the beverage after the test is complete
    beverage_crud.delete_beverage_by_id(created_id, db)


# --- Integration Test ---

def test_beverage_stock_management_and_availability(db: Session, setup_beverage):
    """
    Tests both beverage_is_available and change_stock_of_beverage functions
    across various scenarios (create, read, update, boundary conditions).
    """
    created_id, _ = setup_beverage
    non_existent_id = uuid.uuid4()

    # --- 1. Test initial availability (Stock: 5) ---
    assert beverage_is_available(created_id, db) is True
    assert beverage_is_available(non_existent_id, db) is False

    # --- 2. Test valid stock decrease (Stock: 5 -> 2) ---
    assert change_stock_of_beverage(created_id, -3, db) is True

    # Verify stock update in DB
    updated_beverage = beverage_crud.get_beverage_by_id(created_id, db)
    assert updated_beverage.stock == 2
    assert beverage_is_available(created_id, db) is True

    # --- 3. Test edge case: stock equals zero (Stock: 2 -> 0) ---
    assert change_stock_of_beverage(created_id, -2, db) is True
    updated_beverage = beverage_crud.get_beverage_by_id(created_id, db)
    assert updated_beverage.stock == 0
    # Availability check for stock >= 0
    assert beverage_is_available(created_id, db) is True

    # --- 4. Test invalid stock decrease (Stock: 0 -> should remain 0) ---
    # Attempt to go below zero, which should fail
    assert change_stock_of_beverage(created_id, -1, db) is False

    # Verify stock remains unchanged (still 0)
    updated_beverage = beverage_crud.get_beverage_by_id(created_id, db)
    assert updated_beverage.stock == 0
    assert beverage_is_available(created_id, db) is True

    # --- 5. Test valid stock increase (Stock: 0 -> 10) ---
    assert change_stock_of_beverage(created_id, 10, db) is True
    updated_beverage = beverage_crud.get_beverage_by_id(created_id, db)
    assert updated_beverage.stock == 10

    # --- 6. Test change_stock_of_beverage on non-existent ID ---
    assert change_stock_of_beverage(non_existent_id, 5, db) is False