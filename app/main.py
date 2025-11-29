from fastapi import (
    FastAPI, Depends, Request, HTTPException, Form
)
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func, asc, desc
from typing import List, Optional
from starlette.middleware.sessions import SessionMiddleware
from passlib.hash import bcrypt
from fastapi import Query

from .database import engine, Base, get_db, SessionLocal
from . import models, schemas
import os

app = FastAPI(title="BeeBee Library")

# Create tables
Base.metadata.create_all(bind=engine)

# --------------------------------------------------
# Initialize default row ONLY when SQLite DB is newly created
# --------------------------------------------------
import os
from sqlalchemy import select

def seed_sqlite_once():
    # Only applies to sqlite
    if not str(engine.url).startswith("sqlite"):
        print("Not sqlite.")
        return

    db_path = str(engine.url).replace("sqlite:///", "")

    print("Seeding SQLite with initial data...")

    db = SessionLocal()
    try:
        # Check if ANY user exists — safest check
        existing = db.scalars(select(models.User)).first()

        if existing:
            print("DB already seeded. Skip!")
            return

        from .models import User
        from passlib.hash import bcrypt

        # Hardcoded default user
        user = User(
            username="admin",
            password_hash=bcrypt.hash("admin")
        )
        db.add(user)
        db.commit()

        print("Default user created successfully.")

    finally:
        db.close()

seed_sqlite_once()
# --------------------------------------------------


# Sessions (signed cookies)
SECRET_KEY = os.getenv("LIBRARY_SECRET_KEY", "dev-secret-change-me")
app.add_middleware(
    SessionMiddleware, 
    secret_key=SECRET_KEY,
    session_cookie="library_session",
    max_age = 60 * 60 * 24 * 30,
    same_site="lax",
    https_only=False
)

# Static & templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# -----------------
# Helpers
# -----------------
def current_user(request: Request, db: Session) -> Optional[models.User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(models.User, user_id)

def require_login(request: Request, db: Session):
    user = current_user(request, db)
    if not user:
        # send to login
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# -----------------
# Public pages
# -----------------
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/books", response_class=HTMLResponse)
def books_page(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    return templates.TemplateResponse(
        "list.html",
        {"request": request, "logged_in": bool(user)}
    )

# -----------------
# Auth pages
# -----------------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.scalars(select(models.User).where(models.User.username == username)).first()
    if not user or not bcrypt.verify(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials."}, status_code=400)
    # Set session
    request.session["user_id"] = user.id
    return RedirectResponse(url="/add", status_code=303)

@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    exists = db.scalars(select(models.User).where(models.User.username == username)).first()
    if exists:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already taken."}, status_code=400)
    pwd_hash = bcrypt.hash(password)
    user = models.User(username=username, password_hash=pwd_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    # Auto-login
    request.session["user_id"] = user.id
    return RedirectResponse(url="/add", status_code=303)

# -----------------
# Protected page
# -----------------
@app.get("/add", response_class=HTMLResponse)
def add_page(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("add.html", {"request": request, "username": user.username})

# -----------------
# API
# -----------------
SORT_MAP = {
    "title_asc":  (lambda m: asc(m.title)),
    "title_desc": (lambda m: desc(m.title)),
    "author_asc":  (lambda m: (asc(m.author_last), asc(m.author_first))),
    "author_desc": (lambda m: (desc(m.author_last), desc(m.author_first))),
    "year_asc":   (lambda m: asc(m.year)),
    "year_desc":  (lambda m: desc(m.year)),
    "newest":     (lambda m: desc(m.id)),
}

@app.get("/api/books", response_model=schemas.BookSearchResponse)
def get_books(
    q: Optional[str] = None,
    author: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    sort: str = Query("title_asc", pattern="^(title|author|year)_(asc|desc)|newest$"),
    page: Optional[int] = Query(None, ge=1),          # <-- optional now
    page_size: Optional[int] = Query(None, ge=1, le=100),  # <-- optional now
    db: Session = Depends(get_db),
):
    stmt = select(models.Book)

    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(
            models.Book.title.ilike(like),
            models.Book.author_first.ilike(like),
            models.Book.author_last.ilike(like),
            models.Book.year.ilike(like),
            models.Book.isbn.ilike(like),
        ))
    if author:
        stmt = stmt.where(or_(
            models.Book.author_first.ilike(f"%{author}%"),
            models.Book.author_last.ilike(f"%{author}%"),
        ))
    if year_from:
        stmt = stmt.where(models.Book.year >= str(year_from))
    if year_to:
        stmt = stmt.where(models.Book.year <= str(year_to))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    # sort
    orderer = SORT_MAP.get(sort, SORT_MAP["title_asc"])
    order_cols = orderer(models.Book)
    if isinstance(order_cols, tuple):
        stmt = stmt.order_by(*order_cols)
    else:
        stmt = stmt.order_by(order_cols)

    # paginate ONLY if page/page_size provided
    if page is not None or page_size is not None:
        p = page or 1
        ps = page_size or 20
        stmt = stmt.offset((p - 1) * ps).limit(ps)
        items = db.scalars(stmt).all()
        return {"items": items, "total": total, "page": p, "page_size": ps}

    # default: return ALL items (no limit/offset)
    items = db.scalars(stmt).all()
    return {"items": items, "total": total, "page": 1, "page_size": total or len(items)}

@app.post("/api/books", response_model=schemas.BookRead)
def create_book(
    book: schemas.BookCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    # Require login for creating books
    _ = require_login(request, db)

    dup = db.scalars(
        select(models.Book).where(
            models.Book.isbn == book.isbn
        )
    ).first()
    if dup:
        raise HTTPException(status_code=409, detail="Book already exists.")
    obj = models.Book(**book.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.patch("/api/books/{book_id}", response_model=schemas.BookRead)
def update_book(
    book_id: int,
    book: schemas.BookUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    # Require login
    _ = require_login(request, db)

    obj = db.get(models.Book, book_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Book not found.")

    data = book.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj

@app.delete("/api/books/{book_id}", status_code=204)
def delete_book(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    # Require login
    _ = require_login(request, db)

    obj = db.get(models.Book, book_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Book not found.")

    db.delete(obj)
    db.commit()
    return

@app.get("/edit/{book_id}", response_class=HTMLResponse)
def edit_page(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")

    return templates.TemplateResponse(
        "edit.html",
        {"request": request, "book": book}
    )