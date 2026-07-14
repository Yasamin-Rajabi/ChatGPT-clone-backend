from rest_framework import permissions

class IsOwnerOnly(permissions.BasePermission):
    """
    اجازه دسترسی به منابع را تنها به صاحب اصلی آن منبع می‌دهد.
    """
    def harms_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False

class IsAssistantOwnerOrPublic(permissions.BasePermission):
    """
    دستیارها یا عمومی هستند یا باید متعلق به خود کاربر باشند تا بتواند آن‌ها را بخواند/ویرایش کند.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS and obj.is_public:
            return True
        return obj.user == request.user

class IsSuperuserOrReadOnly(permissions.BasePermission):
    """
    تغییر مدل‌های هوش مصنوعی فقط مختص Superuser است و کاربران عادی فقط دسترسی خواندن دارند.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_superuser