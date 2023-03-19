from fastapi import Depends
from libgravatar import Gravatar

from sqlalchemy.orm import Session
from src.database.connect import get_db
from src.database.models import Contact
from src.schemas import ContactModel, UpdateContactRoleModel


async def get_contacts(db: Session):
    """
    Retrieves a list of all contacts in database.

    :param db: The database session
    :type db: Session
    :return: A list all contacts
    :rtype: List[Contact]
    """
    contacts = db.query(Contact).all()
    return contacts


async def get_contact(contact_id: int, db: Session):
    """
    Retrieves a single note with the specified ID for a specific contact.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param db: The database session
    :type db: Session
    :return: The contact with the specified ID, or None if it doesn't exist.
    :rtype: Contact
    """
    contact = db.query(Contact).filter_by(id=contact_id).first()
    return contact


async def create_contact(body: ContactModel, db: Session = Depends(get_db)):
    """
    Creates a new contact.

    :param body: The data for the contact to create.
    :type body: ContactModel
    :param db: The database session.
    :type db: Session
    :return: The newly created contact
    :rtype: Contact
    """
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
    """
    Retrieves a contact with a specific email.

    :param body: The contact data to be checked.
    :type body: ContactModel
    :param db: The database session
    :type db: Session
    :return: Contact, if it's email is in database, or None if the email wasn't found.
    :rtype: Contact
    """
    check_mail = db.query(Contact).filter_by(email=body.email).first()
    return check_mail


async def update_token(contact: Contact, token: str | None, db: Session) -> None:
    """
    Updates contact's token if is invalid.

    :param contact: The data of the existing contact.
    :type contact: Contact
    :param token: New refresh token to be put in the system.
    :type token: str | None
    :param db: The database session.
    :type db: Session
    """
    contact.refresh_token = token
    db.commit()


async def update_contact(
    body: ContactModel, contact_id: int, db: Session = Depends(get_db)
):
    """
    Updates data of a contact by specific ID.

    :param body: The new data to be saved instead of an existing one.
    :type body: ContactModel
    :param contact_id: A specific contact ID.
    :type contact_id: int
    :param db: The database session.
    :type db: Session
    :return: Updated contact.
    :rtype: Contact
    """
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
    """
    Changes contact's role.

    :param body: A specific data to be used as an update.
    :type body: UpdateContactRoleModel
    :param contact_id: A contact's specific ID.
    :type contact_id: int
    :param db: The database session.
    :type db: Session, optional
    :return: A contact with a new role.
    :rtype: Contact
    """
    contact = db.query(Contact).filter_by(id=contact_id).first()
    if contact:
        contact.roles = body.roles
        db.commit()
    return contact


async def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Deletes a specific contact.

    :param contact_id: A specific ID peremetr of the existing contact.
    :type contact_id: int
    :param db: The database session.
    :type db: Session
    :return: Deleted contact.
    :rtype: Contact
    """
    contact = db.query(Contact).filter_by(id=contact_id).first()
    if contact:
        db.delete(contact)
        db.commit()
    return contact


async def search_first_name(inquiry: str, db: Session = Depends(get_db)):
    """
    Retrieves a list of contacts which are found by first name.

    :param inquiry: User's input to be searched.
    :type inquiry: str
    :param db: The database session
    :type db: Session
    :return: A list of all contact which are found by first name.
    :rtype: List[Contact]
    """
    contacts = db.query(Contact).filter_by(first_name=inquiry).all()
    return contacts


async def search_last_name(inquiry: str, db: Session = Depends(get_db)):
    """
    Retrieves a list of contacts which are found by last name.

    :param inquiry: User's input to be searched.
    :type inquiry: str
    :param db: The database session
    :type db: Session, optional
    :return: A list of all contact which are found by last name.
    :rtype: List[Contact]
    """
    contacts = db.query(Contact).filter_by(last_name=inquiry).all()
    return contacts


async def search_by_mail(inquiry: str, db: Session = Depends(get_db)):
    """
    Returns a single contact which was found by specific e-mail.

    :param inquiry: User's input to be searched.
    :type inquiry: str
    :param db: The database session.
    :type db: Session
    :return: A contact which is found by specific e-mail.
    :rtype: Contact
    """
    contacts = db.query(Contact).filter_by(email=inquiry).first()
    return contacts


async def search_by_mail_ilike_method(inquiry: str, db: Session = Depends(get_db)):
    """
    Returns a list of contacts by matches founded in all contacts' e-mails.

    :param inquiry: User's input to be searched.
    :type inquiry: str
    :param db: The database session.
    :type db: Session
    :return: A list of contacts by matches founded in all contacts' e-mails.
    :rtype: List[Contact]
    """
    contacts = db.query(Contact).filter(Contact.email.ilike(f"%{inquiry}%")).all()
    return contacts


async def confirmed_email(email: str, db: Session):
    """
    Confirms contact's e-mail.

    :param email: Contact's email to be confirmed.
    :type email: str
    :param db: The database session.
    :type db: Session
    """
    user = await search_by_mail(email, db)
    user.confirmed = True
    db.commit()


async def update_avatar(email: str, url: str, db: Session) -> Contact:
    """
    Updates contact's avatar.

    :param email: Contact's e-mail.
    :type email: str
    :param url: URL to a new avatar.
    :type url: str
    :param db: The database session
    :type db: Session
    :return: A contact with it's new avatar.
    :rtype: Contact
    """
    contact = await search_by_mail(email, db)
    contact.avatar = url
    db.commit()
    return contact
