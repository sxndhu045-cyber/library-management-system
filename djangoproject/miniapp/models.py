from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True)
    pages = models.IntegerField()
    summary = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='books/', null=True, blank=True)
    category = models.CharField(max_length=100, blank=True)
    shelf_location = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def total_copies(self):
        return self.copies.count()

    @property
    def available_copies(self):
        return self.copies.filter(status='available').count()

    @property
    def issued_copies(self):
        return self.copies.filter(status='issued').count()


class BookCopy(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('issued', 'Issued'),
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    copy_number = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')

    class Meta:
        unique_together = ('book', 'copy_number')
        ordering = ['book', 'copy_number']

    def __str__(self):
        return f'{self.book.title} - Copy #{self.copy_number}'


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=200)
    contact = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['student_id']

    def __str__(self):
        return f'{self.student_id} - {self.full_name}'


class IssueRecord(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),   # student asked to issue, awaiting librarian approval
        ('reserved', 'Reserved'),     # student reserved an unavailable book
        ('issued', 'Issued'),         # librarian approved and handed over a copy
        ('returned', 'Returned'),     # book has been returned
        ('rejected', 'Rejected'),     # librarian declined the request
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issue_records')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issue_records')
    copy = models.ForeignKey(
        BookCopy, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='issue_records',
        help_text='Assigned once the librarian approves and hands over a specific copy'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f'{self.user.username} - {self.book.title} ({self.status})'
    
    