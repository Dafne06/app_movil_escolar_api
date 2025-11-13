from django.db.models import *
from django.db import transaction
from app_movil_escolar_api.serializers import UserSerializer
from app_movil_escolar_api.models import *
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import Group
import json

class MaestroView(generics.CreateAPIView):
    # Registrar nuevo maestro
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user_serializer = UserSerializer(data=request.data)

        if user_serializer.is_valid():
            role = request.data['rol']
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            email = request.data['email']
            password = request.data['password']

        
            if User.objects.filter(email=email).exists():
                return Response({"message": f"Email {email} ya está registrado"}, status=400)
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

            

            maestro = Maestros.objects.create(
                user=user,
                email=email,
                id_trabajador=request.data.get("id_trabajador"),
                telefono=request.data.get("telefono"),
                rfc=request.data.get("rfc", "").upper(),
                cubiculo=request.data.get("cubiculo"),
                area_investigacion=request.data.get("area_investigacion"),
                fecha_nacimiento=request.data.get("fecha_nacimiento"),
                materias=request.data.get("materias", []),
            )
            maestro.save()

            return Response({"maestro_created_id": maestro.id}, status=201)

        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
