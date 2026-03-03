from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Profile, Team, Task, Feedback

User = get_user_model()


class AddMemberForm(forms.Form):
    """Form for team leads to create a new user (new hire) and optionally add to teams."""
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm password')
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, initial='member')
    teams = forms.ModelMultipleChoiceField(
        queryset=Team.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError('A user with this username already exists.')
        return username

    def clean(self):
        data = super().clean()
        if data.get('password1') != data.get('password2'):
            raise forms.ValidationError({'password2': 'Passwords do not match.'})
        return data


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, initial='member')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Profile.objects.update_or_create(
                user=user,
                defaults={'role': self.cleaned_data['role']},
            )
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('role', 'avatar')


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ('name', 'description')


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = (
            'title', 'description', 'team', 'assigned_to', 'status',
            'priority', 'deadline', 'tags',
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'team': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }


class TaskStatusOnlyForm(forms.ModelForm):
    """Form for members to update only task status."""
    class Meta:
        model = Task
        fields = ('status',)
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ('content', 'rating')
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
        }
