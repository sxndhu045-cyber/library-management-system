from django.contrib import admin
from .models import Book, BookCopy, Student, IssueRecord
# Register your models here.
admin.site.register(Book)
admin.site.register(BookCopy)
admin.site.register(Student)
admin.site.register(IssueRecord)


