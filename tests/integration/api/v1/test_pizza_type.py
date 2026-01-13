import pytest
from decimal import Decimal
import app.api.v1.endpoints.pizza_type.crud as pizza_type_crud
from app.api.v1.endpoints.pizza_type.schemas import PizzaTypeCreateSchema
from app.api.v1.endpoints.sauce.schemas import SauceCreateSchema
from app.database.connection import SessionLocal
from app.api.v1.endpoints.dough.schemas import DoughCreateSchema
from app.api.v1.endpoints.dough import crud as dough_crud
from app.database.models import SpicinessType
import app.api.v1.endpoints.sauce.crud as sauce_crud


@pytest.fixture(scope='module')
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_pizza_type_create_read_delete(db):
    new_pizza_type_name = 'Test Pizza Type'
    new_pizza_type_price = Decimal('9.99')
    new_pizza_type_description = 'Delicious test pizza type'
    number_of_pizza_types_before = len(pizza_type_crud.get_all_pizza_types(db))


    test_dough = DoughCreateSchema(
        name='Test Dough',
        price=Decimal('1.00'),
        description='Standard dough for test',
        stock=10
    )
    # 2. Persist the Dough to the database
    created_dough = dough_crud.create_dough(test_dough, db)
    created_dough_id = created_dough.id

    test_sauce = SauceCreateSchema(
        name='Test Sauce',
        price=Decimal('1.00'),
        description='Standard sauce for test',
        spiciness= SpicinessType.LIGHT,
        stock=10
    )
    created_sauce = sauce_crud.create_sauce(test_sauce, db)
    created_sauce_id = created_sauce.id

    # Arrange: Create a new PizzaType object
    pizza_type = PizzaTypeCreateSchema(
        name=new_pizza_type_name,
        price=new_pizza_type_price,
        description=new_pizza_type_description,
        dough_id = created_dough_id,
        sauce_id = created_sauce_id
    )

    # Act: Add pizza_type to database
    db_pizza_type = pizza_type_crud.create_pizza_type(pizza_type, db)
    created_pizza_type_id = db_pizza_type.id

    # Assert: One more pizza_type in database
    pizza_types = pizza_type_crud.get_all_pizza_types(db)
    assert len(pizza_types) == number_of_pizza_types_before + 1

    # Act: Re-read pizza_type from database
    read_pizza_type = pizza_type_crud.get_pizza_type_by_id(created_pizza_type_id, db)

    # Assert: Correct pizza_type was stored in database
    assert read_pizza_type.id == created_pizza_type_id
    assert read_pizza_type.name == new_pizza_type_name
    assert read_pizza_type.price == new_pizza_type_price
    assert read_pizza_type.description == new_pizza_type_description
    assert read_pizza_type.dough_id == created_dough_id
    assert read_pizza_type.sauce_id == created_sauce_id

    # Act: Delete pizza_type
    pizza_type_crud.delete_pizza_type_by_id(created_pizza_type_id, db)
    dough_crud.delete_dough_by_id(created_dough_id, db)

    # Assert: Correct number of pizza_types in database after deletion
    pizza_types = pizza_type_crud.get_all_pizza_types(db)
    assert len(pizza_types) == number_of_pizza_types_before

    # Assert: Correct pizza_type was deleted from database
    deleted_pizza_type = pizza_type_crud.get_pizza_type_by_id(created_pizza_type_id, db)
    assert deleted_pizza_type is None
