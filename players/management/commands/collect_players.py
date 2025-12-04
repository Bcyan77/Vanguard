"""
Management command to collect player data from Bungie API via clan membership.

Usage:
    # Collect from specific clan
    python manage.py collect_players --clan-id 1234567

    # Search for clan by name
    python manage.py collect_players --clan-search "Korean Raiders"

    # With options
    python manage.py collect_players --clan-id 1234567 --limit 50 --delay 200 --verbose

    # Dry run (preview without saving)
    python manage.py collect_players --clan-id 1234567 --dry-run

    # Refresh global stats after collection
    python manage.py collect_players --clan-id 1234567 --refresh-stats
"""

import time
import logging
from django.core.management.base import BaseCommand

from players.models import DestinyPlayer, DestinyCharacter
from players.bungie_api import (
    search_clans,
    get_clan_members,
    get_player_profile,
)
from players.services import sync_player_from_api, refresh_global_statistics

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Collect player data from Bungie API via clan membership for global statistics'

    def add_arguments(self, parser):
        # Source selection (mutually exclusive group)
        source_group = parser.add_mutually_exclusive_group(required=True)
        source_group.add_argument(
            '--clan-id',
            type=int,
            help='Collect from specific clan by ID'
        )
        source_group.add_argument(
            '--clan-search',
            type=str,
            help='Search for clan by name and select interactively'
        )

        # Collection options
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of players to collect (default: 100)'
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=150,
            help='Delay between API calls in milliseconds (default: 150ms)'
        )

        # Output options
        parser.add_argument(
            '--refresh-stats',
            action='store_true',
            help='Refresh global statistics after collection'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be collected without saving'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress output'
        )

    def handle(self, *args, **options):
        clan_id = options.get('clan_id')
        clan_search = options.get('clan_search')
        limit = options['limit']
        delay_ms = options['delay']
        dry_run = options['dry_run']
        refresh_stats = options['refresh_stats']
        verbose = options['verbose']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN MODE ===\n'))

        # Resolve clan ID
        if clan_search:
            clan_id = self.search_and_select_clan(clan_search)
            if not clan_id:
                return

        # Get clan members
        members = self.get_all_clan_members(clan_id, limit)
        if not members:
            self.stdout.write(self.style.ERROR('No members found'))
            return

        # Collect player data
        stats = self.collect_player_data(members, delay_ms, dry_run, verbose)

        # Optionally refresh statistics
        if refresh_stats and not dry_run:
            self.refresh_statistics()

        # Print summary
        self.print_summary(stats, dry_run)

    def search_and_select_clan(self, search_term):
        """Search for clans and let user select one"""
        self.stdout.write(f'Searching for clans matching "{search_term}"...')

        clans, error = search_clans(search_term)
        if error or not clans:
            self.stdout.write(self.style.ERROR(f'No clans found: {error}'))
            return None

        # Display options
        self.stdout.write(self.style.NOTICE('\nFound clans:'))
        for i, clan in enumerate(clans[:10], 1):
            self.stdout.write(
                f'  {i}. {clan["name"]} ({clan["memberCount"]} members)'
            )
            if clan.get('motto'):
                self.stdout.write(f'     "{clan["motto"]}"')

        # Get user selection
        try:
            selection = int(input('\nSelect clan number (1-10): ')) - 1
            if 0 <= selection < len(clans[:10]):
                selected = clans[selection]
                self.stdout.write(self.style.SUCCESS(
                    f'\nSelected: {selected["name"]} (ID: {selected["groupId"]})'
                ))
                return selected['groupId']
            else:
                self.stdout.write(self.style.ERROR('Invalid selection'))
                return None
        except (ValueError, EOFError):
            # Non-interactive: use first result
            self.stdout.write(self.style.WARNING(
                f'\nNon-interactive mode: using first result "{clans[0]["name"]}"'
            ))
            return clans[0]['groupId']

    def get_all_clan_members(self, clan_id, limit):
        """Fetch all members from clan (paginated)"""
        self.stdout.write(f'\nFetching members from clan {clan_id}...')

        all_members = []
        page = 1

        while len(all_members) < limit:
            members, has_more, error = get_clan_members(clan_id, page)

            if error:
                self.stdout.write(self.style.WARNING(f'Page {page} error: {error}'))
                break

            all_members.extend(members)
            self.stdout.write(f'  Page {page}: {len(members)} members')

            if not has_more:
                break
            page += 1
            time.sleep(0.1)

        # Trim to limit
        all_members = all_members[:limit]
        self.stdout.write(self.style.SUCCESS(
            f'Total: {len(all_members)} members to process'
        ))

        return all_members

    def collect_player_data(self, members, delay_ms, dry_run, verbose):
        """Collect profile data for each member"""
        stats = {
            'total': len(members),
            'success': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
            'errors': [],
        }

        delay_sec = delay_ms / 1000.0

        self.stdout.write(self.style.NOTICE(
            f'\nCollecting player data ({delay_ms}ms delay between requests)...'
        ))

        for i, member in enumerate(members, 1):
            membership_type = member['membershipType']
            membership_id = member['membershipId']
            display_name = member.get('bungieGlobalDisplayName') or member.get('displayName') or 'Unknown'

            # Progress indicator
            if verbose or i % 10 == 0 or i == 1:
                self.stdout.write(f'  [{i}/{stats["total"]}] {display_name}')

            if dry_run:
                stats['success'] += 1
                continue

            try:
                # Fetch profile
                profile_data = get_player_profile(membership_type, membership_id)

                if profile_data:
                    # Check if player exists
                    exists = DestinyPlayer.objects.filter(
                        membership_id=membership_id,
                        membership_type=membership_type
                    ).exists()

                    # Sync to database
                    sync_player_from_api(membership_type, membership_id, profile_data)

                    stats['success'] += 1
                    if exists:
                        stats['updated'] += 1
                    else:
                        stats['created'] += 1

                    if verbose:
                        action = 'Updated' if exists else 'Created'
                        self.stdout.write(self.style.SUCCESS(f'    {action}'))
                else:
                    stats['failed'] += 1
                    stats['errors'].append(f'{display_name}: No profile data')
                    if verbose:
                        self.stdout.write(self.style.WARNING('    Failed: No profile data'))

            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f'{display_name}: {str(e)}')
                if verbose:
                    self.stdout.write(self.style.ERROR(f'    Error: {e}'))
                logger.exception(f'Error collecting player {display_name}')

            # Rate limiting delay
            if i < stats['total']:
                time.sleep(delay_sec)

        return stats

    def refresh_statistics(self):
        """Refresh global statistics cache"""
        self.stdout.write('\nRefreshing global statistics...')
        cache = refresh_global_statistics()
        self.stdout.write(self.style.SUCCESS(
            f'Statistics updated: {cache.total_players} players, '
            f'{cache.total_characters} characters'
        ))

    def print_summary(self, stats, dry_run):
        """Print collection summary"""
        self.stdout.write(self.style.NOTICE('\n' + '=' * 50))
        self.stdout.write(self.style.NOTICE('Collection Summary'))
        self.stdout.write('=' * 50)

        if dry_run:
            self.stdout.write(self.style.WARNING('  (DRY RUN - no data saved)'))

        self.stdout.write(f'  Total members:    {stats["total"]}')
        self.stdout.write(self.style.SUCCESS(f'  Successful:       {stats["success"]}'))

        if not dry_run:
            self.stdout.write(f'    - Created:      {stats["created"]}')
            self.stdout.write(f'    - Updated:      {stats["updated"]}')

        if stats['failed'] > 0:
            self.stdout.write(self.style.ERROR(f'  Failed:           {stats["failed"]}'))
            if stats['errors'][:5]:
                self.stdout.write(self.style.WARNING('\n  Recent errors:'))
                for err in stats['errors'][:5]:
                    self.stdout.write(f'    - {err}')

        if not dry_run:
            # Database totals
            total_players = DestinyPlayer.objects.count()
            total_chars = DestinyCharacter.objects.count()
            self.stdout.write(f'\n  Database totals:')
            self.stdout.write(f'    - Players:      {total_players}')
            self.stdout.write(f'    - Characters:   {total_chars}')
