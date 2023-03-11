import uuid

from typing import List

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Security,
    BackgroundTasks,
    Request,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.database.connect import get_db
from src.schemas import (
    ContactModel,
    ContactDb,
    ResponseContact,
    TokenModel,
    RequestEmail,
    ResetPasswordModel,
    ForgotPasswordModel,
)
from src.repository import contacts as repository_contacts
from src.services.auth import auth_service
from src.services.email import send_email, send_email_reset_password_token

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post(
    "/signup", response_model=ResponseContact, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: ContactModel,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    exist_contact = await repository_contacts.search_by_mail(body.email, db)
    if exist_contact:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    contact = await repository_contacts.create_contact(body, db)
    background_tasks.add_task(
        send_email, contact.email, contact.first_name, request.base_url
    )
    return {
        "contact": contact,
        "detail": "User created successfully. Check you e-mail for confirmation.",
    }


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    contact = await repository_contacts.search_by_mail(body.username, db)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not contact.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )
    if not auth_service.verify_password(body.password, contact.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    # Generate JWT
    access_token = await auth_service.create_access_token(
        data={"sub": contact.email}, expires_delta=7200
    )
    refresh_token = await auth_service.create_refresh_token(data={"sub": contact.email})
    await repository_contacts.update_token(contact, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    contact = await repository_contacts.search_by_mail(email, db)
    if contact.refresh_token != token:
        await repository_contacts.update_token(contact, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_contacts.update_token(contact, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    email = await auth_service.get_email_from_token(token)
    contact = await repository_contacts.search_by_mail(email, db)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if contact.confirmed:
        return {"message": "Your e-mail is already confirmed."}
    await repository_contacts.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    contact = await repository_contacts.search_by_mail(body.email, db)

    if contact.confirmed:
        return {"message": "Your email is already confirmed."}
    if contact:
        background_tasks.add_task(
            send_email, contact.email, contact.first_name, request.base_url
        )
    return {"message": "Check your email for confirmation."}


@router.get(
    "/forgot_password",
    name="Forgot password",
    dependencies=[Depends(RateLimiter(times=2, seconds=5))],
)
async def forgot_password(
    email: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    contact = await repository_contacts.search_by_mail(email, db)
    if bool(contact) == False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not found or doesn't exist."
        )
    reset_password_token = uuid.uuid1()
    background_tasks.add_task(
        send_email_reset_password_token,
        reset_password_token,
        contact.email,
        contact.first_name,
    )

    contact.reset_password_token = reset_password_token
    db.commit()

    return {
        "message": f"Reset password token has been sent to your e-email.{reset_password_token}"
    }


@router.patch(
    "/reset_password",
    name="Reset password",
    response_model=ContactDb,
    dependencies=[
        Depends(RateLimiter(times=2, seconds=5)),
    ],
)
async def reset_password(
    body: ResetPasswordModel,
    db: Session = Depends(get_db),
):

    contact = await repository_contacts.search_by_mail(body.email, db)
    if bool(contact) == False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not found or doesn't exist."
        )

    if body.reset_password_token != contact.reset_password_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Password reset tokens doesn't match.",
        )

    if body.password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="New password is not match."
        )

    body.password = auth_service.get_password_hash(body.password)
    contact.password = body.password
    contact.reset_password_token = None
    db.commit()

    return contact
