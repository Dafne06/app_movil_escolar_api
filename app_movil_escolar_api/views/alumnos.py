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
from django.shortcuts import get_object_or_404

#Esta funcion regresa todos los alumnos registrados 
class AlumnosAll(generics.CreateAPIView):
    #Aquí se valida la autenticación del usuario
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        alumnos = Alumnos.objects.filter(user__is_active = 1).order_by("id")
        lista = AlumnoSerializer(alumnos, many=True).data
        
        return Response(lista, 200)

class AlumnoView(generics.CreateAPIView):
    # Permisos por método (sobrescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación

    #Obtener usuario por ID
    # Verifica que el usuario esté autenticado

    def get(self, request, *args, **kwargs):
        alumno = get_object_or_404(Alumnos, id = request.GET.get("id"))
        alumno = AlumnoSerializer(alumno, many=False).data
        # Si todo es correcto, regresamos la información
        return Response(alumno, 200)

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
            alumno.save()

            return Response({"alumno_created_id": alumno.id}, 201)

        return Response(user_data.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Eliminar alumno con DELETE
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
         alumno = get_object_or_404(Alumnos, id=request.GET.get("id"))
         try:
             alumno.user.delete()
             return Response({"details":"Alumno eliminado"},200)
         except Exception as e:
            return Response({"details":"Algo pasó al eliminar"},400)

class AlumnoViewEdit(generics.CreateAPIView):
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        # ============================
        # Obtener alumno por ID
        # ============================
        alumno = get_object_or_404(Alumnos, id=request.data.get("id"))

        # ============================
        #   ACTUALIZAR ALUMNO
        # ============================
        alumno.matricula = request.data.get("matricula", alumno.matricula)
        alumno.telefono = request.data.get("telefono", alumno.telefono)
        alumno.edad = request.data.get("edad", alumno.edad)
        alumno.fecha_nacimiento = request.data.get("fecha_nacimiento", alumno.fecha_nacimiento)
        alumno.rfc = request.data.get("rfc", alumno.rfc).upper()
        alumno.curp = request.data.get("curp", alumno.curp)
        alumno.ocupacion = request.data.get("ocupacion", alumno.ocupacion)

        alumno.save()

        # ============================
        #   ACTUALIZAR USER
        # ============================
        user = alumno.user
        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)
        user.email = request.data.get("email", user.email)
        user.username = user.email  # mantener sincronización
        user.save()

        # ============================
        #   RESPUESTA
        # ============================
        return Response({
            "message": "Alumno actualizado correctamente",
            "alumno": AlumnoSerializer(alumno).data
        }, status=200)


