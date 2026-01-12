import decimal
import uuid

import pytest
from fastapi.testclient import TestClient

import app.api.v1.endpoints.sauce.crud as sauce_crud
import app.api.v1.endpoints.sauce.schemas as sauce_schemas
from app.database.connection import SessionLocal
from app.database.models import SpicinessType
from app.main import app


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
def client():
    with TestClient(app) as c:
        yield c


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

    sauce_crud.delete_sauce_by_id(created_sauce_id, db=db)


@pytest.fixture(scope='function')
def function_sauce(db):
    # arrange
    test_name = 'func_test_name'
    test_description = 'func_test_description'
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

    sauce_crud.delete_sauce_by_id(created_sauce_id, db=db)


def test_create_sauce(db):
    # arrange
    test_name = 'test_name'
    test_description = 'test_description'
    test_stock = 10
    test_price = decimal.Decimal(3.50)
    test_spiciness = SpicinessType.HOT
    number_of_sauces_before = len(sauce_crud.get_all_sauces(db))

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

    # assert
    number_of_sauces_after = len(sauce_crud.get_all_sauces(db))
    assert number_of_sauces_after == number_of_sauces_before + 1

    # break down
    sauce_crud.delete_sauce_by_id(created_sauce_id, db=db)


def test_read_sauce_by_id(db, sample_sauce):
    # arrange
    sauce = sample_sauce

    # act
    read_sauce = sauce_crud.get_sauce_by_id(sauce_id=sauce.id, db=db)

    # assert
    assert sauce.spiciness == read_sauce.spiciness
    assert sauce.stock == read_sauce.stock
    assert sauce.price == read_sauce.price
    assert sauce.name == read_sauce.name
    assert sauce.description == read_sauce.description


def test_read_sauce_by_name(db, sample_sauce):
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


def test_update_sauce(db, function_sauce):
    # arrange
    changed_sauce = sauce_schemas.SauceCreateSchema(
        name='new name',
        description='new description',
        stock=15,
        price=decimal.Decimal(4.50),
        spiciness=SpicinessType.MEDIUM
    )

    # act
    updated_sauce = sauce_crud.update_sauce(sauce=function_sauce, changed_sauce=changed_sauce, db=db)

    # assert
    assert updated_sauce.id == function_sauce.id
    assert updated_sauce.name == changed_sauce.name
    assert updated_sauce.description == changed_sauce.description
    assert updated_sauce.stock == changed_sauce.stock
    assert updated_sauce.price == changed_sauce.price
    assert updated_sauce.spiciness == changed_sauce.spiciness


def test_delete_sauce(db, function_sauce):
    # arrange
    sauce_id = function_sauce.id

    # act
    sauce_crud.delete_sauce_by_id(sauce_id, db=db)

    # assert
    deleted_sauce = sauce_crud.get_sauce_by_id(sauce_id, db=db)
    assert deleted_sauce is None


def test_delete_non_existent_sauce(db):
    # arrange
    non_existent_id = uuid.uuid4()

    # act
    # Should not raise exception
    sauce_crud.delete_sauce_by_id(non_existent_id, db=db)


def test_check_sauce_availability(db, function_sauce):
    # arrange
    sauce = function_sauce

    # act & assert
    assert sauce_crud.check_sauce_availability(sauce.id, db=db) is True

    # arrange - set stock to 0
    sauce_crud.change_stock_of_sauce(sauce.id, -sauce.stock, db=db)

    # act & assert
    assert sauce_crud.check_sauce_availability(sauce.id, db=db) is False


def test_check_sauce_availability_non_existent(db):
    # arrange
    non_existent_id = uuid.uuid4()

    # act & assert
    assert sauce_crud.check_sauce_availability(non_existent_id, db=db) is False


def test_change_stock_of_sauce(db, function_sauce):
    # arrange
    sauce = function_sauce
    initial_stock = sauce.stock
    increase_amount = 5

    # act
    result = sauce_crud.change_stock_of_sauce(sauce.id, increase_amount, db=db)

    # assert
    assert result is True
    updated_sauce = sauce_crud.get_sauce_by_id(sauce.id, db=db)
    assert updated_sauce.stock == initial_stock + increase_amount

    # act - decrease stock
    decrease_amount = -5
    result = sauce_crud.change_stock_of_sauce(sauce.id, decrease_amount, db=db)

    # assert
    assert result is True
    updated_sauce = sauce_crud.get_sauce_by_id(sauce.id, db=db)
    assert updated_sauce.stock == initial_stock

    # act - decrease too much
    too_much_decrease = -(initial_stock + 10)
    result = sauce_crud.change_stock_of_sauce(sauce.id, too_much_decrease, db=db)

    # assert
    assert result is False
    updated_sauce = sauce_crud.get_sauce_by_id(sauce.id, db=db)
    assert updated_sauce.stock == initial_stock


def test_change_stock_of_non_existent_sauce(db):
    # arrange
    non_existent_id = uuid.uuid4()

    # act
    result = sauce_crud.change_stock_of_sauce(non_existent_id, 10, db=db)

    # assert
    assert result is False


# --- API Tests ---

def test_api_read_all_sauces(client, sample_sauce):
    response = client.get('/v1/sauces')
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_api_create_sauce(client, db):
    # arrange
    sauce_data = {
        'name': f'api_test_sauce_{uuid.uuid4()}',
        'description': 'api test description',
        'stock': 10,
        'price': 3.50,
        'spiciness': 'HOT'
    }

    # act
    response = client.post('/v1/sauces', json=sauce_data)

    # assert
    assert response.status_code == 201
    data = response.json()
    assert data['name'] == sauce_data['name']
    assert 'id' in data

    # cleanup
    sauce_crud.delete_sauce_by_id(uuid.UUID(data['id']), db)


def test_api_create_sauce_duplicate_name(client, sample_sauce):
    # arrange
    sauce_data = {
        'name': sample_sauce.name,  # Existing name
        'description': 'duplicate name test',
        'stock': 10,
        'price': 3.50,
        'spiciness': 'HOT'
    }

    # act
    response = client.post('/v1/sauces', json=sauce_data, follow_redirects=False)

    # assert
    assert response.status_code == 303


def test_api_read_sauce_by_id(client, sample_sauce):
    response = client.get(f'/v1/sauces/{sample_sauce.id}')
    assert response.status_code == 200
    assert response.json()['id'] == str(sample_sauce.id)


def test_api_read_sauce_by_id_not_found(client):
    response = client.get(f'/v1/sauces/{uuid.uuid4()}')
    assert response.status_code == 404


def test_api_update_sauce_same_name(client, function_sauce):
    # arrange
    sauce_id = function_sauce.id
    update_data = {
        'name': function_sauce.name,  # Same name
        'description': 'updated description',
        'stock': 20,
        'price': 5.00,
        'spiciness': 'MEDIUM'
    }

    # act
    response = client.put(f'/v1/sauces/{sauce_id}', json=update_data)

    # assert
    assert response.status_code == 204

    # verify update
    # We need to refresh from DB or check via API
    response_get = client.get(f'/v1/sauces/{sauce_id}')
    assert response_get.json()['description'] == 'updated description'


def test_api_update_sauce_new_name_unique(client, function_sauce, db):
    # arrange
    sauce_id = function_sauce.id
    new_name = f'updated_name_{uuid.uuid4()}'
    update_data = {
        'name': new_name,
        'description': 'updated description',
        'stock': 20,
        'price': 5.00,
        'spiciness': 'MEDIUM'
    }

    # act
    response = client.put(f'/v1/sauces/{sauce_id}', json=update_data)

    # assert
    # According to router logic, this creates a NEW sauce and returns 201
    assert response.status_code == 201
    data = response.json()
    assert data['name'] == new_name
    assert data['id'] != str(sauce_id)

    # cleanup new sauce
    sauce_crud.delete_sauce_by_id(uuid.UUID(data['id']), db)


def test_api_update_sauce_new_name_conflict(client, function_sauce, sample_sauce):
    # arrange
    sauce_id = function_sauce.id
    # Try to update function_sauce to have sample_sauce's name
    update_data = {
        'name': sample_sauce.name,
        'description': 'conflict description',
        'stock': 20,
        'price': 5.00,
        'spiciness': 'MEDIUM'
    }

    # act
    response = client.put(f'/v1/sauces/{sauce_id}', json=update_data, follow_redirects=False)

    # assert
    assert response.status_code == 303


def test_api_update_sauce_not_found(client):
    update_data = {
        'name': 'some name',
        'description': 'desc',
        'stock': 10,
        'price': 1.0,
        'spiciness': 'LIGHT'
    }
    response = client.put(f'/v1/sauces/{uuid.uuid4()}', json=update_data)
    assert response.status_code == 404


def test_api_delete_sauce(client, function_sauce):
    response = client.delete(f'/v1/sauces/{function_sauce.id}')
    assert response.status_code == 204

    # verify deletion
    response_get = client.get(f'/v1/sauces/{function_sauce.id}')
    assert response_get.status_code == 404


def test_api_delete_sauce_not_found(client):
    response = client.delete(f'/v1/sauces/{uuid.uuid4()}')
    assert response.status_code == 404
