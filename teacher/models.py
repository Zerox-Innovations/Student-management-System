from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.db import models
from django.db.models import Q
from admins.models import User
import re

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pen_no = models.CharField(max_length=15, unique=True)
    photo = models.ImageField('profile/',null=True,blank=True)
    def __str__(self):
        return self.user.name


class ClassRoom(models.Model):
    name = models.CharField(max_length=150)
    division = models.CharField(max_length=1)
    capacity = models.PositiveIntegerField(default=50)
    teachers = models.ManyToManyField(
        Teacher, through="ClassRoomTeacher", related_name="classTeacher"
    )
    
    class Meta:
        unique_together = ('name', 'division')
        constraints = [
            models.CheckConstraint(check=models.Q(division__in='ABCDEFGHIJKLMNOPQRSTUVWXYZ'), name='valid_division')
        ]

    def __str__(self):
        return f'{self.name} - {self.division}'
    

class ClassRoomTeacher(models.Model):
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name="classroom_teachers"
    )
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    is_class_teacher = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.teacher.user.name} is the class teacher of {self.classroom.name}"
