from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

class PaymentMethod(models.Model):
    payment_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=16)
    card_holder = models.CharField(max_length=100)
    expiry_date = models.CharField(max_length=5)
    is_default = models.BooleanField(default=False)

class DeliveryAddress(models.Model):
    address_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

class Preferences(models.Model):
    preference_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    notifications_enabled = models.BooleanField(default=True)
    language = models.CharField(max_length=50, default='English')
    theme = models.CharField(max_length=50, default='Light')

class Restaurant(models.Model):
    restaurant_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='restaurant_images/', null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    delivery_charge = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    min_order = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    open_until = models.TimeField(blank=True, null=True)
    weekly_schedule = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class FoodItem(models.Model):
    food_id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='food_images/', null=True, blank=True)
    special_instructions = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    food = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()

class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    status = models.CharField(max_length=20)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    food = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # Rating from 1 to 5
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE, null=True, blank=True)
    food_item = models.ForeignKey('FoodItem', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Review by {self.user.username}"