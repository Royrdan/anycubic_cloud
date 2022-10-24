from django.db import models
import os

# Create your models here.


class upload_file(models.Model):

    filename = models.FileField(upload_to='uploads')

    def full_path(self):
        return os.path.basename(self.filename.name)

    def __str__(self):
        return self.filename
