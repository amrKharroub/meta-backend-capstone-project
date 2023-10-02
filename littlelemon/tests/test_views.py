from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from rest_framework import status
from restaurant.models import MenuItem, Menu
from restaurant.serializers import MenuItemSerializer
from django.urls import reverse


class MenuItemViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.admin = User.objects.create_user(
            username="adminuser", password="adminpassword"
        )
        self.admin_group = Group.objects.create(name="admin")
        self.admin.groups.add(self.admin_group)
        self.menu_item_data = {"title": "Test Item", "price": 10.99, "featured": True}
        self.menu_item = MenuItem.objects.create(**self.menu_item_data)

    def test_get_menu_items_authenticated(self):
        # Ensure an authenticated user can access the list of menu items.
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("menuitem-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_menu_items_unauthenticated(self):
        # Ensure an unauthenticated user cannot access the list of menu items.
        response = self.client.get(reverse("menuitem-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_menu_item_admin(self):
        # Ensure an admin user can create a new menu item.
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("menuitem-list"), self.menu_item_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_menu_item_authenticated(self):
        # Ensure a non-admin user cannot create a new menu item.
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("menuitem-list"), self.menu_item_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_menu_item_admin(self):
        # Ensure an admin user can update an existing menu item.
        self.client.force_authenticate(user=self.admin)
        updated_data = {"title": "Updated Item", "price": 15.99, "featured": False}
        response = self.client.put(
            reverse("menuitem-detail", kwargs={"pk": self.menu_item.id}), updated_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.menu_item.refresh_from_db()
        self.assertEqual(self.menu_item.title, updated_data["title"])

    def test_update_menu_item_authenticated(self):
        # Ensure a non-admin user cannot update an existing menu item.
        self.client.force_authenticate(user=self.user)
        updated_data = {"title": "Updated Item", "price": 15.99, "featured": False}
        response = self.client.put(
            reverse("menuitem-detail", kwargs={"pk": self.menu_item.id}), updated_data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_menu_item_admin(self):
        # Ensure an admin user can delete an existing menu item.
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            reverse("menuitem-detail", kwargs={"pk": self.menu_item.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_menu_item_authenticated(self):
        # Ensure a non-admin user cannot delete an existing menu item.
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            reverse("menuitem-detail", kwargs={"pk": self.menu_item.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MenuViewTest(TestCase):
    def setUp(self):
        Menu.objects.create(title="fsoulia", price=15.5, inventory=20)
        Menu.objects.create(title="Mashawe", price=65, inventory=60)

    def test_getall(self):
        response = self.client.get("/restaurant/menu/")

        self.assertEqual(
            response.status_code, 200
        )  # Check if the response is successful
        self.assertEqual(
            len(response.data), Menu.objects.count()
        )  # Check if the serialized data count matches the number of Menu instances

        # You can add more specific assertions comparing the serialized data with your Menu instances
        # For example:
        self.assertEqual(response.data[0]["title"], "fsoulia")
        self.assertEqual(float(response.data[0]["price"]), 15.5)
        self.assertEqual(response.data[0]["inventory"], 20)

        self.assertEqual(response.data[1]["title"], "Mashawe")
        self.assertEqual(float(response.data[1]["price"]), 65.0)
        self.assertEqual(response.data[1]["inventory"], 60)
