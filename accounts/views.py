from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,generics
from .serializers import RegisterSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveAPIView
from .serializers import UserProfileSerializer
from .serializers import ChangePasswordSerializer


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data = request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message":"User creatd successfully"},
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class MeView(RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )