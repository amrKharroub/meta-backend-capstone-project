from rest_framework import serializers
from .models import Menu, Booking, MenuItem, Category, Cart, Order, OrderItem
from django.contrib.auth.models import User, Group


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "slug", "title"]


class MenuItemSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        allow_null=False,
        write_only=True,
    )
    category_title = serializers.StringRelatedField(source="category", read_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "title", "price", "featured", "category", "category_title"]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(read_only=True, many=True)
    email = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "username", "groups"]


class CartSerializer(serializers.ModelSerializer):
    menuitem = serializers.StringRelatedField(read_only=True)
    menuitem_id = serializers.IntegerField()
    user = serializers.SerializerMethodField(method_name="get_username", read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "user",
            "user_id",
            "menuitem",
            "menuitem_id",
            "quantity",
            "unit_price",
            "price",
        ]

    def get_username(self, cart):
        return cart.user.username


class OrderSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user_id",
            "delivery_crew",
            "status",
            "total",
            "date",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(write_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)
    order = OrderSerializer()
    menuitem = MenuItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "order",
            "order_id",
            "menuitem",
            "menuitem_id",
            "quantity",
            "unit_price",
            "price",
        ]


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = "__all__"


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"
