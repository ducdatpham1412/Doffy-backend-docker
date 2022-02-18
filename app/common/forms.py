from django import forms
from common.models import Images


class ImageForm(forms.ModelForm):
    image = forms.ImageField(label='image')

    class Meta:
        model = Images
        fields = ['image']
