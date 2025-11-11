import pytest

import app.api.v1.endpoints.beverage.crud as beverage_crud
from app.api.v1.endpoints.beverage.schemas import BeverageCreateSchema
from app.database.connection import SessionLocal


@pytest.fixture(scope='module')
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_beverage_create_read_delete(db):
    new_beverage_name = 'test'
    new_beverage_price = 4
    new_beverage_description = 'test'
    new_beverage_stock = 25
    number_of_beverages_before = len(beverage_crud.get_all_beverages(db))

    # Arrange: Instantiate a new beverage object
    beverage = BeverageCreateSchema(name=new_beverage_name, price=new_beverage_price,
                                    description=new_beverage_description, stock=new_beverage_stock)

    # Act: Add user to database
    db_beverage = beverage_crud.create_beverage(beverage,db)
    created_beverage_id = db_beverage.id

    # Assert: One more user in database
    beverages = beverage_crud.get_all_beverages(db)
    assert len(beverages) == number_of_beverages_before + 1

    # Act: Re-read user from database
    read_beverages = beverage_crud.get_beverage_by_id(created_beverage_id, db)

    # Assert: Correct user was stored in database
    assert read_beverages.id == created_beverage_id
    assert read_beverages.name == new_beverage_name
    assert read_beverages.price == new_beverage_price
    assert read_beverages.description == new_beverage_description
    assert read_beverages.stock == new_beverage_stock

    # Act: Delete user
    beverage_crud.delete_beverage_by_id(created_beverage_id, db)

    # Assert: Correct number of users in database after deletion
    beverages = beverage_crud.get_all_beverages(db)
    assert len(beverages) == number_of_beverages_before

    # Assert: Correct user was deleted from database
    deleted_beverage = beverage_crud.get_beverage_by_id(created_beverage_id, db)
    assert deleted_beverage is None