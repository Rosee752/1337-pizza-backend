#import pytest
from decimal import Decimal
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

# --- Imports from your project ---
from app.database.connection import SessionLocal

# --- CRUD Imports ---
import app.api.v1.endpoints.dough.crud as dough_crud
from app.api.v1.endpoints.dough.schemas import DoughCreateSchema
import app.api.v1.endpoints.sauce.crud as sauce_crud
from app.api.v1.endpoints.sauce.schemas import SauceCreateSchema
import app.api.v1.endpoints.pizza_type.crud as pizza_type_crud
from app.api.v1.endpoints.pizza_type.schemas import PizzaTypeCreateSchema
from app.database.models import SpicinessType

# --- SERVICE IMPORTS (Testing the logic directly) ---
from app.api.v1.services.stock_service import (
    validate_and_reduce_ingredients,
    increase_stock_of_ingredients
)


# --- Fixtures ---

@pytest.fixture(scope='module')
def db():
    """Provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_pizza_type(db: Session):
    """
    Creates a PizzaType with Dough (Stock=10) and Sauce (Stock=10).
    """
    unique_id = uuid.uuid4()

    # 1. Create Dough
    dough = dough_crud.create_dough(DoughCreateSchema(
        name=f'StockTest Dough {unique_id}',
        price=Decimal('1.00'), description='desc', stock=10
    ), db)

    # 2. Create Sauce
    sauce = sauce_crud.create_sauce(SauceCreateSchema(
        name=f'StockTest Sauce {unique_id}',
        price=Decimal('1.00'), description='desc', stock=10,
        spiciness=SpicinessType.LIGHT
    ), db)

    # 3. Create PizzaType
    pizza_type = pizza_type_crud.create_pizza_type(PizzaTypeCreateSchema(
        name=f'StockTest Pizza {unique_id}',
        price=Decimal('10.00'), description='desc',
        dough_id=dough.id,
        sauce_id=sauce.id
    ), db)

    yield pizza_type

    # Cleanup
    pizza_type_crud.delete_pizza_type_by_id(pizza_type.id, db)
    sauce_crud.delete_sauce_by_id(sauce.id, db)
    dough_crud.delete_dough_by_id(dough.id, db)


# --- TESTS (Replacing the TestClient Logic) ---

def test_stock_reduction_success(db: Session, sample_pizza_type):
    """
    Equivalent to POST /pizzas
    Verifies that calling the service reduces stock by 1.
    """
    # Arrange
    initial_dough = sample_pizza_type.dough.stock # 10
    initial_sauce = sample_pizza_type.sauce.stock # 10

    # Act (Simulate Order Creation)
    validate_and_reduce_ingredients(sample_pizza_type, db)

    # Assert
    db.refresh(sample_pizza_type.dough)
    db.refresh(sample_pizza_type.sauce)

    assert sample_pizza_type.dough.stock == initial_dough - 1
    assert sample_pizza_type.sauce.stock == initial_sauce - 1


def test_stock_restoration_success(db: Session, sample_pizza_type):
    """
    Equivalent to DELETE /pizzas
    Verifies that calling the service increases stock by 1.
    """
    # Arrange
    initial_dough = sample_pizza_type.dough.stock # 10
    initial_sauce = sample_pizza_type.sauce.stock # 10

    # Act (Simulate Order Deletion)
    increase_stock_of_ingredients(sample_pizza_type, db)

    # Assert
    db.refresh(sample_pizza_type.dough)
    db.refresh(sample_pizza_type.sauce)

    assert sample_pizza_type.dough.stock == initial_dough + 1
    assert sample_pizza_type.sauce.stock == initial_sauce + 1


def test_stock_reduction_fails_if_no_sauce(db: Session, sample_pizza_type):
    """
    Verifies that we cannot order if Sauce is out of stock.
    """
    # Arrange: Set Sauce to 0
    sample_pizza_type.sauce.stock = 0
    db.commit()

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        validate_and_reduce_ingredients(sample_pizza_type, db)

    assert exc.value.status_code == 409
    assert "Sauce" in exc.value.detail