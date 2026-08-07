import datetime
from .models import IssueRecord, Book


def librarian_stats(request):
    if request.user.is_authenticated and request.user.is_staff:
        pending_count = IssueRecord.objects.filter(status__in=['requested', 'reserved']).count()
        total_books = Book.objects.count()
        overdue_count = IssueRecord.objects.filter(
            status='issued', due_date__lt=datetime.date.today()
        ).count()
        return {
            'pending_requests_count': pending_count,
            'total_books_count': total_books,
            'overdue_count': overdue_count,
        }
    return {}