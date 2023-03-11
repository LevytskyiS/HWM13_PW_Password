from typing import List
from fastapi import Depends, HTTPException, status, Request

from src.database.models import Contact, Roles
from src.routes.auth import auth_service


class RolesChecker:
    def __init__(self, allowed_roles: List[Roles]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_contact: Contact = Depends(auth_service.get_current_user),
    ):
        if current_contact.roles not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Operation forbidden"
            )
