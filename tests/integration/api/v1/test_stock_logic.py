import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

# 1. Import 'app' and 'SessionLocal' exactly as defined in your provided files
from app.main import app
from app.database.connection import SessionLocal

# 2. Import CRUD and Schemas for setup
import app.api.v1.endpoints.dough.crud as dough_crud
from app.api.v1.endpoints.dough.schemas import DoughCreateSchema
import app.api.v1.endpoints.sauce.crud as sauce_crud
from app.api.v1.endpoints.sauce.schemas import SauceCreateSchema
import app.api.v1.endpoints.pizza_type.crud as pizza_type_crud
from app.api.v1.endpoints.pizza_type.schemas import PizzaTypeCreateSchema
import app.api.v1.endpoints.order.crud as order_crud
from app.api.v1.endpoints.order.schemas import OrderCreateSchema
from app.api.v1.endpoints.order.address.schemas import AddressCreateSchema
from app.database.models import SpicinessType, User


@pytest.fixture(scope="module")
def db():
    """Create a database session for the test."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    """Create a TestClient using the main FastAPI app."""
    with TestClient(app) as c:
        yield c


def test_stock_reduction_and_restoration_via_api(db, client):
    """
    Integration Test:
    1. Creates Dough, Sauce, PizzaType, User, and Order in DB.
    2. Calls POST /v1/orders/{id}/pizzas to add a pizza.
    3. Verifies Sauce stock decreases (Validation Logic).
    4. Calls DELETE /v1/orders/{id}/pizzas to remove the pizza.
    5. Verifies Sauce stock restores (Restoration Logic).
    """

    # --- 1. SETUP: Create Dependencies ---

    # Create Dough (Stock = 10)
    dough = dough_crud.create_dough(DoughCreateSchema(
        name=f"StockTest Dough {uuid.uuid4()}",
        price=Decimal("1.00"), description="desc", stock=10
    ), db)

    # Create Sauce (Stock = 10) -> THIS IS THE TARGET OF OUR TEST
    sauce = sauce_crud.create_sauce(SauceCreateSchema(
        name=f"StockTest Sauce {uuid.uuid4()}",
        price=Decimal("1.00"), description="desc", stock=10,
        spiciness=SpicinessType.LIGHT
    ), db)

    # Create PizzaType linking them
    pizza_type = pizza_type_crud.create_pizza_type(PizzaTypeCreateSchema(
        name=f"StockTest Pizza {uuid.uuid4()}",
        price=Decimal("10.00"), description="desc",
        dough_id=dough.id,
        sauce_id=sauce.id  # Linked!
    ), db)

    # Create User manually (to avoid user API overhead)
    user = User(username=f"User_{uuid.uuid4()}")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create Order (Status OPEN)
    address_data = AddressCreateSchema(
        post_code="12345", street="Test St", country="DE",
        house_number=1, town="Test Town", first_name="Test", last_name="User"
    )
    order = order_crud.create_order(OrderCreateSchema(
        user_id=user.id, address=address_data
    ), db)

    # --- 2. ACT: Add Pizza via API ---
    # This hits 'router.post', which calls 'stock_service.validate_and_reduce_ingredients'
    response = client.post(
        f"/v1/orders/{order.id}/pizzas",
        json={"pizza_type_id": str(pizza_type.id)}
    )

    # --- 3. ASSERT: Check Success and Stock Reduction ---
    assert response.status_code == 200, f"API call failed: {response.text}"
    pizza_id = response.json()['id']

    # Refresh DB objects to see new stock values
    db.refresh(dough)
    db.refresh(sauce)

    # Stock should decrease by 1
    assert dough.stock == 9, "Dough stock did not decrease!"
    assert sauce.stock == 9, "Sauce stock did not decrease! The Stock Service might not be connected properly."

    # --- 4. ACT: Delete Pizza via API ---
    # This hits 'router.delete', which calls 'stock_service.increase_stock_of_ingredients'
    del_response = client.request(
        "DELETE",
        f"/v1/orders/{order.id}/pizzas",
        json={"id": pizza_id}  # The schema expects 'id' in the body
    )

    # --- 5. ASSERT: Check Restoration ---
    assert del_response.status_code == 200, f"Delete failed: {del_response.text}"

    db.refresh(dough)
    db.refresh(sauce)

    # Stock should be back to 10
    assert dough.stock == 10, "Dough stock did not restore after delete!"
    assert sauce.stock == 10, "Sauce stock did not restore after delete!"

    # --- CLEANUP (Best Effort) ---
    try:
        order_crud.delete_order_by_id(order.id, db)
        pizza_type_crud.delete_pizza_type_by_id(pizza_type.id, db)
        sauce_crud.delete_sauce_by_id(sauce.id, db)
        dough_crud.delete_dough_by_id(dough.id, db)
    except Exception:
        pass  # Ignore cleanup errors