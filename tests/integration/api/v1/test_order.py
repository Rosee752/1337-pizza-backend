import uuid
import pytest


from app.database.connection import SessionLocal
from app.database.models import User, OrderStatus
from app.api.v1.endpoints.order import crud as order_crud
from app.api.v1.endpoints.order.schemas import OrderCreateSchema, OrderBeverageQuantityCreateSchema
from app.api.v1.endpoints.order.address import crud as address_crud
from app.api.v1.endpoints.order.address.schemas import AddressCreateSchema
from app.api.v1.endpoints.user import crud as user_crud
from app.api.v1.endpoints.user.schemas import UserCreateSchema
from app.api.v1.endpoints.beverage import crud as beverage_crud
from app.api.v1.endpoints.beverage.schemas import BeverageCreateSchema


@pytest.fixture(scope='module')
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_order_create_read_delete(db):
    # Arrange: create a real user in the database
    user_id = uuid.uuid4()
    user = User(id=user_id, username='testuser')
    db.add(user)
    db.commit()

    # Arrange: create an address
    address = AddressCreateSchema(
        street='Test Street',
        post_code='12345',
        house_number=1,
        country='Testland',
        town='Testville',
        first_name='Jane',
        last_name='Doe'
    )

    number_of_orders_before = len(order_crud.get_all_orders(db))

    # Create order schema
    order = OrderCreateSchema(user_id=user_id, address=address)

    # Act: Add order to database
    db_order = order_crud.create_order(order, db)
    created_order_id = db_order.id

    # Assert: One more order in database
    orders = order_crud.get_all_orders(db)
    assert len(orders) == number_of_orders_before + 1

    # Act: Re-read order from database
    read_order = order_crud.get_order_by_id(created_order_id, db)

    # Assert: Correct order was stored in database
    assert read_order.id == created_order_id
    assert read_order.user_id == user_id
    assert read_order.address.street == 'Test Street'
    assert read_order.address.post_code == '12345'
    assert read_order.address.house_number == 1
    assert read_order.address.country == 'Testland'
    assert read_order.address.town == 'Testville'
    assert read_order.address.first_name == 'Jane'
    assert read_order.address.last_name == 'Doe'

    # Act: Delete order
    order_crud.delete_order_by_id(created_order_id, db)

    # Assert: Correct number of orders after deletion
    orders = order_crud.get_all_orders(db)
    assert len(orders) == number_of_orders_before

    # Assert: Order was deleted
    deleted_order = order_crud.get_order_by_id(created_order_id, db)
    assert deleted_order is None


def test_update_order_status(db):
    # Arrange: create a real user in the database
    user_id = uuid.uuid4()
    user = User(id=user_id, username='testuser_status')
    db.add(user)
    db.commit()

    # Arrange: create an order
    address = AddressCreateSchema(
        street='Test Street',
        post_code='12345',
        house_number=1,
        country='Testland',
        town='Testville',
        first_name='Jane',
        last_name='Doe'
    )
    order = OrderCreateSchema(user_id=user_id, address=address)
    db_order = order_crud.create_order(order, db)
    created_order_id = db_order.id

    # Act: Update order status
    from app.database.models import OrderStatus
    updated_order = order_crud.update_order_status(db_order, OrderStatus.COMPLETED, db)

    # Assert: Order status was updated
    assert updated_order.order_status == OrderStatus.COMPLETED
    db.refresh(db_order)
    assert db_order.order_status == OrderStatus.COMPLETED

    # Cleanup
    order_crud.delete_order_by_id(created_order_id, db)
    db.delete(user)
    db.commit()


def test_get_all_orders(db):
    # Arrange: create a real user in the database
    user_id = uuid.uuid4()
    user = User(id=user_id, username='testuser_all')
    db.add(user)
    db.commit()

    # Arrange: create orders
    address = AddressCreateSchema(
        street='Test Street',
        post_code='12345',
        house_number=1,
        country='Testland',
        town='Testville',
        first_name='Jane',
        last_name='Doe'
    )
    number_of_orders_before = len(order_crud.get_all_orders(db))
    
    order1 = OrderCreateSchema(user_id=user_id, address=address)
    order2 = OrderCreateSchema(user_id=user_id, address=address)
    db_order1 = order_crud.create_order(order1, db)
    db_order2 = order_crud.create_order(order2, db)

    # Act: Get all orders
    all_orders = order_crud.get_all_orders(db)

    # Assert: Both orders are in the list
    assert len(all_orders) >= number_of_orders_before + 2
    order_ids = [o.id for o in all_orders]
    assert db_order1.id in order_ids
    assert db_order2.id in order_ids

    # Cleanup
    order_crud.delete_order_by_id(db_order1.id, db)
    order_crud.delete_order_by_id(db_order2.id, db)
    db.delete(user)
    db.commit()

# Constants
INITIAL_QTY = 3
UPDATED_QTY = 5

def test_order_flow(db):

    # Create a User
    user_data = UserCreateSchema(username='testuser')
    db_user = user_crud.create_user(user_data, db)
    user_id = db_user.id

    # Create an Address
    address_data = AddressCreateSchema(
        street='Test Street',
        post_code='12345',
        house_number=1,
        country='Testland',
        town='Testville',
        first_name='Jane',
        last_name='Doe'
    )
    db_address = address_crud.create_address(address_data, db)
    address_id = db_address.id

    # Create a Beverage
    beverage_data = BeverageCreateSchema(
        name='Test Beverage',
        price=2.5,
        description='Delicious',
        stock=10
    )
    db_beverage = beverage_crud.create_beverage(beverage_data, db)
    beverage_id = db_beverage.id

    # Create an Order
    order_data = OrderCreateSchema(user_id=user_id, address=db_address)
    db_order = order_crud.create_order(order_data, db)
    order_id = db_order.id

    # Add Beverage to Order
    order_beverage_data = OrderBeverageQuantityCreateSchema(quantity=3, beverage_id=beverage_id)
    order_crud.create_beverage_quantity(db_order, order_beverage_data, db)

    # Check Order Data
    read_order = order_crud.get_order_by_id(order_id, db)
    assert read_order.user_id == user_id
    assert read_order.address.street == 'Test Street'

    # Check Beverage Quantity
    qty = order_crud.get_beverage_quantity_by_id(order_id, beverage_id, db).quantity
    assert qty == INITIAL_QTY

    # Update Order Status
    order_crud.update_order_status(db_order, OrderStatus.PREPARING, db)
    assert db_order.order_status == OrderStatus.PREPARING

    # Check Price
    total_price = order_crud.get_price_of_order(order_id, db)
    assert total_price == pytest.approx(3 * 2.5)

    # Update Beverage Quantity
    order_crud.update_beverage_quantity_of_order(order_id, beverage_id, 5, db)
    updated_qty = order_crud.get_beverage_quantity_by_id(order_id, beverage_id, db).quantity
    assert updated_qty == UPDATED_QTY
    updated_price = order_crud.get_price_of_order(order_id, db)
    assert updated_price == pytest.approx(5 * 2.5)

    # Delete Beverage from Order
    initial_count = len(order_crud.get_joined_beverage_quantities_by_order(order_id, db))
    order_crud.delete_beverage_from_order(order_id, beverage_id, db)
    assert len(order_crud.get_joined_beverage_quantities_by_order(order_id, db)) == initial_count - 1


    # Cleanup: Delete Order, Address, User, Beverage
    order_crud.delete_order_by_id(order_id, db)
    address_crud.delete_address_by_id(address_id, db)
    user_crud.delete_user_by_id(user_id, db)
    beverage_crud.delete_beverage_by_id(beverage_id, db)

    # Verify cleanup
    assert order_crud.get_order_by_id(order_id, db) is None
    assert address_crud.get_address_by_id(address_id, db) is None
    assert user_crud.get_user_by_id(user_id, db) is None
    assert beverage_crud.get_beverage_by_id(beverage_id, db) is None