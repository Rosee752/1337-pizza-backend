import logging
import uuid
from typing import List, Optional, TypeVar

from fastapi import APIRouter, Depends, Request, Response, status, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

import app.api.v1.endpoints.beverage.crud as beverage_crud
import app.api.v1.endpoints.pizza_type.crud as pizza_type_crud
import app.api.v1.endpoints.user.crud as user_crud
import app.api.v1.endpoints.order.crud as order_crud
from app.api.v1.endpoints.beverage.router import HTTP_ERROR
from app.api.v1.endpoints.order.stock_logic import stock_beverage_crud
from app.api.v1.endpoints.order.stock_logic import stock_ingredients_crud
from app.api.v1.endpoints.order.schemas \
    import OrderSchema, PizzaCreateSchema, JoinedPizzaPizzaTypeSchema, \
    PizzaWithoutPizzaTypeSchema, OrderBeverageQuantityCreateSchema, JoinedOrderBeverageQuantitySchema, \
    OrderPriceSchema, OrderBeverageQuantityBaseSchema, OrderCreateSchema
from app.api.v1.endpoints.user.schemas import UserSchema
from app.database.connection import SessionLocal
from app.api.v1.endpoints.order.schemas import OrderStatus
from app.api.v1.endpoints.order.schemas import OrderStatusPatchSchema
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post('', response_model=OrderSchema, status_code=status.HTTP_201_CREATED, tags=['order'])
def create_order(order: OrderCreateSchema, db: Session = Depends(get_db),
                 copy_order_id: Optional[uuid.UUID] = None):
    if user_crud.get_user_by_id(order.user_id, db) is None:
        log_message = (
            f'tried to find the user{order.user_id}, to create an order but user already exists\n'
        )
        logging.fatal(log_message)
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    # Create Order
    new_order = order_crud.create_order(order, db)

    # Check if Copy Order is specified
    if copy_order_id is None:
        logging.info(f'created order {new_order.id} for user {new_order.user_id}\n')
        return new_order

    # Check Copy Order
    copy_order = order_crud.get_order_by_id(copy_order_id, db)
    if not copy_order:
        logging.fatal(f' other order with id: {copy_order_id} does not exist.'
                      f' Order with id: {new_order.id}, will be deleted\n')
        order_crud.delete_order_by_id(new_order.id, db)
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    logging.info(f'found old order with id:{copy_order_id}\n')

    # Copy Pizzas
    for pizza in copy_order.pizzas:
        pizza_type = pizza.pizza_type
        if not stock_ingredients_crud.ingredients_are_available(pizza_type):
            # Not enough Stock
            logging.fatal(f'stock for pizza type {pizza_type} is not available.'
                          f' Order with id: {new_order.id} will be deleted\n')
            order_crud.delete_order_by_id(new_order.id, db)
            raise HTTPException(status_code=409, detail='Conflict')

        order_crud.add_pizza_to_order(new_order, pizza_type, db)
        logging.info(f'added pizza: {pizza_type} to order with id: {new_order.id}\n')
        stock_ingredients_crud.reduce_stock_of_ingredients(pizza_type, db)
        logging.info(f'reduced stock for pizza: {pizza_type}\n')

    # Copy Beverages
    for beverage_quantity in copy_order.beverages:
        schema = OrderBeverageQuantityCreateSchema(
            **{'quantity': beverage_quantity.quantity, 'beverage_id': beverage_quantity.beverage_id})
        if not stock_beverage_crud.change_stock_of_beverage(beverage_quantity.beverage_id,
                                                            -beverage_quantity.quantity, db):
            # Not enough Stock
            logging.fatal(f'the beverage: {beverage_quantity.beverage_id} '
                          f'does not have enough stock and will be deleted\n')
            order_crud.delete_order_by_id(new_order.id, db)
            raise HTTPException(status_code=409, detail='Conflict')

        logging.info(f'added beverage: {beverage_quantity.beverage_id} to Order {new_order.id}\n')
        order_crud.create_beverage_quantity(new_order, schema, db)

    return new_order

@router.get('',status_code=status.HTTP_200_OK,response_model=List[OrderSchema],tags=['order'])
def get_orders_by_status(statuses: Optional[List[OrderStatus]] = Query(None),db: Session = Depends(get_db)):
    if statuses is None:
        orders = order_crud.get_all_orders(db)
        return orders
    orders = order_crud.get_order_by_status(statuses, db)
    if not orders:
        logging.warning(f'tried to find orders with status: {statuses}'
                        f' but could not find any orders\n')
        raise HTTPException(status_code=404, detail=HTTP_ERROR)
    return orders

@router.get('/{order_id}', response_model=OrderSchema, tags=['order'])
def get_order(
        order_id: uuid.UUID,
        db: Session = Depends(get_db)):
    order = order_crud.get_order_by_id(order_id, db)
    if not order:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return order


@router.delete('/{order_id}', response_model=None, tags=['order'])
def delete_order(
        order_id: uuid.UUID,
        db: Session = Depends(get_db),
):
    order = order_crud.get_order_by_id(order_id, db)
    if not order:
        logging.fatal(f'order with id: {order_id} does not exist and can not be deleted\n')
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    ordered_pizzas = order.pizzas
    if ordered_pizzas:
        for pizza in ordered_pizzas:
            stock_ingredients_crud.increase_stock_of_ingredients(pizza.pizza_type, db)
            logging.info(f'pizza with id:{pizza.id} deleted. Stock for pizza type: {pizza.pizza_type} increased\n')
    order_beverages = order_crud.get_joined_beverage_quantities_by_order(order_id, db)
    if order_beverages:
        for order_beverage in order_beverages:
            logging.info(f'order with id: {order_id} will be deleted.'
                         f' changed stock of beverage: {order_beverage.beverage_id}.\n')
            stock_beverage_crud.change_stock_of_beverage(order_beverage.beverage.id, order_beverage.quantity, db)
    order_crud.delete_order_by_id(order_id, db)
    logging.info(f'deleted order with id: {order_id}\n')
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/{order_id}/pizzas', response_model=PizzaWithoutPizzaTypeSchema, tags=['order'])
def add_pizza_to_order(
        order_id: uuid.UUID,
        schema: PizzaCreateSchema,
        db: Session = Depends(get_db),
):
    order = order_crud.get_order_by_id(order_id, db)
    if not order:
        logging.fatal(f' tried to update order with id: {order_id} but could not find such order.\n')
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    pizza_type = pizza_type_crud.get_pizza_type_by_id(schema.pizza_type_id, db)
    if not pizza_type:
        logging.fatal(f'tried to update order with id: {order_id}.'
                      f' but could not find pizza type:{schema.pizza_type_id}\n')
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    if not stock_ingredients_crud.ingredients_are_available(pizza_type):
        logging.fatal(f'tried to update order with id: {order_id}.'
                      f' but ingredients for pizza type: {pizza_type} are not available\n')
        return Response(status_code=status.HTTP_409_CONFLICT)
    stock_ingredients_crud.reduce_stock_of_ingredients(pizza_type, db)
    pizza = order_crud.add_pizza_to_order(order, pizza_type, db)
    logging.info(f'pizza with id: {pizza.id} was successfully added to order: {order_id}\n')
    return pizza


@router.get('/{order_id}/pizzas', response_model=List[JoinedPizzaPizzaTypeSchema], tags=['order'])
def get_pizzas_from_order(
        order_id: uuid.UUID,
        db: Session = Depends(get_db),
):
    order = order_crud.get_order_by_id(order_id, db)
    if not order:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    pizzas = order_crud.get_all_pizzas_of_order(order, db)
    return pizzas


@router.delete('/{order_id}/pizzas', response_model=None, tags=['order'])
def delete_pizza_from_order(
        order_id: uuid.UUID,
        pizza: PizzaWithoutPizzaTypeSchema,
        db: Session = Depends(get_db),
):
    order = order_crud.get_order_by_id(order_id, db)
    if not order:
        logging.fatal(f'tried to delete pizza: {pizza.id}'
                      f' from order: {order_id} but could not find such order\n')
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    pizza_entity = order_crud.get_pizza_by_id(pizza.id, db)
    if not pizza_entity:
        logging.fatal(f'tried to delete pizza: {pizza.id} from order: {order_id}'
                      f' but could not find such pizza\n')
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    stock_ingredients_crud.increase_stock_of_ingredients(pizza_entity.pizza_type, db)
    logging.info(f'pizza with id: {pizza.id} will be deleted from order: {order_id} so stock got increased\n')

    if not order_crud.delete_pizza_from_order(order, pizza.id, db):
        logging.fatal(f'the pizza with id: {pizza.id} is not part of order: {order_id}\n')
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    logging.info(f'pizza with id: {pizza.id} was successfully deleted from order: {order_id}\n')
    return Response(status_code=status.HTTP_200_OK)


# Due to mypy error, this workaround is needed for Union
# see pull request https://github.com/python/mypy/pull/8779
# should be fixed in near future
MyPyEitherItem = TypeVar(
    'MyPyEitherItem',
    List[OrderBeverageQuantityCreateSchema],
    List[JoinedOrderBeverageQuantitySchema],
    None,
)


@router.get(
    '/{order_id}/beverages',
    response_model=MyPyEitherItem,
    tags=['order'],
)
def get_order_beverages(
        order_id: uuid.UUID,
        db: Session = Depends(get_db),
        join: bool = False,
):
    order = order_crud.get_order_by_id(order_id, db)
    if not order:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    order = order_crud.get_order_by_id(order_id, db)

    beverages = order.beverages
    if join:
        beverages = order_crud.get_joined_beverage_quantities_by_order(order.id, db)

    return beverages


@router.post(
    '/{order_id}/beverages',
    response_model=OrderBeverageQuantityCreateSchema,
    status_code=status.HTTP_201_CREATED,
    tags=['order'],
)
def create_order_beverage(
        order_id: uuid.UUID,
        beverage_quantity: OrderBeverageQuantityCreateSchema,
        request: Request,
        db: Session = Depends(get_db),
):
    order = order_crud.get_order_by_id(order_id, db)
    if not order:
        logging.fatal(f'tried to add beverages: {beverage_quantity.beverage_id}'
                      f' to order: {order_id} but could not find such order\n')
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # Check if new Quantity is valid
    if beverage_quantity.quantity <= 0:
        logging.fatal(f'the quantity of beverage {beverage_quantity.beverage_id} is not enough\n')
        raise HTTPException(status_code=422)

    beverage = beverage_crud.get_beverage_by_id(beverage_quantity.beverage_id, db)
    if not beverage:
        logging.fatal(f'tried to add beverage: {beverage_quantity.beverage_id}'
                      f' but it doesnt exist\n')
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    beverage_quantity_found = order_crud.get_beverage_quantity_by_id(order_id, beverage_quantity.beverage_id, db)
    if beverage_quantity_found:
        url = request.url_for('get_order_beverages', order_id=beverage_quantity_found.order_id)
        logging.warning(f'the beverage with id: {beverage_quantity.beverage_id}'
                        f' already exists in the order: {order_id}\n')
        return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

    # Change Stock of Beverage if enough is available
    if not stock_beverage_crud.beverage_is_available(beverage_quantity.beverage_id, beverage_quantity.quantity, db):
        logging.fatal(f'tried to add beverage: {beverage_quantity.beverage_id} to order{order_id} '
                      f'with qauntity {beverage_quantity.quantity}'
                      f' but it exceeds the stocks limit\n')
        raise HTTPException(status_code=409, detail='Conflict')
    stock_beverage_crud.change_stock_of_beverage(beverage_quantity.beverage_id, -beverage_quantity.quantity, db)
    new_beverage_quantity = order_crud.create_beverage_quantity(order, beverage_quantity, db)
    logging.info(f'added beverage quantity{beverage_quantity.beverage_id} '
                 f'to order: {order_id}\n')
    return new_beverage_quantity


@router.put(
    '/{order_id}/beverages',
    response_model=OrderBeverageQuantityBaseSchema,
    tags=['order'],
)
def update_beverage_of_order(
        order_id: uuid.UUID,
        beverage_quantity: OrderBeverageQuantityCreateSchema,
        db: Session = Depends(get_db),
):
    order = order_crud.get_order_by_id(order_id, db)
    if not order:
        logging.fatal(f'order {order_id} does not exist\n')
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # Check if new Quantity is valid
    if beverage_quantity.quantity <= 0:
        logging.fatal(f'tried to update beverage: {beverage_quantity.beverage_id}'
                      f' to order{order_id} but no more stock available\n')
        return Response(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    beverage_id = beverage_quantity.beverage_id
    order_beverage_quantity = order_crud.get_beverage_quantity_by_id(order_id, beverage_id, db)
    if not order_beverage_quantity:
        logging.fatal(f'tried to update beverage: {beverage_id}'
                      f' to order {order_id} but couldnt find the beverage\n')
        raise HTTPException(status_code=404, detail=HTTP_ERROR)
    new_quantity = beverage_quantity.quantity
    old_quantity = order_beverage_quantity.quantity
    # Change Stock if enough is available: change Amount is Previous - New
    if not stock_beverage_crud.change_stock_of_beverage(beverage_id, old_quantity - new_quantity, db):
        logging.fatal(f'tried to update beverage: {beverage_quantity.beverage_id} to order{order_id} '
                      f'with qauntity {beverage_quantity.quantity}'
                      f' but it exceeds the stocks limit\n')
        raise HTTPException(status_code=409, detail='Conflict')
    # Update
    new_order_beverage_quantity = order_crud.update_beverage_quantity_of_order(
        order_id, beverage_quantity.beverage_id, beverage_quantity.quantity, db)
    # Return updated OrderBeverageQuantity
    if new_order_beverage_quantity:
        logging.info(f'upadated beverage quantity{beverage_quantity.beverage_id} '
                     f'to order: {order_id}\n')
        return new_order_beverage_quantity
    else:
        logging.fatal(f'Couldnt update beverage {beverage_quantity.beverage_id}'
                      f' to order {order_id}\n')
        raise HTTPException(status_code=404, detail=HTTP_ERROR)



@router.delete(
    '/{order_id}/beverages', response_model=None, tags=['order'],
)
def delete_beverage_from_order(
        order_id: uuid.UUID,
        beverage_id: uuid.UUID,
        db: Session = Depends(get_db),
):
    order = order_crud.get_order_by_id(order_id, db)
    if not order:
        logging.fatal(f'tried to delete order: {order_id} but could not find such order\n')
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    order_beverage = order_crud.get_beverage_quantity_by_id(order_id, beverage_id, db)
    if not order_beverage:
        logging.fatal(f'tried to delete beverage {beverage_id}'
                      f' from order {order_id} but could not find beverage.\n')
        raise HTTPException(status_code=404, detail=HTTP_ERROR)
    # Increase Stock by the quantity of the deleted order
    order_quantity = order_beverage.quantity
    stock_beverage_crud.change_stock_of_beverage(beverage_id, order_quantity, db)
    logging.info(f'stock updated with the qauntity of the beverage {beverage_id}'
                 f' of the order {order_id}\n')
    # Delete OrderBeverageQuantity
    order_crud.delete_beverage_from_order(order_id, beverage_id, db)
    logging.info(f'deleted beverage: {beverage_id} from order: {order_id}\n')
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    '/{order_id}/price',
    status_code=status.HTTP_200_OK,
    response_model=OrderPriceSchema,
    tags=['order'],
)
def get_price_of_order(
        order_id: uuid.UUID,
        db: Session = Depends(get_db),
):
    order = order_crud.get_order_by_id(order_id, db)
    if not order:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    price = order_crud.get_price_of_order(order_id, db)

    return OrderPriceSchema(**{
        'price': price,
    })


@router.get('/{order_id}/user',
            status_code=status.HTTP_200_OK,
            response_model=UserSchema,
            tags=['order'],
            )
def get_user_of_order(
        order_id: uuid.UUID,
        db: Session = Depends(get_db),
):
    order = order_crud.get_order_by_id(order_id, db)
    if not order:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    order = order_crud.get_order_by_id(order_id, db)
    if not order:
        raise HTTPException(status_code=404, detail=HTTP_ERROR)
    user = order.user
    return user

@router.put('/{order_id}',status_code=status.HTTP_204_NO_CONTENT, tags=['order'])
def update_order_status(
        order_id: uuid.UUID,
        order_status: OrderStatus = Query(..., description="The new status of the order"),
        db: Session = Depends(get_db)
):
    # 1. Retrieve the order
    order = order_crud.get_order_by_id(order_id, db)

    # 2. Check if order exists
    if not order:
        logging.fatal(f'tried to update status for order: {order_id} but could not find such order\n')
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # 3. Log the change
    logging.info(f'updating order: {order_id} status from {order.order_status} to {order_status}\n')

    # 4. Update the status using existing CRUD
    # Note: Your crud.py already has this function implemented
    updated_order = order_crud.update_order_status(
        order=order,
        changed_order=order_status,
        db=db
    )

    return updated_order