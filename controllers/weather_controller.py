from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx

router = APIRouter()
templates = Jinja2Templates(directory="views")

API_KEY = "0216d151229995ebd5fe3681c34794fc"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


@router.get("/weather", response_class=HTMLResponse)
async def get_weather(request: Request, city: str = None):
    weather = None

    if city:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    BASE_URL,
                    params={"q": city, "appid": API_KEY, "units": "metric", "lang": "bg"}
                )
                print("СТАТУС:", response.status_code)
                print("ОТГОВОР:", response.text)

                if response.status_code == 200:
                    data = response.json()
                    weather = {
                        "city": data["name"],
                        "temp": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "description": data["weather"][0]["description"].capitalize(),
                    }
                else:
                    weather = {"error": "Неуспешна заявка към OpenWeather."}
        except Exception as e:
            weather = {"error": f"Грешка при свързване: {e}"}

    return templates.TemplateResponse("weather.html", {"request": request, "weather": weather})
