from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.database.models import Dough, Sauce, Topping, PizzaType


def validate_and_reduce_ingredients(pizza_type: PizzaType, db: Session):
    """
    Validates that enough stock exists for Dough, Sauce, and Toppings.
    If valid, reduces the stock immediately.
    """
    # 1. Check and Reduce Dough
    dough = db.query(Dough).filter(Dough.id == pizza_type.dough_id).with_for_update().first()
    if not dough or dough.stock < 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Not enough stock for Dough: {dough.name if dough else pizza_type.dough_id}",
        )
    dough.stock -= 1

    # 2. Check and Reduce Sauce
    sauce = db.query(Sauce).filter(Sauce.id == pizza_type.sauce_id).with_for_update().first()
    if not sauce or sauce.stock < 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Not enough stock for Sauce: {sauce.name if sauce else pizza_type.sauce_id}",
        )
    sauce.stock -= 1

    # 3. Check and Reduce Toppings
    for pt_topping in pizza_type.toppings:
        topping = db.query(Topping).filter(Topping.id == pt_topping.topping_id).with_for_update().first()
        qty_needed = pt_topping.quantity

        if not topping or topping.stock < qty_needed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Not enough stock for Topping: {topping.name if topping else pt_topping.topping_id}",
            )
        topping.stock -= qty_needed

    db.commit()


def increase_stock_of_ingredients(pizza_type: PizzaType, db: Session):
    """
    Restores stock for Dough, Sauce, and Toppings (used when deleting an order).
    """
    # 1. Increase Dough
    dough = db.query(Dough).filter(Dough.id == pizza_type.dough_id).with_for_update().first()
    if dough:
        dough.stock += 1

    # 2. Increase Sauce
    sauce = db.query(Sauce).filter(Sauce.id == pizza_type.sauce_id).with_for_update().first()
    if sauce:
        sauce.stock += 1

    # 3. Increase Toppings
    for pt_topping in pizza_type.toppings:
        topping = db.query(Topping).filter(Topping.id == pt_topping.topping_id).with_for_update().first()
        if topping:
            topping.stock += pt_topping.quantity

    db.commit()