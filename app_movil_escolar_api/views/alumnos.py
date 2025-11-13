from django.db.models import *
from django.db import transaction
from app_movil_escolar_api.serializers import UserSerializer
from app_movil_escolar_api.serializers import *
from app_movil_escolar_api.models import *
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import Group

class AlumnoView(generics.CreateAPIView):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user_data = UserSerializer(data=request.data)
        if user_data.is_valid():
            role = request.data['rol']
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            email = request.data['email']
            password = request.data['password']

            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                return Response({"message": f"Email {email} ya está registrado"}, 400)

            user = User.objects.create(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            user.set_password(password)
            user.save()

            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)

            alumno = Alumnos.objects.create(
                user=user,
                email=email,
                matricula=request.data["matricula"],
                telefono=request.data.get("telefono"),
                edad=request.data.get("edad"),
                fecha_nacimiento=request.data.get("fecha_nacimiento"),
                rfc=request.data.get("rfc", "").upper(),
                curp=request.data.get("curp"),
                ocupacion=request.data.get("ocupacion")
            )

            return Response({"alumno_created_id": alumno.id}, 201)

        return Response(user_data.errors, status=status.HTTP_400_BAD_REQUEST)
