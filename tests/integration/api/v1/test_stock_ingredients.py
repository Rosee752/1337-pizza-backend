import uuid

import pytest

import app.api.v1.endpoints.dough.crud as dough_crud
import app.api.v1.endpoints.pizza_type.crud as pizza_type_crud
import app.api.v1.endpoints.sauce.crud as sauce_crud
import app.api.v1.endpoints.topping.crud as topping_crud
from app.api.v1.endpoints.dough.schemas import DoughCreateSchema
from app.api.v1.endpoints.pizza_type.schemas import (
    PizzaTypeCreateSchema,
    PizzaTypeToppingQuantityCreateSchema,
)
from app.api.v1.endpoints.sauce.schemas import SauceCreateSchema
from app.api.v1.endpoints.topping.schemas import ToppingCreateSchema
from app.database.connection import SessionLocal
from app.database.models import SpicinessType


@pytest.fixture(scope='module')
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_dough(db):
    dough = DoughCreateSchema(
        name=f'Test Dough {uuid.uuid4()}',
        price=1.50,
        description='Test dough',
        stock=10
    )
    db_dough = dough_crud.create_dough(dough, db)
    yield db_dough
    dough_crud.delete_dough_by_id(db_dough.id, db)


@pytest.fixture
def sample_topping(db):
    topping = ToppingCreateSchema(
        name=f'Test Topping {uuid.uuid4()}',
        price=0.50,
        description='Test topping',
        stock=20
    )
    db_topping = topping_crud.create_topping(topping, db)
    yield db_topping
    topping_crud.delete_topping_by_id(db_topping.id, db)


@pytest.fixture
def sample_sauce(db):
    sauce = SauceCreateSchema(
        name=f'Test Sauce {uuid.uuid4()}',
        price=0.50,
        description='Stock test sauce',
        stock=20,
        spiciness=SpicinessType.LIGHT
    )
    db_sauce = sauce_crud.create_sauce(sauce, db)
    yield db_sauce
    sauce_crud.delete_sauce_by_id(db_sauce.id, db)


@pytest.fixture
def sample_pizza_type(db, sample_dough, sample_topping, sample_sauce):
    """Create a test pizza type with dough, sauce and topping and clean it up after"""
    # First create the pizza type without toppings
    pizza_type_schema = PizzaTypeCreateSchema(
        name=f'Test Pizza {uuid.uuid4()}',
        price=8.00,
        description='Test pizza',
        dough_id=sample_dough.id,
        sauce_id=sample_sauce.id
    )
    
    db_pizza_type = pizza_type_crud.create_pizza_type(pizza_type_schema, db)
    
    # Then add the topping
    topping_quantity = PizzaTypeToppingQuantityCreateSchema(
        topping_id=sample_topping.id,
        quantity=2
    )
    pizza_type_crud.add_topping_to_pizza_type(db_pizza_type.id, topping_quantity, db)

    yield db_pizza_type
    pizza_type_crud.delete_pizza_type_by_id(db_pizza_type.id, db)


def test_ingredients_are_available_with_sufficient_stock(db, sample_pizza_type):
    """Test verification of stock availability"""
    # Act
    is_available = pizza_type_crud.are_ingredients_available(sample_pizza_type.id, 1, db)

    # Assert
    assert is_available is True


def test_ingredients_not_available_insufficient_stock(db, sample_pizza_type):
    """Test verification fails when stock is insufficient"""
    is_available = pizza_type_crud.are_ingredients_available(sample_pizza_type.id, 11, db)

    # Assert
    assert is_available is False