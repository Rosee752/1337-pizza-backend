from app.api.v1.endpoints.sauce.schemas import SauceSchema, SauceCreateSchema,SauceListItemSchema
from app.database.connection import SessionLocal
from fastapi import APIRouter, Depends, Request, Response, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import app.api.v1.endpoints.sauce.crud as sauce_crud
from typing import List
import logging
import uuid


HTTP_ERROR = 'Item not found'

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter()

@router.get('', response_model=List[SauceListItemSchema], tags=['sauce'])
def get_all_sauces(db: Session = Depends(get_db)):
    sauces = sauce_crud.get_all_sauces(db)
    return sauces


@router.post('', response_model=SauceSchema, status_code=status.HTTP_201_CREATED, tags=['sauce'])
def create_sauce(sauce: SauceCreateSchema,
                    request: Request,
                    db: Session = Depends(get_db)):
    sauce_found = sauce_crud.get_sauce_by_name(sauce.name, db)

    if sauce_found:
        url = request.url_for('get_sauce', sauce_id=sauce_found.id)
        logging.warning(f'the sauce with name: {sauce.name} already exists with id: {sauce_found.id}\n')
        return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

    new_sauce = sauce_crud.create_sauce(sauce, db)
    if new_sauce is not None:
        logging.info('the new sauce with name: {} created\n'.format(new_sauce.name))
    if new_sauce is None:
        logging.fatal('the sauce with name: {} could not be created\n'.format(sauce.name))
    return new_sauce


@router.put('/{sauce_id}', response_model=SauceSchema, tags=['sauce'])
def update_sauce(
        sauce_id: uuid.UUID,
        changed_sauce: SauceCreateSchema,
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
):
    sauce_found = sauce_crud.get_sauce_by_id(sauce_id, db)

    if sauce_found:
        if sauce_found.name == changed_sauce.name:
            sauce_crud.update_sauce(sauce_found, changed_sauce, db)
            log_message = (
                f'the sauce with name: {changed_sauce.name} was updated successfully:\n'
                f'new sauce description: {changed_sauce.description}\n'
                f'new sauce name: {changed_sauce.name}\n'
                f'new sauce stock: {changed_sauce.stock}\n'
            )
            logging.info(log_message)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            sauce_name_found = sauce_crud.get_sauce_by_name(changed_sauce.name, db)
            if sauce_name_found:
                url = request.url_for('get_sauce', sauce_id=sauce_name_found.id)
                log_message = (
                    f'the given id {sauce_id} does not match the given name {changed_sauce.name}\n'
                    f'sauce with name: {changed_sauce.name} found with id {sauce_name_found.id}\n'
                )
                logging.warning(log_message)
                return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
            else:
                updated_sauce = sauce_crud.create_sauce(changed_sauce, db)
                response.status_code = status.HTTP_201_CREATED
                logging.info('new sauce with name: {} created\n'.format(changed_sauce.name))
    else:
        logging.fatal('id {} does not exist\n'.format(sauce_id))
        raise HTTPException(status_code=404, detail=HTTP_ERROR)
    return updated_sauce


@router.get('/{sauce_id}', response_model=SauceSchema, tags=['sauce'])
def get_sauce(
        sauce_id: uuid.UUID,
        db: Session = Depends(get_db),
):
    sauce = sauce_crud.get_sauce_by_id(sauce_id, db)

    if not sauce:
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    return sauce


@router.delete('/{sauce_id}', response_model=None, tags=['sauce'])
def delete_sauce(
        sauce_id: uuid.UUID,
        db: Session = Depends(get_db)):
    sauce = sauce_crud.get_sauce_by_id(sauce_id, db)

    if not sauce:
        logging.fatal('the sauce with id: {} does not exist\n'.format(sauce_id))
        raise HTTPException(status_code=404, detail=HTTP_ERROR)

    sauce_crud.delete_sauce_by_id(sauce_id, db)
    logging.info('the sauce with id: {} deleted\n'.format(sauce_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)