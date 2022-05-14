from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import *


class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = '__all__'


class CreateCustomerForm(ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists!")
        return email  


class ChangePasswordForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['password1', 'password2']
