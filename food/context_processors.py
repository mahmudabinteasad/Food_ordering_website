# food/context_processors.py
from .models import Cart, Customer

def cart_count(request):
    total_items = 0
    if 'customer_id' in request.session:
        customer_id = request.session['customer_id']
        customer = Customer.objects.get(user_id=customer_id)
        cart_items = Cart.objects.filter(customer=customer)
        total_items = sum(item.quantity for item in cart_items)
    return {'total_items': total_items}

def preferences_processor(request):
    preferences = None
    if 'customer_id' in request.session:
        try:
            customer_id = request.session['customer_id']
            customer = Customer.objects.get(user_id=customer_id)
            # Assuming your Customer model has a OneToOne or ForeignKey to Preferences
            preferences = getattr(customer, 'preferences', None)
        except Customer.DoesNotExist:
            preferences = None
    return {'preferences': preferences}