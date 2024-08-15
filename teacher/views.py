from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets
from teacher.serializers import (
    TeacherLoginSerializer,
    BusStudentSerializer,
    StudentSerializer,
    PaymentSerializer,
    PaymentDetailSerializer,
    TeacherProfileSerializer
)
from admins.utilities.permission import IsAdminUser
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
from admins.utilities.token import get_tokens_for_user
from rest_framework.permissions import IsAuthenticated, AllowAny
import logging
from admins.models import User
from .models import Teacher, ClassRoomTeacher, ClassRoom
from student.models import Student, StudentBusService
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from admins.utilities.permission import IsTeacher
from rest_framework.decorators import action
from student.models import Payment
from rest_framework.generics import CreateAPIView
from django.db.models import Sum
from admins.utilities.permission import IsAdminOrTeacher


class TeacherProfileViewset(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Teacher.objects.filter(user=user)

    def retrieve(self, request, *args, **kwargs):
        teacher = self.get_queryset().first()
        if teacher:
            serializer = self.get_serializer(teacher)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        teacher = self.get_queryset().first()
        if not teacher:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(teacher, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


    
class StudentViewset(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsTeacher]

    def get_classroom(self, user):
        try:
            classroom_teacher = ClassRoomTeacher.objects.get(
                teacher__user=user, is_class_teacher=True
            )
            return classroom_teacher.classroom
        except ClassRoomTeacher.DoesNotExist:
            return None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not request.user.is_superuser and request.user.is_staff:
            classroom = self.get_classroom(request.user)
            queryset = queryset.filter(classRoom=classroom)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["GET"])
    def get_bus_students(self, request):
        queryset = self.get_queryset()
        if not request.user.is_superuser and request.user.is_staff:
            classroom = self.get_classroom(request.user)
            queryset = queryset.filter(is_bus=True, classRoom=classroom)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response("yoyoyooyo")


class BusStudentsViewset(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = BusStudentSerializer
    permission_classes = [IsAdminOrTeacher]

    def get_student_bus_details(self, user_id):
        try:
            bus_service = StudentBusService.objects.select_related("student__user").get(
                student__id=user_id
            )
            return bus_service
        except StudentBusService.DoesNotExist:
            return None

    def retrieve(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        bus_service = self.get_student_bus_details(user_id)
        serializer = self.get_serializer(bus_service)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentCreateAPIView(CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        payment = serializer.instance
        return Response(
            {
                "message": "Payment done successfully",
                "data": PaymentSerializer(payment).data
            },
            status=status.HTTP_201_CREATED
        )

    

class TransactionViewset(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        queryset = super().get_queryset()
        if user_id:
            queryset = queryset.filter(student_id=user_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user_id = request.query_params.get('user_id')
        
        payment = queryset.order_by('-created_at').first()
        
        if payment:
            total_paid_amount = payment.paid_amount
            total_balance_amount = payment.balance_amount
        else:
            total_paid_amount = 0
            total_balance_amount = 0
        
        try:
            student = Student.objects.get(pk=user_id) 
            bus_service_data = {
                "annual_fees": student.bus_service.annual_fees
            }
        except Student.DoesNotExist:
            return Response({"detail": "Student does not exist"}, status=status.HTTP_404_NOT_FOUND)
        except Student.bus_service.RelatedObjectDoesNotExist:
            return Response({"detail": "Student has no bus service"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(queryset, many=True)
        response_data = {
            "paid_amount": total_paid_amount,
            "balance_amount": total_balance_amount,
            "bus_service": bus_service_data,
            "transactions": serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)



    
    def get(self, request, pk=None):
        try:
            payment = Payment.objects.get(id=pk)
            serializer = self.get_serializer(payment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({"message": "Payment not found"}, status=status.HTTP_404_NOT_FOUND) 
        