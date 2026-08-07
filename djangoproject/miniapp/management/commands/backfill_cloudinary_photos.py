import os

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from miniapp.models import Book


class Command(BaseCommand):
    help = (
        "Uploads existing local book cover photos to Cloudinary. "
        "Needed for Book.photo values that were saved before media storage "
        "was switched to Cloudinary, since changing the storage backend "
        "does not migrate already-uploaded files."
    )

    def handle(self, *args, **options):
        uploaded = skipped_exists = skipped_missing = 0
        for book in Book.objects.exclude(photo=""):
            name = book.photo.name
            if book.photo.storage.exists(name):
                skipped_exists += 1
                continue
            local_path = os.path.join(settings.MEDIA_ROOT, name)
            if not os.path.exists(local_path):
                self.stdout.write(
                    self.style.WARNING(f'Missing local file for "{book}": {local_path}')
                )
                skipped_missing += 1
                continue
            with open(local_path, "rb") as f:
                book.photo.save(os.path.basename(name), File(f), save=True)
            uploaded += 1
            self.stdout.write(self.style.SUCCESS(f'Uploaded cover for "{book}"'))

        self.stdout.write(
            f"Done. Uploaded: {uploaded}, already on Cloudinary: {skipped_exists}, "
            f"missing locally: {skipped_missing}"
        )
