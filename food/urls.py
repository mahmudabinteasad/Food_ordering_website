# food/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('search/', views.search, name='search'),
    path('menu/<int:restaurant_id>/', views.menu, name='menu'),
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('cart/', views.cart, name='cart'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout, name='logout'),
    path('add_to_cart/<int:food_id>/', views.add_to_cart, name='add_to_cart'),  # 🔥 New route
    path('restaurant/<int:restaurant_id>/menu/', views.restaurant_menu_view, name='restaurant_menu'),
    path('remove_from_cart/<int:food_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('delete_from_cart/<int:food_id>/', views.delete_from_cart, name='delete_from_cart'),
]