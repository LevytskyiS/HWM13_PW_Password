from fastapi import Depends
from libgravatar import Gravatar

from sqlalchemy.orm import Session
from src.database.connect import get_db
from src.database.models import Contact
from src.schemas import ContactModel, UpdateContactRoleModel


async def get_contacts(db: Session):
    contacts = db.query(Contact).all()
    return contacts


async def get_contact(contact_id: int, db: Session):
    contact = db.query(Contact).filter_by(id=contact_id).first()
    return contact


async def create_contact(body: ContactModel, db: Session = Depends(get_db)):
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    contact = Contact(**body.dict(), avatar=avatar)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def check_exist_mail(body: ContactModel, db: Session = Depends(get_db)):
    check_mail = db.query(Contact).filter_by(email=body.email).first()
    return check_mail


async def update_token(contact: Contact, token: str | None, db: Session) -> None:
    contact.refresh_token = token
    db.commit()


async def update_contact(
    body: ContactModel, contact_id: int, db: Session = Depends(get_db)
):
    contact = db.query(Contact).filter_by(id=contact_id).first()
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone = body.phone
        contact.birthday = body.birthday
        db.commit()
    return contact


async def change_contact_role(
    body: UpdateContactRoleModel, contact_id: int, db: Session = Depends(get_db)
):
    contact = db.query(Contact).filter_by(id=contact_id).first()
    if contact:
        contact.roles = body.roles
        db.commit()
    return contact


async def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter_by(id=contact_id).first()
    if contact:
        db.delete(contact)
        db.commit()
    return contact


async def search_first_name(inquiry: str, db: Session = Depends(get_db)):
    contacts = db.query(Contact).filter_by(first_name=inquiry).all()
    return contacts


async def search_last_name(inquiry: str, db: Session = Depends(get_db)):
    contacts = db.query(Contact).filter_by(last_name=inquiry).all()
    return contacts


async def search_by_mail(inquiry: str, db: Session = Depends(get_db)):
    contacts = db.query(Contact).filter_by(email=inquiry).first()
    return contacts


async def search_by_mail_ilike_method(inquiry: str, db: Session = Depends(get_db)):
    contacts = db.query(Contact).filter(Contact.email.ilike(f"%{inquiry}%")).all()
    return contacts


async def confirmed_email(email: str, db: Session):
    user = await search_by_mail(email, db)
    user.confirmed = True
    db.commit()


async def update_avatar(email: str, url: str, db) -> Contact:
    contact = await search_by_mail(email, db)
    contact.avatar = url
    db.commit()
    return contact
