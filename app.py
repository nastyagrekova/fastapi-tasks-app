from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from controllers import tasks_controller, weather_controller

app = FastAPI(title="Интелигентен помощник")

app.include_router(tasks_controller.router)
app.include_router(weather_controller.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
