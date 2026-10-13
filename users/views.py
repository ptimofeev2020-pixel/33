from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.models import User, Payment
from users.permissions import IsProfileOwner
from lms.models import Course
from users.serializers import (
    UserSerializer,
    UserPublicSerializer,
    UserRegisterSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
)
from users.services import (
    StripeServiceError,
    create_stripe_product,
    create_stripe_price,
    create_stripe_session,
    retrieve_stripe_session,
)


class UserRegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserSerializer
        if self.action == 'retrieve' and self.get_object() != self.request.user:
            return UserPublicSerializer
        if self.action == 'list':
            return UserPublicSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            permission_classes = [IsAuthenticated, IsProfileOwner]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class PaymentListAPIView(generics.ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['paid_course', 'paid_lesson', 'payment_method']
    ordering_fields = ['payment_date']
    ordering = ['payment_date']


class PaymentCreateAPIView(APIView):
    @extend_schema(
        summary='Оплата курса через Stripe',
        description='Создаёт продукт, цену (в копейках) и сессию оплаты в Stripe, сохраняет платёж '
                    'и возвращает ссылку на оплату.',
        request=PaymentCreateSerializer,
        responses={
            201: PaymentSerializer,
            400: OpenApiResponse(description='Некорректные данные или курс без цены'),
            404: OpenApiResponse(description='Курс не найден'),
            502: OpenApiResponse(description='Ошибка платёжного сервиса Stripe'),
        },
        tags=['payments'],
    )
    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = get_object_or_404(Course, pk=serializer.validated_data['course_id'])
        if not course.price or course.price <= 0:
            return Response({'error': 'У курса не указана цена.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product_id = create_stripe_product(course.name)
            price_id = create_stripe_price(product_id, course.price)
            session_id, link = create_stripe_session(price_id)
        except StripeServiceError as error:
            return Response({'error': str(error)}, status=status.HTTP_502_BAD_GATEWAY)

        payment = Payment.objects.create(
            user=request.user,
            paid_course=course,
            amount=course.price,
            payment_method=Payment.METHOD_TRANSFER,
            stripe_product_id=product_id,
            stripe_price_id=price_id,
            session_id=session_id,
            link=link,
            status='open',
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentStatusAPIView(APIView):
    @extend_schema(
        summary='Проверка статуса оплаты',
        description='Получает сессию из Stripe по session_id платежа и обновляет статус платежа.',
        responses={
            200: PaymentSerializer,
            404: OpenApiResponse(description='Платёж не найден'),
            502: OpenApiResponse(description='Ошибка платёжного сервиса Stripe'),
        },
        tags=['payments'],
    )
    def get(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk, user=request.user)
        if not payment.session_id:
            return Response({'error': 'У платежа нет сессии Stripe.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            session_status, payment_status = retrieve_stripe_session(payment.session_id)
        except StripeServiceError as error:
            return Response({'error': str(error)}, status=status.HTTP_502_BAD_GATEWAY)
        payment.status = payment_status or session_status
        payment.save(update_fields=['status'])
        return Response(PaymentSerializer(payment).data)
