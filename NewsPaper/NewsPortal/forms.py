from django import forms
from .models import Post, Category
from allauth.account.forms import SignupForm
from django.contrib.auth.models import Group


class NewsCreateForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'author', 'categories']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget = forms.Textarea(attrs={'rows': 5})


class CustomSignupForm(SignupForm):
    def save(self, request):
        user = super().save(request)
        common_group = Group.objects.get(name='common')
        common_group.user_set.add(user)

        return user
