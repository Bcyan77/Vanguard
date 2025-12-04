from django.db import models


class DestinyPlayer(models.Model):
    """플레이어 프로필 데이터 저장 (캐싱 및 통계용)"""

    MEMBERSHIP_TYPE_CHOICES = [
        (1, 'Xbox'),
        (2, 'PlayStation'),
        (3, 'Steam'),
        (4, 'Blizzard'),
        (5, 'Stadia'),
        (6, 'Epic Games'),
        (10, 'Demon'),
        (254, 'BungieNext'),
    ]

    membership_id = models.CharField(max_length=50, db_index=True)
    membership_type = models.IntegerField(choices=MEMBERSHIP_TYPE_CHOICES)

    display_name = models.CharField(max_length=255)
    bungie_global_display_name = models.CharField(max_length=255, blank=True, null=True)
    bungie_global_display_name_code = models.CharField(max_length=10, blank=True, null=True)
    icon_path = models.CharField(max_length=500, blank=True, null=True)

    active_triumph_score = models.IntegerField(default=0)
    lifetime_triumph_score = models.IntegerField(default=0)

    first_seen = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Destiny Player'
        verbose_name_plural = 'Destiny Players'
        unique_together = ['membership_id', 'membership_type']
        indexes = [
            models.Index(fields=['membership_type', 'membership_id']),
            models.Index(fields=['bungie_global_display_name']),
            models.Index(fields=['last_updated']),
        ]

    def __str__(self):
        if self.bungie_global_display_name and self.bungie_global_display_name_code:
            return f"{self.bungie_global_display_name}#{self.bungie_global_display_name_code}"
        return self.display_name

    def get_platform_display(self):
        return dict(self.MEMBERSHIP_TYPE_CHOICES).get(self.membership_type, 'Unknown')


class DestinyCharacter(models.Model):
    """캐릭터 데이터 저장"""

    CLASS_TYPE_CHOICES = [
        (0, 'Titan'),
        (1, 'Hunter'),
        (2, 'Warlock'),
    ]

    RACE_TYPE_CHOICES = [
        (0, 'Human'),
        (1, 'Awoken'),
        (2, 'Exo'),
    ]

    GENDER_TYPE_CHOICES = [
        (0, 'Male'),
        (1, 'Female'),
    ]

    player = models.ForeignKey(
        'DestinyPlayer',
        on_delete=models.CASCADE,
        related_name='characters'
    )

    character_id = models.CharField(max_length=50, db_index=True)

    class_type = models.IntegerField(choices=CLASS_TYPE_CHOICES)
    race_type = models.IntegerField(choices=RACE_TYPE_CHOICES, null=True, blank=True)
    gender_type = models.IntegerField(choices=GENDER_TYPE_CHOICES, null=True, blank=True)

    light_level = models.IntegerField(default=0)
    minutes_played_total = models.BigIntegerField(default=0)

    emblem_path = models.CharField(max_length=500, blank=True)
    emblem_background_path = models.CharField(max_length=500, blank=True)

    date_last_played = models.DateTimeField(null=True, blank=True)

    first_seen = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Destiny Character'
        verbose_name_plural = 'Destiny Characters'
        unique_together = ['player', 'character_id']
        ordering = ['-date_last_played']
        indexes = [
            models.Index(fields=['character_id']),
            models.Index(fields=['class_type']),
        ]

    def __str__(self):
        class_name = self.get_class_type_display()
        return f"{self.player.display_name} - {class_name} ({self.light_level})"


class PlayerTriumphSnapshot(models.Model):
    """일별 트라이엄프 점수 기록 (통계용)"""

    player = models.ForeignKey(
        'DestinyPlayer',
        on_delete=models.CASCADE,
        related_name='triumph_snapshots'
    )

    active_triumph_score = models.IntegerField()
    lifetime_triumph_score = models.IntegerField()

    snapshot_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Player Triumph Snapshot'
        verbose_name_plural = 'Player Triumph Snapshots'
        unique_together = ['player', 'snapshot_date']
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['snapshot_date']),
        ]

    def __str__(self):
        return f"{self.player} - {self.snapshot_date}: {self.active_triumph_score}"


class CharacterLightSnapshot(models.Model):
    """일별 캐릭터 광레벨 기록 (통계용)"""

    character = models.ForeignKey(
        'DestinyCharacter',
        on_delete=models.CASCADE,
        related_name='light_snapshots'
    )

    light_level = models.IntegerField()
    snapshot_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Character Light Snapshot'
        verbose_name_plural = 'Character Light Snapshots'
        unique_together = ['character', 'snapshot_date']
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"{self.character} - {self.snapshot_date}: {self.light_level}"


class GlobalStatisticsCache(models.Model):
    """전역 통계 캐시 (싱글톤, pk=1)"""

    # Light Level Statistics
    avg_light_level = models.FloatField(default=0)
    stddev_light_level = models.FloatField(default=0)
    light_level_distribution = models.JSONField(default=dict)

    # Triumph Score Statistics
    avg_triumph_score = models.FloatField(default=0)
    stddev_triumph_score = models.FloatField(default=0)
    triumph_score_distribution = models.JSONField(default=dict)

    # Class Distribution
    titan_count = models.IntegerField(default=0)
    hunter_count = models.IntegerField(default=0)
    warlock_count = models.IntegerField(default=0)

    # Play Time Statistics (hours)
    avg_play_time_hours = models.FloatField(default=0)
    stddev_play_time_hours = models.FloatField(default=0)
    play_time_distribution = models.JSONField(default=dict)

    # Metadata
    total_players = models.IntegerField(default=0)
    total_characters = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Global Statistics Cache'
        verbose_name_plural = 'Global Statistics Caches'

    def __str__(self):
        return f"Global Statistics (Updated: {self.last_updated})"
