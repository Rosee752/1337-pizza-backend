import logging
import uuid
from typing import List, TypeVar

from fastapi import APIRouter, Depends, Request, Response, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

import app.api.v1.endpoints.dough.crud as dough_crud
import app.api.v1.endpoints.pizza_type.crud as pizza_type_crud
import app.api.v1.endpoints.topping.crud as topping_crud
import app.api.v1.endpoints.sauce.crud as sauce_crud
from app.api.v1.endpoints.beverage.router import HTTP_ERROR
from app.api.v1.endpoints.dough.schemas import DoughSchema
from app.api.v1.endpoints.sauce.schemas import SauceSchema
from app.api.v1.endpoints.pizza_type.schemas import \
    JoinedPizzaTypeQuantitySchema, \
    PizzaTypeSchema, \
    PizzaTypeCreateSchema, \
    PizzaTypeToppingQuantityCreateSchema
from app.database.connection import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get('', response_model=List[PizzaTypeSchema], tags=['pizza_type'])
def get_all_pizza_types(db: Session = Depends(get_db)):
    pizza_types = pizza_type_crud.get_all_pizza_types(db)
    return pizza_types


@router.post('', response_model=PizzaTypeSchema, tags=['pizza_type'])
def create_pizza_type(
        pizza_type: PizzaTypeCreateSchema, request: Request,
        response: Response, db: Session = Depends(get_db),
):
    pizza_type_found = pizza_type_crud.get_pizza_type_by_name(pizza_type.name, db)

    if pizza_type_found:
        url = request.url_for('get_pizza_type', pizza_type_id=pizza_type_found.id)
        logging.warning(f'pizza_type with name: {pizza_type.name} already exists with id: {pizza_type_found.id}\n')
        return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

    dough = dough_crud.get_dough_by_id(pizza_type.dough_id, db)
    if not dough:
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    if not sauce_crud.get_sauce_by_id(pizza_type.sauce_id, db):
        logging.warning(f'sauce id {pizza_type.sauce_id} not found')
        raise HTTPException(status_code=404, detail='Sauce not found')

    new_pizza_type = pizza_type_crud.create_pizza_type(pizza_type, db)
    logging.info(f'new pizza_type with name: {new_pizza_type.name} created\n')
    response.status_code = status.HTTP_201_CREATED
    return new_pizza_type


@router.put('/{pizza_type_id}', response_model=PizzaTypeSchema, tags=['pizza_type'])
def update_pizza_type(
        pizza_type_id: uuid.UUID,
        changed_pizza_type: PizzaTypeCreateSchema,
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
):
    pizza_type_found = pizza_type_crud.get_pizza_type_by_id(pizza_type_id, db)
    updated_pizza_type = None

    if pizza_type_found:
        if pizza_type_found.name == changed_pizza_type.name:

            if pizza_type_found.sauce_id != changed_pizza_type.sauce_id:
                if not sauce_crud.get_sauce_by_id(changed_pizza_type.sauce_id, db):
                    raise HTTPException(status_code=404, detail='Sauce not found')

            pizza_type_crud.update_pizza_type(pizza_type_found, changed_pizza_type, db)
            log_message = (
                f'the pizza_type with name: {changed_pizza_type.name} was updated successfully:\n'
                f'new pizza_type description: {changed_pizza_type.description}\n'
                f'new pizza_type name: {changed_pizza_type.name}\n'
            )
            logging.info(log_message)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            pizza_type_name_found = pizza_type_crud.get_pizza_type_by_name(changed_pizza_type.name, db)
            if pizza_type_name_found:
                url = request.url_for('get_pizza_type', pizza_type_id=pizza_type_name_found.id)
                log_message = (
                    f'the given id {pizza_type_id} does not match the given name {changed_pizza_type.name}\n'
                    f'dough with name: {changed_pizza_type.name} found with id {pizza_type_id}\n'
                )
                logging.warning(log_message)
                return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
            else:
                updated_pizza_type = pizza_type_crud.create_pizza_type(changed_pizza_type, db)
                logging.info('new pizza_type with name: {} created\n'.format(changed_pizza_type.name))
                response.status_code = status.HTTP_201_CREATED
    else:
        logging.fatal('id {} does not exist\n'.format(pizza_type_id))
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    return updated_pizza_type


@router.get('/{pizza_type_id}', response_model=PizzaTypeSchema, tags=['pizza_type'])
def get_pizza_type(
        pizza_type_id: uuid.UUID,
        db: Session = Depends(get_db),
):
    pizza_type = pizza_type_crud.get_pizza_type_by_id(pizza_type_id, db)

    if not pizza_type:
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    return pizza_type


@router.delete('/{pizza_type_id}', response_model=None, tags=['pizza_type'])
def delete_pizza_type(pizza_type_id: uuid.UUID,
                      db: Session = Depends(get_db),
                      ):
    pizza_type = pizza_type_crud.get_pizza_type_by_id(pizza_type_id, db)

    if not pizza_type:
        logging.fatal('the pizza_type with id: {} does not exist\n'.format(pizza_type_id))
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    pizza_type_crud.delete_pizza_type_by_id(pizza_type_id, db)
    logging.info('the pizza_type with id: {} deleted\n'.format(pizza_type_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Due to mypy error, this workaround is needed for Union
# see pull request https://github.com/python/mypy/pull/8779
# should be fixed in near future
MyPyEitherItem = TypeVar(
    'MyPyEitherItem',
    List[PizzaTypeToppingQuantityCreateSchema],
    List[JoinedPizzaTypeQuantitySchema],
    None,
)


@router.get(
    '/{pizza_type_id}/toppings',
    response_model=MyPyEitherItem,
    tags=['pizza_type'],
)
def get_pizza_type_toppings(
        pizza_type_id: uuid.UUID,
        response: Response,
        db: Session = Depends(get_db),
        join: bool = False,
):
    pizza_type = pizza_type_crud.get_pizza_type_by_id(pizza_type_id, db)

    if not pizza_type:
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    toppings = pizza_type.toppings
    if join:
        toppings = pizza_type_crud.get_joined_topping_quantities_by_pizza_type(pizza_type.id, db)

    return toppings


@router.post(
    '/{pizza_type_id}/toppings',
    response_model=PizzaTypeToppingQuantityCreateSchema,
    status_code=status.HTTP_201_CREATED,
    tags=['pizza_type'],
)
def create_pizza_type_topping(
        pizza_type_id: uuid.UUID,
        topping_quantity: PizzaTypeToppingQuantityCreateSchema,
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
):
    pizza_type = pizza_type_crud.get_pizza_type_by_id(pizza_type_id, db)
    if not pizza_type:
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    if not topping_crud.get_topping_by_id(topping_quantity.topping_id, db):
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    topping_quantity_found = pizza_type_crud.get_topping_quantity_by_id(pizza_type_id, topping_quantity.topping_id, db)
    if topping_quantity_found:
        url = request.url_for('get_pizza_type_toppings', pizza_type_id=topping_quantity_found.pizza_type_id)
        return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

    new_topping_quantity = pizza_type_crud.create_topping_quantity(pizza_type, topping_quantity, db)
    return new_topping_quantity


@router.get(
    '/{pizza_type_id}/dough',
    response_model=DoughSchema,
    tags=['pizza_type'],
)
def get_pizza_type_dough(
        pizza_type_id: uuid.UUID,
        response: Response,
        db: Session = Depends(get_db),
):
    pizza_type = pizza_type_crud.get_pizza_type_by_id(pizza_type_id, db)

    if not pizza_type:
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    dough = pizza_type.dough

    return dough

@router.get(
    '/{pizza_type_id}/sauce',
    response_model=SauceSchema,
    tags=['pizza_type'],
)
def get_pizza_type_sauce(
        pizza_type_id: uuid.UUID,
        response: Response,
        db: Session = Depends(get_db),
):
    pizza_type = pizza_type_crud.get_pizza_type_by_id(pizza_type_id, db)

    if not pizza_type:
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    sauce = pizza_type.sauce

    return sauce