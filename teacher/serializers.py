from rest_framework import serializers
from schoolbus.models import Bus, BusPoint, Route
from rest_framework import serializers
from admins.models import User
from student.models import Student, StudentBusService
from teacher.models import ClassRoom, Teacher
from student.models import Payment
from decimal import Decimal
from django.db.models import Sum

class TeacherLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id','name','gender']

class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Teacher
        fields = ('id', 'user', 'pen_no', 'photo')

    def update(self, instance, validated_data):
        # Update nested user data
        user_data = validated_data.pop('user', None)
        if user_data:
            user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()

        instance.pen_no = validated_data.get('pen_no', instance.pen_no)
        instance.photo = validated_data.get('photo', instance.photo)
        instance.save()
        return instance


class BusPointChoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = BusPoint
        fields = ["id", "route", "name", "fee"]


class RouteChoiceSerializer(serializers.ModelSerializer):
    bus_points = BusPointChoiceSerializer(many=True,write_only=True)
    class Meta:
        model = Route
        fields = ["id", "bus", "route_no", "from_location", "to_location","bus_points"]


class BusListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bus
        fields = ["id", "bus_no", "driver_name", "plate_number", "capacity"]


class StudentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "gender"]


class UserStudentSerializer(serializers.ModelSerializer):
    user = StudentListSerializer(read_only=True)

    class Meta:
        model = Student
        fields = ["id", "admission_no", "user"]


class StudentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True) 
    user = StudentListSerializer()

    class Meta:
        model = Student
        fields = ("id","admission_no", "user", "classRoom")
        read_only_fields = ("admission_no",)


class BusStudentSerializer(serializers.ModelSerializer):
    student = UserStudentSerializer()
    bus = BusListSerializer()
    route = RouteChoiceSerializer()
    bus_point = BusPointChoiceSerializer()

    class Meta:
        model = StudentBusService
        fields = ["student", "bus", "route", "bus_point"]


class PaymentSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    balance_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Payment
        fields = ('id', 'student', 'amount', 'paid_amount', 'balance_amount', 'created_at')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be positive.")
        return value

    def validate(self, data):
        student = data['student']
        bus_service = getattr(student, 'bus_service', None)

        if not bus_service:
            raise serializers.ValidationError("Student does not have a bus service assigned.")

        total_paid = Payment.objects.filter(student=student).aggregate(total=Sum('amount'))['total'] or 0
        annual_fees = bus_service.annual_fees  # Keep the annual fees constant

        if total_paid + data['amount'] > annual_fees:
            raise serializers.ValidationError("Payment amount exceeds the remaining total fees.")

        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        bus_service = instance.student.bus_service

        # Calculate total paid amount including this instance
        total_paid = Payment.objects.filter(student=instance.student).aggregate(total=Sum('amount'))['total'] or 0
        annual_fees = bus_service.annual_fees  # Ensure this is correctly fetched
        balance_amount = annual_fees - total_paid

        # Set paid_amount and balance_amount in the representation
        representation['paid_amount'] = total_paid
        representation['balance_amount'] = balance_amount

        return representation
    
    def update(self, instance, validated_data):
        instance.amount = validated_data.get('amount', instance.amount)
        instance.save()

        total_paid = Payment.objects.filter(student=instance.student).aggregate(total=Sum('amount'))['total'] or 0
        annual_fees = instance.student.bus_service.annual_fees
        instance.paid_amount = total_paid
        instance.balance_amount = annual_fees - total_paid
        instance.save() 

        return instance


class PaymentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

