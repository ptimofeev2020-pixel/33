from rest_framework.permissions import BasePermission


class IsModerator(BasePermission):
    message = 'Доступно только модераторам.'

    def has_permission(self, request, view):
        return request.user.groups.filter(name='moderators').exists()

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsOwner(BasePermission):
    message = 'Доступно только владельцу.'

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsProfileOwner(BasePermission):
    message = 'Редактировать можно только свой профиль.'

    def has_object_permission(self, request, view, obj):
        return obj == request.user
