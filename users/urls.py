from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import (
    UserViewSet,
    UserRegisterAPIView,
    PaymentListAPIView,
    PaymentCreateAPIView,
    PaymentStatusAPIView,
)

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('register/', UserRegisterAPIView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(permission_classes=(AllowAny,)), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(permission_classes=(AllowAny,)), name='token_refresh'),
    path('payments/', PaymentListAPIView.as_view(), name='payment_list'),
    path('payments/create/', PaymentCreateAPIView.as_view(), name='payment_create'),
    path('payments/<int:pk>/status/', PaymentStatusAPIView.as_view(), name='payment_status'),
]

urlpatterns += router.urls
