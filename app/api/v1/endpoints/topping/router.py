import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, Request, Response, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

import app.api.v1.endpoints.topping.crud as topping_crud
from app.api.v1.endpoints.beverage.router import HTTP_ERROR
from app.api.v1.endpoints.topping.schemas import ToppingSchema, ToppingCreateSchema, ToppingListItemSchema
from app.database.connection import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get('', response_model=List[ToppingListItemSchema], tags=['topping'])
def get_all_toppings(db: Session = Depends(get_db)):
    toppings = topping_crud.get_all_toppings(db)
    return toppings


@router.post('', response_model=ToppingSchema, status_code=status.HTTP_201_CREATED, tags=['topping'])
def create_topping(topping: ToppingCreateSchema,
                   request: Request,
                   db: Session = Depends(get_db),
                   ):
    topping_found = topping_crud.get_topping_by_name(topping.name, db)

    if topping_found:
        url = request.url_for('get_topping', topping_id=topping_found.id)
        logging.warning(f'topping with name: {topping.name} already exists with id: {topping_found.id}\n')
        return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

    new_topping = topping_crud.create_topping(topping, db)
    logging.info(f'new topping with name: {new_topping.name} created\n')
    return new_topping


@router.put('/{topping_id}', response_model=ToppingSchema, tags=['topping'])
def update_topping(
        topping_id: uuid.UUID,
        changed_topping: ToppingCreateSchema,
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
):
    topping_found = topping_crud.get_topping_by_id(topping_id, db)
    updated_topping = None

    if topping_found:
        if topping_found.name == changed_topping.name:
            topping_crud.update_topping(topping_found, changed_topping, db)
            log_message = (
                f'the topping with name: {changed_topping.name} was updated successfully:\n'
                f'new topping description: {changed_topping.description}\n'
                f'new topping name: {changed_topping.name}\n'
                f'new topping stock: {changed_topping.stock}\n'
            )
            logging.info(log_message)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            topping_name_found = topping_crud.get_topping_by_name(changed_topping.name, db)
            if topping_name_found:
                url = request.url_for('get_topping', topping_id=topping_name_found.id)
                log_message = (
                    f'the given id {topping_id} does not match the given name {changed_topping.name}\n'
                    f'topping with name: {changed_topping.name} found with id {topping_name_found.id}\n'
                )
                logging.warning(log_message)
                return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
            else:
                updated_topping = topping_crud.create_topping(changed_topping, db)
                logging.info('new topping with name: {} created\n'.format(changed_topping.name))
                response.status_code = status.HTTP_201_CREATED
    else:
        logging.fatal('id {} does not exist\n'.format(topping_id))
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    return updated_topping


@router.get('/{topping_id}', response_model=ToppingSchema, tags=['topping'])
def get_topping(topping_id: uuid.UUID,
                response: Response,
                db: Session = Depends(get_db),
                ):
    topping = topping_crud.get_topping_by_id(topping_id, db)

    if not topping:
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    return topping


@router.delete('/{topping_id}', response_model=None, tags=['topping'])
def delete_topping(topping_id: uuid.UUID, db: Session = Depends(get_db)):
    topping = topping_crud.get_topping_by_id(topping_id, db)

    if not topping:
        logging.fatal('the topping with id: {} does not exist\n'.format(topping_id))
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    topping_crud.delete_topping_by_id(topping_id, db)
    logging.info('the topping with id: {} deleted\n'.format(topping_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
