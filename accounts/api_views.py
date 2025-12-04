from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .serializers import BungieUserProfileSerializer
from fireteams.serializers import ErrorResponseSerializer


class CurrentUserProfileAPIView(APIView):
    """
    API endpoint for getting the current authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get current user profile",
        description="Get the profile information of the currently authenticated user.",
        responses={
            200: BungieUserProfileSerializer,
            401: ErrorResponseSerializer,
        },
        tags=['Accounts']
    )
    def get(self, request):
        serializer = BungieUserProfileSerializer(request.user)
        return Response(serializer.data)
