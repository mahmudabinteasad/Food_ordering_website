from django import forms
from .models import Customer, Restaurant, FoodItem
from .models import Review

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = Customer
        fields = ['username', 'email', 'password', 'phone']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'address', 'phone', 'description', 'image', 'email', 'delivery_charge', 'min_order', 'open_until', 'weekly_schedule']

class FoodItemForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = ['name', 'price', 'description', 'image', 'special_instructions']

class RestaurantReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'review_text']

class FoodItemReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'review_text']