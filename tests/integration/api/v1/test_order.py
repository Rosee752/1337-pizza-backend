import pytest

import app.api.v1.endpoints.order.crud as order_crud
import app.api.v1.endpoints.user.crud as user_crud
import app.api.v1.endpoints.order.address.crud as address_crud
import app.api.v1.endpoints.pizza_type.crud as pizza_type_crud
import app.api.v1.endpoints.beverage.crud as beverage_crud
import app.api.v1.endpoints.dough.crud as dough_crud
from app.api.v1.endpoints.order.stock_logic import stock_beverage_crud
from app.api.v1.endpoints.order.address.schemas import AddressCreateSchema
from app.api.v1.endpoints.order.schemas import OrderCreateSchema
from app.api.v1.endpoints.user.schemas import UserCreateSchema
from app.api.v1.endpoints.pizza_type.schemas import PizzaTypeCreateSchema
from app.api.v1.endpoints.order.schemas import OrderBeverageQuantityCreateSchema
from app.api.v1.endpoints.beverage.schemas import BeverageCreateSchema
from app.api.v1.endpoints.dough.schemas import DoughCreateSchema
from app.database.models import Order
from app.database.models import PizzaType
from app.database.models import Dough
from app.database.connection import SessionLocal



@pytest.fixture(scope='module')
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_order_create_read_delete(db):
    # User anlegen (Pflichtfeld user_id wird benötigt)
    user = UserCreateSchema(username='testuser')
    db_user = user_crud.create_user(user, db)
    user_id = db_user.id

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
    # Zusätzlich: User wieder löschen, um Datenbank aufzuräumen
    user_crud.delete_user_by_id(user_id, db)

def test_order_address(db):

        #arrange
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

        #act
        db_address = address_crud.create_address(created_address, db)
        created_address_id = db_address.id

        #assert
        number_of_addresses_after = address_crud.get_all_addresses(db)
        assert len(number_of_addresses_before) + 1 == len(number_of_addresses_after)

        #act
        read_address = address_crud.get_address_by_id(created_address_id, db)

        #assert
        assert read_address.street == street
        assert read_address.post_code == post_code
        assert read_address.house_number == house_number
        assert read_address.first_name == first_name
        assert read_address.last_name == last_name

        #act
        address_crud.delete_address_by_id(created_address_id, db)
        number_of_addresses_after = address_crud.get_all_addresses(db)

        #assert
        assert len(number_of_addresses_before) == len(number_of_addresses_after)

def test_order_pizza(db):

    #arrange
    street = 'test street'
    post_code = 'test postcode'
    house_number = 112
    country = 'test country'
    town = 'test town'
    first_name = 'test first name'
    last_name = 'test last name'

    user = UserCreateSchema(username='test user')
    db_user = user_crud.create_user(user, db)
    user_id = db_user.id

    address = AddressCreateSchema(
        street= street,
        post_code=post_code,
        house_number=house_number,
        country=country,
        town=town,
        first_name=first_name,
        last_name=last_name
    )

    created_order = OrderCreateSchema(
        address=address,
        user_id=user_id
    )

    order: Order = order_crud.create_order(created_order, db)

    dough = DoughCreateSchema(
        name='test dough',
        description='test dough disc.',
        price=1,
        stock=25
    )

    created_dough:Dough = dough_crud.create_dough(dough, db)


    pizza = PizzaTypeCreateSchema(
        name='test pizza type',
        description='test pizza type disc.',
        price=2,
        dough_id=created_dough.id
    )

    created_pizza_type:PizzaType = pizza_type_crud.create_pizza_type(pizza, db)


    number_of_pizzas_before = len(order_crud.get_all_pizzas_of_order(order, db))

    #act
    added_pizza = order_crud.add_pizza_to_order(order,created_pizza_type, db)
    order_pizzas = order_crud.get_all_pizzas_of_order(order,db)

    #assert
    assert len(order_pizzas) == number_of_pizzas_before + 1
    assert added_pizza.id == order_pizzas[0].id

    #act
    order_crud.delete_pizza_from_order(order=order,pizza_id=added_pizza.id,db=db)
    deleted_pizza = order_crud.get_pizza_by_id(added_pizza.id, db)

    #assert
    assert deleted_pizza is None

    order_crud.delete_order_by_id(order_id=order.id, db=db)
    pizza_type_crud.delete_pizza_type_by_id(pizza_type_id=created_pizza_type.id, db=db)
    dough_crud.delete_dough_by_id(dough_id=created_dough.id, db=db)

def test_order_beverage(db):
    # arrange
    street = 'test street'
    post_code = 'test postcode'
    house_number = 112
    country = 'test country'
    town = 'test town'
    first_name = 'test first name'
    last_name = 'test last name'

    user = UserCreateSchema(username='test user')
    db_user = user_crud.create_user(user, db)
    user_id = db_user.id

    address = AddressCreateSchema(
        street=street,
        post_code=post_code,
        house_number=house_number,
        country=country,
        town=town,
        first_name=first_name,
        last_name=last_name
    )

    created_order = OrderCreateSchema(
        address=address,
        user_id=user_id
    )

    order:Order = order_crud.create_order(created_order, db)



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

    #act
    added_beverage_quantity = order_crud.create_beverage_quantity(
                                        order,beverage_quantity, db)
    read_beverage_quantity = order_crud.get_beverage_quantity_by_id(
                            order.id,created_beverage_id, db)

    #assert
    assert read_beverage_quantity.quantity == beverage_quantity.quantity

    #arrange
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

    #act
    added_beverage_quantity_2 = order_crud.create_beverage_quantity(
        order,beverage_quantity_2, db
    )
    joined_beverage_quantity = order_crud.get_joined_beverage_quantities_by_order(
        order.id,db
    )

    #assert
    assert len(joined_beverage_quantity) == added_beverage_quantity_2.quantity + added_beverage_quantity.quantity

    #act
    order_crud.delete_beverage_from_order(order.id,added_beverage_quantity.beverage_id,db)
    joined_beverage_quantity = order_crud.get_joined_beverage_quantities_by_order(order.id,db)

    #assert
    assert len(joined_beverage_quantity) == added_beverage_quantity_2.quantity

    order_crud.delete_beverage_from_order(order.id,added_beverage_quantity_2.beverage_id,db)
    order_crud.delete_order_by_id(order.id, db)
    beverage_crud.delete_beverage_by_id(created_beverage_id, db)
    beverage_crud.delete_beverage_by_id(created_beverage_id_2, db)

def test_stock_beverage(db):
    #arrange
    beverage = BeverageCreateSchema(
        name='test beverage',
        description='test beverage disc.',
        price=3,
        stock=15
    )

    #act
    created_beverage = beverage_crud.create_beverage(beverage, db)
    created_beverage_id = created_beverage.id
    beverage_available = stock_beverage_crud.beverage_is_available(created_beverage_id, db)

    #assert
    assert beverage_available

    #act
    stock_before_change = created_beverage.stock
    change_amount = -5
    stock_beverage_crud.change_stock_of_beverage(created_beverage_id,change_amount, db)


    #assert
    assert created_beverage.stock == stock_before_change + change_amount

    beverage_crud.delete_beverage_by_id(created_beverage_id, db)