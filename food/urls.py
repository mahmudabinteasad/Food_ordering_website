# food/urls.py

from django.urls import path
from . import views
from .views import delete_cart_items

urlpatterns = [
    path('', views.home, name='home'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('search/', views.search, name='search'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('coming-soon/<str:platform>/', views.coming_soon, name='coming_soon'),
    path('menu/<int:restaurant_id>/', views.menu, name='menu'),
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('cart/', views.cart, name='cart'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout, name='logout'),
    path('add_to_cart/<int:food_id>/', views.add_to_cart, name='add_to_cart'),  # 🔥 New route
    path('restaurant/<int:restaurant_id>/menu/', views.restaurant_menu_view, name='restaurant_menu'),
    path('remove_from_cart/<int:food_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('delete_from_cart/<int:food_id>/', views.delete_from_cart, name='delete_from_cart'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('add_payment_method/', views.add_payment_method, name='add_payment_method'),
    path('add_delivery_address/', views.add_delivery_address, name='add_delivery_address'),
    path('update_preferences/', views.update_preferences, name='update_preferences'),
    path('order_details/<int:order_id>/', views.order_details, name='order_details'),
    path('place_order/', views.place_order, name='place_order'),
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('confirm_order/<int:order_id>/', views.confirm_order, name='confirm_order'),
    path('delete_cart_items/', views.delete_cart_items, name='delete_cart_items'),
    path('add_restaurant/', views.add_restaurant, name='add_restaurant'),
    path('add_food_items/<int:restaurant_id>/', views.add_food_items, name='add_food_items'),
    path('submit_for_approval/<int:restaurant_id>/', views.submit_for_approval, name='submit_for_approval'),
    path('restaurant/login/', views.restaurant_login, name='restaurant_login'),
    path('restaurant/login/submit/', views.restaurant_login_submit, name='restaurant_login_submit'),
    path('restaurant/<int:restaurant_id>/', views.restaurant_page, name='restaurant_page'),
    path('restaurant/<int:pk>/edit/', views.edit_restaurant, name='edit_restaurant'),
    path('fooditem/<int:pk>/edit/', views.edit_food_item, name='edit_food_item'),
    path('food-item/<int:pk>/delete/', views.delete_food_item, name='delete_food_item'),
    path('restaurant/<int:restaurant_id>/delete/', views.delete_restaurant, name='delete_restaurant'),
    path('add_restaurant_review/<int:restaurant_id>/', views.add_restaurant_review, name='add_restaurant_review'),
    path('add_food_item_review/<int:food_item_id>/', views.add_food_item_review, name='add_food_item_review'),
    path('dont-copy/', views.dont_copy, name='dont_copy'),
]