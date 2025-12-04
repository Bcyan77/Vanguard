"""
Management command to fetch Destiny 2 activity definitions from Bungie API
and populate the database
"""

import requests
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from parties.models import (
    DestinyActivityType,
    DestinySpecificActivity,
    DestinyActivityMode,
    ActivityModeAvailability
)
from accounts.bungie_oauth import get_manifest_api_request

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch Destiny 2 activity definitions from Bungie API and update database (3-tier system)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tier',
            type=str,
            choices=['types', 'activities', 'modes', 'all'],
            default='all',
            help='Which tier to load: types (Tier 1), activities (Tier 2), modes (Tier 3), or all',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading new ones',
        )
        parser.add_argument(
            '--language',
            type=str,
            default='en',
            help='Language code for manifest (default: en)',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write(self.style.NOTICE('Starting Destiny 2 activity sync (3-tier system)...'))

        tier = options['tier']
        language = options['language']

        # Step 1: Get manifest metadata
        manifest_data = self.get_manifest_metadata()
        if not manifest_data:
            self.stdout.write(self.style.ERROR('Failed to fetch manifest metadata'))
            return

        # Step 2: Load data based on tier selection
        if tier in ['types', 'all']:
            self.load_activity_types(manifest_data, language, options['clear'])

        if tier in ['activities', 'all']:
            self.load_specific_activities(manifest_data, language, options['clear'])

        if tier in ['modes', 'all']:
            self.load_activity_modes(manifest_data, language, options['clear'])

        # Step 3: Link activities to modes (only if loading all or activities)
        if tier in ['activities', 'all']:
            self.link_activities_to_modes(manifest_data, language)

        self.stdout.write(self.style.SUCCESS('Sync completed!'))

    def get_manifest_metadata(self):
        """Fetch manifest metadata from Bungie API"""
        self.stdout.write('Fetching manifest metadata...')
        return get_manifest_api_request('/Destiny2/Manifest/')

    def get_definition_url(self, manifest_data, language, definition_name):
        """Extract definition URL from manifest"""
        try:
            json_world_component_content_paths = manifest_data.get(
                'jsonWorldComponentContentPaths', {}
            )

            language_paths = json_world_component_content_paths.get(language, {})
            if not language_paths:
                self.stdout.write(self.style.WARNING(
                    f'Language "{language}" not found, falling back to "en"'
                ))
                language_paths = json_world_component_content_paths.get('en', {})

            definition_path = language_paths.get(definition_name)

            if definition_path:
                full_url = f"https://www.bungie.net{definition_path}"
                self.stdout.write(f'{definition_name} URL: {full_url}')
                return full_url
            else:
                self.stdout.write(self.style.ERROR(
                    f'{definition_name} not found in manifest'
                ))
                return None

        except Exception as e:
            logger.error(f"Error extracting {definition_name} URL: {e}")
            return None

    def download_definitions(self, url, definition_name):
        """Download definitions JSON file"""
        self.stdout.write(f'Downloading {definition_name} from {url}...')

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            data = response.json()
            self.stdout.write(self.style.SUCCESS(
                f'Downloaded {len(data)} {definition_name} entries'
            ))
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {definition_name}: {e}")
            return None

    def load_activity_types(self, manifest_data, language, clear):
        """Load Tier 1: Activity Types"""
        self.stdout.write(self.style.NOTICE('\n=== Loading Tier 1: Activity Types ==='))

        # Get URL
        url = self.get_definition_url(manifest_data, language, 'DestinyActivityTypeDefinition')
        if not url:
            return

        # Download
        activity_types = self.download_definitions(url, 'Activity Types')
        if not activity_types:
            return

        # Clear if requested
        if clear:
            deleted_count = DestinyActivityType.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Cleared {deleted_count} existing activity types'))

        # Save
        created_count = 0
        updated_count = 0

        for hash_key, activity_def in activity_types.items():
            # Skip redacted entries
            if activity_def.get('redacted', False):
                continue

            display_props = activity_def.get('displayProperties', {})

            # Skip entries without names (invalid)
            name = display_props.get('name', '').strip()
            if not name:
                continue

            # Convert hash from string to integer
            hash_int = int(hash_key)

            # Get or create activity type
            activity_type, created = DestinyActivityType.objects.update_or_create(
                hash=hash_int,
                defaults={
                    'index': activity_def.get('index', 0),
                    'name': name,
                    'description': display_props.get('description', ''),
                    'icon_path': display_props.get('icon', ''),
                    'has_icon': display_props.get('hasIcon', False),
                    'redacted': activity_def.get('redacted', False),
                    'is_active': True,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'  + Created: {name}')
            else:
                updated_count += 1
                self.stdout.write(f'  ~ Updated: {name}')

        self.stdout.write(self.style.SUCCESS(
            f'Activity Types: {created_count} created, {updated_count} updated'
        ))

    def load_specific_activities(self, manifest_data, language, clear):
        """Load Tier 2: Specific Activities"""
        self.stdout.write(self.style.NOTICE('\n=== Loading Tier 2: Specific Activities ==='))

        # Get URL
        url = self.get_definition_url(manifest_data, language, 'DestinyActivityDefinition')
        if not url:
            return

        # Download
        activities = self.download_definitions(url, 'Specific Activities')
        if not activities:
            return

        # Clear if requested
        if clear:
            deleted_count = DestinySpecificActivity.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Cleared {deleted_count} existing specific activities'))

        # Save
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for hash_key, activity_def in activities.items():
            # Skip redacted entries
            if activity_def.get('redacted', False):
                continue

            display_props = activity_def.get('displayProperties', {})

            # Skip entries without names (invalid)
            name = display_props.get('name', '').strip()
            if not name:
                continue

            # Get activity type hash (Tier 1 link)
            activity_type_hash = activity_def.get('activityTypeHash')
            if not activity_type_hash:
                skipped_count += 1
                continue

            # Check if activity type exists
            try:
                activity_type = DestinyActivityType.objects.get(hash=activity_type_hash)
            except DestinyActivityType.DoesNotExist:
                skipped_count += 1
                continue

            # Convert hash from string to integer
            hash_int = int(hash_key)

            # Get or create specific activity
            specific_activity, created = DestinySpecificActivity.objects.update_or_create(
                hash=hash_int,
                defaults={
                    'index': activity_def.get('index', 0),
                    'name': name,
                    'description': display_props.get('description', ''),
                    'icon_path': display_props.get('icon', ''),
                    'has_icon': display_props.get('hasIcon', False),
                    'activity_type': activity_type,
                    'activity_level': activity_def.get('activityLevel', 0),
                    'activity_light_level': activity_def.get('activityLightLevel', 0),
                    'tier': activity_def.get('tier', 0),
                    'is_playlist': activity_def.get('isPlaylist', False),
                    'redacted': activity_def.get('redacted', False),
                    'is_active': True,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'  + Created: {name} ({activity_type.name})')
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Specific Activities: {created_count} created, {updated_count} updated, {skipped_count} skipped'
        ))

    def load_activity_modes(self, manifest_data, language, clear):
        """Load Tier 3: Activity Modes"""
        self.stdout.write(self.style.NOTICE('\n=== Loading Tier 3: Activity Modes ==='))

        # Get URL
        url = self.get_definition_url(manifest_data, language, 'DestinyActivityModeDefinition')
        if not url:
            return

        # Download
        modes = self.download_definitions(url, 'Activity Modes')
        if not modes:
            return

        # Clear if requested
        if clear:
            deleted_count = DestinyActivityMode.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Cleared {deleted_count} existing activity modes'))

        # Save
        created_count = 0
        updated_count = 0

        for hash_key, mode_def in modes.items():
            # Skip redacted entries
            if mode_def.get('redacted', False):
                continue

            display_props = mode_def.get('displayProperties', {})

            # Skip entries without names (invalid)
            name = display_props.get('name', '').strip()
            if not name:
                continue

            # Convert hash from string to integer
            hash_int = int(hash_key)

            # Get or create activity mode
            activity_mode, created = DestinyActivityMode.objects.update_or_create(
                hash=hash_int,
                defaults={
                    'index': mode_def.get('index', 0),
                    'name': name,
                    'description': display_props.get('description', ''),
                    'icon_path': display_props.get('icon', ''),
                    'has_icon': display_props.get('hasIcon', False),
                    'mode_type': mode_def.get('modeType', 0),
                    'activity_mode_category': mode_def.get('activityModeCategory', 0),
                    'is_team_based': mode_def.get('isTeamBased', False),
                    'display_order': mode_def.get('order', 0),
                    'redacted': mode_def.get('redacted', False),
                    'is_active': True,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'  + Created: {name}')
            else:
                updated_count += 1
                self.stdout.write(f'  ~ Updated: {name}')

        self.stdout.write(self.style.SUCCESS(
            f'Activity Modes: {created_count} created, {updated_count} updated'
        ))

    def link_activities_to_modes(self, manifest_data, language):
        """Link specific activities to their available modes"""
        self.stdout.write(self.style.NOTICE('\n=== Linking Activities to Modes ==='))

        # Get activity definitions again to extract mode links
        url = self.get_definition_url(manifest_data, language, 'DestinyActivityDefinition')
        if not url:
            return

        activities = self.download_definitions(url, 'Activity Definitions')
        if not activities:
            return

        # Clear existing links
        ActivityModeAvailability.objects.all().delete()

        linked_count = 0

        for hash_key, activity_def in activities.items():
            hash_int = int(hash_key)

            # Check if specific activity exists
            try:
                specific_activity = DestinySpecificActivity.objects.get(hash=hash_int)
            except DestinySpecificActivity.DoesNotExist:
                continue

            # Get direct activity mode hashes
            mode_hashes = activity_def.get('directActivityModeHash')
            if mode_hashes:
                # directActivityModeHash can be a single int or None
                if isinstance(mode_hashes, int):
                    mode_hashes = [mode_hashes]
                elif not isinstance(mode_hashes, list):
                    continue

                for mode_hash in mode_hashes:
                    try:
                        activity_mode = DestinyActivityMode.objects.get(hash=mode_hash)
                        ActivityModeAvailability.objects.get_or_create(
                            specific_activity=specific_activity,
                            activity_mode=activity_mode
                        )
                        linked_count += 1
                    except DestinyActivityMode.DoesNotExist:
                        continue

        self.stdout.write(self.style.SUCCESS(
            f'Created {linked_count} activity-mode links'
        ))
