from rest_framework.throttling import ScopedRateThrottle

class SubscriptionRateThrottle(ScopedRateThrottle):
    """
    اگر کاربر رایگان باشد، محدودیت نرخ اعمال می‌شود؛ اما برای کاربران ویژه بی اثر است.
    """
    def allow_request(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.subscription_type == 'PREMIUM':
                return True # کاربران ویژه بدون محدودیت
        return super().allow_request(request, view)