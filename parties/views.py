from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Party, PartyMember, PartyTag, PartyApplication


def party_list(request):
    """
    List all parties with filtering options
    """
    parties = Party.objects.all().select_related('creator').prefetch_related('tags', 'members')
    
    # Filter by activity type
    activity_type = request.GET.get('activity_type')
    if activity_type:
        parties = parties.filter(activity_type=activity_type)
    
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
    
    context = {
        'parties': parties,
        'activity_types': Party.ACTIVITY_TYPE_CHOICES,
        'selected_activity': activity_type,
        'selected_status': status,
        'search_query': search,
    }
    
    return render(request, 'parties/list.html', context)


@login_required
def party_create(request):
    """
    Create a new party
    """
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title')
        description = request.POST.get('description')
        activity_type = request.POST.get('activity_type')
        max_members = int(request.POST.get('max_members', 6))
        requires_mic = request.POST.get('requires_mic') == 'on'
        min_power_level = request.POST.get('min_power_level')
        scheduled_time = request.POST.get('scheduled_time')
        tags = request.POST.get('tags', '').split(',')
        
        # Create party
        party = Party.objects.create(
            title=title,
            description=description,
            activity_type=activity_type,
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
    
    context = {
        'activity_types': Party.ACTIVITY_TYPE_CHOICES,
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
    Edit an existing party
    """
    party = get_object_or_404(Party, pk=pk)
    
    # Only creator can edit
    if party.creator != request.user:
        messages.error(request, 'You do not have permission to edit this party.')
        return redirect('parties:party_detail', pk=pk)
    
    if request.method == 'POST':
        party.title = request.POST.get('title')
        party.description = request.POST.get('description')
        party.activity_type = request.POST.get('activity_type')
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
    
    context = {
        'party': party,
        'activity_types': Party.ACTIVITY_TYPE_CHOICES,
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
