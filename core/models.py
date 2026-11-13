from django.contrib.auth.models import User
from django.db import models


class Plant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plants')
    name = models.CharField(max_length=100)
    plant_type = models.CharField(max_length=100)
    planting_date = models.DateField()
    location = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.plant_type})'

    @property
    def latest_observation(self):
        return self.observations.order_by('-captured_on', '-created_at').first()


class Observation(models.Model):
    STATUS_CHOICES = [('healthy', 'Healthy'), ('good', 'Good'), ('normal', 'Normal'), ('slow', 'Slow')]
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='observations')
    image = models.ImageField(upload_to='plant_images/%Y/%m/')
    captured_on = models.DateField()
    estimated_height_cm = models.FloatField(default=0)
    leaf_count = models.PositiveIntegerField(default=0)
    leaf_area_percent = models.FloatField(default=0)
    growth_percent = models.FloatField(default=0)
    growth_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='normal')
    analysis_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['captured_on', 'created_at']

    def __str__(self):
        return f'{self.plant.name} - {self.captured_on}'
