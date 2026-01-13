import uuid
import pytest

from app.database.connection import SessionLocal
import app.api.v1.endpoints.dough.crud as dough_crud
from app.api.v1.endpoints.dough.schemas import DoughCreateSchema
import app.api.v1.endpoints.topping.crud as topping_crud
from app.api.v1.endpoints.topping.schemas import ToppingCreateSchema
import app.api.v1.endpoints.pizza_type.crud as pizza_type_crud
from app.api.v1.endpoints.pizza_type.schemas import PizzaTypeCreateSchema, PizzaTypeToppingQuantityCreateSchema
from app.api.v1.endpoints.order.stock_logic.stock_ingredients_crud import (
    ingredients_are_available,
    reduce_stock_of_ingredients,
    increase_stock_of_ingredients,
)


@pytest.fixture(scope='module')
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_dough(db):
    """Create a test dough and clean it up after"""
    dough = DoughCreateSchema(
        name=f'Test Dough {uuid.uuid4()}',
        price=1.50,
        description='Test dough',
        stock=10,
    )
    db_dough = dough_crud.create_dough(dough, db)
    yield db_dough
    # Cleanup
    dough_crud.delete_dough_by_id(db_dough.id, db)


@pytest.fixture
def sample_topping(db):
    """Create a test topping and clean it up after"""
    topping = ToppingCreateSchema(
        name=f'Test Topping {uuid.uuid4()}',
        price=0.50,
        description='Test topping',
        stock=20,
    )
    db_topping = topping_crud.create_topping(topping, db)
    yield db_topping
    # Cleanup
    topping_crud.delete_topping_by_id(db_topping.id, db)


@pytest.fixture
def sample_pizza_type(db, sample_dough, sample_topping):
    """Create a test pizza type with dough and topping and clean it up after"""
    pizza_type = PizzaTypeCreateSchema(
        name=f'Test Pizza {uuid.uuid4()}',
        price=8.00,
        description='Test pizza',
        dough_id=sample_dough.id,
        toppings=[
            PizzaTypeToppingQuantityCreateSchema(
                topping_id=sample_topping.id,
                quantity=2
            )
        ]
    )
    db_pizza_type = pizza_type_crud.create_pizza_type(pizza_type, db)
    yield db_pizza_type
    # Cleanup
    pizza_type_crud.delete_pizza_type_by_id(db_pizza_type.id, db)


def test_ingredients_are_available_with_sufficient_stock(db, sample_pizza_type):
    # arrange
    db.refresh(sample_pizza_type)
    db.refresh(sample_pizza_type.dough)
    for topping_qty in sample_pizza_type.toppings:
        db.refresh(topping_qty.topping)

    # act
    result = ingredients_are_available(sample_pizza_type)

    # assert
    assert result is True


def test_ingredients_are_available_with_exact_stock(db, sample_pizza_type):
    # arrange
    sample_pizza_type.dough.stock = 1
    for topping_qty in sample_pizza_type.toppings:
        topping_qty.topping.stock = topping_qty.quantity
    db.commit()
    db.refresh(sample_pizza_type)
    db.refresh(sample_pizza_type.dough)
    for topping_qty in sample_pizza_type.toppings:
        db.refresh(topping_qty.topping)

    # act
    result = ingredients_are_available(sample_pizza_type)

    # assert
    assert result is True


def test_ingredients_are_available_when_dough_stock_is_zero(db, sample_pizza_type):
    # arrange
    sample_pizza_type.dough.stock = 0
    db.commit()
    db.refresh(sample_pizza_type)
    db.refresh(sample_pizza_type.dough)

    # act
    result = ingredients_are_available(sample_pizza_type)

    # assert
    assert result is False


def test_reduce_stock_of_ingredients_success(db, sample_pizza_type):
    # arrange
    db.refresh(sample_pizza_type)
    db.refresh(sample_pizza_type.dough)
    for topping_qty in sample_pizza_type.toppings:
        db.refresh(topping_qty.topping)
    
    initial_dough_stock = sample_pizza_type.dough.stock
    initial_topping_stocks = {tq.topping.id: tq.topping.stock for tq in sample_pizza_type.toppings}

    # act
    reduce_stock_of_ingredients(sample_pizza_type, db)

    # assert
    db.refresh(sample_pizza_type.dough)
    assert sample_pizza_type.dough.stock == initial_dough_stock - 1
    
    for topping_qty in sample_pizza_type.toppings:
        db.refresh(topping_qty.topping)
        assert topping_qty.topping.stock == initial_topping_stocks[topping_qty.topping.id] - topping_qty.quantity


def test_increase_stock_of_ingredients_success(db, sample_pizza_type):
    # arrange
    db.refresh(sample_pizza_type)
    db.refresh(sample_pizza_type.dough)
    for topping_qty in sample_pizza_type.toppings:
        db.refresh(topping_qty.topping)
    
    initial_dough_stock = sample_pizza_type.dough.stock
    initial_topping_stocks = {tq.topping.id: tq.topping.stock for tq in sample_pizza_type.toppings}

    # act
    increase_stock_of_ingredients(sample_pizza_type, db)

    # assert
    db.refresh(sample_pizza_type.dough)
    assert sample_pizza_type.dough.stock == initial_dough_stock + 1
    
    for topping_qty in sample_pizza_type.toppings:
        db.refresh(topping_qty.topping)
        assert topping_qty.topping.stock == initial_topping_stocks[topping_qty.topping.id] + topping_qty.quantity

