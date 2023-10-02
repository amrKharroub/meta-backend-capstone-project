from django.shortcuts import render
from rest_framework import generics
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth.models import User, Group
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import MenuItem, Cart, Order, OrderItem, Menu, Booking
from .serializers import (
    MenuItemSerializer,
    UserSerializer,
    CartSerializer,
    OrderSerializer,
    OrderItemSerializer,
    MenuSerializer,
    BookingSerializer,
)
from rest_framework import status
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from itertools import groupby
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from datetime import date


# Create your views here.
class MenuItemView(
    generics.ListCreateAPIView, generics.UpdateAPIView, generics.DestroyAPIView
):
    queryset = MenuItem.objects.prefetch_related("category")
    serializer_class = MenuItemSerializer
    ordering_fields = ["title", "price"]
    filterset_fields = ["price", "featured"]
    search_fields = ["title"]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAdminUser()]


class SingleMenuItemView(
    generics.RetrieveAPIView, generics.RetrieveUpdateDestroyAPIView
):
    queryset = MenuItem.objects.select_related("category")
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAdminUser()]


class ManagerView(generics.ListCreateAPIView):
    queryset = User.objects.filter(groups=Group.objects.get(name="Manager"))
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer

    def get(self, request):
        # returns all managers
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    def post(self, request):
        # assign a user to manager group
        username = request.data["username"]
        if username:
            user = get_object_or_404(User, username=username)
        else:
            return Response(
                {"message": "a username isn't provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        manager = Group.objects.get(name="Manager")
        manager.user_set.add(user)
        delveryCrew = Group.objects.get(name="Delivery Crew")
        delveryCrew.user_set.remove(user)
        message = "User {} is set as a manager".format(username)
        return Response({"message": message}, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def RemoveManagerView(request, pk):
    user = get_object_or_404(User, pk=pk)
    manager = Group.objects.get(name="Manager")
    manager.user_set.remove(user)
    return Response({"message": "user removed from manager"}, status=status.HTTP_200_OK)


class DeliveryCrewView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        queryset = User.objects.filter(Group.objects.get(name="Delivery Crew"))
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    def post(self, request):
        username = request.data["username"]
        if username:
            user = get_object_or_404(User, username=username)
        else:
            return Response(
                {"message": "username required"}, status=status.HTTP_400_BAD_REQUEST
            )
        delivery_crew = Group.objects.get(name="Delivary Crew")
        delivery_crew.user_set.add(user)
        message = "User {} is set as a manager".format(username)
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        manager = Group.objects.get(name="delivary crew")
        manager.user_set.remove(user)
        return Response(
            {"message": "user removed from delivery crew"}, status=status.HTTP_200_OK
        )


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user:
            queryset = Cart.objects.select_related("user").filter(user=user)
        serializer = CartSerializer(queryset, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    def post(self, request):
        menuitem = request.data["menuitem"]
        quantity = request.data["quantity"]
        try:
            unit_price = MenuItem.objects.get(pk=menuitem).price
        except ObjectDoesNotExist:
            return Response(
                {"message": "invalid menu item"}, status=status.HTTP_400_BAD_REQUEST
            )

        price = Decimal(quantity) * unit_price
        data = {
            "menuitem_id": menuitem,
            "quantity": quantity,
            "unit_price": unit_price,
            "price": price,
            "user_id": request.user.pk,
        }
        serializer = CartSerializer(data=data)
        if serializer.is_valid(raise_exception=False):
            serializer.save()
            message = "item is added to the cart"
            return Response({"message": message}, status=status.HTTP_201_CREATED)
        else:
            message = serializer.error_messages
            Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        if user:
            queryset = Cart.objects.select_related("user").filter(user=user)
            queryset.delete()
        return Response(
            {"message": "your cart is empty now!"}, status=status.HTTP_200_OK
        )


class OrderView(APIView):
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "date"]
    pagination_class = PageNumberPagination

    def get(self, request):
        user = request.user
        if user.groups.filter(name="Manager").exists():
            # Query to retrieve OrderItems along with the aggregated data
            order_items = OrderItem.objects.select_related("order").all()

            to_price = request.query_params.get("to_price")
            search = request.query_params.get("search")
            ordering = request.query_params.get("ordering")

            if to_price:
                order_items = order_items.filter(total__lte=to_price)
            if search:
                order_items = order_items.filter(status__icontains=search)
            if ordering:
                ordering_fields = ordering.split(",")
                order_items = order_items.order_by(*ordering_fields)
            paginator = (
                self.pagination_class()
            )  # Create an instance of the pagination class
            paginated_order_items = paginator.paginate_queryset(order_items, request)
            serializer = OrderItemSerializer(paginated_order_items, many=True)
            grouped_order_items = groupby(serializer.data, key=lambda x: x.pop("order"))

            # Create a list of dictionaries containing the grouped order_items
            grouped_orders_list = []
            for order, items in grouped_order_items:
                order_items_list = list(items)
                order_dict = {
                    "order": order,
                    "items": order_items_list,
                }
                grouped_orders_list.append(order_dict)
            return paginator.get_paginated_response(grouped_orders_list)
        elif user.groups.filter(name="Delivery Crew").exists():
            delivery_orders = Order.objects.filter(delivery_crew=user.pk)
            order_items = OrderItem.objects.filter(order__in=delivery_orders)
            serializer = OrderItemSerializer(order_items, many=True)
            paginated_data = self.pagination_class().paginate_queryset(
                serializer.data, request
            )
            return self.pagination_class().get_paginated_response(paginated_data)
        else:
            user_orders = Order.objects.filter(user=user.pk)
            order_items = OrderItem.objects.filter(order__in=user_orders)

            orderitem_ser = OrderItemSerializer(order_items, many=True)
            paginator = (
                self.pagination_class()
            )  # Create an instance of the pagination class
            paginated_order_items = paginator.paginate_queryset(
                orderitem_ser.data, request
            )

            # Return the paginated response
            return paginator.get_paginated_response(paginated_order_items)

    def post(self, request):
        cartview_endpoint = CartView().get(request=request)
        total = 0
        for item in cartview_endpoint.data:
            total += Decimal(item["price"])

        order_data = {
            "user_id": request.user.id,
            "delivery_crew": None,
            "total": total,
            "date": date.today(),
        }
        serializer = OrderSerializer(data=order_data)
        if serializer.is_valid():
            serializer.save()
            order_id = serializer.data.get("id")
            order_items = [{**x, "order_id": order_id} for x in cartview_endpoint.data]
            item_serializer = OrderItemSerializer(data=order_items, many=True)
            if item_serializer.is_valid():
                item_serializer.save()
                del_response = CartView().delete(request=request)
                if del_response.status_code == 200:
                    return Response(
                        {"message:": "items added to a new order"},
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        {"message": "error while deleting"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            else:
                return Response(item_serializer.errors)
        else:
            return Response(
                serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SingleOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        print(order.user)
        if order.user == request.user:
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        else:
            return Response(
                {"message": "unauthorized access"}, status=status.HTTP_403_FORBIDDEN
            )

    def delete(self, request, pk):
        user = request.user
        if user.groups.filter(name="Manager").exists():
            queryset = get_object_or_404(Order, pk=pk)
            queryset.delete()
        return Response(
            {"message": "your cart is empty now!"}, status=status.HTTP_200_OK
        )

    def put(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if not request.user.groups.filter(name="Manager").exists():
            return Response(
                {"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN
            )
        serialized_item = OrderSerializer(order, data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if request.user.groups.filter(name="Delivery Crew").exists():
            # delivery crew can only PATCH the order where the delivery crew is him/her.
            if order.delivery_crew != request.user:
                return Response(
                    {"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN
                )
            # only status of the order can be changed
            deliverystatus = request.data["status"]
            status_data = {"status": deliverystatus}
            serialized_item = OrderSerializer(order, data=status_data, partial=True)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)
        if request.user.groups.filter(name="Manager").exists():
            serialized_item = OrderSerializer(order, data=request.data, partial=True)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.data, status.HTTP_205_RESET_CONTENT)

        return Response(
            {"message": "You are not authorized."}, status.HTTP_403_FORBIDDEN
        )


def index(request):
    return render(request, "index.html", {})


class MenuItemsView(generics.ListCreateAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer


class SingleMenuItemView(generics.DestroyAPIView, generics.RetrieveUpdateAPIView):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer


class BookingViewSet(ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
