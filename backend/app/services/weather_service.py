import requests
import os


class WeatherService:
    @staticmethod
    def get_weather(city):
        try:
            api_key = os.getenv('OPENWEATHERMAP_API_KEY', '')
            
            if not api_key:
                return None, "Weather API key not configured"
            
            url = 'https://api.openweathermap.org/data/2.5/weather'
            params = {
                'q': city,
                'appid': api_key,
                'units': 'metric',  # Celsius
                'lang': 'de'
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            weather_info = {
                'temperature': round(data['main']['temp'], 1),
                'feels_like': round(data['main']['feels_like'], 1),
                'description': data['weather'][0]['description'].capitalize(),
                'icon': data['weather'][0]['icon'],
                'humidity': data['main']['humidity'],
                'city': data['name']
            }
            
            return weather_info, None
            
        except requests.exceptions.Timeout:
            return None, "Weather API timeout"
        except requests.exceptions.RequestException as e:
            return None, f"Weather API error: {str(e)}"
        except (KeyError, IndexError) as e:
            return None, f"Invalid weather data: {str(e)}"
    
    @staticmethod
    def format_weather_string(weather_info):
        if not weather_info:
            return "Wetter nicht verfügbar"
        
        temp = weather_info['temperature']
        desc = weather_info['description']
        
        return f"{temp}°C, {desc}"
    
    @staticmethod
    def get_clothing_recommendation(temperature):
        if temperature < 0:
            return "Winterjacke, Schal und Handschuhe empfohlen"
        elif temperature < 10:
            return "Warme Jacke empfohlen"
        elif temperature < 15:
            return "Leichte Jacke oder Pullover"
        elif temperature < 20:
            return "Leichte Jacke optional"
        elif temperature < 25:
            return "Leichte Kleidung ausreichend"
        else:
            return "Kurze Kleidung, Sonnenschutz nicht vergessen"