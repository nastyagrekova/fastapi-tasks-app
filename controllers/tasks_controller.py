from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models.task_model import Task, SessionLocal
from datetime import datetime, date
import random, httpx, logging

router = APIRouter()
templates = Jinja2Templates(directory="views")

logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def update_statuses(db: Session):
    today = date.today()
    tasks = db.query(Task).all()
    changed = False
    for t in tasks:
        if t.status == "Завършена":
            continue
        if t.due_date < today and t.status != "Стара":
            t.status = "Стара"
            changed = True
        elif t.due_date >= today and t.status != "Нова":
            t.status = "Нова"
            changed = True
    if changed:
        db.commit()


def generate_ai_advice(tasks):
    if not tasks:
        return "Няма задачи за анализ."
    urgent = [t for t in tasks if t.priority == 1]
    if urgent:
        return "Започни с най-важните задачи – тези с приоритет 1."
    elif len(tasks) > 5:
        return "Имаш доста задачи – опитай се да ги групираш по тип."
    else:
        return "Продължавай в този ритъм – балансът е добър!"


def shift_priorities_for_new(db: Session, new_priority: int):
    tasks = db.query(Task).order_by(Task.priority.asc()).all()
    for t in tasks:
        if t.priority >= new_priority:
            t.priority += 1
    db.commit()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    db = SessionLocal()
    update_statuses(db)
    tasks = db.query(Task).order_by(Task.priority.asc()).all()
    db.close()
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks})


@router.get("/add", response_class=HTMLResponse)
async def add_task_page(request: Request):
    db = SessionLocal()
    update_statuses(db)
    tasks = db.query(Task).order_by(Task.priority.asc()).all()
    db.close()
    return templates.TemplateResponse("add_task.html", {"request": request, "tasks": tasks})


@router.post("/add")
async def add_task(
    name: str = Form(...),
    priority: int = Form(...),
    due_date: str = Form(...),
    category: str = Form(...)
):
    db = SessionLocal()
    due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
    shift_priorities_for_new(db, priority)
    new_task = Task(
        name=name,
        priority=priority,
        due_date=due_date_obj,
        status="Нова" if due_date_obj >= date.today() else "Стара",
        category=category
    )
    db.add(new_task)
    db.commit()
    db.close()
    return RedirectResponse(url="/add", status_code=303)


@router.post("/edit/{task_id}")
async def edit_task(
    task_id: int,
    name: str = Form(None),
    priority: int = Form(None),
    due_date: str = Form(None),
    status: str = Form(None),
    category: str = Form(None)
):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        if name:
            task.name = name
        if priority:
            task.priority = priority
        if due_date:
            task.due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        if status:
            task.status = status
        if category:
            task.category = category

        if task.status != "Завършена":
            task.status = "Стара" if task.due_date < date.today() else "Нова"

        db.commit()
    db.close()
    return RedirectResponse(url="/add", status_code=303)


@router.post("/delete/{task_id}")
async def delete_task(task_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()
    db.close()
    return RedirectResponse(url="/add", status_code=303)


@router.post("/complete/{task_id}")
async def complete_task(task_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.status = "Завършена"
        db.commit()
    db.close()
    return RedirectResponse(url="/schedule", status_code=303)


@router.get("/schedule", response_class=HTMLResponse)
async def schedule(request: Request):
    db = SessionLocal()
    update_statuses(db)
    tasks = db.query(Task).order_by(Task.priority.asc(), Task.due_date).all()
    total = len(tasks)
    completed = len([t for t in tasks if t.status == "Завършена"])
    progress_percent = int((completed / total) * 100) if total > 0 else 0
    ai_advice = generate_ai_advice(tasks)
    db.close()
    return templates.TemplateResponse(
        "schedule.html",
        {
            "request": request,
            "tasks": tasks,
            "progress_percent": progress_percent,
            "ai_advice": ai_advice
        }
    )


@router.get("/inspiration", response_class=HTMLResponse)
async def inspiration(request: Request):
    mock_advices = [
        "Започни с най-трудната задача – след това всичко ще е по-лесно.",
        "Не забравяй да направиш кратка почивка – мозъкът ти ще ти благодари.",
        "Приоритизирай задачите си по важност, не по спешност.",
        "Провери дали днешните ти задачи водят към дългосрочните ти цели.",
        "Една завършена малка задача е по-добра от десет недовършени големи."
    ]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://zenquotes.io/api/random")
            data = response.json()[0]
            quote = data["q"]
            author = data["a"]
        except Exception:
            quote = "Дори най-дългият път започва с първата крачка."
            author = "Конфуций"

    tip = random.choice(mock_advices)
    return templates.TemplateResponse(
        "inspiration.html",
        {"request": request, "quote": quote, "author": author, "tip": tip}
    )
