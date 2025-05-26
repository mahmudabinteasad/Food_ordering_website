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
