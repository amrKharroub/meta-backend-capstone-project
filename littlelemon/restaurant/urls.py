from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("menu/", views.MenuItemsView.as_view(), name="api-menu"),
    path("menu/<int:pk>", views.SingleMenuItemView.as_view(), name="api-menu-item"),
    path("api-token-auth/", obtain_auth_token, name="api-get-token"),
    path("menu-items", views.MenuItemView.as_view()),
    path("menu-items/<int:pk>", views.SingleMenuItemView.as_view()),
    path("groups/manager/users", views.ManagerView.as_view()),
    path("groups/manager/users/<int:pk>", views.RemoveManagerView),
    path(
        "groups/delivery-crew/users",
        views.DeliveryCrewView.as_view(),
        name="dc_listcreate",
    ),
    path(
        "groups/delivery-crew/users/<int:pk>",
        views.DeliveryCrewView.as_view(),
        name="dc_delete",
    ),
    path("cart/menu-items", views.CartView.as_view()),
    path("orders", views.OrderView.as_view()),
    path("orders/<int:pk>", views.SingleOrderView.as_view()),
]
