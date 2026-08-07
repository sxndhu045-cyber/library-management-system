from . import views
from django .urls import path
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('book/<int:id>/', views.book_detail, name='book_detail'),
    path('html/', views.html, name='html'),
    # Authentication
    path('login/', views.RoleBasedLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),

    # Student: reserve / request issue
    path('book/<int:pk>/reserve/', views.reserve_book, name='reserve_book'),
    path('book/<int:pk>/request-issue/', views.request_issue, name='request_issue'),
 

    # Librarian: manage books
    path('librarian/books/', views.librarian_book_list, name='librarian_book_list'),
    path('librarian/books/add/', views.librarian_book_add, name='librarian_book_add'),
    path('librarian/books/<int:pk>/edit/', views.librarian_book_edit, name='librarian_book_edit'),
    path('librarian/books/<int:pk>/delete/', views.librarian_book_delete, name='librarian_book_delete'),

# Librarian: manage students
path('librarian/students/', views.librarian_student_list, name='librarian_student_list'),
path('librarian/students/add/', views.librarian_student_add, name='librarian_student_add'),
path('librarian/students/<int:pk>/edit/', views.librarian_student_edit, name='librarian_student_edit'),
path('librarian/students/<int:pk>/delete/', views.librarian_student_delete, name='librarian_student_delete'),


# Librarian: issue requests
    path('librarian/requests/', views.librarian_issue_requests, name='librarian_issue_requests'),
    path('librarian/requests/<int:pk>/approve/', views.librarian_approve_request, name='librarian_approve_request'),
    path('librarian/requests/<int:pk>/reject/', views.librarian_reject_request, name='librarian_reject_request'),
    path('librarian/requests/<int:pk>/return/', views.librarian_mark_returned, name='librarian_mark_returned'),
    path('librarian/requests/<int:pk>/due-date/', views.librarian_edit_due_date, name='librarian_edit_due_date'),
    path('librarian/requests/history/', views.librarian_request_history, name='librarian_request_history'),
]

