from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .models import (
    Fireteam, FireteamMember, FireteamTag, FireteamApplication,
    DestinyActivity, DestinyActivityType,
    DestinySpecificActivity, DestinyActivityMode
)


def fireteam_list(request):
    """
    List all fireteams with 3-tier filtering options
    """
    fireteams = Fireteam.objects.all().select_related(
        'creator',
        'selected_activity_type',
        'selected_specific_activity',
        'selected_activity_mode'
    ).prefetch_related('tags', 'members')

    # 3-Tier filtering
    activity_type_id = request.GET.get('activity_type')
    if activity_type_id:
        fireteams = fireteams.filter(selected_activity_type_id=activity_type_id)

    specific_activity_id = request.GET.get('specific_activity')
    if specific_activity_id:
        fireteams = fireteams.filter(selected_specific_activity_id=specific_activity_id)

    activity_mode_id = request.GET.get('activity_mode')
    if activity_mode_id:
        fireteams = fireteams.filter(selected_activity_mode_id=activity_mode_id)

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        fireteams = fireteams.filter(status=status)

    # Search by title or description
    search = request.GET.get('search')
    if search:
        fireteams = fireteams.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    # Filter by tags
    tag = request.GET.get('tag')
    if tag:
        fireteams = fireteams.filter(tags__name__iexact=tag)

    # Get active canonical activity types for filter dropdown (Tier 1)
    activity_types = DestinyActivityType.objects.filter(is_active=True, is_canonical=True).order_by('name')

    context = {
        'fireteams': fireteams,
        'activity_types': activity_types,
        'selected_activity_type': activity_type_id,
        'selected_specific_activity': specific_activity_id,
        'selected_activity_mode': activity_mode_id,
        'selected_status': status,
        'search_query': search,
    }

    return render(request, 'fireteams/list.html', context)


@login_required
def fireteam_create(request):
    """
    Create a new fireteam with 3-tier activity selection
    """
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title')
        description = request.POST.get('description')

        # 3-Tier activity selection
        activity_type_hash = request.POST.get('activity_type')
        specific_activity_hash = request.POST.get('specific_activity')
        activity_mode_hash = request.POST.get('activity_mode')  # Optional

        max_members = int(request.POST.get('max_members', 6))
        requires_mic = request.POST.get('requires_mic') == 'on'
        min_power_level = request.POST.get('min_power_level')
        scheduled_time = request.POST.get('scheduled_time')
        tags = request.POST.get('tags', '').split(',')

        # Validate and get 3-tier activity objects
        try:
            activity_type = DestinyActivityType.objects.get(pk=activity_type_hash) if activity_type_hash else None
            specific_activity = DestinySpecificActivity.objects.get(pk=specific_activity_hash) if specific_activity_hash else None
            activity_mode = DestinyActivityMode.objects.get(pk=activity_mode_hash) if activity_mode_hash else None

            if not specific_activity:
                raise ValueError('Specific activity is required')

        except (DestinyActivityType.DoesNotExist, DestinySpecificActivity.DoesNotExist,
                DestinyActivityMode.DoesNotExist, ValueError) as e:
            # Check if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid activity selection: {str(e)}'
                }, status=400)

            messages.error(request, f'Invalid activity selection: {str(e)}')
            return redirect('fireteams:fireteam_list')

        # Create fireteam
        fireteam = Fireteam.objects.create(
            title=title,
            description=description,
            selected_activity_type=activity_type,
            selected_specific_activity=specific_activity,
            selected_activity_mode=activity_mode,
            max_members=max_members,
            requires_mic=requires_mic,
            min_power_level=int(min_power_level) if min_power_level else None,
            scheduled_time=scheduled_time if scheduled_time else None,
            creator=request.user,
            status='open'
        )

        # Create fireteam member for creator
        FireteamMember.objects.create(
            fireteam=fireteam,
            user=request.user,
            role='leader',
            status='active'
        )

        # Update member count
        fireteam.update_member_count()

        # Add tags
        for tag_name in tags:
            tag_name = tag_name.strip()
            if tag_name:
                FireteamTag.objects.create(fireteam=fireteam, name=tag_name)

        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('fireteams:fireteam_detail', args=[fireteam.pk])
            })

        messages.success(request, f'Fireteam "{fireteam.title}" created successfully!')
        return redirect('fireteams:fireteam_detail', pk=fireteam.pk)

    # GET request: redirect to fireteam list (modal is now used for creation)
    return redirect('fireteams:fireteam_list')


def fireteam_detail(request, pk):
    """
    Display fireteam details
    """
    fireteam = get_object_or_404(
        Fireteam.objects.select_related('creator').prefetch_related('tags', 'members__user'),
        pk=pk
    )

    # Check if user is a member
    is_member = False
    is_creator = False
    has_pending_application = False

    if request.user.is_authenticated:
        is_member = fireteam.is_member(request.user)
        is_creator = fireteam.is_creator(request.user)
        has_pending_application = FireteamApplication.objects.filter(
            fireteam=fireteam,
            applicant=request.user,
            status='pending'
        ).exists()

    context = {
        'fireteam': fireteam,
        'is_member': is_member,
        'is_creator': is_creator,
        'has_pending_application': has_pending_application,
    }

    return render(request, 'fireteams/detail.html', context)


@login_required
def fireteam_edit(request, pk):
    """
    Edit an existing fireteam with 3-tier activity selection
    """
    fireteam = get_object_or_404(Fireteam, pk=pk)

    # Only creator can edit
    if fireteam.creator != request.user:
        messages.error(request, 'You do not have permission to edit this fireteam.')
        return redirect('fireteams:fireteam_detail', pk=pk)

    if request.method == 'POST':
        fireteam.title = request.POST.get('title')
        fireteam.description = request.POST.get('description')

        # 3-Tier activity selection
        activity_type_hash = request.POST.get('activity_type')
        specific_activity_hash = request.POST.get('specific_activity')
        activity_mode_hash = request.POST.get('activity_mode')  # Optional

        # Validate and get 3-tier activity objects
        try:
            activity_type = DestinyActivityType.objects.get(pk=activity_type_hash) if activity_type_hash else None
            specific_activity = DestinySpecificActivity.objects.get(pk=specific_activity_hash) if specific_activity_hash else None
            activity_mode = DestinyActivityMode.objects.get(pk=activity_mode_hash) if activity_mode_hash else None

            if not specific_activity:
                raise ValueError('Specific activity is required')

            fireteam.selected_activity_type = activity_type
            fireteam.selected_specific_activity = specific_activity
            fireteam.selected_activity_mode = activity_mode

        except (DestinyActivityType.DoesNotExist, DestinySpecificActivity.DoesNotExist,
                DestinyActivityMode.DoesNotExist, ValueError) as e:
            messages.error(request, f'Invalid activity selection: {str(e)}')
            activity_types = DestinyActivityType.objects.filter(is_active=True, is_canonical=True).order_by('name')
            return render(request, 'fireteams/edit.html', {'fireteam': fireteam, 'activity_types': activity_types})

        fireteam.max_members = int(request.POST.get('max_members', 6))
        fireteam.requires_mic = request.POST.get('requires_mic') == 'on'
        min_power_level = request.POST.get('min_power_level')
        fireteam.min_power_level = int(min_power_level) if min_power_level else None
        scheduled_time = request.POST.get('scheduled_time')
        fireteam.scheduled_time = scheduled_time if scheduled_time else None
        fireteam.save()

        # Update tags
        fireteam.tags.all().delete()
        tags = request.POST.get('tags', '').split(',')
        for tag_name in tags:
            tag_name = tag_name.strip()
            if tag_name:
                FireteamTag.objects.create(fireteam=fireteam, name=tag_name)

        messages.success(request, 'Fireteam updated successfully!')
        return redirect('fireteams:fireteam_detail', pk=pk)

    # GET: Get active activity types for form
    activity_types = DestinyActivityType.objects.filter(is_active=True, is_canonical=True).order_by('name')

    context = {
        'fireteam': fireteam,
        'activity_types': activity_types,
    }

    return render(request, 'fireteams/edit.html', context)


@login_required
def fireteam_delete(request, pk):
    """
    Delete a fireteam
    """
    fireteam = get_object_or_404(Fireteam, pk=pk)

    # Only creator can delete
    if fireteam.creator != request.user:
        messages.error(request, 'You do not have permission to delete this fireteam.')
        return redirect('fireteams:fireteam_detail', pk=pk)

    if request.method == 'POST':
        fireteam_title = fireteam.title
        fireteam.delete()
        messages.success(request, f'Fireteam "{fireteam_title}" deleted successfully!')
        return redirect('fireteams:fireteam_list')

    return render(request, 'fireteams/delete_confirm.html', {'fireteam': fireteam})


@login_required
def fireteam_apply(request, pk):
    """
    Apply to join a fireteam
    """
    fireteam = get_object_or_404(Fireteam, pk=pk)

    # Check if already a member
    if fireteam.is_member(request.user):
        messages.info(request, 'You are already a member of this fireteam.')
        return redirect('fireteams:fireteam_detail', pk=pk)

    # Check if fireteam is full
    if fireteam.is_full():
        messages.error(request, 'This fireteam is full.')
        return redirect('fireteams:fireteam_detail', pk=pk)

    # Check if already applied
    existing_application = FireteamApplication.objects.filter(
        fireteam=fireteam,
        applicant=request.user,
        status='pending'
    ).first()

    if existing_application:
        messages.info(request, 'You have already applied to this fireteam.')
        return redirect('fireteams:fireteam_detail', pk=pk)

    if request.method == 'POST':
        message = request.POST.get('message', '')

        FireteamApplication.objects.create(
            fireteam=fireteam,
            applicant=request.user,
            message=message,
            status='pending'
        )

        messages.success(request, 'Application submitted successfully!')
        return redirect('fireteams:fireteam_detail', pk=pk)

    return render(request, 'fireteams/apply.html', {'fireteam': fireteam})


@login_required
def fireteam_leave(request, pk):
    """
    Leave a fireteam
    """
    fireteam = get_object_or_404(Fireteam, pk=pk)

    # Can't leave if you're the creator
    if fireteam.creator == request.user:
        messages.error(request, 'Fireteam creator cannot leave. Delete the fireteam instead.')
        return redirect('fireteams:fireteam_detail', pk=pk)

    membership = FireteamMember.objects.filter(
        fireteam=fireteam,
        user=request.user,
        status='active'
    ).first()

    if not membership:
        messages.error(request, 'You are not a member of this fireteam.')
        return redirect('fireteams:fireteam_detail', pk=pk)

    if request.method == 'POST':
        membership.status = 'left'
        membership.save()

        fireteam.update_member_count()
        fireteam.auto_update_status()

        messages.success(request, f'You have left "{fireteam.title}".')
        return redirect('fireteams:fireteam_list')

    return render(request, 'fireteams/leave_confirm.html', {'fireteam': fireteam})


@login_required
def fireteam_applications(request, pk):
    """
    View and manage applications for a fireteam (creator only)
    """
    fireteam = get_object_or_404(Fireteam, pk=pk)

    # Only creator can view applications
    if fireteam.creator != request.user:
        messages.error(request, 'You do not have permission to view applications.')
        return redirect('fireteams:fireteam_detail', pk=pk)

    applications = fireteam.applications.filter(status='pending').select_related('applicant')

    context = {
        'fireteam': fireteam,
        'applications': applications,
    }

    return render(request, 'fireteams/applications.html', context)


@login_required
def application_accept(request, application_id):
    """
    Accept an application
    """
    application = get_object_or_404(FireteamApplication, pk=application_id)
    fireteam = application.fireteam

    # Only creator can accept
    if fireteam.creator != request.user:
        messages.error(request, 'You do not have permission to accept applications.')
        return redirect('fireteams:fireteam_detail', pk=fireteam.pk)

    if application.accept(request.user):
        messages.success(request, f'{application.applicant.display_name} has been added to the fireteam!')
    else:
        messages.error(request, 'Failed to accept application. Fireteam may be full.')

    return redirect('fireteams:fireteam_applications', pk=fireteam.pk)


@login_required
def application_reject(request, application_id):
    """
    Reject an application
    """
    application = get_object_or_404(FireteamApplication, pk=application_id)
    fireteam = application.fireteam

    # Only creator can reject
    if fireteam.creator != request.user:
        messages.error(request, 'You do not have permission to reject applications.')
        return redirect('fireteams:fireteam_detail', pk=fireteam.pk)

    if application.reject(request.user):
        messages.success(request, f'{application.applicant.display_name}\'s application has been rejected.')
    else:
        messages.error(request, 'Failed to reject application.')

    return redirect('fireteams:fireteam_applications', pk=fireteam.pk)


# API Endpoints for 3-Tier Cascading Selection

@require_http_methods(["GET"])
def api_get_specific_activities(request):
    """
    API endpoint to get specific activities (Tier 2) for a given activity type (Tier 1)
    GET /fireteams/api/specific-activities/?type_hash=<hash>
    """
    type_hash = request.GET.get('type_hash')

    if not type_hash:
        return JsonResponse({'error': 'type_hash parameter is required'}, status=400)

    try:
        # Get specific activities for this type
        activities = DestinySpecificActivity.objects.filter(
            activity_type_id=type_hash,
            is_active=True
        ).values('hash', 'name').order_by('name')

        return JsonResponse({
            'activities': list(activities),
            'count': len(activities)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_get_activity_modes(request):
    """
    API endpoint to get activity modes (Tier 3) for a given specific activity (Tier 2)
    GET /fireteams/api/activity-modes/?activity_hash=<hash>
    """
    activity_hash = request.GET.get('activity_hash')

    if not activity_hash:
        return JsonResponse({'error': 'activity_hash parameter is required'}, status=400)

    try:
        # Get modes available for this specific activity
        modes = DestinyActivityMode.objects.filter(
            activities__specific_activity_id=activity_hash,
            is_active=True
        ).order_by('display_order', 'name').values('hash', 'name')

        return JsonResponse({
            'modes': list(modes),
            'count': len(modes)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
