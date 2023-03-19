from datetime import date

import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

import src
from src.database.models import Contact
from src.schemas import ContactModel, UpdateContactRoleModel
from src.repository.contacts import (
    get_contacts,
    get_contact,
    create_contact,
    check_exist_mail,
    update_token,
    update_contact,
    change_contact_role,
    delete_contact,
    search_first_name,
    search_last_name,
    search_by_mail,
    search_by_mail_ilike_method,
    confirmed_email,
    update_avatar,
)

# python -m unittest -v tests/test_unit_repository_contacts.py


class TestContacts(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.contact = Contact(
            first_name="Mike",
            last_name="Black",
            email="testmike@test.com",
            phone=777,
            birthday=date.today(),
            password="qweasd",
        )

    async def test_get_contact(self):
        contact = self.contact
        self.session.query().filter_by(id=contact.id).first.return_value = contact
        result = await get_contact(contact_id=1, db=self.session)
        self.assertEqual(result, contact)

    async def test_get_contacts(self):
        contacts = [Contact(), Contact, Contact()]
        self.session.query().all.return_value = contacts
        result = await get_contacts(db=self.session)
        self.assertEqual(result, contacts)

    async def test_create_contact(self):
        body = ContactModel(
            first_name="Nick",
            last_name="White",
            email="testnick@test.com",
            phone=555,
            birthday=date.today(),
            password="qweasd",
            refresh_token="abcd",
        )
        result = await create_contact(body=body, db=self.session)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)

    def test_check_exist_mail(self):
        body = ContactModel(
            first_name="Nick",
            last_name="White",
            email="testnick@test.com",
            phone=555,
            birthday=date.today(),
            password="qweasd",
        )
        self.session.query().filter_by(email=body.email).first.return_value = body
        result = check_exist_mail(body=body, db=self.session)
        self.assertEqual(result.email, body.email)

    async def test_update_token(self):
        token = "12345"
        contact = Contact()
        contact_refresh_token_before_update = contact.refresh_token
        result = await update_token(contact=contact, token=token, db=self.session)
        self.assertNotEqual(contact.refresh_token, contact_refresh_token_before_update)

    async def test_update_contact(self):
        body = ContactModel(
            first_name="Nick",
            last_name="White",
            email="testnick@test.com",
            phone=555,
            birthday=date.today(),
            password="qweasd",
        )
        contact = ContactModel(
            first_name="Mike",
            last_name="Black",
            email="testmike@test.com",
            phone=777,
            birthday=date.today(),
            password="qweasd",
        )
        self.session.query().filter_by(id=1).first.return_value = contact
        self.session.commit.return_value = None
        result = await update_contact(body=body, contact_id=1, db=self.session)
        self.assertEqual(result, contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)

    async def test_change_contact_role(self):
        body = UpdateContactRoleModel(roles="admin")
        contact = Contact()
        self.session.query().filter_by(id=1).first.return_value = contact
        result = await change_contact_role(
            body=body,
            contact_id=contact.id,
            db=self.session,
        )
        self.assertEqual(result.roles, contact.roles)

    async def test_delete_contact(self):
        contact = Contact()
        self.session.query().filter_by().first.return_value = contact
        result = await delete_contact(contact_id=contact.id, db=self.session)
        self.assertEqual(result, contact)

    async def test_search_first_name(self):
        inquiry = "Kim"
        contacts = [Contact(), Contact()]
        self.session.query().filter_by(first_name=inquiry).all.return_value = contacts
        result = await search_first_name(inquiry=inquiry, db=self.session)
        self.assertEqual(result, contacts)

    async def test_search_last_name(self):
        inquiry = "White"
        contacts = [Contact(), Contact()]
        self.session.query().filter_by(last_name=inquiry).all.return_value = contacts
        result = await search_first_name(inquiry=inquiry, db=self.session)
        self.assertEqual(result, contacts)

    async def test_search_by_mail(self):
        inquiry = "test1@test.com"
        contacts = [Contact(), Contact()]
        self.session.query().filter_by(email=inquiry).all.return_value = contacts
        result = await search_first_name(inquiry=inquiry, db=self.session)
        self.assertEqual(result, contacts)

    async def test_search_by_mail_ilike_method(self):
        inquiry = "TEST1@test.com"
        contacts = [Contact(email="test1@test.com"), Contact(email="teST1@test.com")]
        self.session.query().filter(
            Contact.email.ilike(f"%{inquiry}%")
        ).all.return_value = contacts
        result = await search_by_mail_ilike_method(inquiry=inquiry, db=self.session)
        self.assertEqual(result, contacts)

    async def test_confirmed_email(self):
        with patch.object(src.repository.contacts, "search_by_mail") as search_mock:
            search_mock.return_value = Contact(
                first_name="Mike",
                last_name="Black",
                email="testmike@test.com",
                phone=777,
                birthday=date.today(),
                password="qweasd",
                confirmed=None,
            )
            contact = search_mock.return_value
            result = await confirmed_email(email=contact.email, db=self.session)
            self.assertTrue(contact.confirmed)

    async def test_update_avatar(self):
        with patch.object(src.repository.contacts, "search_by_mail") as search_mock:
            search_mock.return_value = Contact(
                first_name="Mike",
                last_name="Black",
                email="testmike@test.com",
                phone=777,
                birthday=date.today(),
                password="qweasd",
                confirmed=None,
            )
            new_avatar = "new_avatar"
            result = await update_avatar(
                email=search_mock.return_value.email, url=new_avatar, db=self.session
            )
            self.assertEqual(search_mock.return_value.avatar, new_avatar)


if __name__ == "__main__":
    unittest.main()
