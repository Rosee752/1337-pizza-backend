import pytest
from decimal import Decimal
import uuid
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.database.models import PizzaTypeToppingQuantity

import app.api.v1.endpoints.dough.crud as dough_crud
from app.api.v1.endpoints.dough.schemas import DoughCreateSchema
import app.api.v1.endpoints.topping.crud as topping_crud
from app.api.v1.endpoints.topping.schemas import ToppingCreateSchema
import app.api.v1.endpoints.pizza_type.crud as pizza_type_crud
from app.api.v1.endpoints.pizza_type.schemas import PizzaTypeCreateSchema
import app.api.v1.endpoints.sauce.crud as sauce_crud
from app.api.v1.endpoints.sauce.schemas import SauceCreateSchema
from app.database.models import SpicinessType

from app.api.v1.endpoints.order.stock_logic.stock_ingredients_crud import (
    ingredients_are_available,
    reduce_stock_of_ingredients,
    increase_stock_of_ingredients
)


@pytest.fixture(scope='module')
def db():
    """Provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def pizza_type_with_toppings(db: Session):
    """
    Creates a PizzaType with:
    - Dough: Stock = 10
    - Topping: Stock = 10
    - Topping Quantity needed: 2 (Important to test the loop)
    """
    unique_id = uuid.uuid4()

    dough = dough_crud.create_dough(DoughCreateSchema(
        name=f'IngTest Dough {unique_id}',
        price=Decimal('1.00'), description='desc', stock=10
    ), db)

    sauce = sauce_crud.create_sauce(SauceCreateSchema(
        name=f'IngTest Sauce {unique_id}',
        price=Decimal('1.00'), description='desc', stock=10,
        spiciness=SpicinessType.LIGHT
    ), db)

    topping = topping_crud.create_topping(ToppingCreateSchema(
        name=f'IngTest Topping {unique_id}',
        price=Decimal('0.50'), description='desc', stock=10
    ), db)

    pizza_type = pizza_type_crud.create_pizza_type(PizzaTypeCreateSchema(
        name=f'IngTest Pizza {unique_id}',
        price=Decimal('10.00'), description='desc',
        dough_id=dough.id,
        sauce_id=sauce.id
    ), db)

    link = PizzaTypeToppingQuantity(
        pizza_type_id=pizza_type.id,
        topping_id=topping.id,
        quantity=2
    )
    db.add(link)
    db.commit()
    db.refresh(pizza_type)

    yield pizza_type

    db.delete(link)
    db.commit()
    pizza_type_crud.delete_pizza_type_by_id(pizza_type.id, db)
    topping_crud.delete_topping_by_id(topping.id, db)
    dough_crud.delete_dough_by_id(dough.id, db)
    sauce_crud.delete_sauce_by_id(sauce.id, db)


def test_ingredients_available_success(db: Session, pizza_type_with_toppings):
    """
    Covers: return True
    Scenario: Dough=10, Topping=10, Needed=2. All good.
    """
    assert ingredients_are_available(pizza_type_with_toppings) is True


def test_ingredients_available_fail_no_dough(db: Session, pizza_type_with_toppings):
    """
    Covers: if pizza_type.dough.stock == 0: return False
    """
    pizza_type_with_toppings.dough.stock = 0
    db.commit()

    result = ingredients_are_available(pizza_type_with_toppings)

    assert result is False

    pizza_type_with_toppings.dough.stock = 10
    db.commit()


def test_ingredients_available_fail_not_enough_topping(db: Session, pizza_type_with_toppings):
    """
    Covers: if topping_quantity.topping.stock < topping_quantity.quantity: return False
    """
    pt_topping_qty = pizza_type_with_toppings.toppings[0]
    real_topping = pt_topping_qty.topping

    real_topping.stock = 1
    db.commit()

    result = ingredients_are_available(pizza_type_with_toppings)

    assert result is False

    real_topping.stock = 10
    db.commit()


def test_reduce_stock_success(db: Session, pizza_type_with_toppings):
    """
    Covers:
    - pizza_type.dough.stock -= 1
    - topping_quantity.topping.stock -= topping_quantity.quantity
    """
    initial_dough = pizza_type_with_toppings.dough.stock
    pt_topping_qty = pizza_type_with_toppings.toppings[0]
    initial_topping = pt_topping_qty.topping.stock
    qty_needed = pt_topping_qty.quantity

    reduce_stock_of_ingredients(pizza_type_with_toppings, db)

    db.refresh(pizza_type_with_toppings.dough)
    db.refresh(pt_topping_qty.topping)

    assert pizza_type_with_toppings.dough.stock == initial_dough - 1
    assert pt_topping_qty.topping.stock == initial_topping - qty_needed


def test_increase_stock_success(db: Session, pizza_type_with_toppings):
    """
    Covers:
    - pizza_type.dough.stock += 1
    - topping_quantity.topping.stock += topping_quantity.quantity
    """
    initial_dough = pizza_type_with_toppings.dough.stock
    pt_topping_qty = pizza_type_with_toppings.toppings[0]
    initial_topping = pt_topping_qty.topping.stock
    qty_restored = pt_topping_qty.quantity

    increase_stock_of_ingredients(pizza_type_with_toppings, db)

    db.refresh(pizza_type_with_toppings.dough)
    db.refresh(pt_topping_qty.topping)

    assert pizza_type_with_toppings.dough.stock == initial_dough + 1
    assert pt_topping_qty.topping.stock == initial_topping + qty_restored