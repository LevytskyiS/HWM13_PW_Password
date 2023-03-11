import cloudinary
import cloudinary.uploader
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.database.connect import get_db
from src.database.models import Contact, Roles
from src.schemas import ContactModel, ResponseContact, ContactDb, UpdateContactRoleModel
from src.repository import contacts as repository_contacts
from src.services.auth import auth_service
from src.services.roles import RolesChecker
from src.conf.config import settings

router = APIRouter(prefix="/contacts", tags=["contacts"])

allowed_get_contacts = RolesChecker([Roles.admin, Roles.moderator, Roles.user])
allowed_create_contact = RolesChecker([Roles.admin, Roles.moderator, Roles.user])
allowed_get_contact_by_id = RolesChecker([Roles.admin, Roles.moderator, Roles.user])
allowed_update_contact = RolesChecker([Roles.admin, Roles.moderator])
allowed_change_contact_role = RolesChecker([Roles.admin, Roles.moderator])
allowed_delete_contact = RolesChecker([Roles.admin])
allowed_search_first_name = RolesChecker([Roles.admin, Roles.moderator, Roles.user])
allowed_search_last_name = RolesChecker([Roles.admin, Roles.moderator, Roles.user])
allowed_search_email = RolesChecker([Roles.admin, Roles.moderator, Roles.user])
allowed_search = RolesChecker([Roles.admin, Roles.moderator, Roles.user])


@router.post(
    "/create",
    response_model=ResponseContact,
    name="Create contact",
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(allowed_create_contact),
        Depends(RateLimiter(times=2, seconds=5)),
    ],
)
async def create_contact(body: ContactModel, db: Session = Depends(get_db)):
    check_mail = repository_contacts.check_exist_mail(body, db)
    if check_mail:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Such mail already registered",
        )
    body.password = auth_service.get_password_hash(body.password)
    contact = await repository_contacts.create_contact(body, db)
    return {"contact": contact, "detail": "Contact was created"}


@router.get(
    "/",
    response_model=List[ContactDb],
    name="All contacts",
    dependencies=[
        Depends(allowed_get_contacts),
        Depends(RateLimiter(times=2, seconds=5)),
    ],
)
async def get_contacts(
    db: Session = Depends(get_db),
    current_contact: Contact = Depends(auth_service.get_current_user),
):
    contacts = await repository_contacts.get_contacts(db)
    return contacts


@router.get(
    "/{contact_id}",
    response_model=ContactDb,
    name="Get contact",
    dependencies=[
        Depends(allowed_get_contact_by_id),
        Depends(RateLimiter(times=2, seconds=5)),
    ],
)
async def get_contact_by_id(
    contact_id: int = Path(1, ge=1),
    db: Session = Depends(get_db),
    current_contact: Contact = Depends(auth_service.get_current_user),
):
    contact = await repository_contacts.get_contact(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return contact


@router.put(
    "/update/{contact_id}",
    response_model=ContactDb,
    name="Change contact",
    dependencies=[
        Depends(allowed_update_contact),
        Depends(RateLimiter(times=2, seconds=5)),
    ],
)
async def update_contact(
    body: ContactModel,
    contact_id: int = Path(1, ge=1),
    db: Session = Depends(get_db),
    current_contact: Contact = Depends(auth_service.get_current_user),
):
    contact = await repository_contacts.update_contact(body, contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contact


@router.patch(
    "/change_role/{contact_id}",
    response_model=ContactDb,
    name="Change role",
    dependencies=[
        Depends(allowed_change_contact_role),
        Depends(RateLimiter(times=2, seconds=5)),
    ],
)
async def change_contact_role(
    body: UpdateContactRoleModel,
    contact_id: int = Path(1, ge=1),
    db: Session = Depends(get_db),
    current_contact: Contact = Depends(auth_service.get_current_user),
):
    contact = await repository_contacts.change_contact_role(body, contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contact


@router.delete(
    "/delete/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    name="Delete contact",
    dependencies=[
        Depends(allowed_delete_contact),
        Depends(RateLimiter(times=2, seconds=5)),
    ],
)
async def delete_contact(
    contact_id: int = Path(1, ge=1),
    db: Session = Depends(get_db),
    current_contact: Contact = Depends(auth_service.get_current_user),
):
    contact = await repository_contacts.delete_contact(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contact


@router.get(
    "/search_first_name/{inquiry}",
    response_model=List[ContactDb],
    name="Search by first name",
    dependencies=[
        Depends(allowed_search_first_name),
        Depends(RateLimiter(times=2, seconds=5)),
    ],
)
async def search_first_name(
    inquiry: str = Path(min_length=1),
    db: Session = Depends(get_db),
    current_contact: Contact = Depends(auth_service.get_current_user),
):
    contacts = await repository_contacts.search_first_name(inquiry, db)
    if bool(contacts) == False:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contacts


@router.get(
    "/search_last_name/{inquiry}",
    response_model=List[ContactDb],
    name="Search by last name",
    dependencies=[
        Depends(allowed_search_last_name),
        Depends(RateLimiter(times=2, seconds=5)),
    ],
)
async def search_last_name(
    inquiry: str = Path(min_length=1),
    db: Session = Depends(get_db),
    current_contact: Contact = Depends(auth_service.get_current_user),
):
    contacts = await repository_contacts.search_last_name(inquiry, db)
    if bool(contacts) == False:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contacts


@router.get(
    "/search_mail/{inquiry}",
    response_model=ContactDb,
    name="Search by email",
    dependencies=[
        Depends(allowed_search_email),
        Depends(RateLimiter(times=2, seconds=5)),
    ],
)
async def search_email(
    inquiry: str = Path(min_length=1),
    db: Session = Depends(get_db),
    current_contact: Contact = Depends(auth_service.get_current_user),
):
    contacts = await repository_contacts.search_by_mail(inquiry, db)
    if bool(contacts) == False:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contacts


@router.get(
    "/search/{inquiry}",
    response_model=List[ContactDb],
    name="Search",
    dependencies=[Depends(allowed_search), Depends(RateLimiter(times=2, seconds=5))],
)
async def search(
    inquiry: str = Path(min_length=1),
    db: Session = Depends(get_db),
    current_contact: Contact = Depends(auth_service.get_current_user),
):
    contacts = await repository_contacts.search_by_mail_ilike_method(inquiry, db)
    if bool(contacts) == False:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contacts


@router.get("/me/", response_model=ContactDb)
async def read_users_me(
    current_user: ContactModel = Depends(auth_service.get_current_user),
):
    return current_user


@router.patch(
    "/avatar",
    response_model=ContactDb,
    name="Change avatar",
    dependencies=[
        Depends(RateLimiter(times=2, seconds=5)),
    ],
)
async def change_contact_avatar(
    file: UploadFile = File(),
    db: Session = Depends(get_db),
    current_contact: Contact = Depends(auth_service.get_current_user),
):
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_secret,
        secure=True,
    )
    cloudinary.uploader.upload(
        file.file,
        public_id=f"HWM13/{current_contact.first_name}{current_contact.id}",
        overwrite=True,
    )
    src_url = cloudinary.CloudinaryImage(
        f"HWM13/{current_contact.first_name}"
    ).build_url(width=250, height=250, crop="fill")

    contact = await repository_contacts.update_avatar(
        current_contact.email, src_url, db
    )

    return contact
