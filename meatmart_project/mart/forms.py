from django import forms
from .models import User, Shop
from .models import Feedback


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'location', 'password', 'role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Your area / address'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        role = cleaned_data.get("role")
        phone_number = cleaned_data.get("phone_number")
        
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
          # ✅ Make phone number required if role = customer
        if role == "customer" and not phone_number:
            raise forms.ValidationError("Phone number is required for customers")

        
        return cleaned_data

class ShopRegistrationForm(forms.ModelForm):
    
     class Meta:
        model = Shop
        fields = ['shop_image', 'name', 'address', 'location', 'phone_number', 'payment_phone_number',
                 'product_image', 'product_name', 'quantity', 'rate', 'description'
                 ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class':'form-select'}, choices=[(i,i) for i in range(1,6)]),
            'comment': forms.Textarea(attrs={'class':'form-control', 'rows':3, 'placeholder':'Write your feedback...'}),
        }

