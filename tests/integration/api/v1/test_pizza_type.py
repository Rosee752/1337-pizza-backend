import pytest
import uuid
from decimal import Decimal

import app.api.v1.endpoints.pizza_type.crud as pizza_type_crud
from app.api.v1.endpoints.pizza_type.schemas import PizzaTypeCreateSchema
from app.database.connection import SessionLocal

# --- Imports für Dough ---
from app.api.v1.endpoints.dough.schemas import DoughCreateSchema
from app.api.v1.endpoints.dough import crud as dough_crud

# --- Imports für Sauce (DAS MUSS DA SEIN) ---
import app.api.v1.endpoints.sauce.crud as sauce_crud
from app.api.v1.endpoints.sauce.schemas import SauceCreateSchema
from app.database.models import SpicinessType


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

    # 1. Dough erstellen
    test_dough = DoughCreateSchema(
        name=f'Test Dough {uuid.uuid4()}',
        price=Decimal('1.00'),
        description='Standard dough for test',
        stock=10
    )
    created_dough = dough_crud.create_dough(test_dough, db)
    created_dough_id = created_dough.id

    # 2. Sauce erstellen (DIESER BLOCK FEHLT IN DER PIPELINE)
    test_sauce = SauceCreateSchema(
        name=f'Test Sauce {uuid.uuid4()}',
        price=Decimal('0.50'),
        description='Standard sauce',
        stock=20,
        spiciness=SpicinessType.LIGHT
    )
    created_sauce = sauce_crud.create_sauce(test_sauce, db)
    created_sauce_id = created_sauce.id

    # Arrange: Create a new PizzaType object
    pizza_type = PizzaTypeCreateSchema(
        name=new_pizza_type_name,
        price=new_pizza_type_price,
        description=new_pizza_type_description,
        dough_id=created_dough_id,
        sauce_id=created_sauce_id  # <--- UND HIER DIE VERKNÜPFUNG
    )

    created_pizza_type_id = None

    try:
        # Act
        db_pizza_type = pizza_type_crud.create_pizza_type(pizza_type, db)
        created_pizza_type_id = db_pizza_type.id

        # Assert
        pizza_types = pizza_type_crud.get_all_pizza_types(db)
        assert len(pizza_types) == number_of_pizza_types_before + 1

        read_pizza_type = pizza_type_crud.get_pizza_type_by_id(created_pizza_type_id, db)
        assert read_pizza_type.id == created_pizza_type_id
        assert read_pizza_type.name == new_pizza_type_name
        assert read_pizza_type.sauce_id == created_sauce_id # Prüfen

    finally:
        # Cleanup
        if created_pizza_type_id:
            pizza_type_crud.delete_pizza_type_by_id(created_pizza_type_id, db)

        dough_crud.delete_dough_by_id(created_dough_id, db)
        sauce_crud.delete_sauce_by_id(created_sauce_id, db) # Aufräumen