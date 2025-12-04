"""
Context processors for making data available to all templates
"""

def user_fireteams(request):
    """
    Add user's fireteams and applications to template context
    """
    context = {}

    if request.user.is_authenticated:
        # Get user's created fireteams
        created_fireteams = request.user.created_fireteams.filter(
            status__in=['open', 'full']
        ).order_by('-created_at')[:5]

        # Get user's active memberships
        from fireteams.models import FireteamMember
        active_memberships = FireteamMember.objects.filter(
            user=request.user,
            status='active'
        ).exclude(
            fireteam__creator=request.user
        ).select_related('fireteam').order_by('-joined_at')[:5]

        # Get pending applications
        from fireteams.models import FireteamApplication
        pending_applications = FireteamApplication.objects.filter(
            applicant=request.user,
            status='pending'
        ).select_related('fireteam').order_by('-applied_at')[:5]

        context['sidebar_created_fireteams'] = created_fireteams
        context['sidebar_memberships'] = active_memberships
        context['sidebar_pending_applications'] = pending_applications

    return context
