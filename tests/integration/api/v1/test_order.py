import pytest
import uuid

import app.api.v1.endpoints.order.crud as order_crud
import app.api.v1.endpoints.user.crud as user_crud
from app.api.v1.endpoints.order.address.schemas import AddressCreateSchema
from app.api.v1.endpoints.order.schemas import OrderCreateSchema
from app.api.v1.endpoints.user.schemas import UserCreateSchema
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
    order = OrderCreateSchema(
        address=address,
        user_id=user_id
    )

    # Order in DB speichern
    db_order = order_crud.create_order(order, db)
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
