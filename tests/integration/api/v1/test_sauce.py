import decimal

import pytest
from app.database.connection import SessionLocal
import app.api.v1.endpoints.sauce.schemas as sauce_schemas
from app.database.models import SpicinessType
import app.api.v1.endpoints.sauce.crud as sauce_crud

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

@pytest.fixture(scope='module')
def sample_sauce(db):
    # arrange
    test_name = 'test_name'
    test_description = 'test_description'
    test_stock = 10
    test_price = decimal.Decimal(3.50)
    test_spiciness = SpicinessType.HOT

    # act
    sauce = sauce_schemas.SauceCreateSchema(
        name=test_name,
        description=test_description,
        stock=test_stock,
        price=test_price,
        spiciness=test_spiciness,
    )

    new_sauce = sauce_crud.create_sauce(schema=sauce, db=db)
    created_sauce_id = new_sauce.id
    yield new_sauce

    sauce_crud.delete_sauce_by_id(created_sauce_id,db=db)

def test_create_sauce(db):
    #arrange
    test_name = 'test_name'
    test_description = 'test_description'
    test_stock = 10
    test_price = decimal.Decimal(3.50)
    test_spiciness = SpicinessType.HOT
    number_of_sauces_before = len(sauce_crud.get_all_sauces(db))

    #act
    sauce = sauce_schemas.SauceCreateSchema(
        name=test_name,
        description=test_description,
        stock=test_stock,
        price=test_price,
        spiciness=test_spiciness,
    )

    new_sauce = sauce_crud.create_sauce(schema=sauce, db=db)
    created_sauce_id = new_sauce.id

    #assert
    number_of_sauces_after = len(sauce_crud.get_all_sauces(db))
    assert number_of_sauces_after == number_of_sauces_before + 1

    #break down
    sauce_crud.delete_sauce_by_id(created_sauce_id,db=db)

def test_read_sauce_by_id(db,sample_sauce):
    #arrange
    sauce = sample_sauce

    #act
    read_sauce = sauce_crud.get_sauce_by_id(sauce_id=sauce.id,db=db)

    #assert
    assert sauce.spiciness == read_sauce.spiciness
    assert sauce.stock == read_sauce.stock
    assert sauce.price == read_sauce.price
    assert sauce.name == read_sauce.name
    assert sauce.description == read_sauce.description

def test_read_sauce_by_name(db,sample_sauce):
        # arrange
        sauce = sample_sauce

        # act
        read_sauce = sauce_crud.get_sauce_by_name(sauce_name=sauce.name, db=db)

        # assert
        assert sauce.spiciness == read_sauce.spiciness
        assert sauce.stock == read_sauce.stock
        assert sauce.price == read_sauce.price
        assert sauce.name == read_sauce.name
        assert sauce.description == read_sauce.description

def test_update_sauce(db,sample_sauce):
    #arrange
    changed_sauce = sauce_schemas.SauceCreateSchema(
        name= 'new name',
        description= 'new description',
        stock= 15,
        price= decimal.Decimal(4.50),
        spiciness = SpicinessType.MEDIUM
    )

    #act
    updated_sauce = sauce_crud.update_sauce(sauce=sample_sauce, changed_sauce=changed_sauce, db=db)

    #assert
    assert updated_sauce.id == sample_sauce.id
    assert updated_sauce.name == changed_sauce.name
    assert updated_sauce.description == changed_sauce.description
    assert updated_sauce.stock == changed_sauce.stock
    assert updated_sauce.price == changed_sauce.price
    assert updated_sauce.spiciness == changed_sauce.spiciness

