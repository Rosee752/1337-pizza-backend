import pytest
import uuid
from typing import List
from sqlalchemy.orm import Session

import app.api.v1.endpoints.order.crud as order_crud
import app.api.v1.endpoints.user.crud as user_crud
import app.api.v1.endpoints.order.address.crud as address_crud
import app.api.v1.endpoints.pizza_type.crud as pizza_type_crud
import app.api.v1.endpoints.beverage.crud as beverage_crud
import app.api.v1.endpoints.dough.crud as dough_crud
from app.api.v1.endpoints.order.address.schemas import AddressCreateSchema
from app.api.v1.endpoints.order.schemas import OrderCreateSchema
from app.api.v1.endpoints.user.schemas import UserCreateSchema
from app.api.v1.endpoints.pizza_type.schemas import PizzaTypeCreateSchema
from app.api.v1.endpoints.order.schemas import OrderBeverageQuantityCreateSchema
from app.api.v1.endpoints.beverage.schemas import BeverageCreateSchema
from app.api.v1.endpoints.dough.schemas import DoughCreateSchema
from app.database.models import Order, User, Dough, PizzaType
from app.database.connection import SessionLocal
from app.api.v1.endpoints.order.schemas import OrderStatus


# --- Fixtures ---

@pytest.fixture(scope='module')
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_user(db: Session):
    """Creates and deletes a test user."""
    user = UserCreateSchema(username=f'testuser_{uuid.uuid4()}')
    db_user = user_crud.create_user(user, db)
    yield db_user
    # Cleanup: Delete the user
    user_crud.delete_user_by_id(db_user.id, db)


@pytest.fixture
def sample_order(db: Session, sample_user: User):
    """
    Creates a user, an address, and an order.
    This replaces the duplicated setup code.
    """
    # 1. Create the address schema
    address = AddressCreateSchema(
        street='test street',
        post_code='test postcode',
        house_number=112,
        country='test country',
        town='test town',
        first_name='test first name',
        last_name='test last name'
    )

    # 2. Create the order schema
    created_order = OrderCreateSchema(
        address=address,
        user_id=sample_user.id
    )

    # 3. Create the order in the DB
    db_order = order_crud.create_order(created_order, db)
    yield db_order

    # 4. Cleanup: Delete the order
    # The associated address is deleted automatically via cascade
    # The user is deleted by the sample_user fixture
    order_crud.delete_order_by_id(db_order.id, db)

@pytest.fixture
def order_factory(db: Session, sample_user: User):
    # Liste, um die erstellten Orders zu tracken (für das Cleanup)
    created_orders = []

    def _create_orders(count: int = 3) -> List[Order]:
        new_orders = []
        for i in range(count):
            address = AddressCreateSchema(
                street=f'test street {i}',
                post_code=f'1234{i}',
                house_number=10 + i,
                country='test country',
                town='test town',
                first_name=f'test name {i}',
                last_name='test last name'
            )

            created_order_schema = OrderCreateSchema(
                address=address,
                user_id=sample_user.id
            )

            db_order = order_crud.create_order(created_order_schema, db)
            new_orders.append(db_order)
            created_orders.append(db_order)

        return new_orders

    yield _create_orders

    for order in created_orders:
        try:
            order_crud.delete_order_by_id(order.id, db)
        except Exception:
            pass


# --- Tests ---

def test_order_create_read_delete(db: Session, sample_user: User):
    # Use the sample_user fixture
    user_id = sample_user.id

    # Address anlegen (must use exact field names as per schema)
    address = AddressCreateSchema(
        street='test street',
        post_code='test postcode',
        house_number=112,
        country='test country',
        town='test town',
        first_name='test first name',
        last_name='test last name'
    )

    number_of_orders_before = len(order_crud.get_all_orders(db))

    # Order anlegen (mit user_id und Adresse)
    created_order = OrderCreateSchema(
        address=address,
        user_id=user_id
    )

    # Order in DB speichern
    db_order = order_crud.create_order(created_order, db)
    created_order_id = db_order.id

    # Prüfen: Anzahl der Bestellungen erhöht sich um 1
    orders = order_crud.get_all_orders(db)
    assert len(orders) == number_of_orders_before + 1

    # Order aus DB abfragen und prüfen
    read_order = order_crud.get_order_by_id(created_order_id, db)
    assert read_order.id == created_order_id
    assert read_order.address.street == address.street
    assert read_order.user_id == user_id

    # Order löschen
    order_crud.delete_order_by_id(created_order_id, db)

    # Anzahl der Bestellungen wieder prüfen
    orders = order_crud.get_all_orders(db)
    assert len(orders) == number_of_orders_before

    # Prüfen, dass Order gelöscht wurde
    deleted_order = order_crud.get_order_by_id(created_order_id, db)
    assert deleted_order is None
    # User cleanup is handled by the fixture


def test_order_address(db):
    # This test is for the address CRUD, so it should
    # create its own data and not use fixtures. It's fine as-is.

    # arrange
    street = 'test street'
    post_code = 'test postcode'
    house_number = 112
    country = 'test country'
    town = 'test town'
    first_name = 'test first name'
    last_name = 'test last name'

    number_of_addresses_before = address_crud.get_all_addresses(db)

    created_address = AddressCreateSchema(
        street=street,
        post_code=post_code,
        house_number=house_number,
        country=country,
        town=town,
        first_name=first_name,
        last_name=last_name
    )

    # act
    db_address = address_crud.create_address(created_address, db)
    created_address_id = db_address.id

    # assert
    number_of_addresses_after = address_crud.get_all_addresses(db)
    assert len(number_of_addresses_before) + 1 == len(number_of_addresses_after)

    # act
    read_address = address_crud.get_address_by_id(created_address_id, db)

    # assert
    assert read_address.street == street
    assert read_address.post_code == post_code
    assert read_address.house_number == house_number
    assert read_address.first_name == first_name
    assert read_address.last_name == last_name

    # act
    address_crud.delete_address_by_id(created_address_id, db)
    number_of_addresses_after = address_crud.get_all_addresses(db)

    # assert
    assert len(number_of_addresses_before) == len(number_of_addresses_after)


def test_order_pizza(db: Session, sample_order: Order):
    """This test now uses the sample_order fixture, removing duplication."""

    # arrange
    # The 'sample_order' fixture has already created the user, address, and order.
    # We just need to create the pizza-specific items.
    dough = DoughCreateSchema(
        name='test dough',
        description='test dough disc.',
        price=1,
        stock=25
    )
    created_dough: Dough = dough_crud.create_dough(dough, db)

    pizza = PizzaTypeCreateSchema(
        name='test pizza type',
        description='test pizza type disc.',
        price=2,
        dough_id=created_dough.id
    )
    created_pizza_type: PizzaType = pizza_type_crud.create_pizza_type(pizza, db)

    number_of_pizzas_before = len(order_crud.get_all_pizzas_of_order(sample_order, db))

    # act
    added_pizza = order_crud.add_pizza_to_order(sample_order, created_pizza_type, db)
    order_pizzas = order_crud.get_all_pizzas_of_order(sample_order, db)

    # assert
    assert len(order_pizzas) == number_of_pizzas_before + 1
    assert added_pizza.id == order_pizzas[0].id

    # act
    order_crud.delete_pizza_from_order(order=sample_order, pizza_id=added_pizza.id, db=db)
    deleted_pizza = order_crud.get_pizza_by_id(added_pizza.id, db)

    # assert
    assert deleted_pizza is None

    # Cleanup: Order and user are deleted by fixtures.
    # We only need to delete the items created *in this test*.
    pizza_type_crud.delete_pizza_type_by_id(pizza_type_id=created_pizza_type.id, db=db)
    dough_crud.delete_dough_by_id(dough_id=created_dough.id, db=db)


def test_order_beverage(db: Session, sample_order: Order):
    """This test also uses the sample_order fixture, removing duplication."""

    # arrange
    # The 'sample_order' fixture has already created the user, address, and order.
    # We just need to create the beverage-specific items.
    beverage = BeverageCreateSchema(
        name='test beverage',
        description='test beverage disc.',
        price=3,
        stock=15
    )
    created_beverage = beverage_crud.create_beverage(beverage, db)
    created_beverage_id = created_beverage.id

    beverage_quantity = OrderBeverageQuantityCreateSchema(
        quantity=1,
        beverage_id=created_beverage_id
    )

    # act
    added_beverage_quantity = order_crud.create_beverage_quantity(
        sample_order, beverage_quantity, db)
    read_beverage_quantity = order_crud.get_beverage_quantity_by_id(
        sample_order.id, created_beverage_id, db)

    # assert
    assert read_beverage_quantity.quantity == beverage_quantity.quantity

    # arrange
    beverage = BeverageCreateSchema(
        name='test beverage 2',
        description='test beverage disc. 2',
        price=3,
        stock=15
    )
    created_beverage_2 = beverage_crud.create_beverage(beverage, db)
    created_beverage_id_2 = created_beverage_2.id

    beverage_quantity_2 = OrderBeverageQuantityCreateSchema(
        quantity=1,
        beverage_id=created_beverage_id_2
    )

    # act
    added_beverage_quantity_2 = order_crud.create_beverage_quantity(
        sample_order, beverage_quantity_2, db
    )
    joined_beverage_quantity = order_crud.get_joined_beverage_quantities_by_order(
        sample_order.id, db
    )

    # assert
    assert len(joined_beverage_quantity) == added_beverage_quantity_2.quantity + added_beverage_quantity.quantity

    # act
    order_crud.delete_beverage_from_order(sample_order.id, added_beverage_quantity.beverage_id, db)
    joined_beverage_quantity = order_crud.get_joined_beverage_quantities_by_order(sample_order.id, db)

    # assert
    assert len(joined_beverage_quantity) == added_beverage_quantity_2.quantity

    # Cleanup: Order and user are deleted by fixtures.
    # We only need to delete the items created *in this test*.
    order_crud.delete_beverage_from_order(sample_order.id, added_beverage_quantity_2.beverage_id, db)
    beverage_crud.delete_beverage_by_id(created_beverage_id, db)
    beverage_crud.delete_beverage_by_id(created_beverage_id_2, db)

def test_filter_order_by_status(db: Session, order_factory):
    """This test also uses the sample_order fixture, removing duplication."""

    #arrange
    new_orders = order_factory(count=3)
    test_status1 = OrderStatus.OPEN
    test_status2 = OrderStatus.PREPARING

    #act
    filtered_orders = order_crud.get_order_by_status([test_status1], db)

    #assert
    for order in filtered_orders:
        assert order.order_status == test_status1

    #act
    order_crud.update_order_status(new_orders[0], test_status2, db)
    filtered_orders = order_crud.get_order_by_status([test_status1,test_status2], db)

    #assert
    for order in filtered_orders:
        assert order.order_status == test_status2 or test_status1

    #act
    order_crud.update_order_status(new_orders[2], OrderStatus.COMPLETED, db)
    filtered_orders = order_crud.get_order_by_status([test_status1,test_status2], db)

    # assert
    for order in filtered_orders:
        assert order.order_status == test_status2 or test_status1

def test_update_order_status_logic(db: Session, order_factory):
            """
            Testet explizit die update_order_status CRUD-Funktion.
            """
            # ARRANGE: Eine Order erstellen
            orders = order_factory(count=1)
            test_order = orders[0]
            original_status = test_order.order_status

            # Ziel-Status definieren (anders als der aktuelle)
            target_status = OrderStatus.IN_DELIVERY

            # ACT: Status ändern
            updated_order = order_crud.update_order_status(
                order=test_order,
                changed_order=target_status,
                db=db
            )

            # ASSERT:
            # 1. Prüfen, ob das Rückgabe-Objekt aktualisiert ist
            assert updated_order.order_status == target_status
            assert updated_order.id == test_order.id

            # 2. Prüfen, ob es wirklich in der DB persistiert wurde
            # Dazu laden wir das Objekt frisch aus der DB
            db.refresh(test_order)
            assert test_order.order_status == target_status
            assert test_order.order_status != original_status