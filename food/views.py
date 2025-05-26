from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages
from .forms import SignUpForm
from .models import Restaurant, FoodItem, Cart, Customer, Order, OrderItem, PaymentMethod, DeliveryAddress, Preferences

def home(request):
    if 'customer_id' in request.session:
        return redirect('restaurant_list')
    return render(request, 'home.html')

def signin(request):
    if request.method == 'POST':
        username_or_email = request.POST['username_or_email']
        password = request.POST['password']

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM food_customer WHERE username = %s OR email = %s", [username_or_email, username_or_email])
                customer = cursor.fetchone()

            if customer is None:
                messages.error(request, 'Invalid username/email or password')
                return render(request, 'signin.html')

            if check_password(password, customer[3]):
                request.session['customer_id'] = customer[0]
                return redirect('restaurant_list')
            else:
                messages.error(request, 'Invalid username/email or password')

        except Exception:
            messages.error(request, 'An error occurred during sign-in')
            return render(request, 'signin.html')

    return render(request, 'signin.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = make_password(form.cleaned_data['password'])
            phone = form.cleaned_data['phone']

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO food_customer (username, email, password, phone)
                    VALUES (%s, %s, %s, %s)
                """, [username, email, password, phone])

            return redirect('signin')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def search(request):
    query = request.GET.get('q')
    restaurants = Restaurant.objects.filter(name__icontains=query)
    food_items = FoodItem.objects.filter(name__icontains=query)

    username = None
    if 'customer_id' in request.session:
        customer_id = request.session['customer_id']
        with connection.cursor() as cursor:
            cursor.execute("SELECT username FROM food_customer WHERE user_id = %s", [customer_id])
            username = cursor.fetchone()[0]

    return render(request, 'search_results.html', {
        'restaurants': restaurants,
        'food_items': food_items,
        'query': query,
        'username': username
    })

def menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(restaurant_id=restaurant_id)
    food_items = FoodItem.objects.filter(restaurant=restaurant).order_by('name')

    username = None
    if 'customer_id' in request.session:
        customer_id = request.session['customer_id']
        with connection.cursor() as cursor:
            cursor.execute("SELECT username FROM food_customer WHERE user_id = %s", [customer_id])
            username = cursor.fetchone()[0]

    return render(request, 'menu.html', {
        'restaurant': restaurant,
        'food_items': food_items,
        'username': username
    })

def restaurant_menu_view(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    query = request.GET.get('q', '')

    if query:
        # Filter food items by restaurant and name matching query
        food_items = FoodItem.objects.filter(
            restaurant=restaurant,
            name__icontains=query
        )
    else:
        food_items = FoodItem.objects.filter(restaurant=restaurant)

    return render(request, 'restaurant/menu.html', {
        'restaurant': restaurant,
        'food_items': food_items,
    })

def restaurant_list(request):
    if 'customer_id' not in request.session:
        return redirect('signin')

    all_restaurants = Restaurant.objects.all()
    featured_restaurants = Restaurant.objects.filter(is_featured=True)

    customer_id = request.session['customer_id']
    with connection.cursor() as cursor:
        cursor.execute("SELECT username FROM food_customer WHERE user_id = %s", [customer_id])
        username = cursor.fetchone()[0]

    return render(request, 'home_logged_in.html', {
        'featured_restaurants': featured_restaurants,
        'all_restaurants': all_restaurants,
        'username': username
    })

def cart(request):
    if 'customer_id' not in request.session:
        return redirect('signin')

    customer_id = request.session['customer_id']
    customer = get_object_or_404(Customer, user_id=customer_id)

    # Fetch cart items with related food and restaurant information
    cart_items = Cart.objects.filter(customer=customer).select_related('food__restaurant')

    # Calculate total price for all items in the cart
    total = sum(item.food.price * item.quantity for item in cart_items)

    # Calculate total number of items in the cart
    total_items = sum(item.quantity for item in cart_items)

    # Fetch delivery addresses
    delivery_addresses = DeliveryAddress.objects.filter(customer=customer)

    with connection.cursor() as cursor:
        cursor.execute("SELECT username FROM food_customer WHERE user_id = %s", [customer_id])
        username = cursor.fetchone()[0]

    return render(request, 'cart.html', {
        'username': username,
        'customer': customer,
        'cart_items': cart_items,
        'total': total,
        'delivery_addresses': delivery_addresses,
        'total_items': total_items  # Pass total_items to the template
    })

def place_order(request):
    if 'customer_id' not in request.session:
        messages.error(request, 'You need to be logged in to place an order.')
        return redirect('signin')

    if request.method == 'POST':
        try:
            print("Place Order view called")  # Debugging
            print("POST data:", request.POST)  # Debugging

            customer_id = request.session['customer_id']
            customer = get_object_or_404(Customer, user_id=customer_id)

            # Get selected cart item IDs
            selected_items = request.POST.getlist('selected_items')
            print("Selected items:", selected_items)  # Debugging

            if not selected_items:
                messages.error(request, 'No items selected for order.')
                return redirect('cart')

            # Fetch only selected cart items
            cart_items = Cart.objects.filter(customer=customer, food__food_id__in=selected_items).select_related('food')

            if not cart_items.exists():
                messages.error(request, 'No valid items selected for order.')
                return redirect('cart')

            # Calculate total price
            total_price = sum(item.food.price * item.quantity for item in cart_items)

            # Get selected delivery address
            selected_address_id = request.POST.get('delivery_address')
            print("Selected address ID:", selected_address_id)  # Debugging

            if not selected_address_id:
                messages.error(request, 'No delivery address selected.')
                return redirect('cart')

            selected_address = get_object_or_404(DeliveryAddress, address_id=selected_address_id)

            # Create order
            with transaction.atomic():
                order = Order.objects.create(
                    customer=customer,
                    status='Pending',
                    total_price=total_price,
                    delivery_address=selected_address.address
                )

                # Add ordered items to OrderItem and delete only those from cart
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        food=item.food,
                        quantity=item.quantity
                    )
                    item.delete()  # ✅ Only this ordered item is removed from the cart

            messages.success(request, 'Order placed successfully!')
            return redirect('order_confirmation', order_id=order.order_id)

        except Exception as e:
            print("Error placing order:", e)  # Debugging
            messages.error(request, f'An error occurred while placing the order: {str(e)}')
            return redirect('cart')

    return redirect('cart')

def delete_cart_items(request):
    if request.method == 'POST':
        item_ids = request.POST.getlist('item_ids[]')
        customer_id = request.session.get('customer_id')

        if customer_id:
            Cart.objects.filter(food_id__in=item_ids, customer_id=customer_id).delete()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def order_confirmation(request, order_id):
    if 'customer_id' not in request.session:
        return redirect('signin')

    order = get_object_or_404(Order, order_id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    return render(request, 'order_confirmation.html', {
        'order': order,
        'order_items': order_items
    })

def confirm_order(request, order_id):
    if 'customer_id' not in request.session:
        return redirect('signin')

    order = get_object_or_404(Order, order_id=order_id)

    # Update the order status to 'Confirmed'
    order.status = 'Confirmed'
    order.save()

    messages.success(request, 'Order confirmed successfully!')
    return redirect('order_confirmation', order_id=order.order_id)

def add_to_cart(request, food_id):
    if 'customer_id' not in request.session:
        return redirect('signin')

    customer_id = request.session['customer_id']
    customer = Customer.objects.get(user_id=customer_id)
    food = FoodItem.objects.get(food_id=food_id)

    cart_item = Cart.objects.filter(customer=customer, food=food).first()

    if cart_item:
        cart_item.quantity += 1
        cart_item.save()
    else:
        Cart.objects.create(customer=customer, food=food, quantity=1)
        messages.success(request, 'Added to cart successfully!')

    return redirect(request.META.get('HTTP_REFERER', 'cart'))

def remove_from_cart(request, food_id):
    if 'customer_id' not in request.session:
        return redirect('signin')

    customer_id = request.session['customer_id']
    customer = Customer.objects.get(user_id=customer_id)
    food = get_object_or_404(FoodItem, food_id=food_id)

    cart_item = Cart.objects.filter(customer=customer, food=food).first()

    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

    return redirect('cart')

def delete_from_cart(request, food_id):
    if 'customer_id' not in request.session:
        return redirect('signin')

    customer_id = request.session['customer_id']
    customer = Customer.objects.get(user_id=customer_id)
    food = get_object_or_404(FoodItem, food_id=food_id)

    Cart.objects.filter(customer=customer, food=food).delete()

    return redirect('cart')

def profile(request):
    if 'customer_id' not in request.session:
        return redirect('signin')

    customer_id = request.session['customer_id']
    customer = get_object_or_404(Customer, user_id=customer_id)

    # Fetch order history
    orders = Order.objects.filter(customer=customer).order_by('-timestamp')

    # Fetch payment methods
    payment_methods = PaymentMethod.objects.filter(customer=customer)

    # Fetch delivery addresses
    delivery_addresses = DeliveryAddress.objects.filter(customer=customer)

    # Fetch preferences
    preferences = Preferences.objects.filter(customer=customer).first()

    with connection.cursor() as cursor:
        cursor.execute("SELECT username FROM food_customer WHERE user_id = %s", [customer_id])
        username = cursor.fetchone()[0]

    return render(request, 'profile.html', {
        'username': username,
        'customer': customer,
        'orders': orders,
        'payment_methods': payment_methods,
        'delivery_addresses': delivery_addresses,
        'preferences': preferences
    })

def update_profile(request):
    if 'customer_id' not in request.session:
        return redirect('signin')

    customer_id = request.session['customer_id']
    customer = get_object_or_404(Customer, user_id=customer_id)

    if request.method == 'POST':
        customer.username = request.POST.get('username', customer.username)
        customer.email = request.POST.get('email', customer.email)
        customer.phone = request.POST.get('phone', customer.phone)
        customer.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'update_profile.html', {'customer': customer})

def add_payment_method(request):
    if 'customer_id' not in request.session:
        return redirect('signin')

    customer_id = request.session['customer_id']
    customer = get_object_or_404(Customer, user_id=customer_id)

    if request.method == 'POST':
        card_number = request.POST.get('card_number')
        card_holder = request.POST.get('card_holder')
        expiry_date = request.POST.get('expiry_date')

        PaymentMethod.objects.create(
            customer=customer,
            card_number=card_number,
            card_holder=card_holder,
            expiry_date=expiry_date
        )

        messages.success(request, 'Payment method added successfully!')
        return redirect('profile')

    return render(request, 'add_payment_method.html', {'customer': customer})

def add_delivery_address(request):
    if 'customer_id' not in request.session:
        return redirect('signin')

    customer_id = request.session['customer_id']
    customer = get_object_or_404(Customer, user_id=customer_id)

    if request.method == 'POST':
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')

        DeliveryAddress.objects.create(
            customer=customer,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code
        )

        messages.success(request, 'Delivery address added successfully!')
        return redirect('profile')

    return render(request, 'add_delivery_address.html', {'customer': customer})

def update_preferences(request):
    if 'customer_id' not in request.session:
        return redirect('signin')

    customer_id = request.session['customer_id']
    customer = get_object_or_404(Customer, user_id=customer_id)
    preferences, created = Preferences.objects.get_or_create(customer=customer)

    if request.method == 'POST':
        preferences.notifications_enabled = request.POST.get('notifications_enabled', 'off') == 'on'
        preferences.language = request.POST.get('language', preferences.language)
        preferences.theme = request.POST.get('theme', preferences.theme)
        preferences.save()
        messages.success(request, 'Preferences updated successfully!')
        return redirect('profile')

    return render(request, 'update_preferences.html', {'preferences': preferences})

def order_details(request, order_id):
    if 'customer_id' not in request.session:
        return redirect('signin')

    order = get_object_or_404(Order, order_id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    return render(request, 'order_details.html', {
        'order': order,
        'order_items': order_items
    })

def logout(request):
    if 'customer_id' in request.session:
        del request.session['customer_id']
    return redirect('home')