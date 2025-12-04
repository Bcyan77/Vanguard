from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import (
    Party, PartyMember, PartyTag, PartyApplication,
    DestinyActivity, DestinyActivityType,
    DestinySpecificActivity, DestinyActivityMode
)


def party_list(request):
    """
    List all parties with 3-tier filtering options
    """
    parties = Party.objects.all().select_related(
        'creator',
        'selected_activity_type',
        'selected_specific_activity',
        'selected_activity_mode'
    ).prefetch_related('tags', 'members')

    # 3-Tier filtering
    activity_type_id = request.GET.get('activity_type')
    if activity_type_id:
        parties = parties.filter(selected_activity_type_id=activity_type_id)

    specific_activity_id = request.GET.get('specific_activity')
    if specific_activity_id:
        parties = parties.filter(selected_specific_activity_id=specific_activity_id)

    activity_mode_id = request.GET.get('activity_mode')
    if activity_mode_id:
        parties = parties.filter(selected_activity_mode_id=activity_mode_id)

    # Filter by status
    status = request.GET.get('status', 'open')
    if status:
        parties = parties.filter(status=status)

    # Search by title or description
    search = request.GET.get('search')
    if search:
        parties = parties.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    # Filter by tags
    tag = request.GET.get('tag')
    if tag:
        parties = parties.filter(tags__name__iexact=tag)

    # Get active activity types for filter dropdown (Tier 1)
    activity_types = DestinyActivityType.objects.filter(is_active=True).order_by('name')

    context = {
        'parties': parties,
        'activity_types': activity_types,
        'selected_activity_type': activity_type_id,
        'selected_specific_activity': specific_activity_id,
        'selected_activity_mode': activity_mode_id,
        'selected_status': status,
        'search_query': search,
    }

    return render(request, 'parties/list.html', context)


@login_required
def party_create(request):
    """
    Create a new party with 3-tier activity selection
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
            messages.error(request, f'Invalid activity selection: {str(e)}')
            activity_types = DestinyActivityType.objects.filter(is_active=True).order_by('name')
            return render(request, 'parties/create.html', {'activity_types': activity_types})

        # Create party
        party = Party.objects.create(
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

        # Create party member for creator
        PartyMember.objects.create(
            party=party,
            user=request.user,
            role='leader',
            status='active'
        )

        # Update member count
        party.update_member_count()

        # Add tags
        for tag_name in tags:
            tag_name = tag_name.strip()
            if tag_name:
                PartyTag.objects.create(party=party, name=tag_name)

        messages.success(request, f'Party "{party.title}" created successfully!')
        return redirect('parties:party_detail', pk=party.pk)

    # GET: Get active activity types for form (Tier 1)
    activity_types = DestinyActivityType.objects.filter(is_active=True).order_by('name')

    context = {
        'activity_types': activity_types,
    }

    return render(request, 'parties/create.html', context)


def party_detail(request, pk):
    """
    Display party details
    """
    party = get_object_or_404(
        Party.objects.select_related('creator').prefetch_related('tags', 'members__user'),
        pk=pk
    )
    
    # Check if user is a member
    is_member = False
    is_creator = False
    has_pending_application = False
    
    if request.user.is_authenticated:
        is_member = party.is_member(request.user)
        is_creator = party.is_creator(request.user)
        has_pending_application = PartyApplication.objects.filter(
            party=party,
            applicant=request.user,
            status='pending'
        ).exists()
    
    context = {
        'party': party,
        'is_member': is_member,
        'is_creator': is_creator,
        'has_pending_application': has_pending_application,
    }
    
    return render(request, 'parties/detail.html', context)


@login_required
def party_edit(request, pk):
    """
    Edit an existing party with 3-tier activity selection
    """
    party = get_object_or_404(Party, pk=pk)

    # Only creator can edit
    if party.creator != request.user:
        messages.error(request, 'You do not have permission to edit this party.')
        return redirect('parties:party_detail', pk=pk)

    if request.method == 'POST':
        party.title = request.POST.get('title')
        party.description = request.POST.get('description')

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

            party.selected_activity_type = activity_type
            party.selected_specific_activity = specific_activity
            party.selected_activity_mode = activity_mode

        except (DestinyActivityType.DoesNotExist, DestinySpecificActivity.DoesNotExist,
                DestinyActivityMode.DoesNotExist, ValueError) as e:
            messages.error(request, f'Invalid activity selection: {str(e)}')
            activity_types = DestinyActivityType.objects.filter(is_active=True).order_by('name')
            return render(request, 'parties/edit.html', {'party': party, 'activity_types': activity_types})

        party.max_members = int(request.POST.get('max_members', 6))
        party.requires_mic = request.POST.get('requires_mic') == 'on'
        min_power_level = request.POST.get('min_power_level')
        party.min_power_level = int(min_power_level) if min_power_level else None
        scheduled_time = request.POST.get('scheduled_time')
        party.scheduled_time = scheduled_time if scheduled_time else None
        party.save()

        # Update tags
        party.tags.all().delete()
        tags = request.POST.get('tags', '').split(',')
        for tag_name in tags:
            tag_name = tag_name.strip()
            if tag_name:
                PartyTag.objects.create(party=party, name=tag_name)

        messages.success(request, 'Party updated successfully!')
        return redirect('parties:party_detail', pk=pk)

    # GET: Get active activity types for form
    activity_types = DestinyActivityType.objects.filter(is_active=True).order_by('name')

    context = {
        'party': party,
        'activity_types': activity_types,
    }

    return render(request, 'parties/edit.html', context)


@login_required
def party_delete(request, pk):
    """
    Delete a party
    """
    party = get_object_or_404(Party, pk=pk)
    
    # Only creator can delete
    if party.creator != request.user:
        messages.error(request, 'You do not have permission to delete this party.')
        return redirect('parties:party_detail', pk=pk)
    
    if request.method == 'POST':
        party_title = party.title
        party.delete()
        messages.success(request, f'Party "{party_title}" deleted successfully!')
        return redirect('parties:party_list')
    
    return render(request, 'parties/delete_confirm.html', {'party': party})


@login_required
def party_apply(request, pk):
    """
    Apply to join a party
    """
    party = get_object_or_404(Party, pk=pk)
    
    # Check if already a member
    if party.is_member(request.user):
        messages.info(request, 'You are already a member of this party.')
        return redirect('parties:party_detail', pk=pk)
    
    # Check if party is full
    if party.is_full():
        messages.error(request, 'This party is full.')
        return redirect('parties:party_detail', pk=pk)
    
    # Check if already applied
    existing_application = PartyApplication.objects.filter(
        party=party,
        applicant=request.user,
        status='pending'
    ).first()
    
    if existing_application:
        messages.info(request, 'You have already applied to this party.')
        return redirect('parties:party_detail', pk=pk)
    
    if request.method == 'POST':
        message = request.POST.get('message', '')
        
        PartyApplication.objects.create(
            party=party,
            applicant=request.user,
            message=message,
            status='pending'
        )
        
        messages.success(request, 'Application submitted successfully!')
        return redirect('parties:party_detail', pk=pk)
    
    return render(request, 'parties/apply.html', {'party': party})


@login_required
def party_leave(request, pk):
    """
    Leave a party
    """
    party = get_object_or_404(Party, pk=pk)
    
    # Can't leave if you're the creator
    if party.creator == request.user:
        messages.error(request, 'Party creator cannot leave. Delete the party instead.')
        return redirect('parties:party_detail', pk=pk)
    
    membership = PartyMember.objects.filter(
        party=party,
        user=request.user,
        status='active'
    ).first()
    
    if not membership:
        messages.error(request, 'You are not a member of this party.')
        return redirect('parties:party_detail', pk=pk)
    
    if request.method == 'POST':
        membership.status = 'left'
        membership.save()
        
        party.update_member_count()
        party.auto_update_status()
        
        messages.success(request, f'You have left "{party.title}".')
        return redirect('parties:party_list')
    
    return render(request, 'parties/leave_confirm.html', {'party': party})


@login_required
def party_applications(request, pk):
    """
    View and manage applications for a party (creator only)
    """
    party = get_object_or_404(Party, pk=pk)
    
    # Only creator can view applications
    if party.creator != request.user:
        messages.error(request, 'You do not have permission to view applications.')
        return redirect('parties:party_detail', pk=pk)
    
    applications = party.applications.filter(status='pending').select_related('applicant')
    
    context = {
        'party': party,
        'applications': applications,
    }
    
    return render(request, 'parties/applications.html', context)


@login_required
def application_accept(request, application_id):
    """
    Accept an application
    """
    application = get_object_or_404(PartyApplication, pk=application_id)
    party = application.party
    
    # Only creator can accept
    if party.creator != request.user:
        messages.error(request, 'You do not have permission to accept applications.')
        return redirect('parties:party_detail', pk=party.pk)
    
    if application.accept(request.user):
        messages.success(request, f'{application.applicant.display_name} has been added to the party!')
    else:
        messages.error(request, 'Failed to accept application. Party may be full.')
    
    return redirect('parties:party_applications', pk=party.pk)


@login_required
def application_reject(request, application_id):
    """
    Reject an application
    """
    application = get_object_or_404(PartyApplication, pk=application_id)
    party = application.party
    
    # Only creator can reject
    if party.creator != request.user:
        messages.error(request, 'You do not have permission to reject applications.')
        return redirect('parties:party_detail', pk=party.pk)
    
    if application.reject(request.user):
        messages.success(request, f'{application.applicant.display_name}\'s application has been rejected.')
    else:
        messages.error(request, 'Failed to reject application.')

    return redirect('parties:party_applications', pk=party.pk)


# API Endpoints for 3-Tier Cascading Selection

@require_http_methods(["GET"])
def api_get_specific_activities(request):
    """
    API endpoint to get specific activities (Tier 2) for a given activity type (Tier 1)
    GET /parties/api/specific-activities/?type_hash=<hash>
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
    GET /parties/api/activity-modes/?activity_hash=<hash>
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
