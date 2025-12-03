"""
Context processors for making data available to all templates
"""

def user_parties(request):
    """
    Add user's parties and applications to template context
    """
    context = {}
    
    if request.user.is_authenticated:
        # Get user's created parties
        created_parties = request.user.created_parties.filter(
            status__in=['open', 'full']
        ).order_by('-created_at')[:5]
        
        # Get user's active memberships
        from parties.models import PartyMember
        active_memberships = PartyMember.objects.filter(
            user=request.user,
            status='active'
        ).exclude(
            party__creator=request.user
        ).select_related('party').order_by('-joined_at')[:5]
        
        # Get pending applications
        from parties.models import PartyApplication
        pending_applications = PartyApplication.objects.filter(
            applicant=request.user,
            status='pending'
        ).select_related('party').order_by('-applied_at')[:5]
        
        context['sidebar_created_parties'] = created_parties
        context['sidebar_memberships'] = active_memberships
        context['sidebar_pending_applications'] = pending_applications
    
    return context
