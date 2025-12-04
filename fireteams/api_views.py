from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from .models import (
    Fireteam, FireteamMember, FireteamApplication,
    DestinyActivityType, DestinySpecificActivity, DestinyActivityMode
)
from .serializers import (
    FireteamListSerializer, FireteamDetailSerializer,
    FireteamCreateSerializer, FireteamUpdateSerializer,
    FireteamApplicationSerializer, FireteamApplicationCreateSerializer,
    DestinyActivityTypeSerializer, DestinySpecificActivitySerializer,
    DestinyActivityModeSerializer, ErrorResponseSerializer
)


# ============================================================
# Fireteam API Views
# ============================================================

class FireteamListCreateAPIView(APIView):
    """
    API endpoint for listing and creating fireteams.
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List all fireteams",
        description="Get a list of all fireteams with optional filtering by activity type, specific activity, status, etc.",
        parameters=[
            OpenApiParameter(name='activity_type', type=int, description='Filter by activity type hash (Tier 1)'),
            OpenApiParameter(name='specific_activity', type=int, description='Filter by specific activity hash (Tier 2)'),
            OpenApiParameter(name='activity_mode', type=int, description='Filter by activity mode hash (Tier 3)'),
            OpenApiParameter(name='status', type=str, description='Filter by status (open, full, closed, completed)'),
            OpenApiParameter(name='requires_mic', type=bool, description='Filter by mic requirement'),
            OpenApiParameter(name='search', type=str, description='Search in title and description'),
        ],
        responses={200: FireteamListSerializer(many=True)},
        tags=['Fireteams']
    )
    def get(self, request):
        fireteams = Fireteam.objects.all().select_related(
            'creator',
            'selected_activity_type',
            'selected_specific_activity',
            'selected_activity_mode'
        ).prefetch_related('tags', 'members')

        # Filtering
        activity_type = request.GET.get('activity_type')
        if activity_type:
            fireteams = fireteams.filter(selected_activity_type_id=activity_type)

        specific_activity = request.GET.get('specific_activity')
        if specific_activity:
            fireteams = fireteams.filter(selected_specific_activity_id=specific_activity)

        activity_mode = request.GET.get('activity_mode')
        if activity_mode:
            fireteams = fireteams.filter(selected_activity_mode_id=activity_mode)

        status_filter = request.GET.get('status')
        if status_filter:
            fireteams = fireteams.filter(status=status_filter)

        requires_mic = request.GET.get('requires_mic')
        if requires_mic is not None:
            fireteams = fireteams.filter(requires_mic=requires_mic.lower() == 'true')

        search = request.GET.get('search')
        if search:
            fireteams = fireteams.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        serializer = FireteamListSerializer(fireteams, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary="Create a new fireteam",
        description="Create a new fireteam. The creator is automatically added as the leader.",
        request=FireteamCreateSerializer,
        responses={
            201: FireteamDetailSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
        },
        tags=['Fireteams']
    )
    def post(self, request):
        serializer = FireteamCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            fireteam = serializer.save()
            response_serializer = FireteamDetailSerializer(fireteam, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class FireteamDetailAPIView(APIView):
    """
    API endpoint for retrieving, updating, and deleting a fireteam.
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        return get_object_or_404(Fireteam, pk=pk)

    @extend_schema(
        summary="Get fireteam details",
        description="Get detailed information about a specific fireteam including members.",
        responses={
            200: FireteamDetailSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Fireteams']
    )
    def get(self, request, pk):
        fireteam = self.get_object(pk)
        serializer = FireteamDetailSerializer(fireteam, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary="Update a fireteam",
        description="Update a fireteam. Only the creator can update.",
        request=FireteamUpdateSerializer,
        responses={
            200: FireteamDetailSerializer,
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Fireteams']
    )
    def put(self, request, pk):
        fireteam = self.get_object(pk)

        if not fireteam.is_creator(request.user):
            return Response({'error': 'Only the creator can update this fireteam.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = FireteamUpdateSerializer(fireteam, data=request.data, context={'request': request})
        if serializer.is_valid():
            fireteam = serializer.save()
            response_serializer = FireteamDetailSerializer(fireteam, context={'request': request})
            return Response(response_serializer.data)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Partially update a fireteam",
        description="Partially update a fireteam. Only the creator can update.",
        request=FireteamUpdateSerializer,
        responses={
            200: FireteamDetailSerializer,
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Fireteams']
    )
    def patch(self, request, pk):
        fireteam = self.get_object(pk)

        if not fireteam.is_creator(request.user):
            return Response({'error': 'Only the creator can update this fireteam.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = FireteamUpdateSerializer(fireteam, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            fireteam = serializer.save()
            response_serializer = FireteamDetailSerializer(fireteam, context={'request': request})
            return Response(response_serializer.data)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete a fireteam",
        description="Delete a fireteam. Only the creator can delete.",
        responses={
            204: None,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Fireteams']
    )
    def delete(self, request, pk):
        fireteam = self.get_object(pk)

        if not fireteam.is_creator(request.user):
            return Response({'error': 'Only the creator can delete this fireteam.'}, status=status.HTTP_403_FORBIDDEN)

        fireteam.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FireteamApplyAPIView(APIView):
    """
    API endpoint for applying to join a fireteam.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Apply to join a fireteam",
        description="Submit an application to join a fireteam.",
        request=FireteamApplicationCreateSerializer,
        responses={
            201: FireteamApplicationSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Fireteams']
    )
    def post(self, request, pk):
        fireteam = get_object_or_404(Fireteam, pk=pk)

        # Check if already a member
        if fireteam.is_member(request.user):
            return Response({'error': 'You are already a member of this fireteam.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if already applied
        existing_application = FireteamApplication.objects.filter(
            fireteam=fireteam,
            applicant=request.user,
            status='pending'
        ).first()
        if existing_application:
            return Response({'error': 'You have already applied to this fireteam.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if fireteam is full
        if fireteam.is_full():
            return Response({'error': 'This fireteam is full.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if fireteam is open
        if fireteam.status not in ['open']:
            return Response({'error': 'This fireteam is not accepting applications.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FireteamApplicationCreateSerializer(data=request.data)
        if serializer.is_valid():
            application = FireteamApplication.objects.create(
                fireteam=fireteam,
                applicant=request.user,
                message=serializer.validated_data.get('message', '')
            )
            response_serializer = FireteamApplicationSerializer(application)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class FireteamLeaveAPIView(APIView):
    """
    API endpoint for leaving a fireteam.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Leave a fireteam",
        description="Leave a fireteam. The creator (leader) cannot leave.",
        responses={
            200: {"type": "object", "properties": {"message": {"type": "string"}}},
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Fireteams']
    )
    def post(self, request, pk):
        fireteam = get_object_or_404(Fireteam, pk=pk)

        # Check if the user is the creator
        if fireteam.is_creator(request.user):
            return Response({'error': 'The creator cannot leave the fireteam. Delete it instead.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user is a member
        membership = FireteamMember.objects.filter(
            fireteam=fireteam,
            user=request.user,
            status='active'
        ).first()

        if not membership:
            return Response({'error': 'You are not a member of this fireteam.'}, status=status.HTTP_400_BAD_REQUEST)

        membership.status = 'left'
        membership.save()

        fireteam.update_member_count()
        fireteam.auto_update_status()

        return Response({'message': 'You have left the fireteam.'})


class FireteamApplicationsAPIView(APIView):
    """
    API endpoint for managing fireteam applications.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List fireteam applications",
        description="Get all pending applications for a fireteam. Only the creator can view.",
        responses={
            200: FireteamApplicationSerializer(many=True),
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Fireteams']
    )
    def get(self, request, pk):
        fireteam = get_object_or_404(Fireteam, pk=pk)

        if not fireteam.is_creator(request.user):
            return Response({'error': 'Only the creator can view applications.'}, status=status.HTTP_403_FORBIDDEN)

        applications = FireteamApplication.objects.filter(fireteam=fireteam, status='pending')
        serializer = FireteamApplicationSerializer(applications, many=True)
        return Response(serializer.data)


class FireteamApplicationAcceptAPIView(APIView):
    """
    API endpoint for accepting a fireteam application.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Accept a fireteam application",
        description="Accept a pending application. Only the creator can accept.",
        responses={
            200: FireteamApplicationSerializer,
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Fireteams']
    )
    def post(self, request, pk, application_id):
        fireteam = get_object_or_404(Fireteam, pk=pk)
        application = get_object_or_404(FireteamApplication, pk=application_id, fireteam=fireteam)

        if not fireteam.is_creator(request.user):
            return Response({'error': 'Only the creator can accept applications.'}, status=status.HTTP_403_FORBIDDEN)

        if application.accept(reviewer=request.user):
            serializer = FireteamApplicationSerializer(application)
            return Response(serializer.data)
        return Response({'error': 'Failed to accept application. The fireteam may be full or the application is not pending.'}, status=status.HTTP_400_BAD_REQUEST)


class FireteamApplicationRejectAPIView(APIView):
    """
    API endpoint for rejecting a fireteam application.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Reject a fireteam application",
        description="Reject a pending application. Only the creator can reject.",
        responses={
            200: FireteamApplicationSerializer,
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Fireteams']
    )
    def post(self, request, pk, application_id):
        fireteam = get_object_or_404(Fireteam, pk=pk)
        application = get_object_or_404(FireteamApplication, pk=application_id, fireteam=fireteam)

        if not fireteam.is_creator(request.user):
            return Response({'error': 'Only the creator can reject applications.'}, status=status.HTTP_403_FORBIDDEN)

        if application.reject(reviewer=request.user):
            serializer = FireteamApplicationSerializer(application)
            return Response(serializer.data)
        return Response({'error': 'Failed to reject application. The application may not be pending.'}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# Activity API Views (Tier 1, 2, 3)
# ============================================================

class ActivityTypesAPIView(APIView):
    """
    API endpoint for listing activity types (Tier 1).
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List activity types",
        description="Get all active activity types (Tier 1) for fireteam creation.",
        responses={200: DestinyActivityTypeSerializer(many=True)},
        tags=['Activities']
    )
    def get(self, request):
        activity_types = DestinyActivityType.objects.filter(
            is_active=True,
            is_canonical=True
        ).order_by('name')
        serializer = DestinyActivityTypeSerializer(activity_types, many=True)
        return Response(serializer.data)


class SpecificActivitiesAPIView(APIView):
    """
    API endpoint for listing specific activities (Tier 2).
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List specific activities",
        description="Get specific activities (Tier 2) for a given activity type.",
        parameters=[
            OpenApiParameter(name='type_hash', type=int, required=True, description='Activity type hash (Tier 1)')
        ],
        responses={
            200: DestinySpecificActivitySerializer(many=True),
            400: ErrorResponseSerializer,
        },
        tags=['Activities']
    )
    def get(self, request):
        type_hash = request.GET.get('type_hash')
        if not type_hash:
            return Response({'error': 'type_hash parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        activities = DestinySpecificActivity.objects.filter(
            activity_type_id=type_hash,
            is_active=True
        ).order_by('name')
        serializer = DestinySpecificActivitySerializer(activities, many=True)
        return Response(serializer.data)


class ActivityModesAPIView(APIView):
    """
    API endpoint for listing activity modes (Tier 3).
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List activity modes",
        description="Get activity modes (Tier 3) for a given specific activity.",
        parameters=[
            OpenApiParameter(name='activity_hash', type=int, required=True, description='Specific activity hash (Tier 2)')
        ],
        responses={
            200: DestinyActivityModeSerializer(many=True),
            400: ErrorResponseSerializer,
        },
        tags=['Activities']
    )
    def get(self, request):
        activity_hash = request.GET.get('activity_hash')
        if not activity_hash:
            return Response({'error': 'activity_hash parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        modes = DestinyActivityMode.objects.filter(
            activities__specific_activity_id=activity_hash,
            is_active=True
        ).order_by('display_order', 'name')
        serializer = DestinyActivityModeSerializer(modes, many=True)
        return Response(serializer.data)
