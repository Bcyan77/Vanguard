from django.db import models
from django.conf import settings
from django.utils import timezone


class Party(models.Model):
    """
    Model representing a party/fireteam recruitment post
    """
    
    ACTIVITY_TYPE_CHOICES = [
        ('raid', 'Raid'),
        ('dungeon', 'Dungeon'),
        ('nightfall', 'Nightfall'),
        ('crucible', 'Crucible'),
        ('gambit', 'Gambit'),
        ('strike', 'Strike'),
        ('patrol', 'Patrol/Exploration'),
        ('seasonal', 'Seasonal Activity'),
        ('exotic', 'Exotic Quest'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('full', 'Full'),
        ('closed', 'Closed'),
        ('completed', 'Completed'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPE_CHOICES)
    
    # Party size
    max_members = models.IntegerField(default=6)
    current_members_count = models.IntegerField(default=1)
    
    # Creator and status
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_parties'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    requires_mic = models.BooleanField(default=False)
    min_power_level = models.IntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Party'
        verbose_name_plural = 'Parties'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_activity_type_display()}"
    
    def is_full(self):
        """Check if party is at max capacity"""
        return self.current_members_count >= self.max_members
    
    def update_member_count(self):
        """Update the current member count based on active members"""
        self.current_members_count = self.members.filter(status='active').count()
        self.save()
    
    def auto_update_status(self):
        """Automatically update status based on member count"""
        if self.is_full() and self.status == 'open':
            self.status = 'full'
            self.save()
        elif not self.is_full() and self.status == 'full':
            self.status = 'open'
            self.save()
    
    def get_available_slots(self):
        """Get number of available slots"""
        return self.max_members - self.current_members_count
    
    def is_member(self, user):
        """Check if user is a member of this party"""
        return self.members.filter(user=user, status='active').exists()
    
    def is_creator(self, user):
        """Check if user is the creator"""
        return self.creator == user


class PartyMember(models.Model):
    """
    Model representing a member of a party
    """
    
    ROLE_CHOICES = [
        ('leader', 'Leader'),
        ('member', 'Member'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('left', 'Left'),
        ('kicked', 'Kicked'),
    ]
    
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='party_memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Party Member'
        verbose_name_plural = 'Party Members'
        unique_together = ['party', 'user']
        ordering = ['joined_at']
    
    def __str__(self):
        return f"{self.user.display_name} in {self.party.title}"


class PartyTag(models.Model):
    """
    Model representing tags for parties (e.g., "Sherpa", "KWTD", "Chill")
    """
    
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = 'Party Tag'
        verbose_name_plural = 'Party Tags'
        unique_together = ['party', 'name']
    
    def __str__(self):
        return self.name


class PartyApplication(models.Model):
    """
    Model representing an application to join a party
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='party_applications'
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    
    class Meta:
        verbose_name = 'Party Application'
        verbose_name_plural = 'Party Applications'
        unique_together = ['party', 'applicant']
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.applicant.display_name} -> {self.party.title} ({self.status})"
    
    def accept(self, reviewer):
        """Accept the application and add user to party"""
        if self.status != 'pending':
            return False
        
        if self.party.is_full():
            return False
        
        # Create party member
        PartyMember.objects.create(
            party=self.party,
            user=self.applicant,
            role='member',
            status='active'
        )
        
        # Update application status
        self.status = 'accepted'
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        self.save()
        
        # Update party member count and status
        self.party.update_member_count()
        self.party.auto_update_status()
        
        return True
    
    def reject(self, reviewer):
        """Reject the application"""
        if self.status != 'pending':
            return False
        
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        self.save()
        
        return True
    
    def withdraw(self):
        """Withdraw the application"""
        if self.status != 'pending':
            return False
        
        self.status = 'withdrawn'
        self.save()
        
        return True
