import datetime

from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.db.models import Q, Max
# Create your views here.

from .models import Book, BookCopy, Student, IssueRecord
from .forms import BookForm, StudentCreateForm, StudentEditForm, DueDateForm

DEFAULT_LOAN_DAYS = 14


def is_librarian(user):
    return user.is_staff


class RoleBasedLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse('librarian_book_list')
        return reverse('homepage')


def book_detail(request, id):
    book = get_object_or_404(Book, id=id)
    return render(request, "book_detail.html", {"book": book})


def html(request):
    return render(request, 'index.html')


def homepage(request):
    query = request.GET.get('q', '')
    books = Book.objects.all()
    if query:
        books = books.filter(
            Q(title__icontains=query) | Q(author__icontains=query) | Q(category__icontains=query)
        )
    available_books = [b for b in books if b.available_copies > 0]
    archived_books = [b for b in books if b.available_copies == 0]
    return render(request, 'homepage.html', {
        'available_books': available_books,
        'archived_books': archived_books,
        'query': query,
    })


# ---- Student: profile ----

@login_required
def profile(request):
    student = get_object_or_404(Student, user=request.user)
    records = IssueRecord.objects.filter(user=request.user)
    current_issued = records.filter(status='issued')
    past_issued = records.filter(status='returned')
    reserved = records.filter(status='reserved')
    return render(request, 'profile.html', {
        'student': student,
        'current_issued': current_issued,
        'past_issued': past_issued,
        'reserved': reserved,
    })


# ---- Student: reserve / request issue ----

@login_required
def reserve_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        if book.available_copies > 0:
            messages.error(request, 'This book currently has copies available — you can request to issue it instead.')
        else:
            already = IssueRecord.objects.filter(user=request.user, book=book, status__in=['reserved', 'requested', 'issued']).exists()
            if already:
                messages.error(request, 'You already have an active request or reservation for this book.')
            else:
                IssueRecord.objects.create(user=request.user, book=book, status='reserved')
                messages.success(request, f'"{book.title}" reserved. You will be notified when a copy is available.')
        return redirect('book_detail', id=book.pk)
    return render(request, 'reserve_confirm.html', {'book': book})


@login_required
def request_issue(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        if book.available_copies == 0:
            messages.error(request, 'No copies available — reserve this book instead.')
        else:
            already = IssueRecord.objects.filter(user=request.user, book=book, status__in=['reserved', 'requested', 'issued']).exists()
            if already:
                messages.error(request, 'You already have an active request or reservation for this book.')
            else:
                IssueRecord.objects.create(user=request.user, book=book, status='requested')
                messages.success(request, f'Issue request sent for "{book.title}". A librarian will process it.')
        return redirect('book_detail', id=book.pk)
    return render(request, 'request_issue_confirm.html', {'book': book})


# ---- Librarian: manage books ----

@login_required
@user_passes_test(is_librarian)
def librarian_book_list(request):
    query = request.GET.get('q', '')
    books = Book.objects.all()
    if query:
        books = books.filter(
            Q(title__icontains=query) | Q(author__icontains=query) | Q(isbn__icontains=query)
        )
    return render(request, 'librarian/book_list.html', {'books': books, 'query': query})


@login_required
@user_passes_test(is_librarian)
def librarian_book_add(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            num_copies = form.cleaned_data.get('num_copies') or 1
            for i in range(1, num_copies + 1):
                BookCopy.objects.create(book=book, copy_number=i)
            messages.success(request, f'"{book.title}" added with {num_copies} copies.')
            return redirect('librarian_book_list')
    else:
        form = BookForm()
    return render(request, 'librarian/book_form.html', {'form': form, 'page_title': 'Add book'})


@login_required
@user_passes_test(is_librarian)
def librarian_book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        form.fields['num_copies'].label = 'Total copies'
        if form.is_valid():
            book = form.save()
            target = form.cleaned_data['num_copies']
            current_count = book.copies.count()

            if target > current_count:
                last_num = book.copies.aggregate(Max('copy_number'))['copy_number__max'] or 0
                for i in range(1, target - current_count + 1):
                    BookCopy.objects.create(book=book, copy_number=last_num + i)

            elif target < current_count:
                to_remove = current_count - target
                removable = list(
                    book.copies.filter(status='available').order_by('-copy_number')[:to_remove]
                )
                BookCopy.objects.filter(pk__in=[c.pk for c in removable]).delete()
                if len(removable) < to_remove:
                    messages.warning(
                        request,
                        f'Could only remove {len(removable)} of {to_remove} requested copies — '
                        f'the rest are currently issued and cannot be deleted.'
                    )

            messages.success(request, f'"{book.title}" updated.')
            return redirect('librarian_book_list')
    else:
        form = BookForm(instance=book, initial={'num_copies': book.copies.count()})
        form.fields['num_copies'].label = 'Total copies'
        form.fields['num_copies'].help_text = f'Currently {book.available_copies} of {book.copies.count()} available'

    return render(request, 'librarian/book_form.html', {
        'form': form, 'page_title': 'Edit book', 'book': book,
    })


@login_required
@user_passes_test(is_librarian)
def librarian_book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f'"{title}" deleted.')
        return redirect('librarian_book_list')
    return render(request, 'librarian/book_confirm_delete.html', {'book': book})


# ---- Librarian: manage students (login accounts) ----

@login_required
@user_passes_test(is_librarian)
def librarian_student_list(request):
    query = request.GET.get('q', '')
    students = Student.objects.all()
    if query:
        students = students.filter(
            Q(student_id__icontains=query) | Q(full_name__icontains=query) | Q(contact__icontains=query)
        )
    return render(request, 'librarian/student_list.html', {'students': students, 'query': query})


@login_required
@user_passes_test(is_librarian)
def librarian_student_add(request):
    if request.method == 'POST':
        form = StudentCreateForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['student_id'],
                password=form.cleaned_data['password'],
            )
            Student.objects.create(
                user=user,
                student_id=form.cleaned_data['student_id'],
                full_name=form.cleaned_data['full_name'],
                contact=form.cleaned_data.get('contact', ''),
            )
            messages.success(
                request,
                f"Account created for {form.cleaned_data['full_name']} "
                f"(username: {form.cleaned_data['student_id']}). Share the password with them directly."
            )
            return redirect('librarian_student_list')
    else:
        form = StudentCreateForm()
    return render(request, 'librarian/student_form.html', {'form': form, 'page_title': 'Add student'})


@login_required
@user_passes_test(is_librarian)
def librarian_student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentEditForm(request.POST, student=student)
        if form.is_valid():
            student.student_id = form.cleaned_data['student_id']
            student.full_name = form.cleaned_data['full_name']
            student.contact = form.cleaned_data.get('contact', '')
            student.save()
            student.user.username = form.cleaned_data['student_id']
            new_password = form.cleaned_data.get('new_password')
            if new_password:
                student.user.set_password(new_password)
            student.user.save()
            if new_password:
                messages.success(
                    request,
                    f'Updated {student.full_name}. New password: {new_password} — share this with them directly.'
                )
            else:
                messages.success(request, f'Updated {student.full_name}.')
            return redirect('librarian_student_list')
    else:
        form = StudentEditForm(student=student, initial={
            'student_id': student.student_id,
            'full_name': student.full_name,
            'contact': student.contact,
        })
    return render(request, 'librarian/student_form.html', {
        'form': form, 'page_title': 'Edit student', 'is_edit': True, 'student': student,
    })


@login_required
@user_passes_test(is_librarian)
def librarian_student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    active_count = student.user.issue_records.filter(status__in=['issued', 'requested', 'reserved']).count()
    if request.method == 'POST':
        if active_count:
            messages.error(
                request,
                f'Cannot delete {student.full_name} — they have {active_count} active issue(s)/reservation(s). '
                f'Resolve those first.'
            )
            return redirect('librarian_student_list')
        name = student.full_name
        student.user.delete()
        messages.success(request, f'Deleted {name}.')
        return redirect('librarian_student_list')
    return render(request, 'librarian/student_confirm_delete.html', {
        'student': student, 'active_count': active_count,
    })


# ---- Librarian: issue requests ----

@login_required
@user_passes_test(is_librarian)
def librarian_issue_requests(request):
    requests_qs = IssueRecord.objects.filter(status__in=['requested', 'reserved'])
    return render(request, 'librarian/issue_requests.html', {'requests': requests_qs})


@login_required
@user_passes_test(is_librarian)
def librarian_approve_request(request, pk):
    record = get_object_or_404(IssueRecord, pk=pk)
    if request.method == 'POST':
        copy = record.book.copies.filter(status='available').first()
        if not copy:
            messages.error(request, 'No available copies left to issue.')
        else:
            copy.status = 'issued'
            copy.save()
            record.copy = copy
            record.status = 'issued'
            record.issue_date = datetime.date.today()
            record.due_date = datetime.date.today() + datetime.timedelta(days=DEFAULT_LOAN_DAYS)
            record.save()
            messages.success(
                request,
                f'"{record.book.title}" issued to {record.user.username}.',
                extra_tags='stamp-issued'
            )
        return redirect('librarian_issue_requests')
    return render(request, 'librarian/approve_confirm.html', {'record': record})


@login_required
@user_passes_test(is_librarian)
def librarian_reject_request(request, pk):
    record = get_object_or_404(IssueRecord, pk=pk)
    if request.method == 'POST':
        record.status = 'rejected'
        record.save()
        messages.success(
            request,
            f'Request for "{record.book.title}" rejected.',
            extra_tags='stamp-rejected'
        )
        return redirect('librarian_issue_requests')
    return render(request, 'librarian/reject_confirm.html', {'record': record})


@login_required
@user_passes_test(is_librarian)
def librarian_mark_returned(request, pk):
    record = get_object_or_404(IssueRecord, pk=pk, status='issued')
    if request.method == 'POST':
        record.status = 'returned'
        record.return_date = datetime.date.today()
        record.save()

        freed_copy = record.copy
        if freed_copy:
            freed_copy.status = 'available'
            freed_copy.save()

        messages.success(
            request,
            f'"{record.book.title}" marked as returned.',
            extra_tags='stamp-returned'
        )

        # Auto-convert the oldest pending reservation for this book, if any
        next_reservation = IssueRecord.objects.filter(
            book=record.book, status='reserved'
        ).order_by('requested_at').first()

        if next_reservation and freed_copy:
            freed_copy.status = 'issued'
            freed_copy.save()
            next_reservation.copy = freed_copy
            next_reservation.status = 'issued'
            next_reservation.issue_date = datetime.date.today()
            next_reservation.due_date = datetime.date.today() + datetime.timedelta(days=DEFAULT_LOAN_DAYS)
            next_reservation.save()
            messages.success(
                request,
                f'"{next_reservation.book.title}" automatically issued to {next_reservation.user.username} '
                f'from their reservation.',
                extra_tags='stamp-issued'
            )

        return redirect('librarian_issue_requests')
    return render(request, 'librarian/return_confirm.html', {'record': record})


@login_required
@user_passes_test(is_librarian)
def librarian_edit_due_date(request, pk):
    record = get_object_or_404(IssueRecord, pk=pk, status='issued')
    if request.method == 'POST':
        form = DueDateForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, f'Due date for "{record.book.title}" updated to {record.due_date}.')
            return redirect('librarian_request_history')
    else:
        form = DueDateForm(instance=record)
    return render(request, 'librarian/edit_due_date.html', {'form': form, 'record': record})


@login_required
@user_passes_test(is_librarian)
def librarian_request_history(request):
    records = IssueRecord.objects.filter(status__in=['issued', 'returned', 'rejected'])
    query = request.GET.get('q', '')
    if query:
        records = records.filter(
            Q(user__student__student_id__icontains=query) |
            Q(user__student__full_name__icontains=query) |
            Q(book__title__icontains=query)
        )
    return render(request, 'librarian/request_history.html', {'records': records, 'query': query})