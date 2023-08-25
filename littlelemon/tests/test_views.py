from django.test import TestCase
from restaurant.models import Menu


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
