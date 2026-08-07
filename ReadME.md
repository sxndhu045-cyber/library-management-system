# Library Management System

A Django-based library management system with separate student and librarian roles, supporting book browsing, reservations, issue requests, and full librarian-side inventory and lending management.

## Features

### Public / no login required
- Browse available and archived (fully checked-out) books from the homepage
- Search books by title, author, or category
- View full book details: author, ISBN, category, shelf location, page count, summary, and cover photo

### Student features
- Log in with a student ID and password (issued by a librarian)
- View a personal profile page showing:
  - Currently issued books (with issue and due dates)
  - Active reservations
  - Past issued books (return history)
- Request to issue a book when copies are available
- Reserve a book when all copies are currently checked out
- Automatic duplicate-request protection (can't request/reserve the same book twice while a request is active)

### Librarian features
- Log in with an admin ID and password
- Full book catalog management: add, edit, delete books
- Manage total copy count per book directly from the edit form (copies are added or removed automatically, with safeguards so currently-issued copies are never deleted)
- Create student login accounts
- Dashboard with at-a-glance stats: total books, copies available, and overdue count
- Unified issue requests queue showing both direct issue requests and reservations
- Approve or reject pending requests
- Mark issued books as returned
- **Automatic reservation fulfillment**: when a book is returned, the oldest pending reservation for that title is automatically converted into an issue and assigned the freed copy
- Full request history log (issued / returned / rejected) with search by student ID, name, or book title
- Responsive layout that adapts to mobile screens

## Tech stack
- **Backend**: Django 6.0
- **Database**: SQLite (default)
- **Frontend**: Django templates, Bootstrap 5 (student-facing pages), custom CSS (librarian dashboard)

## Project structure

```
djangoproject/
├── djangoproject/           # Project settings, root urls.py
├── miniapp/                 # Main app
│   ├── models.py            # Book, BookCopy, Student, IssueRecord
│   ├── views.py             # Student and librarian views
│   ├── forms.py             # BookForm, StudentCreateForm
│   ├── urls.py               # App-level URL routing
│   ├── context_processors.py # Librarian stats (available on all librarian pages)
│   ├── migrations/
│   └── templates/
│       ├── layout.html               # Student-facing base template
│       ├── homepage.html
│       ├── book_detail.html
│       ├── profile.html
│       ├── reserve_confirm.html
│       ├── request_issue_confirm.html
│       ├── registration/
│       │   └── login.html
│       └── librarian/
│           ├── base.html             # Librarian dashboard base template
│           ├── book_list.html
│           ├── book_form.html
│           ├── book_confirm_delete.html
│           ├── student_list.html
│           ├── student_form.html
│           ├── issue_requests.html
│           ├── request_history.html
│           ├── approve_confirm.html
│           ├── reject_confirm.html
│           └── return_confirm.html
└── manage.py
```

## Data model overview

- **Book** — title, author, ISBN, pages, summary, photo, category, shelf location. Copy counts are derived from related `BookCopy` records.
- **BookCopy** — an individual physical copy of a book, with a status of `available` or `issued`.
- **Student** — links to Django's built-in `User` model, adds a student ID, full name, and contact info.
- **IssueRecord** — the central record connecting a user, a book, and (once approved) a specific copy. Tracks status through its lifecycle: `requested` → `issued` → `returned`, or `reserved` → `issued` → `returned`, or `requested`/`reserved` → `rejected`.

## Setup

1. Clone the repository and navigate into the project folder:
   ```bash
   git clone <your-repo-url>
   cd djangoproject
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # macOS/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a librarian (admin/staff) account:
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

7. Visit `http://127.0.0.1:8000/` for the public homepage, or log in at `http://127.0.0.1:8000/login/`.

   Librarian accounts (`is_staff=True`) are redirected to the librarian dashboard on login; student accounts are redirected to the homepage.

## Creating student accounts

Student accounts aren't self-service — a librarian creates them from the dashboard under **Students → Add student**, which generates a Django `User` and linked `Student` profile with a student ID and password to hand to the student directly.

## Notes

- The default loan period is 14 days from the date a request is approved, configurable via `DEFAULT_LOAN_DAYS` in `views.py`.
- A book is considered "overdue" once its due date has passed and it has not yet been marked returned; this is calculated live on every librarian page load, not via a scheduled task.
- Reservations are automatically converted into issues, in first-reserved-first-served order, whenever a copy of that book is returned.