# Family Photo Site

## Overview

I created this site to share photos with my family. I designed it to have a retro futuristic theme. It is built with Django and htmx, neither of which I am all that familiar with. I am using opencode to help me create the site.

## Installation

To run the site locally, first activate they python virtual environment: `source venv/bin/activate` which will install the dependencies and activate the virtual environment. Then run `python manage.py runserver` to start the development server or `python manage.py test gallery` to run the tests for the gallery app.

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
