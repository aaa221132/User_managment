from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, create_engine, Session, select
from passlib.hash import bcrypt

from models import Audiobook, User

app = FastAPI()

# Подключение баз данных
engine = create_engine("sqlite:///audiobooks.db")
users = create_engine("sqlite:///users.db")

# Создание таблиц
SQLModel.metadata.create_all(engine, tables=[Audiobook.__table__])
SQLModel.metadata.create_all(users, tables=[User.__table__])

# Шаблоны и статика
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    with Session(engine) as session:
        books = session.exec(select(Audiobook)).all()
    return templates.TemplateResponse("lib.html", {"request": request, "books": books})


@app.get("/lib", response_class=HTMLResponse)
def show_library(request: Request):
    with Session(engine) as session:
        books = session.exec(select(Audiobook)).all()
    return templates.TemplateResponse("lib.html", {"request": request, "books": books})


@app.get("/book/{book_id}", response_class=HTMLResponse)
def book_detail(request: Request, book_id: int):
    with Session(engine) as session:
        book = session.get(Audiobook, book_id)
    if book:
        return templates.TemplateResponse("book_detail.html", {"request": request, "book": book})
    return HTMLResponse(content="Book not found", status_code=404)


@app.get("/add", response_class=HTMLResponse)
def add_book_form(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})


@app.post("/add")
async def add_book(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    image: UploadFile = File(None)
):
    user_login = request.cookies.get("user_login")
    if not user_login:
        return RedirectResponse(url="/login", status_code=303)

    file_bytes = await file.read()
    image_bytes = await image.read() if image else None

    book = Audiobook(
        title=title,
        author=author,
        description=description,
        file_data=file_bytes,
        file_name=file.filename,
        file_content_type=file.content_type,
        image_data=image_bytes,
        image_name=image.filename if image else None,
        image_content_type=image.content_type if image else None,
        user=user_login
    )

    with Session(engine) as session:
        session.add(book)
        session.commit()

    return RedirectResponse(url="/", status_code=303)


@app.post("/delete/{book_id}")
def delete_book(book_id: int):
    with Session(engine) as session:
        book = session.get(Audiobook, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Книга не знайдена")
        session.delete(book)
        session.commit()
    return RedirectResponse(url="/del", status_code=303)


@app.get("/play/{book_id}")
def play_audio(book_id: int):
    with Session(engine) as session:
        book = session.get(Audiobook, book_id)
    if not book or not book.file_data:
        raise HTTPException(status_code=404, detail="Аудіо не знайдено")
    return StreamingResponse(
        iter([book.file_data]),
        media_type=book.file_content_type,
        headers={"Content-Disposition": f'inline; filename="{book.file_name}"'}
    )


@app.get("/image/{book_id}")
def get_image(book_id: int):
    with Session(engine) as session:
        book = session.get(Audiobook, book_id)
    if not book or not book.image_data:
        raise HTTPException(status_code=404, detail="Зображення не знайдено")
    return StreamingResponse(
        iter([book.image_data]),
        media_type=book.image_content_type,
        headers={"Content-Disposition": f'inline; filename="{book.image_name}"'}
    )


@app.get("/api/books")
def api_books():
    with Session(engine) as session:
        books = session.exec(select(Audiobook)).all()
        return [
            {"id": book.id, "title": book.title, "author": book.author, "description": book.description}
            for book in books
        ]


@app.get("/register", response_class=HTMLResponse)
def show_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, username: str = Form(...), password: str = Form(...)):
    with Session(users) as session:
        existing_user = session.exec(select(User).where(User.username == username)).first()
        if existing_user:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "repeat": "Імʼя вже зайняте"
            })

        hashed_pw = bcrypt.hash(password)
        new_user = User(username=username, hashed_password=hashed_pw)
        session.add(new_user)
        session.commit()

    return templates.TemplateResponse("register.html", {
        "request": request,
        "continue": "Реєстрація успішна"
    })


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    with Session(users) as session:
        user = session.exec(select(User).where(User.username == username)).first()

    if user and bcrypt.verify(password, user.hashed_password):
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="user_login", value=username)
        return response
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "invalid": "Невірне ім’я користувача або пароль"
        })


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("user_login")
    return response


@app.get("/del", response_class=HTMLResponse)
def delete_page(request: Request):
    with Session(engine) as session:
        books = session.exec(select(Audiobook)).all()
    return templates.TemplateResponse("index.html", {"request": request, "books": books})



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
