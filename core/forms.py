from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Observation, Plant


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'username'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
        }


class PlantForm(forms.ModelForm):
    class Meta:
        model = Plant
        fields = ('name', 'plant_type', 'planting_date', 'location', 'notes')
        widgets = {'planting_date': forms.DateInput(attrs={'type': 'date'})}


class ObservationForm(forms.ModelForm):
    class Meta:
        model = Observation
        fields = ('image', 'captured_on')
        widgets = {
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*', 'capture': 'environment'}),
            'captured_on': forms.DateInput(attrs={'type': 'date'}),
        }
