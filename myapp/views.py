from django.shortcuts import render, redirect, get_object_or_404
from .models import Polygon, Details, tools, Crop, ResourceItem
from .forms import PolygonForm, RegistrationForm
import requests
import json
from datetime import datetime, timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
@login_required
def dashboard(request):
    polygon_id = "67969e9650f5a45f841b8c23"
    details = get_object_or_404(Details, polygon__polygon_id=polygon_id)
    api = details.api_key
    result = requests.get(f"http://api.agromonitoring.com/agro/1.0/polygons/{polygon_id}?appid={api}")
    weather = requests.get(f"https://api.agromonitoring.com/agro/1.0/weather/forecast?lat={result.json()['center'][1]}&lon={result.json()['center'][0]}&appid={api}")

    # Fetch news data
    news_api_key = 'ffe32e11bcce44b8b1877ca0af6cbf35'
    news_url = f"https://newsapi.org/v2/top-headlines?country=us&category=business&apiKey={news_api_key}"
    news_response = requests.get(news_url)
    news_data = news_response.json().get('articles', [])[:3]  # Get top 3 news articles

    context = {
        "weather": weather.json(),
        "news": news_data
    }
    return render(request, 'myapp/dashboard.html', context)


@login_required
def services(request):
    return render(request, 'myapp/services.html')
@login_required
def Tool(request):
    products = tools.objects.all()
    return render(request, 'myapp/tools.html', {'products': products})

def about(request):
    return render(request, 'myapp/about.html')
@login_required
def resources(request):
    return render(request, 'myapp/resources.html')
@login_required
def resources_view(request):
    # Get category choices from model
    categories = []
    for choice in ResourceItem.CATEGORY_CHOICES:
        category_slug, category_name = choice
        items = ResourceItem.objects.filter(category=category_slug)
        categories.append({
            'slug': category_slug,
            'name': category_name,
            'items': items
        })
    
    context = {
        'categories': categories
    }
    return render(request, 'myapp/resources.html', context)
@login_required
def market(request):
    crops = Crop.objects.prefetch_related('historical_prices').all().order_by('name')
    return render(request, 'myapp/market.html', {'crops': crops})
@login_required
def trade(request):
    return render(request, 'myapp/trade.html')

def login_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'myapp/login.html', {'form': form})
def handlelogout(request):
    logout(request)
    return redirect('/login')
def logout_view(request):
    logout(request)
    return redirect('login')
def privacy(request):
    return render(request,'myapp/privacy.html')

def TandC(request):
    return render(request,'myapp/TandC.html')

def FAQs(request):
    return render(request,'myapp/FAQs.html')

def add_polygon(request):
    if request.method == 'POST':
        form = PolygonForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('polygon_list')
    else:
        form = PolygonForm()
    return render(request, 'myapp/add_polygon.html', {'form': form})

def polygon_list(request):
    polygons = Polygon.objects.all()
    return render(request, 'myapp/polygon_list.html', {'polygons': polygons})
@login_required
def news(request):
    url="https://newsapi.org/v2/everything?q=farmer&from=2025-05-25&sortBy=popularity&apiKey=ffe32e11bcce44b8b1877ca0af6cbf35"
    
    farmer_news = requests.get(url).json()
    
    a = farmer_news['articles']
    desc = []
    title = []
    img = []
    
    for i in range(len(a)):
        f = a[i]
        title.append(f['title'])
        desc.append(f['description'])
        img.append(f['urlToImage'])
        
    mylist = zip(title, desc, img)
    context = {'mylist': mylist}
    print(farmer_news)
    return render(request, 'myapp/news.html', context)

def get_agro_data(request, polygon_id):
    api_key = 'b4dfb6aa45d5601e695f381d85217b11'
    url = f'https://api.agromonitoring.com/data?api_key={api_key}&polygon_id={polygon_id}'
    response = requests.get(url)
    data = response.json() if response.status_code == 200 else None
    return render(request, 'myapp/agro_data.html', {'data': data})

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Add custom field handling here if needed
            # For example, if you have a Profile model:
            # profile = user.profile
            # profile.polygon_id = form.cleaned_data.get('polygon_id')
            # profile.save()
            
            login(request, user)
                
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()
    
    return render(request, 'myapp/register.html', {'form': form})

def fetch_weather_data(polygon_id):
    api_key = 'b4dfb6aa45d5601e695f381d85217b11'
    url = f'https://api.agromonitoring.com/data?api_key={api_key}&polygon_id={polygon_id}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def weather_dashboard(request):
    # Assuming you want to display data for the first polygon
    polygon = Polygon.objects.first()
    data = fetch_weather_data(polygon.polygon_id) if polygon else None
    return render(request, 'myapp/weather_dashboard.html', {'data': data})

def main_dashboard(request):
    # Assuming you want to display data for the first polygon
    polygon = Polygon.objects.first()
    data = fetch_weather_data(polygon.polygon_id) if polygon else None
    return render(request, 'myapp/main_dashboard.html', {'data': data})
@login_required
def details(request, polygon_id):
    details = get_object_or_404(Details, polygon__polygon_id=polygon_id)
    api = details.api_key

    # Get user input for start and end dates
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Convert dates to Unix timestamp if provided
    if end_date:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        end_datetime = timezone.make_aware(end_datetime, timezone.get_current_timezone())  # Make it timezone-aware
        end_timestamp = int(end_datetime.timestamp())
    else:
        end_timestamp = details.end_date.timestamp()  # Default end timestamp

    if start_date:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        start_datetime = timezone.make_aware(start_datetime, timezone.get_current_timezone())  # Make it timezone-aware
        start_timestamp = int(start_datetime.timestamp())
    else:
        start_timestamp = details.start_date.timestamp()  # Default start timestamp

    # Fetch data from the API
    result = requests.get(f"http://api.agromonitoring.com/agro/1.0/polygons/{polygon_id}?appid={api}")
    ndvi = requests.get(f"http://api.agromonitoring.com/agro/1.0/ndvi/history?start={start_timestamp}&end={end_timestamp}&polyid={polygon_id}&appid={api}")
    weather = requests.get(f"https://api.agromonitoring.com/agro/1.0/weather/forecast?lat={result.json()['center'][1]}&lon={result.json()['center'][0]}&appid={api}")
    soil = requests.get(f"http://api.agromonitoring.com/agro/1.0/soil?polyid={polygon_id}&appid={api}")
    uv_index = requests.get(f"http://api.agromonitoring.com/agro/1.0/uvi?polyid={polygon_id}&appid={api}")

    # Process UV index data
    uv_index_data = uv_index.json()
    uv_index_value = uv_index_data.get('uvi')
    uv_index_date = datetime.utcfromtimestamp(uv_index_data.get('dt')).strftime('%Y-%m-%d %H:%M:%S')

    return render(request, "myapp/details.html", {
        "api_data_json": result.json(),
        "ndvi_data_json": ndvi.json(),
        "start_date": start_date,
        "end_date": end_date,
        "polygon_id": polygon_id,
        "weather": weather.json(),
        "soil": soil.json(),
        "uv_index_value": uv_index_value,
        "uv_index_date": uv_index_date
    })

@method_decorator(csrf_exempt, name='dispatch')
class ChatbotView(View):
    def get(self, request):
        return render(request, 'chatbot/chat_popup.html')

    def post(self, request):
        try:
            data = json.loads(request.body)
            message = data.get('message', '')

            headers = {
                'Authorization': f'Bearer {settings.GEMINI_API_KEY}',
                'Content-Type': 'application/json'
            }
            payload = {
                "input": message
            }
            response = requests.post(
                'https://api.gemini.com/v1/chat',
                headers=headers,
                json=payload
            )
            response_data = response.json()
            print("Gemini API response:", response_data)  # Debugging line
            bot_response = response_data.get('response', 'Sorry, I could not understand that.')
            return JsonResponse({'message': bot_response})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
