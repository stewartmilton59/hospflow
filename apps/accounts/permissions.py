"""HospFlow Role-Based Access Control Permissions"""
from rest_framework import permissions


class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "doctor"


class IsNurse(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "nurse"


class IsPharmacist(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "pharmacist"


class IsReceptionist(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "receptionist"


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsClinicalStaff(permissions.BasePermission):
    """Doctors, Nurses, Lab Techs can access patient records"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["doctor", "nurse", "lab_tech"]


class IsBillingStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["accountant", "admin", "receptionist"]
