"""
Management command to normalize Bungie API activity data for 3-tier dropdown system

This command:
1. Parses activity names to extract difficulty/mode information
2. Deduplicates Activity Type entries with the same name
3. Auto-links activities to modes based on parsed information

Usage:
    python manage.py normalize_activity_data [--dry-run] [--step STEP]

    --dry-run: Preview changes without modifying database
    --step: Run specific step (parse|deduplicate|link|all)
"""

import re
import logging
from django.core.management.base import BaseCommand
from django.db.models import Count
from parties.models import (
    DestinyActivityType,
    DestinySpecificActivity,
    DestinyActivityMode,
    ActivityModeAvailability,
    Party
)

logger = logging.getLogger(__name__)


# Keywords for identifying difficulty and mode in activity names
DIFFICULTY_KEYWORDS = {
    'heroic', 'legend', 'legendary', 'master', 'grandmaster',
    'expert', 'normal', 'hard', 'prestige', 'nightmare',
    'adept', 'contest', 'guided'
}

MODE_KEYWORDS = {
    'matchmade', 'private', 'guided', 'solo', 'fireteam',
    'competitive', 'quickplay', 'freelance', 'classic', 'labs'
}


class Command(BaseCommand):
    help = 'Normalize activity data for 3-tier dropdown system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without modifying database',
        )
        parser.add_argument(
            '--step',
            type=str,
            choices=['parse', 'deduplicate', 'link', 'all'],
            default='all',
            help='Which step to run (default: all)',
        )

    def handle(self, *args, **options):
        """Main command handler"""
        dry_run = options['dry_run']
        step = options['step']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN MODE (no database changes) ===\n'))

        self.stdout.write(self.style.NOTICE('Starting activity data normalization...\n'))

        # Run requested steps
        if step in ['parse', 'all']:
            self.parse_activity_names(dry_run)

        if step in ['deduplicate', 'all']:
            self.deduplicate_activity_types(dry_run)

        if step in ['link', 'all']:
            self.auto_link_modes(dry_run)

        self.stdout.write(self.style.SUCCESS('\n✓ Normalization completed!'))

    def parse_activity_names(self, dry_run=False):
        """
        Parse activity names to extract clean name, difficulty, and mode
        """
        self.stdout.write(self.style.NOTICE('\n=== STEP 1: Parsing Activity Names ==='))

        activities = DestinySpecificActivity.objects.filter(is_active=True)
        total_count = activities.count()

        parsed_count = 0
        review_count = 0
        clean_count = 0

        for activity in activities:
            # Skip if already parsed
            if activity.original_name:
                continue

            # Parse the name
            result = self._parse_name(activity.name)

            # Check if parsing changed anything
            if result['clean_name'] != activity.name or result['difficulty'] or result['mode']:
                parsed_count += 1

                if not dry_run:
                    activity.original_name = activity.name
                    activity.name = result['clean_name']
                    activity.parsed_clean_name = result['clean_name']
                    activity.parsed_difficulty = result['difficulty']
                    activity.parsed_mode = result['mode']
                    activity.parsing_notes = result['notes']
                    activity.needs_manual_review = result['needs_review']
                    activity.save()

                if result['needs_review']:
                    review_count += 1
                    self.stdout.write(
                        f'  ⚠ Review: "{activity.name}" → "{result["clean_name"]}"'
                        f'\n    Difficulty: {result["difficulty"]}, Mode: {result["mode"]}'
                        f'\n    Notes: {result["notes"]}\n'
                    )
            else:
                clean_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nParsing Results:'
            f'\n  Total activities: {total_count}'
            f'\n  Parsed: {parsed_count}'
            f'\n  Clean (no changes): {clean_count}'
            f'\n  Flagged for review: {review_count}'
        ))

    def _parse_name(self, name):
        """
        Parse activity name to extract clean name, difficulty, and mode

        Returns dict with:
            - clean_name: Activity name without mode/difficulty
            - difficulty: Extracted difficulty string
            - mode: Extracted mode string
            - pattern: Which pattern matched
            - notes: Human-readable parsing notes
            - needs_review: Boolean flag for ambiguous cases
        """
        result = {
            'clean_name': name,
            'difficulty': '',
            'mode': '',
            'pattern': 'clean',
            'notes': '',
            'needs_review': False
        }

        # PATTERN 1: Leading parentheses (Heroic) Activity Name
        if name.startswith('(') and ')' in name:
            match = re.match(r'^\(([^)]+)\)\s*(.+)$', name)
            if match:
                difficulty_text = match.group(1).strip()
                clean_name = match.group(2).strip()

                result['difficulty'] = difficulty_text
                result['clean_name'] = clean_name
                result['pattern'] = 'leading_paren'
                result['notes'] = f'Extracted leading difficulty: {difficulty_text}'
                return result

        # PATTERN 2: Trailing parentheses Activity Name (Expert) or (Expert | Private)
        if name.endswith(')') and '(' in name:
            last_open_paren = name.rfind('(')
            if last_open_paren > 0:
                clean_part = name[:last_open_paren].strip()
                paren_content = name[last_open_paren+1:-1].strip()

                # Verify content looks like mode/difficulty
                if self._is_mode_or_difficulty(paren_content):
                    result['clean_name'] = clean_part
                    result['pattern'] = 'trailing_paren'

                    # Handle pipe-separated: (Expert | Private)
                    if '|' in paren_content:
                        parts = [p.strip() for p in paren_content.split('|')]
                        result['difficulty'] = parts[0] if len(parts) > 0 else ''
                        result['mode'] = parts[1] if len(parts) > 1 else ''
                        result['notes'] = f'Pipe-separated: {paren_content}'
                    else:
                        # Classify as difficulty or mode
                        if self._is_difficulty_keyword(paren_content):
                            result['difficulty'] = paren_content
                        else:
                            result['mode'] = paren_content
                        result['notes'] = f'Trailing: {paren_content}'

                    return result

        # PATTERN 3: Colon-separated Location: Activity: Mode
        if ':' in name:
            parts = [p.strip() for p in name.split(':')]

            # EDGE CASE: Starts with colon (": Matchmade")
            if name.startswith(':'):
                result['mode'] = parts[-1] if parts else ''
                result['clean_name'] = ''
                result['pattern'] = 'colon_pattern'
                result['needs_review'] = True
                result['notes'] = 'EDGE CASE: Leading colon, empty activity name'
                return result

            # Check if last segment is a mode keyword
            last_part = parts[-1]
            if self._is_mode_keyword(last_part):
                result['mode'] = last_part
                result['clean_name'] = ':'.join(parts[:-1]).strip()
                result['pattern'] = 'colon_pattern'
                result['notes'] = f'Mode from last segment: {last_part}'
                return result

            # Check if any segment is a difficulty keyword
            for i, part in enumerate(parts):
                if self._is_difficulty_keyword(part):
                    result['difficulty'] = part
                    remaining = [p for j, p in enumerate(parts) if j != i]
                    result['clean_name'] = ':'.join(remaining).strip()
                    result['pattern'] = 'colon_pattern'
                    result['notes'] = f'Difficulty from segment {i}: {part}'
                    return result

            # Complex colon pattern with no clear mode/difficulty
            if len(parts) > 2:
                result['needs_review'] = True
                result['notes'] = f'Complex colon pattern ({len(parts)} parts), unclear mode/difficulty'

        # PATTERN 4: No pattern matched - clean name
        return result

    def _is_mode_or_difficulty(self, text):
        """Check if text looks like a mode or difficulty keyword"""
        lower_text = text.lower()
        return (
            self._is_difficulty_keyword(text) or
            self._is_mode_keyword(text) or
            '|' in text  # Pipe-separated is likely mode/difficulty
        )

    def _is_difficulty_keyword(self, text):
        """Check if text matches a difficulty keyword"""
        lower_text = text.lower().strip()
        return lower_text in DIFFICULTY_KEYWORDS

    def _is_mode_keyword(self, text):
        """Check if text matches a mode keyword"""
        lower_text = text.lower().strip()
        return lower_text in MODE_KEYWORDS

    def deduplicate_activity_types(self, dry_run=False):
        """
        Deduplicate Activity Types with the same name
        Keeps canonical entry (has_icon=True, lowest index, lowest hash)
        """
        self.stdout.write(self.style.NOTICE('\n=== STEP 2: Deduplicating Activity Types ==='))

        # Find all duplicate names
        duplicates = DestinyActivityType.objects.values('name').annotate(
            count=Count('hash')
        ).filter(count__gt=1).order_by('-count')

        stats = {
            'groups_processed': 0,
            'entries_marked_duplicate': 0,
            'fk_updates_specific_activity': 0,
            'fk_updates_party': 0
        }

        for dup_info in duplicates:
            name = dup_info['name']

            # Get all entries with this name, ordered by preference
            entries = DestinyActivityType.objects.filter(name=name).order_by(
                '-has_icon',  # Prefer entries with icons
                'index',      # Then prefer lowest index
                'hash'        # Tie-breaker: lowest hash
            )

            canonical = entries.first()
            duplicates_to_merge = entries[1:]

            self.stdout.write(
                f'\n{name} ({dup_info["count"]} entries):'
                f'\n  CANONICAL: Hash {canonical.hash} '
                f'(index={canonical.index}, icon={canonical.has_icon})'
            )

            if not dry_run:
                # Mark canonical entry
                canonical.is_canonical = True
                canonical.duplicate_group_name = name
                canonical.save()

                # Process each duplicate
                for dup_entry in duplicates_to_merge:
                    # Mark as duplicate (do NOT delete - preserve for reference)
                    dup_entry.is_canonical = False
                    dup_entry.canonical_entry = canonical
                    dup_entry.duplicate_group_name = name
                    dup_entry.is_active = False  # Hide from dropdowns
                    dup_entry.save()

                    # Update FK: DestinySpecificActivity.activity_type
                    specific_count = DestinySpecificActivity.objects.filter(
                        activity_type=dup_entry
                    ).update(activity_type=canonical)

                    # Update FK: Party.selected_activity_type
                    party_count = Party.objects.filter(
                        selected_activity_type=dup_entry
                    ).update(selected_activity_type=canonical)

                    total_updated = specific_count + party_count

                    stats['entries_marked_duplicate'] += 1
                    stats['fk_updates_specific_activity'] += specific_count
                    stats['fk_updates_party'] += party_count

                    self.stdout.write(
                        f'  DUPLICATE: Hash {dup_entry.hash} → '
                        f'Remapped {total_updated} FK references '
                        f'({specific_count} activities, {party_count} parties)'
                    )
            else:
                # Dry run - just show what would happen
                for dup_entry in duplicates_to_merge:
                    specific_count = DestinySpecificActivity.objects.filter(
                        activity_type=dup_entry
                    ).count()
                    party_count = Party.objects.filter(
                        selected_activity_type=dup_entry
                    ).count()

                    self.stdout.write(
                        f'  DUPLICATE: Hash {dup_entry.hash} → '
                        f'Would remap {specific_count + party_count} FK references'
                    )

            stats['groups_processed'] += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDeduplication Results:'
            f'\n  Duplicate groups: {stats["groups_processed"]}'
            f'\n  Entries marked as duplicates: {stats["entries_marked_duplicate"]}'
            f'\n  FK updates (SpecificActivity): {stats["fk_updates_specific_activity"]}'
            f'\n  FK updates (Party): {stats["fk_updates_party"]}'
        ))

    def auto_link_modes(self, dry_run=False):
        """
        Auto-link activities to modes based on parsed difficulty/mode information
        """
        self.stdout.write(self.style.NOTICE('\n=== STEP 3: Auto-Linking Modes ==='))

        # Build lookup dictionary: lowercase name → DestinyActivityMode
        modes_by_name = {}
        for mode in DestinyActivityMode.objects.filter(is_active=True):
            modes_by_name[mode.name.lower()] = mode

        # Get all activities with parsed difficulty or mode
        activities_to_link = DestinySpecificActivity.objects.filter(
            is_active=True
        ).exclude(
            parsed_difficulty='',
            parsed_mode=''
        )

        stats = {
            'total_activities': DestinySpecificActivity.objects.count(),
            'activities_with_parsed_info': activities_to_link.count(),
            'links_created': 0,
            'links_already_existed': 0,
            'no_match_found': []
        }

        for activity in activities_to_link:
            # Try to match difficulty
            if activity.parsed_difficulty:
                mode = self._find_matching_mode(
                    activity.parsed_difficulty,
                    modes_by_name
                )
                if mode:
                    if not dry_run:
                        link, created = ActivityModeAvailability.objects.get_or_create(
                            specific_activity=activity,
                            activity_mode=mode
                        )
                        if created:
                            stats['links_created'] += 1
                            self.stdout.write(
                                f'  ✓ Linked {activity.name} → {mode.name} (difficulty)'
                            )
                        else:
                            stats['links_already_existed'] += 1
                    else:
                        stats['links_created'] += 1
                else:
                    stats['no_match_found'].append({
                        'activity': activity.name,
                        'parsed': activity.parsed_difficulty,
                        'type': 'difficulty'
                    })

            # Try to match mode (separately, can have both)
            if activity.parsed_mode:
                mode = self._find_matching_mode(
                    activity.parsed_mode,
                    modes_by_name
                )
                if mode:
                    if not dry_run:
                        link, created = ActivityModeAvailability.objects.get_or_create(
                            specific_activity=activity,
                            activity_mode=mode
                        )
                        if created:
                            stats['links_created'] += 1
                            self.stdout.write(
                                f'  ✓ Linked {activity.name} → {mode.name} (mode)'
                            )
                        else:
                            stats['links_already_existed'] += 1
                    else:
                        stats['links_created'] += 1
                else:
                    stats['no_match_found'].append({
                        'activity': activity.name,
                        'parsed': activity.parsed_mode,
                        'type': 'mode'
                    })

        # Report unmatched
        if stats['no_match_found']:
            self.stdout.write(self.style.WARNING(
                f'\n{len(stats["no_match_found"])} unmatched terms:'
            ))
            for item in stats['no_match_found'][:20]:  # Show first 20
                self.stdout.write(
                    f'  ✗ No match: "{item["parsed"]}" ({item["type"]}) '
                    f'in {item["activity"]}'
                )

        self.stdout.write(self.style.SUCCESS(
            f'\nMode Linking Results:'
            f'\n  Activities with parsed info: {stats["activities_with_parsed_info"]}'
            f'\n  Links created: {stats["links_created"]}'
            f'\n  Links already existed: {stats["links_already_existed"]}'
            f'\n  Terms without match: {len(stats["no_match_found"])}'
        ))

    def _find_matching_mode(self, parsed_text, modes_by_name):
        """
        Find matching DestinyActivityMode for parsed text

        Tries three strategies:
        1. Exact match (case-insensitive)
        2. Parsed text contained in mode name
        3. Mode name contained in parsed text
        """
        parsed_lower = parsed_text.lower().strip()

        # Strategy 1: Exact match
        if parsed_lower in modes_by_name:
            return modes_by_name[parsed_lower]

        # Strategy 2: Parsed text in mode name (e.g., "hero" matches "Heroic Adventure")
        for mode_name, mode_obj in modes_by_name.items():
            if parsed_lower in mode_name:
                return mode_obj

        # Strategy 3: Mode name in parsed text (e.g., "Heroic" matches "heroic adventure")
        for mode_name, mode_obj in modes_by_name.items():
            if mode_name in parsed_lower:
                return mode_obj

        return None
