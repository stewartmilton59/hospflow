"""Accounts URL Configuration"""
from django.urls import path
from .views import UserListCreateView, UserDetailView, LoginView, LogoutView

urlpatterns = [
    path("users/", UserListCreateView.as_view(), name="user-list"),
    path("users/<uuid:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
