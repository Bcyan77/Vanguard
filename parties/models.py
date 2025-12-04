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

    # DEPRECATED: Legacy activity type field (to be removed)
    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text='DEPRECATED: Use selected_* fields instead'
    )

    # DEPRECATED: Link to old single-tier activity (to be removed)
    activity = models.ForeignKey(
        'DestinyActivityType',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='old_parties',
        help_text='DEPRECATED: Use selected_* fields instead'
    )

    # NEW: 3-Tier Activity Selection
    selected_activity_type = models.ForeignKey(
        'DestinyActivityType',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='parties_by_type',
        help_text='Tier 1: Activity Type (Raid, Dungeon, etc.)'
    )

    selected_specific_activity = models.ForeignKey(
        'DestinySpecificActivity',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='parties',
        help_text='Tier 2: Specific Activity (Deep Stone Crypt, etc.)'
    )

    selected_activity_mode = models.ForeignKey(
        'DestinyActivityMode',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='parties_by_mode',
        help_text='Tier 3: Difficulty/Mode (Master, Heroic, etc.) - Optional'
    )

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
        return f"{self.title} - {self.get_activity_display()}"

    def get_activity_display(self):
        """Get activity name (supports 3-tier and legacy fields)"""
        # Priority 1: 3-tier system
        if self.selected_specific_activity:
            parts = []
            if self.selected_activity_type:
                parts.append(self.selected_activity_type.name)
            parts.append(self.selected_specific_activity.name)
            if self.selected_activity_mode:
                parts.append(f"({self.selected_activity_mode.name})")
            return " > ".join(parts)

        # Priority 2: Legacy single-tier
        if self.activity:
            return self.activity.name

        # Priority 3: Legacy hardcoded
        if self.activity_type:
            return self.get_activity_type_display()

        return "Unknown Activity"
    
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


class DestinyActivityType(models.Model):
    """
    Tier 1: Activity Type categories from Bungie API (Raid, Dungeon, Strike, etc.)
    Formerly known as DestinyActivity
    """

    # Bungie API identifiers
    hash = models.BigIntegerField(primary_key=True, unique=True)
    index = models.IntegerField()

    # Display properties
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon_path = models.CharField(max_length=500, blank=True)
    has_icon = models.BooleanField(default=False)

    # Metadata
    redacted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Data management
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Destiny Activity Type'
        verbose_name_plural = 'Destiny Activity Types'
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
        ]
        db_table = 'parties_destinyactivity'  # Keep old table name for backward compatibility

    def __str__(self):
        return self.name

    def get_icon_url(self):
        """Get full Bungie CDN URL for icon"""
        if self.has_icon and self.icon_path:
            return f"https://www.bungie.net{self.icon_path}"
        return None


# Alias for backward compatibility in code
DestinyActivity = DestinyActivityType


class DestinySpecificActivity(models.Model):
    """
    Tier 2: Specific activities from Bungie API (Vault of Glass, Deep Stone Crypt, etc.)
    """

    # Bungie API identifiers
    hash = models.BigIntegerField(primary_key=True, unique=True)
    index = models.IntegerField()

    # Display properties
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon_path = models.CharField(max_length=500, blank=True)
    has_icon = models.BooleanField(default=False)

    # Link to Tier 1
    activity_type = models.ForeignKey(
        'DestinyActivityType',
        on_delete=models.CASCADE,
        related_name='specific_activities'
    )

    # Bungie API metadata
    activity_level = models.IntegerField(default=0)
    activity_light_level = models.IntegerField(default=0)
    tier = models.IntegerField(default=0)
    is_playlist = models.BooleanField(default=False)

    # Metadata
    redacted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Data management
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Destiny Specific Activity'
        verbose_name_plural = 'Destiny Specific Activities'
        ordering = ['name']
        indexes = [
            models.Index(fields=['activity_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.activity_type.name})"

    def get_icon_url(self):
        """Get full Bungie CDN URL for icon"""
        if self.has_icon and self.icon_path:
            return f"https://www.bungie.net{self.icon_path}"
        return None


class DestinyActivityMode(models.Model):
    """
    Tier 3: Activity modes/difficulty from Bungie API (Normal, Heroic, Master, etc.)
    """

    # Bungie API identifiers
    hash = models.BigIntegerField(primary_key=True, unique=True)
    index = models.IntegerField()

    # Display properties
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon_path = models.CharField(max_length=500, blank=True)
    has_icon = models.BooleanField(default=False)

    # Bungie API metadata
    mode_type = models.IntegerField(default=0)
    activity_mode_category = models.IntegerField(default=0)
    is_team_based = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    # Metadata
    redacted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Data management
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Destiny Activity Mode'
        verbose_name_plural = 'Destiny Activity Modes'
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'display_order']),
        ]

    def __str__(self):
        return self.name

    def get_icon_url(self):
        """Get full Bungie CDN URL for icon"""
        if self.has_icon and self.icon_path:
            return f"https://www.bungie.net{self.icon_path}"
        return None


class ActivityModeAvailability(models.Model):
    """
    Join table: Links specific activities to their available modes/difficulties
    """

    specific_activity = models.ForeignKey(
        'DestinySpecificActivity',
        on_delete=models.CASCADE,
        related_name='available_modes'
    )
    activity_mode = models.ForeignKey(
        'DestinyActivityMode',
        on_delete=models.CASCADE,
        related_name='activities'
    )

    class Meta:
        verbose_name = 'Activity Mode Availability'
        verbose_name_plural = 'Activity Mode Availabilities'
        unique_together = ['specific_activity', 'activity_mode']

    def __str__(self):
        return f"{self.specific_activity.name} - {self.activity_mode.name}"
