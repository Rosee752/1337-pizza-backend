import pytest

import app.api.v1.endpoints.dough.crud as dough_crud
from app.api.v1.endpoints.dough.schemas import DoughCreateSchema
from app.database.connection import SessionLocal


@pytest.fixture(scope='module')
def db():
    """
    Fixture for creating a database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_dough_create_read_delete(db):
    """
    Test that we can create a dough record
    """
    name = 'Test thin dough record'
    price = 1.00
    description = 'Test dough'
    stock = 100
    number_of_doughs_before = len(dough_crud.get_all_doughs(db))

    dough = DoughCreateSchema(
        name=name,
        price=price,
        description=description,
        stock=stock,
    )

    db_dough = dough_crud.create_dough(dough, db)
    created_dough_id = db_dough.id

    doughs = dough_crud.get_all_doughs(db)
    assert len(doughs) == number_of_doughs_before + 1

    read_dough = dough_crud.get_dough_by_id(created_dough_id, db)

    assert read_dough is not None
    assert read_dough.id == created_dough_id
    assert read_dough.name == name
    assert read_dough.price == pytest.approx(price, rel=1e-9)
    assert read_dough.description == description
    assert read_dough.stock == stock

    dough_crud.delete_dough_by_id(created_dough_id, db)

    doughs = dough_crud.get_all_doughs(db)
    assert len(doughs) == number_of_doughs_before

    deleted_dough = dough_crud.get_dough_by_id(created_dough_id, db)
    assert deleted_dough is None