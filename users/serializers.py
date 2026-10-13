from rest_framework import serializers

from users.models import User, Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'payment_date', 'paid_course', 'paid_lesson', 'amount', 'payment_method',
            'stripe_product_id', 'stripe_price_id', 'session_id', 'link', 'status',
        ]
        read_only_fields = [
            'user', 'amount', 'payment_date', 'stripe_product_id', 'stripe_price_id', 'session_id', 'link', 'status',
        ]


class PaymentCreateSerializer(serializers.Serializer):
    course_id = serializers.IntegerField(help_text='ID оплачиваемого курса')


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'phone', 'city']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'city', 'avatar', 'payments']
        read_only_fields = ['email']


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'phone', 'city', 'avatar']
