from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html', email_template_name='registration/password_reset_email.html', subject_template_name='registration/password_reset_subject.txt'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('plants/new/', views.plant_create, name='plant_create'),
    path('plants/<int:plant_id>/', views.plant_detail, name='plant_detail'),
    path('plants/<int:plant_id>/delete/', views.plant_delete, name='plant_delete'),
    path('plants/<int:plant_id>/upload/', views.upload_observation, name='upload_observation'),
    path('plants/<int:plant_id>/analyze/', views.upload_observation, name='analyze'),
    path('plants/<int:plant_id>/comparison/', views.comparison, name='comparison'),
    path('plants/', views.plants, name='plants'),
    path('ai/disease-scan/', views.disease_scan, name='disease_scan'),
    path('analytics/', views.analytics, name='analytics'),
    path('predictions/', views.predictions, name='predictions'),
    path('history/', views.history, name='history'),
    path('notifications/', views.notifications, name='notifications'),
    path('settings/', views.settings_page, name='settings'),
    path('ai/suggestion/', views.ai_suggestion, name='ai_suggestion'),
]
