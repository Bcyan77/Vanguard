# Generated manually for party->fireteam rename
# This migration handles both app table prefix (parties_ -> fireteams_) and model rename (Party -> Fireteam)

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fireteams', '0005_destinyactivitytype_canonical_entry_and_more'),
    ]

    operations = [
        # Step 1: Rename database tables from parties_* to fireteams_* using raw SQL
        migrations.RunSQL(
            'ALTER TABLE parties_party RENAME TO fireteams_fireteam;',
            'ALTER TABLE fireteams_fireteam RENAME TO parties_party;',
        ),
        migrations.RunSQL(
            'ALTER TABLE parties_partymember RENAME TO fireteams_fireteammember;',
            'ALTER TABLE fireteams_fireteammember RENAME TO parties_partymember;',
        ),
        migrations.RunSQL(
            'ALTER TABLE parties_partytag RENAME TO fireteams_fireteamtag;',
            'ALTER TABLE fireteams_fireteamtag RENAME TO parties_partytag;',
        ),
        migrations.RunSQL(
            'ALTER TABLE parties_partyapplication RENAME TO fireteams_fireteamapplication;',
            'ALTER TABLE fireteams_fireteamapplication RENAME TO parties_partyapplication;',
        ),
        migrations.RunSQL(
            'ALTER TABLE parties_activitymodeavailability RENAME TO fireteams_activitymodeavailability;',
            'ALTER TABLE fireteams_activitymodeavailability RENAME TO parties_activitymodeavailability;',
        ),
        migrations.RunSQL(
            'ALTER TABLE parties_destinyactivitymode RENAME TO fireteams_destinyactivitymode;',
            'ALTER TABLE fireteams_destinyactivitymode RENAME TO parties_destinyactivitymode;',
        ),
        migrations.RunSQL(
            'ALTER TABLE parties_destinyspecificactivity RENAME TO fireteams_destinyspecificactivity;',
            'ALTER TABLE fireteams_destinyspecificactivity RENAME TO parties_destinyspecificactivity;',
        ),
        # Rename parties_destinyactivity to fireteams_destinyactivity
        migrations.RunSQL(
            'ALTER TABLE parties_destinyactivity RENAME TO fireteams_destinyactivity;',
            'ALTER TABLE fireteams_destinyactivity RENAME TO parties_destinyactivity;',
        ),

        # Step 2: Rename the FK column party_id to fireteam_id
        migrations.RunSQL(
            'ALTER TABLE fireteams_fireteammember RENAME COLUMN party_id TO fireteam_id;',
            'ALTER TABLE fireteams_fireteammember RENAME COLUMN fireteam_id TO party_id;',
        ),
        migrations.RunSQL(
            'ALTER TABLE fireteams_fireteamtag RENAME COLUMN party_id TO fireteam_id;',
            'ALTER TABLE fireteams_fireteamtag RENAME COLUMN fireteam_id TO party_id;',
        ),
        migrations.RunSQL(
            'ALTER TABLE fireteams_fireteamapplication RENAME COLUMN party_id TO fireteam_id;',
            'ALTER TABLE fireteams_fireteamapplication RENAME COLUMN fireteam_id TO party_id;',
        ),

        # Step 3: Rename indexes from parties_* to fireteams_*
        # SQLite doesn't support ALTER INDEX, so we drop and recreate
        # Index on destinyactivitymode
        migrations.RunSQL(
            'DROP INDEX IF EXISTS parties_des_is_acti_829621_idx;',
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'CREATE INDEX IF NOT EXISTS fireteams_d_is_acti_5c28d3_idx ON fireteams_destinyactivitymode (is_active, display_order);',
            'DROP INDEX IF EXISTS fireteams_d_is_acti_5c28d3_idx;',
        ),
        # Index on destinyactivitytype
        migrations.RunSQL(
            'DROP INDEX IF EXISTS parties_des_is_acti_efa391_idx;',
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'CREATE INDEX IF NOT EXISTS fireteams_d_is_acti_0914c3_idx ON fireteams_destinyactivity (is_active, name);',
            'DROP INDEX IF EXISTS fireteams_d_is_acti_0914c3_idx;',
        ),
        # Index on destinyspecificactivity
        migrations.RunSQL(
            'DROP INDEX IF EXISTS parties_des_activit_142e88_idx;',
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'CREATE INDEX IF NOT EXISTS fireteams_d_activit_1f4f12_idx ON fireteams_destinyspecificactivity (activity_type_id, is_active);',
            'DROP INDEX IF EXISTS fireteams_d_activit_1f4f12_idx;',
        ),

        # Step 4: Update migration state to recognize the new model names
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameModel(
                    old_name='Party',
                    new_name='Fireteam',
                ),
                migrations.RenameModel(
                    old_name='PartyMember',
                    new_name='FireteamMember',
                ),
                migrations.RenameModel(
                    old_name='PartyTag',
                    new_name='FireteamTag',
                ),
                migrations.RenameModel(
                    old_name='PartyApplication',
                    new_name='FireteamApplication',
                ),
                migrations.RenameField(
                    model_name='fireteammember',
                    old_name='party',
                    new_name='fireteam',
                ),
                migrations.RenameField(
                    model_name='fireteamtag',
                    old_name='party',
                    new_name='fireteam',
                ),
                migrations.RenameField(
                    model_name='fireteamapplication',
                    old_name='party',
                    new_name='fireteam',
                ),
                migrations.AlterModelOptions(
                    name='fireteam',
                    options={'ordering': ['-created_at'], 'verbose_name': 'Fireteam', 'verbose_name_plural': 'Fireteams'},
                ),
                migrations.AlterModelOptions(
                    name='fireteammember',
                    options={'ordering': ['joined_at'], 'verbose_name': 'Fireteam Member', 'verbose_name_plural': 'Fireteam Members'},
                ),
                migrations.AlterModelOptions(
                    name='fireteamtag',
                    options={'verbose_name': 'Fireteam Tag', 'verbose_name_plural': 'Fireteam Tags'},
                ),
                migrations.AlterModelOptions(
                    name='fireteamapplication',
                    options={'ordering': ['-applied_at'], 'verbose_name': 'Fireteam Application', 'verbose_name_plural': 'Fireteam Applications'},
                ),
                migrations.AlterUniqueTogether(
                    name='fireteammember',
                    unique_together={('fireteam', 'user')},
                ),
                migrations.AlterUniqueTogether(
                    name='fireteamtag',
                    unique_together={('fireteam', 'name')},
                ),
                migrations.AlterUniqueTogether(
                    name='fireteamapplication',
                    unique_together={('fireteam', 'applicant')},
                ),
            ],
            database_operations=[],
        ),
    ]
