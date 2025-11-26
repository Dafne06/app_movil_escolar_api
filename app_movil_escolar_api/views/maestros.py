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
import json
from django.shortcuts import get_object_or_404

class MaestrosAll(generics.CreateAPIView):
    #Obtener todos los maestros
    # Necesita permisos de autenticación de usuario para poder acceder a la petición
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        maestros = Maestros.objects.filter(user__is_active=1).order_by("id")
        lista = MaestroSerializer(maestros, many=True).data
        for maestro in lista:
            if isinstance(maestro, dict) and "materias" in maestro:
                try:
                    maestro["materias"] = json.loads(maestro["materias"])
                except Exception:
                    maestro["materias"] = []
        return Response(lista, 200)

class MaestroView(generics.CreateAPIView):
    # Permisos por método (sobrescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación
    
    #Obtener usuario por ID
    # Verifica que el usuario esté autenticado
    def get(self, request, *args, **kwargs):
     maestro = get_object_or_404(Maestros, id=request.GET.get("id"))
     data = MaestroSerializer(maestro, many=False).data

     # Convertir materias a lista si viene en string
     materias = data.get("materias")

     if isinstance(materias, str):
         try:
             data["materias"] = json.loads(materias)
         except:
             data["materias"] = []
     return Response(data, 200)

    
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

            # ========= CONVERSIÓN DE MATERIAS =========
            materias = request.data.get("materias", [])

            if isinstance(materias, str):
              try:
                materias = json.loads(materias)
              except:
                materias = []

        # Crear maestro
            maestro = Maestros.objects.create(
             user=user,
             email=email,
             id_trabajador=request.data.get("id_trabajador"),
             telefono=request.data.get("telefono"),
             rfc=request.data.get("rfc", "").upper(),
             cubiculo=request.data.get("cubiculo"),
             area_investigacion=request.data.get("area_investigacion"),
             fecha_nacimiento=request.data.get("fecha_nacimiento"),
             materias=materias  # 👈 YA ES LISTA
           )
            

           # maestro = Maestros.objects.create(
           #     user=user,
           #     email=email,
           #     id_trabajador=request.data.get("id_trabajador"),
           #     telefono=request.data.get("telefono"),
           #     rfc=request.data.get("rfc", "").upper(),
           #     cubiculo=request.data.get("cubiculo"),
           #     area_investigacion=request.data.get("area_investigacion"),
           #     fecha_nacimiento=request.data.get("fecha_nacimiento"),
            #    materias=request.data.get("materias", []),
           # )
                      
            maestro.save()

            return Response({"maestro_created_id": maestro.id}, status=201)

        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
         maestro = get_object_or_404(Maestros, id=request.GET.get("id"))
         try:
             maestro.user.delete()
             return Response({"details":"Maestro eliminado"},200)
         except Exception as e:
            return Response({"details":"Algo pasó al eliminar"},400)

class MaestroViewEdit(generics.CreateAPIView):
     # Actualizar datos del administrador
     
     @transaction.atomic
     def put(self, request, *args, **kwargs):
      maestro = get_object_or_404(Maestros, id=request.data.get("id"))

      maestro.id_trabajador = request.data.get("id_trabajador", maestro.id_trabajador)
      maestro.telefono = request.data.get("telefono", maestro.telefono)
      maestro.rfc = request.data.get("rfc", maestro.rfc).upper()
      maestro.cubiculo = request.data.get("cubiculo", maestro.cubiculo)
      maestro.area_investigacion = request.data.get("area_investigacion", maestro.area_investigacion)
      maestro.fecha_nacimiento = request.data.get("fecha_nacimiento", maestro.fecha_nacimiento)

    # ========= NUEVO: actualizar materias =========
      materias = request.data.get("materias", maestro.materias)

      if isinstance(materias, str):
        try:
            materias = json.loads(materias)
        except:
            materias = []

      maestro.materias = materias

      maestro.save()

    # Actualizar usuario
      user = maestro.user
      user.first_name = request.data.get("first_name", user.first_name)
      user.last_name = request.data.get("last_name", user.last_name)
      user.email = request.data.get("email", user.email)
      user.username = user.email
      user.save()

      return Response({
        "message": "Maestro actualizado correctamente",
        "maestro": MaestroSerializer(maestro).data
      }, status=200)

     
     # Eliminar maestro con delete (Borrar realmente)
     #@transaction.atomic
     #def delete(self, request, *args, **kwargs):
     #   maestro = get_object_or_404(Maestros, id=request.GET.get("id"))
     #   try:
     #       maestro.user.delete()
     #       return Response({"details":"Maestro eliminado"},200)
     #   except Exception as e:
      #      return Response({"details":"Algo pasó al eliminar"},400)
    
    #Eliminar maestro (Desactivar usuario)
    # @transaction.atomic
    # def delete(self, request, *args, **kwargs):
    #     id_maestro = kwargs.get('id_maestro', None)
    #     if id_maestro:
    #         try:
    #             maestro = Maestros.objects.get(id=id_maestro)
    #             user = maestro.user
    #             user.is_active = 0
    #             user.save()
    #             return Response({"message":"Maestro con ID "+str(id_maestro)+" eliminado correctamente."},200)
    #         except Maestros.DoesNotExist:
    #             return Response({"message":"Maestro con ID "+str(id_maestro)+" no encontrado."},404)
    #     return Response({"message":"Se necesita el ID del maestro."},400)   
