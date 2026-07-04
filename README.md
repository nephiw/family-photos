# Family Photo Site

## Overview

I created this site to share photos with my family. I designed it to have a retro futuristic theme. It is built with Django and htmx, neither of which I am all that familiar with. I am using opencode to help me create the site.

## Installation

To run the site locally:

### 1. Install Python dependencies

Activate the virtual environment and install dependencies:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Install and start Redis

Celery uses Redis as a message broker for async thumbnail generation.

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Linux (apt):**
```bash
sudo apt install redis-server
sudo service redis-server start
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### 3. Start the Celery worker

In a separate terminal, activate the venv and start the worker:

```bash
source venv/bin/activate
celery -A family_photos worker -l info
```

### 4. Start the development server

```bash
python manage.py runserver
```

### 5. (Optional) Generate thumbnails for existing photos

If you already uploaded photos before setting up Redis/Celery, generate their thumbnails:

```bash
python manage.py generate_thumbnails
```

### Run tests

```bash
python manage.py test gallery
```

## Deploying to Render

This project includes a `render.yaml` for infrastructure-as-code deployment on [Render](https://render.com).

### One-click deploy

1. Push this repo to GitHub/GitLab
2. In the Render dashboard, click **New Blueprint**
3. Connect your repository
4. Render reads `render.yaml` and creates three services automatically:

| Service | Type | Purpose |
|---|---|---|
| `family-photos` | Web | Django app (Gunicorn) |
| `family-photos-worker` | Worker | Celery async task processor |
| `family-photos-db` | PostgreSQL | Database |
| `family-photos-redis` | Redis | Celery message broker |

### Required environment variables

Render auto-generates `DATABASE_URL` (PostgreSQL) and `REDIS_URL` (Redis) from the managed services. The `SECRET_KEY` is generated automatically. Set these manually if needed:

- `ADMIN_USERNAME` / `ADMIN_PASSWORD` — auto-creates a superuser on first deploy
- `ALLOWED_HOSTS` — add your custom domain if you have one

### Celery worker

The worker service runs `celery -A family_photos worker -l info` and connects to the same Redis and PostgreSQL instances as the web service. No additional configuration is needed — Render starts and monitors it automatically.

### Important notes

- The free-tier Redis (`maxmemoryPolicy: allkeys-lru`) may evict older task results under memory pressure, but active tasks are not affected.
- The free-tier PostgreSQL has a 90-day idle timeout for inactive projects. Set up a cron or periodic health check to keep it alive.
- `render.yaml` uses the **Blueprint** (Infrastructure as Code) workflow. You can also create services manually via the Render dashboard instead.

## Current Capabilities

Currently, the site can:
* Upload Photos
* View photos
* Login as an administrator
* Login as a family member
* Admin's can create new family member accounts

# Bugs
* Drag and Drop phtoto upload does not work in the Chrome browser, but it does work in all of the other browsers I have tested.

## Near Future Capabilities
This is not even close to where I want it to be. Here are some of the things I want to add:
* Be able to undelete photos
  * Admin's can delete any photo
  * Family members can delete their own photos
  * Photos are put into a trash can and can be restored by the admin or original uploader
  * Photos and metadata are deleted permanently after a month in the trash, but I don't want to do a chron job, I want it to be checked when the photos are fetched as a side effect. Maybe in a different process?
* I want users to be able to create their own albums to organize the photos they like, and then be able to download the whole album as a zip file.
  * Albums are created by the user and can be named whatever they like
  * Albums can be downloaded as a zip file containing all the photos in the album
  * Albums can be shared with other family members to view or download
* Create a method of viewing photos where swiping up/down goes to previous or next photo while swiping left/right chooses to add it to a photo album or remove it from the current album
  * They can view all of the photos, or they can view an album. When they view an album, if they swipe left the photo is removed, swiping right the first time allows them to pick an album to add the photo to, or if one is already selected, adding the photo to that album.
  * Every user starts off with a default album that contains no photos.

## Far Future Capabilities

These are things I want to add eventually, but not right away.
* Facial recognition and the ability to auto-add photos of yourself or family members to face based photo album
* Show a map of where photos were taken as a heat map
* Sorting / Filtering by date taken, face, location, or other things
