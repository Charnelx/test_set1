from django import forms
# from .models import TURL

class UrlForm(forms.Form):

    turl = forms.CharField(label='URL to shorter', max_length=200)
