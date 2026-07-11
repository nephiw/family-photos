from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password


class RetroUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'email@example.com'}))

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'retro-input',
                'autocomplete': 'off'
            })


class AdminUserUpdateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"placeholder": "Leave blank to keep current"}),
        strip=False,
        required=False,
    )
    password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat new password"}),
        strip=False,
        required=False,
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_superuser", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "retro-input", "autocomplete": "off"})

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Passwords do not match.")
            validate_password(p1, self.instance)
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        new_pw = self.cleaned_data.get("password1")
        if new_pw:
            user.set_password(new_pw)
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    old_password = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(attrs={"placeholder": "Required to save changes"}),
        strip=False,
    )
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"placeholder": "Leave blank to keep current"}),
        strip=False,
        required=False,
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat new password"}),
        strip=False,
        required=False,
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} retro-input".strip()
            field.widget.attrs["autocomplete"] = "off"

    def clean_old_password(self):
        old = self.cleaned_data.get("old_password")
        if not self.instance.check_password(old):
            raise forms.ValidationError("Current password is incorrect.")
        return old

    def clean_new_password2(self):
        p1 = self.cleaned_data.get("new_password1")
        p2 = self.cleaned_data.get("new_password2")
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("New passwords do not match.")
            validate_password(p1, self.instance)
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        new_pw = self.cleaned_data.get("new_password1")
        if new_pw:
            user.set_password(new_pw)
        if commit:
            user.save()
        return user
