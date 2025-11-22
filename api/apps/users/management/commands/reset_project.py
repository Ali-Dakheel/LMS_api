import os
import shutil
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from django.core.management import call_command

APPS_TO_RESET = [
    'academics',
    'administration',
    'ai_tools',
    'assessments',
    'communications',
    'content',
    'courses',
    'progress',
    'users'
]

class Command(BaseCommand):
    help = "Fully resets the database and all migrations for selected apps."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(' Resetting project...'))

        #  DELETE MIGRATION FILES AND __pycache__ FOLDERS
        self.stdout.write('Deleting migration files...')
        for app in APPS_TO_RESET:
            migrations_dir = os.path.join(settings.BASE_DIR, 'apps', app, 'migrations')
            if os.path.exists(migrations_dir):
                for filename in os.listdir(migrations_dir):
                    if filename == "__init__.py":
                        continue
                    file_path = os.path.join(migrations_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        self.stdout.write(f"  Deleted file: {file_path}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        self.stdout.write(f"  Deleted folder: {file_path}")

        #  CLEAR DJANGO MIGRATION HISTORY (if table exists)
        self.stdout.write('Clearing django_migrations entries...')
        with connection.cursor() as cursor:
            cursor.execute("""
                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename='django_migrations') THEN
                        DELETE FROM django_migrations;
                    END IF;
                END
                $$;
            """)
        self.stdout.write(self.style.SUCCESS('✔ django_migrations cleared (if existed).'))

        #  DROP ALL TABLES
        self.stdout.write('Dropping all tables...')
        with connection.cursor() as cursor:
            cursor.execute("""
                DO $$ DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
                        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                END $$;
            """)
        self.stdout.write(self.style.SUCCESS('✔ All tables dropped.'))

        #  REBUILD MIGRATIONS
        self.stdout.write('Recreating migrations...')
        call_command('makemigrations')

        #  APPLY MIGRATIONS
        self.stdout.write('Applying migrations...')
        call_command('migrate')

        self.stdout.write(self.style.SUCCESS('Project fully reset to a clean state!'))
