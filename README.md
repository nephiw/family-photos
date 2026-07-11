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

### 2. Set up environment variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

At minimum, fill in `SECRET_KEY` and set `DEBUG=True`. For S3 support, set `USE_S3=True` and provide AWS credentials.

### 3. Run database migrations

```bash
python manage.py migrate
```

### 4. Install and start Redis

Celery uses Redis as a message broker for async thumbnail/medium generation.

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

### 5. Start the Celery worker

In a separate terminal, activate the venv and start the worker:

```bash
source venv/bin/activate
celery -A family_photos worker -l info
```

### 6. Start the development server

```bash
python manage.py runserver
```

### 7. (Optional) Generate thumbnails / medium images for existing photos

If you already uploaded photos before setting up Redis/Celery, generate their thumbnails and web-optimized images:

```bash
python manage.py generate_thumbnails
```

For large batches, you can queue via Celery instead (requires running worker):

```bash
python manage.py generate_thumbnails --async
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
6. **Configure the web service** — Add these environment variables (use Railway's `${{Service.KEY}}` reference syntax):

   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   REDIS_URL=${{Redis.REDIS_URL}}
   SECRET_KEY=<generate a secure random key>
   DEBUG=False
   ALLOWED_HOSTS=.railway.app
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=<choose a password>
   ```

   Then under **Settings**, configure:
   - **Start Command**: `gunicorn family_photos.wsgi`
   - **Pre-deploy Command**: `python manage.py migrate`
   - **Healthcheck Path**: `/`

7. **Set up the Celery worker** — Click **Create** → **Empty Service**. Connect the same GitHub repo. Add the same environment variables from step 6. Under **Settings**, configure:

   - **Start Command**: `celery -A family_photos worker --loglevel=info`
   - **Pre-deploy Command**: leave empty (workers never run migrations)
   - **Healthcheck Path**: leave empty (workers don't serve HTTP)

### S3 storage (optional)

The site can store photos on AWS S3 instead of the local filesystem.

1. **Create an S3 bucket** in your preferred region
2. **Create an IAM user** with this policy (replace the bucket ARN):

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::your-bucket-name",
           "arn:aws:s3:::your-bucket-name/*"
         ]
       }
     ]
   }
   ```

3. **Add these environment variables** to both the web and worker services:

   ```
   USE_S3=True
   AWS_ACCESS_KEY_ID=<your-access-key>
   AWS_SECRET_ACCESS_KEY=<your-secret-key>
   AWS_STORAGE_BUCKET_NAME=<your-bucket-name>
   AWS_S3_REGION_NAME=<your-bucket-region>
   ```

### Service overview

| Service | Type | Start Command | Pre-deploy | Healthcheck |
|---|---|---|---|---|
| Web (auto-created) | Public | `gunicorn family_photos.wsgi` | `python manage.py migrate` | `/` |
| Worker (manual) | Private | `celery -A family_photos worker --loglevel=info` | (none) | (none) |
| PostgreSQL | Plugin | — | — | — |
| Redis | Plugin | — | — | — |

### Required environment variables

All services need these variables (use Railway's `${{Service.KEY}}` reference syntax):

| Variable | Reference / Value | Purpose |
|---|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | PostgreSQL connection |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | Celery broker |
| `SECRET_KEY` | Generate a random value | Django signing |
| `DEBUG` | `False` | Production mode |
| `ALLOWED_HOSTS` | `.railway.app` | Allowed domains |
| `CSRF_TRUSTED_ORIGINS` | `https://your-custom-domain.com` | Required for custom domains |
| `ADMIN_USERNAME` | Your choice | Auto-creates superuser |
| `ADMIN_PASSWORD` | Your choice | Superuser password |

### Custom domain

If you use a custom domain (e.g., `photos.nephiw.com`):

1. Add the domain in **Web service → Settings → Networking → Custom Domain**
2. Point your DNS to the CNAME target shown in Railway
3. Set these environment variables:

   ```
   RAILWAY_PUBLIC_DOMAIN=photos.yourdomain.com
   CSRF_TRUSTED_ORIGINS=https://photos.yourdomain.com
   ```

   Update `ALLOWED_HOSTS` to include your domain:
   ```
   ALLOWED_HOSTS=.railway.app,photos.yourdomain.com
   ```

### One-off commands (e.g., generate missing thumbnails)

Use the **Console** tab in the Railway dashboard for your web service. This runs inside the running container with full access to the private network:

```bash
python manage.py generate_thumbnails
```

For photos that were uploaded before the `medium` image field was added, this will generate both the 600x600 thumbnail and the 1920x1920 web-optimized version.

### Upload limits

Multiple concurrent uploads are limited to 4 simultaneous XHR requests. Django enforces a 50MB per-request limit and streams files larger than 1MB to disk.

### Notes

- Only the web service needs a public domain — generate one under **Settings → Networking → Generate Domain**.
- The worker connects to the same PostgreSQL and Redis over Railway's private network.
- Railway's free tier includes $5 of free credits per month, enough for this stack.
- The `railway.json` file only contains build configuration — all deploy settings (healthcheck, pre-deploy, start command) are configured per-service in the Railway dashboard.

## Current Capabilities

* Upload photos with drag-and-drop or file picker
* Organize photos into **albums** (each user has private albums + a shared "Family Photos" album)
* **Bulk actions** — select multiple photos to delete, add to another album, or create a new album from selection
* **Download** — download all photos or individual albums as ZIP files
* View photos with EXIF metadata, date taken, and album tags
* Photo detail view with prev/next navigation following sort order
* **Admin user management** — create, edit, and view family member accounts
* **Admin album oversight** — admins can view any user's private albums via `/users/:id/albums`
* Login as administrator or family member
* Thumbnails and web-optimized medium images generated asynchronously via Celery
* Retro 80s synthwave/neon UI theme

# Bugs
* Drag and Drop photo upload does not work in the Chrome browser, but it does work in all of the other browsers I have tested.

## Near Future Capabilities
* Soft delete / trash can for photos with auto-cleanup
* Swipe-based mobile photo viewer (swipe up/down for prev/next, left/right for album management)
* Album sharing between users (currently albums are private to their creator)
* Facial recognition to auto-sort photos into face-based albums

## Far Future Capabilities

These are things I want to add eventually, but not right away.
* Facial recognition and the ability to auto-add photos of yourself or family members to face based photo album
* Show a map of where photos were taken as a heat map
* Sorting / Filtering by face, location, or other things
