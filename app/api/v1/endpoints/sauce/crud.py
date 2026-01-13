import uuid

from sqlalchemy.orm import Session

from app.api.v1.endpoints.sauce.schemas import SauceCreateSchema
from app.database.models import Sauce


def create_sauce(schema: SauceCreateSchema, db: Session):
    entity = Sauce(**schema.model_dump())
    db.add(entity)
    db.commit()

    return entity


def get_sauce_by_id(sauce_id: uuid.UUID, db: Session):
    entity = db.query(Sauce).filter(Sauce.id == sauce_id).first()
    return entity


def get_sauce_by_name(sauce_name: str, db: Session):
    entity = db.query(Sauce).filter(Sauce.name == sauce_name).first()
    return entity


def get_all_sauces(db: Session):
    return db.query(Sauce).all()


def update_sauce(sauce: Sauce, changed_sauce: SauceCreateSchema, db: Session):
    for key, value in changed_sauce.model_dump().items():
        setattr(sauce, key, value)

    db.commit()
    db.refresh(sauce)

    return sauce


def delete_sauce_by_id(sauce_id: uuid.UUID, db: Session):
    entity = get_sauce_by_id(sauce_id, db)
    if entity:
        db.delete(entity)
        db.commit()
