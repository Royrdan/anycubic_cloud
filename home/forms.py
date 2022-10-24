from django.forms import ModelForm
from .models import upload_file


class upload_form(ModelForm):
    class Meta:
        model = upload_file
        fields = '__all__'
