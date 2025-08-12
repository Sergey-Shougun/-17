from django import forms
from .models import Post, Category
from allauth.account.forms import SignupForm
from django.contrib.auth.models import Group


class CustomSignupForm(SignupForm):
    def save(self, request):
        user = super().save(request)
        common_group = Group.objects.get(name='common')
        common_group.user_set.add(user)

        return user


class PostForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Категории'
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'author', 'categories']