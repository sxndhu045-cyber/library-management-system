from django import forms
from django.contrib.auth.models import User
from .models import Book, IssueRecord


class StudentCreateForm(forms.Form):
    student_id = forms.CharField(max_length=20, label='Student ID (this becomes their username)')
    full_name = forms.CharField(max_length=200)
    contact = forms.CharField(max_length=100, required=False)
    password = forms.CharField(widget=forms.PasswordInput, help_text='Give this to the student along with their ID')

    def clean_student_id(self):
        student_id = self.cleaned_data['student_id'].lower()
        if User.objects.filter(username=student_id).exists():
            raise forms.ValidationError('That student ID is already taken.')
        return student_id


class StudentEditForm(forms.Form):
    student_id = forms.CharField(max_length=20, label='Student ID (this becomes their username)')
    full_name = forms.CharField(max_length=200)
    contact = forms.CharField(max_length=100, required=False)
    new_password = forms.CharField(
        widget=forms.PasswordInput, required=False,
        help_text='Leave blank to keep their current password.'
    )

    def __init__(self, *args, student=None, **kwargs):
        self.student = student
        super().__init__(*args, **kwargs)

    def clean_student_id(self):
        student_id = self.cleaned_data['student_id'].lower()
        if User.objects.filter(username=student_id).exclude(pk=self.student.user_id).exists():
            raise forms.ValidationError('That student ID is already taken.')
        return student_id


class DueDateForm(forms.ModelForm):
    class Meta:
        model = IssueRecord
        fields = ['due_date']
        widgets = {'due_date': forms.DateInput(attrs={'type': 'date'})}


class BookForm(forms.ModelForm):
    num_copies = forms.IntegerField(
        min_value=1, initial=1,
        help_text='How many physical copies to add'
    )

    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'pages', 'summary', 'photo', 'category', 'shelf_location']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 4}),
        }