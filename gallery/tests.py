from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import shutil
from io import BytesIO
from PIL import Image
from .models import Photo

TEMP_MEDIA_ROOT = tempfile.mkdtemp()

def get_temporary_image():
    file_obj = BytesIO()
    image = Image.new("RGB", (100, 100), (255, 0, 127))
    image.save(file_obj, "jpeg")
    file_obj.seek(0)
    return SimpleUploadedFile("test_image.jpg", file_obj.read(), content_type="image/jpeg")

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class GalleryTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='family_member', password='password123')
        self.admin = User.objects.create_superuser(username='admin_operator', password='adminpassword')

    def test_anonymous_redirect(self):
        response = self.client.get(reverse('gallery:home'))
        self.assertRedirects(response, '/auth/')

    def test_authenticated_home(self):
        self.client.login(username='family_member', password='password123')
        response = self.client.get(reverse('gallery:home'))
        self.assertRedirects(response, reverse('gallery:photo_list'))

    def test_authenticated_photo_list(self):
        self.client.login(username='family_member', password='password123')
        response = self.client.get(reverse('gallery:photo_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello, family_member!")
        self.assertContains(response, "No Photos Uploaded Yet")

    def test_upload_photo(self):
        self.client.login(username='family_member', password='password123')
        img = get_temporary_image()

        response = self.client.post(reverse('gallery:photo_upload'), {'photos': [img]})
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Photo.objects.count(), 1)
        photo = Photo.objects.first()
        self.assertEqual(photo.uploaded_by, self.user)

        # Thumbnail is now generated asynchronously; verify the generation logic still works
        thumbnail = photo.make_thumbnail()
        self.assertIsNotNone(thumbnail)
        self.assertTrue('_thumb' in thumbnail.name)
        self.assertTrue(thumbnail.name.endswith('.jpg'))

    def test_zip_download(self):
        self.client.login(username='family_member', password='password123')

        response = self.client.get(reverse('gallery:download_zip'))
        self.assertRedirects(response, reverse('gallery:photo_list'))

        img = get_temporary_image()
        self.client.post(reverse('gallery:photo_upload'), {'photos': [img]})

        response = self.client.get(reverse('gallery:download_zip'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename='))

    def test_admin_only_user_creation(self):
        self.client.login(username='family_member', password='password123')
        response = self.client.get(reverse('gallery:user_add'))
        # user_passes_test redirects to LOGIN_URL when not admin
        self.assertEqual(response.status_code, 302)

        self.client.login(username='admin_operator', password='adminpassword')
        response = self.client.get(reverse('gallery:user_add'))
        self.assertEqual(response.status_code, 200)

        post_data = {
            'username': 'new_grandma',
            'first_name': 'Grandma',
            'last_name': 'Smith',
            'email': 'grandma@family.com',
            'password1': 'grandmapassword123',
            'password2': 'grandmapassword123',
        }
        response = self.client.post(reverse('gallery:user_add'), post_data)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(User.objects.filter(username='new_grandma').exists())
        new_user = User.objects.get(username='new_grandma')
        self.assertEqual(new_user.first_name, 'Grandma')
        self.assertEqual(new_user.email, 'grandma@family.com')
