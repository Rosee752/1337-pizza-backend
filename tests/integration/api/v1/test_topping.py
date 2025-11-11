import pytest

import app.api.v1.endpoints.topping.crud as topping_crud
from app.api.v1.endpoints.topping.schemas import ToppingCreateSchema
from app.database.connection import SessionLocal


@pytest.fixture(scope='module')
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_topping_create_read_delete(db):
    new_topping_name = 'test'
    new_topping_price = 10.0
    new_topping_description = 'test description'
    new_topping_stocks = 4

    number_of_toppings_before = len(topping_crud.get_all_toppings(db))

    # Arrange: Instantiate a new topping object with all required fields
    topping = ToppingCreateSchema(
        name=new_topping_name,
        price=new_topping_price,
        description=new_topping_description,
        stock=new_topping_stocks
    )

    # Act: Add topping to database
    db_topping = topping_crud.create_topping(topping, db)
    created_topping_id = db_topping.id

    # Assert: One more topping in database
    toppings = topping_crud.get_all_toppings(db)
    assert len(toppings) == number_of_toppings_before + 1

    # Act: Re-read topping from database
    read_topping = topping_crud.get_topping_by_id(created_topping_id, db)

    # Assert: Correct topping was stored in database
    assert read_topping.id == created_topping_id
    assert read_topping.name == new_topping_name

    # Act: Delete topping
    topping_crud.delete_topping_by_id(created_topping_id, db)

    # Assert: Correct number of toppings in database after deletion
    toppings = topping_crud.get_all_toppings(db)
    assert len(toppings) == number_of_toppings_before

    # Assert: Correct topping was deleted from database
    deleted_topping = topping_crud.get_topping_by_id(created_topping_id, db)
    assert deleted_topping is None
