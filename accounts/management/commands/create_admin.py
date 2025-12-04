from django.core.management.base import BaseCommand
from accounts.models import BungieUser


class Command(BaseCommand):
    help = 'Create admin account with username and password'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Admin username')
        parser.add_argument(
            '--password',
            type=str,
            help='Admin password (will prompt if not provided)',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options.get('password')

        # Check if username already exists
        if BungieUser.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(
                f'Username "{username}" already exists'
            ))
            return

        # Check if bungie_membership_id collision
        admin_id = f'admin_{username}'
        if BungieUser.objects.filter(bungie_membership_id=admin_id).exists():
            self.stdout.write(self.style.ERROR(
                f'Admin ID collision: {admin_id} already exists'
            ))
            return

        # Get password
        if not password:
            from getpass import getpass
            password = getpass('Password: ')
            password_confirm = getpass('Password (again): ')

            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Passwords do not match'))
                return

        # Create admin user
        try:
            user = BungieUser.objects.create_admin_user(
                username=username,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(
                f'Successfully created admin account: {username}'
            ))
            self.stdout.write(f'  - bungie_membership_id: {user.bungie_membership_id}')
            self.stdout.write(f'  - is_staff: {user.is_staff}')
            self.stdout.write(f'  - is_superuser: {user.is_superuser}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to create admin: {e}'))
