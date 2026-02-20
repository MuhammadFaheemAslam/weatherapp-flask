from flask import Flask, request, render_template
import os, requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import pycountry
from dataclasses import dataclass

load_dotenv()
api_key = os.getenv('API_KEY')
secret_key = os.getenv('SECRET_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key

@dataclass
class WeatherData:
    name: str
    country: str
    temperature: float
    feels_like: float
    description: str
    emoji: str
    humidity: int
    wind_speed: float
    local_time: str
    time_of_day: str
    temp_min: float
    temp_max: float
    pressure: int
    visibility: float

def get_country_name(country_code):
    """Convert a 2-letter country code to full country name."""
    country = pycountry.countries.get(alpha_2=country_code)
    return country.name if country else country_code

def get_weather_emoji(description, time_of_day):
    """Return an emoji based on the weather description and time of day."""
    description = description.lower()
    if "clear" in description:
        if time_of_day == "Morning":
            return "🌅"
        elif time_of_day == "Afternoon":
            return "🌞"
        elif time_of_day == "Evening":
            return "🌇"
        else:
            return "🌙"
    elif "cloud" in description:
        return "☁️"
    elif "rain" in description or "drizzle" in description:
        return "🌧️"
    elif "snow" in description:
        return "❄️"
    elif "thunderstorm" in description:
        return "⛈️"
    elif "fog" in description or "smoke" in description or "mist" in description or "haze" in description:
        return "🌫️"
    else:
        return "🌈"

def get_time_of_day(hour):
    """Classify hour into time of day."""
    if 0 <= hour < 6:
        return "Night"
    elif 6 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 18:
        return "Afternoon"
    elif 18 <= hour < 21:
        return "Evening"
    else:
        return "Late Night"

def process_weather_data(json_data):
    """Process the JSON data from the weather API and return a WeatherData object."""
    timezone_offset = json_data['timezone']
    utc_now = datetime.now(timezone.utc)
    local_time = utc_now + timedelta(seconds=timezone_offset)
    local_time_formatted = local_time.strftime('%Y-%m-%d %I:%M %p')

    time_of_day = get_time_of_day(local_time.hour)
    description = json_data['weather'][0]['description']

    visibility_km = json_data.get('visibility', 0) / 1000

    return WeatherData(
        name=json_data['name'],
        country=get_country_name(json_data['sys']['country']),
        temperature=round(json_data['main']['temp'], 1),
        feels_like=round(json_data['main']['feels_like'], 1),
        description=description,
        emoji=get_weather_emoji(description, time_of_day),
        humidity=json_data['main']['humidity'],
        wind_speed=json_data['wind']['speed'],
        local_time=local_time_formatted,
        time_of_day=time_of_day,
        temp_min=round(json_data['main']['temp_min'], 1),
        temp_max=round(json_data['main']['temp_max'], 1),
        pressure=json_data['main']['pressure'],
        visibility=round(visibility_km, 1),
    )

@app.route("/", methods=['GET', 'POST'])
def home():
    weather_data = None
    error = None
    if request.method == 'POST':
        city_name = request.form.get("city_name", "").strip()
        if city_name:
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
            try:
                resp = requests.get(weather_url, timeout=10).json()
                if resp.get('cod') == 200:
                    weather_data = process_weather_data(resp)
                else:
                    error = "City not found. Please check the name and try again."
            except requests.exceptions.RequestException:
                error = "Unable to connect to weather service. Please try again later."
        else:
            error = "Please enter a city name."

    return render_template("index.html", weather_data=weather_data, error=error)

if __name__ == "__main__":
    app.run(debug=True)
