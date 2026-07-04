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

## Deploying to Railway

This project is designed to deploy on [Railway](https://railway.com) with four services: a web server, a Celery worker, PostgreSQL, and Redis.

### One-click deploy

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/template)

### Manual setup

1. **Push this repo to GitHub**
2. **Create a new Railway project** at https://railway.com/new
3. **Select "Deploy from GitHub repo"** and choose your repository
4. **Add a PostgreSQL database** — Click **Create** → **Database** → **Add PostgreSQL**
5. **Add a Redis database** — Click **Create** → **Database** → **Add Redis**
6. **Configure the web service** — Railway auto-detects Django. Set these environment variables using the Raw Editor (use `${{ServiceName.KEY}}` reference syntax):

   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   REDIS_URL=${{Redis.REDIS_URL}}
   SECRET_KEY=<generate a secure random key>
   DEBUG=False
   ALLOWED_HOSTS=.railway.app
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=<choose a password>
   ```

   The `railway.json` at the project root sets the build and start commands automatically.

7. **Set up the Celery worker** — Click **Create** → **Empty Service**. Connect the same GitHub repo, then under **Settings → Deploy**, set the **Custom Start Command** to:

   ```
   celery -A family_photos worker -l info
   ```

   Add the same environment variables from step 6.

### Service overview

| Service | Type | Start Command |
|---|---|---|
| Web (auto-created) | Public | `gunicorn family_photos.wsgi` |
| Worker (manual) | Private | `celery -A family_photos worker -l info` |
| PostgreSQL | Plugin | — |
| Redis | Plugin | — |

### Required environment variables

All services need these variables (use Railway's `${{Service.KEY}}` reference syntax):

| Variable | Reference | Purpose |
|---|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | PostgreSQL connection |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | Celery broker |
| `SECRET_KEY` | Generate a random value | Django signing |
| `DEBUG` | `False` | Production mode |
| `ALLOWED_HOSTS` | `.railway.app` | Allowed domains |
| `CSRF_TRUSTED_ORIGINS` | `https://your-custom-domain.com` | Required for custom domains |
| `ADMIN_USERNAME` | Your choice | Auto-creates superuser |
| `ADMIN_PASSWORD` | Your choice | Superuser password |

### Notes

- Only the web service needs a public domain — generate one under **Settings → Networking → Generate Domain**.
- The worker connects to the same PostgreSQL and Redis over Railway's private network.
- Railway's free tier includes $5 of free credits per month, enough for this stack.

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
