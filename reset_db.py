#!/usr/bin/env python3
import os
import shutil
import glob
import django

def main():
    print("=== Teardown & Reset Script ===")
    
    # 1. Delete SQLite database
    db_path = 'db.sqlite3'
    if os.path.exists(db_path):
        print(f"Removing database: {db_path}...")
        try:
            os.remove(db_path)
            print("Database removed successfully.")
        except Exception as e:
            print(f"Error removing database: {e}")
    else:
        print("No database file found to remove.")

    # 2. Clean up media folders (photos & thumbnails)
    media_dirs = ['media/photos', 'media/thumbnails']
    for media_dir in media_dirs:
        if os.path.exists(media_dir):
            print(f"Cleaning media folder: {media_dir}...")
            # Delete all files inside directory
            files = glob.glob(os.path.join(media_dir, '*'))
            for f in files:
                try:
                    if os.path.isfile(f):
                        os.remove(f)
                    elif os.path.isdir(f):
                        shutil.rmtree(f)
                except Exception as e:
                    print(f"Error deleting {f}: {e}")
            print(f"Folder {media_dir} cleaned.")
        else:
            # Ensure folder exists
            os.makedirs(media_dir, exist_ok=True)
            print(f"Created media folder: {media_dir}")

    # Set up Django environment settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_photos.settings')
    
    # 3. Run django setup and migrations
    print("Running migrations...")
    django.setup()
    from django.core.management import call_command
    try:
        call_command('migrate', interactive=False)
        print("Migrations completed successfully.")
    except Exception as e:
        print(f"Error running migrations: {e}")
        return

    # 4. Create default accounts
    print("Creating default users...")
    from django.contrib.auth.models import User
    try:
        # Create administrator
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@family.com',
            password='adminpass123'
        )
        print(f"Created Superuser: username='{admin_user.username}', password='adminpass123'")
        
        # Create normal family member
        family_user = User.objects.create_user(
            username='family',
            email='family@family.com',
            password='familypass123'
        )
        print(f"Created Family Member: username='{family_user.username}', password='familypass123'")
        
        print("=== Teardown & Rebuild Complete! ===")
    except Exception as e:
        print(f"Error creating default users: {e}")

if __name__ == '__main__':
    main()
