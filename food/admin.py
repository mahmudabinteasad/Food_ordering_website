from django.contrib import admin
from .models import Restaurant, FoodItem

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_featured', 'address', 'phone')
    list_filter = ('is_featured',)
    search_fields = ('name', 'address')

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'price')
    list_filter = ('restaurant',)
    search_fields = ('name', 'description')
