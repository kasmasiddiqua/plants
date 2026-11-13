from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .forms import AccountSettingsForm, ObservationForm, PlantForm, RegisterForm
from django.contrib.auth.forms import PasswordChangeForm
from .models import Observation, Plant
from .services.image_analysis import analyze_image, detect_disease
from .services.prediction import growth_status, recommendation, predict_next_height


PLANT_INSIGHTS = {
    'tomato': {
        'use': 'Food crop for salads, sauces, and cooking.',
        'body': 'Provides vitamin C, potassium, and lycopene as part of a varied diet.',
        'note': 'Food benefits depend on serving size and preparation; this is not medical advice.',
    },
    'mint': {
        'use': 'Culinary herb for drinks, teas, and fresh dishes.',
        'body': 'Adds flavor and small amounts of antioxidants. Mint tea may feel soothing for some people.',
        'note': 'Do not use herbs as a treatment or replace professional medical care.',
    },
    'basil': {
        'use': 'Culinary herb for sauces, salads, and seasoning.',
        'body': 'Adds flavor and plant compounds while helping reduce the need for excess salt in some recipes.',
        'note': 'Use as food and follow appropriate food-safety practices.',
    },
    'spinach': {
        'use': 'Leafy vegetable for salads, soups, and cooked meals.',
        'body': 'Contains folate, vitamin K, vitamin A, and iron as part of a balanced diet.',
        'note': 'People with specific health conditions should ask a clinician about dietary changes.',
    },
    'aloe': {
        'use': 'Ornamental succulent; commonly grown for its gel in household skincare.',
        'body': 'Topical aloe products may soothe minor skin irritation for some people, but evidence and products vary.',
        'note': 'Do not eat home-prepared aloe; avoid applying it to serious wounds and seek medical advice when needed.',
    },
}

PLANT_KNOWLEDGE = {
    'apple': {
        'where': 'Apples grow best in temperate regions with cool winters, a spring flowering period, and full sun. Most varieties need cross-pollination from a compatible apple tree.',
        'care': 'Use well-drained soil, regular deep watering while young, full sun, and seasonal pruning. Protect flowers from late frost and thin fruit when the tree is overloaded.',
        'harvest': 'Harvest when the fruit has reached its expected size and separates with a gentle upward twist. Ripeness varies by variety, so check local growing guidance.',
    },
    'tomato': {
        'where': 'Tomatoes grow best in warm weather with 6 to 8 hours of sunlight, fertile well-drained soil, and protection from cold nights.',
        'care': 'Water at the soil line when the top layer begins to dry, support the stem, keep leaves reasonably dry, and watch for pests and fungal spots.',
        'harvest': 'Harvest when fruit has developed its mature color and gives slightly to gentle pressure. Pick regularly to encourage more fruit.',
    },
    'mint': {
        'where': 'Mint grows in moist, rich soil with partial shade to bright indirect light. It spreads aggressively, so containers are often useful.',
        'care': 'Keep soil lightly moist, pinch growing tips to encourage bushiness, and trim flowers if you want more leafy growth.',
        'harvest': 'Harvest young stems and leaves before flowering for strong flavor. Use clean scissors and avoid removing more than one-third at once.',
    },
    'basil': {
        'where': 'Basil grows in warm conditions with full sun, well-drained soil, and protection from cold temperatures.',
        'care': 'Water when the surface starts to dry, pinch the top leaves, and remove flower buds to keep the plant producing leaves.',
        'harvest': 'Pick leaves from the top in the morning after the dew dries. Harvest regularly rather than stripping the whole plant.',
    },
    'aloe': {
        'where': 'Aloe prefers warm, bright light and very well-drained, gritty soil. It grows well indoors near a bright window or outdoors in warm climates.',
        'care': 'Let the soil dry fully between waterings and use a pot with drainage. Soft or dark leaves often indicate excess moisture.',
        'harvest': 'For household use, only use correctly identified, mature aloe and commercially prepared products. Do not ingest home-prepared aloe latex or gel.',
    },
    'spinach': {
        'where': 'Spinach prefers cool seasons and partial shade in warmer weather. It grows in fertile soil with consistent moisture.',
        'care': 'Keep soil evenly moist, harvest outer leaves first, and provide shade when temperatures rise to slow bolting.',
        'harvest': 'Harvest outer leaves when they are large enough to use, or cut the whole plant above the crown for a later regrowth attempt.',
    },
}


def plant_insight(plant):
    plant_text = f'{plant.name} {plant.plant_type}'.lower()
    for keyword, insight in PLANT_INSIGHTS.items():
        if keyword in plant_text:
            return insight
    return {
        'use': f'{plant.plant_type or "Plant"} for home growing, observation, and gardening practice.',
        'body': 'Its direct human benefit depends on the species. Confirm identification before eating or using any plant.',
        'note': 'PlantVision provides educational guidance, not medical or dietary advice.',
    }


def knowledge_for_question(question, plants):
    candidates = [plant.name.lower() for plant in plants]
    candidates.extend(PLANT_KNOWLEDGE)
    plant_key = next((name for name in candidates if name in question), None)
    if not plant_key:
        return None
    knowledge = PLANT_KNOWLEDGE.get(plant_key)
    knowledge_topics = ('where', 'climate', 'region', 'place', 'outside', 'care', 'look after', 'maintain', 'soil', 'water', 'light', 'sun', 'harvest', 'pick', 'collect', 'ready', 'eat')
    if not any(word in question for word in knowledge_topics):
        return None
    if not knowledge:
        return f'I recognize {plant_key.title()} in your question, but I need a more specific species profile before giving reliable care or human-use information. Confirm the plant type and upload a clear photo.'
    if any(word in question for word in ('where', 'grow', 'climate', 'region', 'place', 'outside')):
        return knowledge['where']
    if any(word in question for word in ('care', 'look after', 'maintain', 'soil', 'water', 'light', 'sun')):
        return knowledge['care']
    if any(word in question for word in ('harvest', 'pick', 'collect', 'ready', 'eat')):
        return knowledge['harvest']
    return f"{plant_key.title()}: {knowledge['where']} {knowledge['care']} {knowledge['harvest']}"


def landing(request):
    return render(request, 'landing.html')


@login_required
def dashboard(request):
    plants = Plant.objects.filter(user=request.user).prefetch_related('observations')
    latest = Observation.objects.filter(plant__user=request.user).order_by('-captured_on').first()
    analyses = Observation.objects.filter(plant__user=request.user).count()
    leaves = sum(row.leaf_count for plant in plants for row in plant.observations.all())
    return render(request, 'dashboard.html', {
        'plants': plants, 'latest': latest, 'total_plants': plants.count(),
        'analyses': analyses, 'leaves': leaves,
    })


@login_required
def plants(request):
    plant_list = Plant.objects.filter(user=request.user).prefetch_related('observations')
    return render(request, 'plants.html', {'plants': plant_list})

@login_required
def disease_scan(request):
    if request.method != 'POST' or not request.FILES.get('image'):
        return JsonResponse({'error': 'Choose a plant image before scanning.'}, status=400)
    try:
        result = detect_disease(request.FILES['image'])
    except ValueError as error:
        return JsonResponse({'error': str(error)}, status=400)
    return JsonResponse(result)


@login_required
def analytics(request):
    plants = list(Plant.objects.filter(user=request.user).prefetch_related('observations'))
    observations = list(Observation.objects.filter(plant__user=request.user).select_related('plant'))
    plant_insights = []
    for plant in plants:
        rows = list(plant.observations.all())
        latest = rows[-1] if rows else None
        previous = rows[-2] if len(rows) > 1 else None
        change = round(latest.estimated_height_cm - previous.estimated_height_cm, 2) if latest and previous else None
        plant_insights.append({
            'plant': plant,
            'latest': latest,
            'height_change': change,
            'projection': predict_next_height(rows),
            'insight': plant_insight(plant),
            'recommendation': recommendation(latest.growth_status) if latest else 'Upload a first observation to begin growth analysis.',
        })
    chart_rows = observations[-30:]
    chart_data = {
        'labels': [row.captured_on.strftime('%d %b') for row in chart_rows],
        'height': [row.estimated_height_cm for row in chart_rows],
        'leaves': [row.leaf_count for row in chart_rows],
    }
    return render(request, 'analytics.html', {
        'observations': observations, 'plants': plants, 'plant_insights': plant_insights,
        'chart_data': chart_data,
    })


@login_required
def predictions(request):
    plant_list = Plant.objects.filter(user=request.user).prefetch_related('observations')
    predictions_data = [(plant, predict_next_height(list(plant.observations.all()))) for plant in plant_list]
    return render(request, 'predictions.html', {'predictions': predictions_data})


@login_required
def history(request):
    observations = Observation.objects.filter(plant__user=request.user).select_related('plant')
    return render(request, 'history.html', {'observations': observations})


@login_required
def notifications(request):
    return render(request, 'notifications.html')


@login_required
def settings_page(request):
    account_form = AccountSettingsForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    if request.method == 'POST':
        if request.POST.get('form_name') == 'password':
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was changed successfully.')
                return redirect('settings')
        else:
            account_form = AccountSettingsForm(request.POST, instance=request.user)
            if account_form.is_valid():
                account_form.save()
                messages.success(request, 'Your account changes were saved.')
                return redirect('settings')
    return render(request, 'settings.html', {'account_form': account_form, 'password_form': password_form})


@login_required
def ai_suggestion(request):
    question = request.GET.get('question', '').strip().lower()
    plants = list(Plant.objects.filter(user=request.user).prefetch_related('observations'))
    selected_plant = None
    selected_plant_id = request.GET.get('plant_id')
    if selected_plant_id and selected_plant_id.isdigit():
        selected_plant = next((plant for plant in plants if plant.id == int(selected_plant_id)), None)
    if selected_plant:
        plants = [selected_plant]
        if selected_plant.name.lower() not in question:
            question = f'{selected_plant.name.lower()} {question}'
    latest = [plant.latest_observation for plant in plants if plant.latest_observation]
    plant_count = len(plants)
    observation_count = len(latest)
    slow_count = sum(observation.growth_status == 'slow' for observation in latest)
    focus = plants[0].name if plants else 'your plants'

    growth_rows = []
    for plant in plants:
        observations = list(plant.observations.all())
        if not observations:
            continue
        current = observations[-1]
        previous = observations[-2] if len(observations) > 1 else None
        height_change = round(current.estimated_height_cm - previous.estimated_height_cm, 2) if previous else None
        projected_height = predict_next_height(observations)
        growth_rows.append({
            'name': plant.name,
            'status': current.growth_status,
            'growth': current.growth_percent,
            'height_change': height_change,
            'projected_height': projected_height,
        })

    def growth_summary():
        if not growth_rows:
            return 'I do not have enough observations yet. Add at least two dated photos for a meaningful growth comparison.'
        parts = []
        for row in growth_rows:
            if row['height_change'] is None:
                parts.append(f"{row['name']} has one observation so far")
            else:
                trend = 'grew' if row['height_change'] >= 0 else 'decreased'
                projection = f", projected at {row['projected_height']} cm in about 7 days" if row['projected_height'] is not None else ''
                parts.append(f"{row['name']} {trend} {abs(row['height_change'])} cm, latest growth {row['growth']}%{projection}")
        recommendation_text = ' Keep the current routine and capture another photo in 5 to 7 days.'
        if slow_count:
            recommendation_text = ' Review light, watering, pests, and soil for the slow-growth plants, then capture another consistent photo in 3 to 5 days.'
        return 'Growth analysis: ' + '; '.join(parts) + '.' + recommendation_text

    def plant_overview():
        if not plants:
            return 'You have no saved plants yet. Add a plant with its name and type, then upload a photo so I can build its profile.'
        profiles = []
        for plant in plants:
            insight = plant_insight(plant)
            current = plant.latest_observation
            measurement = f" Latest reading: {current.estimated_height_cm} cm, {current.leaf_count} visible leaves, and {current.get_growth_status_display().lower()} growth." if current else ' No image observation has been uploaded yet.'
            profiles.append(f"{plant.name} ({plant.plant_type}): {insight['use']} {insight['body']}{measurement}")
        return 'Here is what I know about your saved plants: ' + ' '.join(profiles) + ' Ask me about care, growth, uses, human value, or the next step for a specific plant.'

    def care_summary():
        if not plants:
            return 'Add a plant name and type first. I can then tailor light, watering, soil, and monitoring suggestions.'
        names = ', '.join(plant.name for plant in plants)
        return f'For {names}, keep light and watering consistent, check the soil before watering, inspect leaves and stems weekly for pests, and record photos from a similar distance. The right routine depends on the exact species, pot, soil, and climate.'

    knowledge_answer = knowledge_for_question(question, plants)
    if not question:
        answer = 'Tell me what you are growing or what looks unusual, and I will suggest the next step.'
    elif knowledge_answer:
        answer = knowledge_answer
    elif any(word in question for word in ('disease', 'diseases', 'fungus', 'fungal', 'pest', 'pests', 'insect')):
        answer = 'Inspect both sides of leaves and the soil surface, isolate a visibly affected plant, remove badly damaged leaves with clean tools, and improve airflow. Avoid spraying chemicals until the plant and problem are identified; follow the product label and keep treatments away from food unless approved for edible crops.'
    elif any(word in question for word in ('prune', 'pruning', 'trim', 'cut')):
        answer = 'Prune with clean, sharp tools and remove dead, damaged, or crossing growth first. Avoid removing more than about one-third of a plant at once, and research the species before cutting flowering or fruiting branches.'
    elif any(word in question for word in ('propagate', 'propagation', 'cutting', 'cuttings', 'seed')):
        answer = 'Propagation depends on the species: common methods include seeds, stem cuttings, division, and offsets. Use clean tools, a sterile well-drained medium, indirect light, and gentle moisture while roots develop.'
    elif any(word in question for word in ('tell me', 'information', 'info', 'about my', 'what plant', 'details', 'profile', 'saved plant')):
        answer = plant_overview()
    elif any(word in question for word in ('benefit', 'useful', 'use', 'body', 'human', 'nutrition', 'eat', 'food')):
        if plants:
            insight = plant_insight(plants[0])
            answer = f'{plants[0].name} is useful for {insight["use"].lower()} {insight["body"]} {insight["note"]}'
        else:
            answer = 'Add an identified plant first so I can explain its likely uses. Never eat or apply an unknown plant.'
    elif any(word in question for word in ('care', 'look after', 'maintain', 'soil', 'fertilizer', 'feed')):
        answer = care_summary()
    elif any(word in question for word in ('yellow', 'yellowing', 'leaf', 'leaves')):
        answer = f'Check {focus} for soil moisture, direct midday sun, and pests under the leaves. Water only when the top layer feels dry, and compare another photo in 3 to 5 days.'
    elif any(word in question for word in ('water', 'watering', 'dry')):
        answer = 'Water slowly until a little drains from the pot, then empty the saucer. Let the top 2 to 3 cm of soil dry before watering again; light and pot size change the schedule.'
    elif any(word in question for word in ('light', 'sun', 'dark')):
        answer = 'Aim for bright, indirect light unless your plant is a full-sun variety. Move it gradually and watch for bleached leaves or long, weak new growth.'
    elif any(word in question for word in ('growth', 'grow', 'progress', 'health')):
        answer = growth_summary()
    else:
        answer = 'I can help with where a plant grows, climate, light, watering, soil, fertilizer, pests, yellow leaves, pruning, harvesting, uses, human value, and growth analysis. Include the plant name in your question, such as “Where does apple grow?” or “How do I care for tomato?”'

    return JsonResponse({'answer': answer})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return auth_views.LoginView.as_view(template_name='registration/login.html')(request)


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'registration/register.html', {'form': form})


@login_required
def plant_create(request):
    form = PlantForm(request.POST or None)
    if form.is_valid():
        plant = form.save(commit=False)
        plant.user = request.user
        plant.save()
        return redirect('plant_detail', plant_id=plant.id)
    return render(request, 'plant_form.html', {'form': form, 'title': 'Register a plant'})


@login_required
def plant_detail(request, plant_id):
    plant = Plant.objects.filter(id=plant_id, user=request.user).first()
    if plant is None:
        messages.warning(request, 'That plant no longer exists in your collection.')
        return redirect('plants')
    observations = list(plant.observations.all())
    prediction = predict_next_height(observations)
    latest = observations[-1] if observations else None
    return render(request, 'plant_detail.html', {
        'plant': plant, 'observations': observations, 'latest': latest,
        'prediction': prediction, 'recommendation': recommendation(latest.growth_status) if latest else None,
        'chart_labels': [row.captured_on.strftime('%d %b') for row in observations],
        'height_data': [row.estimated_height_cm for row in observations],
        'leaf_data': [row.leaf_count for row in observations],
        'growth_data': [row.growth_percent for row in observations],
    })


@login_required
def plant_delete(request, plant_id):
    plant = get_object_or_404(Plant, id=plant_id, user=request.user)
    if request.method == 'POST':
        plant.delete()
        messages.success(request, 'Plant removed from your collection.')
        return redirect('plants')
    return redirect('plant_detail', plant_id=plant.id)


@login_required
def upload_observation(request, plant_id):
    plant = Plant.objects.filter(id=plant_id, user=request.user).first()
    if plant is None:
        messages.warning(request, 'That plant no longer exists, so this upload was cancelled.')
        return redirect('plants')
    form = ObservationForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        observation = form.save(commit=False)
        observation.plant = plant
        previous = plant.observations.order_by('-captured_on').first()
        measurement = analyze_image(observation.image.file)
        observation.estimated_height_cm = measurement['height_cm']
        observation.leaf_count = measurement['leaf_count']
        observation.leaf_area_percent = measurement['leaf_area_percent']
        baseline = previous.estimated_height_cm if previous else 0
        observation.growth_percent = round(((observation.estimated_height_cm - baseline) / baseline) * 100, 2) if baseline else 0
        observation.growth_status = growth_status(observation.growth_percent)
        observation.analysis_note = measurement['note']
        observation.save()
        messages.success(request, 'Image analyzed and observation saved.')
        return redirect('plant_detail', plant_id=plant.id)
    return render(request, 'upload_form.html', {'form': form, 'plant': plant})


@login_required
def comparison(request, plant_id):
    plant = get_object_or_404(Plant, id=plant_id, user=request.user)
    observations = list(plant.observations.all())
    first = observations[0] if observations else None
    latest = observations[-1] if observations else None
    return render(request, 'comparison.html', {
        'plant': plant, 'first': first, 'latest': latest,
        'height_change': round(latest.estimated_height_cm - first.estimated_height_cm, 2) if first and latest else None,
        'leaf_change': latest.leaf_count - first.leaf_count if first and latest else None,
    })
