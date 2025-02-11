from django.shortcuts import render
from rest_framework import views, status
from rest_framework.response import Response
from .serializers import *

# Create your views here.

class SignUpView(views.APIView):
    serializer_class = SignUpSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({'message':'회원가입 성공', 'data':serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'message':'회원가입 실패', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
class LogInView(views.APIView):
    serializer_class= LogInSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            return Response({'message': "로그인 성공", 'data': serializer.validated_data}, status=status.HTTP_200_OK)
        return Response({'message':'로그인 실패', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
