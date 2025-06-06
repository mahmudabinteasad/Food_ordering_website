from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection, transaction
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages
from .forms import SignUpForm
from django.db.models import Q
from .models import Restaurant, FoodItem, Cart, Customer, Order, OrderItem, PaymentMethod, DeliveryAddress, Preferences
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json

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

def get_username_by_id(customer_id):
    customer = Customer.objects.filter(user_id=customer_id).only('username').first()
    return customer.username if customer else None

def search(request):
    query = request.GET.get('q')
    restaurants = Restaurant.objects.filter(name__icontains=query)
    food_items = FoodItem.objects.filter(name__icontains=query)

    username = None
    if 'customer_id' in request.session:
        username = get_username_by_id(request.session['customer_id'])

    return render(request, 'search_results.html', {
        'restaurants': restaurants,
        'food_items': food_items,
        'query': query,
        'username': username
    })

def menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, restaurant_id=restaurant_id)
    search_query = request.GET.get('q', '')

    if search_query:
        food_items = FoodItem.objects.filter(
            Q(restaurant=restaurant) &
            (Q(name__icontains=search_query) | Q(description__icontains=search_query))
        ).order_by('name')
    else:
        food_items = FoodItem.objects.filter(restaurant=restaurant).order_by('name')

    username = None
    if 'customer_id' in request.session:
        username = get_username_by_id(request.session['customer_id'])

    return render(request, 'menu.html', {
        'restaurant': restaurant,
        'food_items': food_items,
        'username': username,
        'search_query': search_query
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

    paginator = Paginator(all_restaurants, 9)
    page = request.GET.get('page', 1)

    try:
        restaurants_page = paginator.page(page)
    except PageNotAnInteger:
        restaurants_page = paginator.page(1)
    except EmptyPage:
        restaurants_page = paginator.page(paginator.num_pages)

    username = get_username_by_id(request.session['customer_id'])

    return render(request, 'home_logged_in.html', {
        'featured_restaurants': featured_restaurants,
        'restaurants_page': restaurants_page,
        'username': username
    })

def cart(request):
    if 'customer_id' not in request.session:
        return redirect('signin')

    customer_id = request.session['customer_id']
    customer = get_object_or_404(Customer, user_id=customer_id)
    cart_items = Cart.objects.filter(customer=customer).select_related('food__restaurant').order_by('-cart_id')
    total = sum(item.food.price * item.quantity for item in cart_items)
    total_items = sum(item.quantity for item in cart_items)
    delivery_addresses = DeliveryAddress.objects.filter(customer=customer)
    username = get_username_by_id(customer_id)

    return render(request, 'cart.html', {
        'username': username,
        'customer': customer,
        'cart_items': cart_items,
        'total': total,
        'delivery_addresses': delivery_addresses,
        'total_items': total_items
    })

def add_to_cart(request, food_id):
    if 'customer_id' not in request.session:
        return redirect('signin')

    customer = get_object_or_404(Customer, user_id=request.session['customer_id'])
    food = get_object_or_404(FoodItem, food_id=food_id)
    quantity = int(request.POST.get('quantity', 1))

    cart_item, created = Cart.objects.get_or_create(customer=customer, food=food, defaults={'quantity': quantity})
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    messages.success(request, f"{food.name} added to cart successfully!")
    return redirect(request.META.get('HTTP_REFERER', 'cart'))

@csrf_exempt
def place_order(request):
    if 'customer_id' not in request.session:
        messages.error(request, 'User not logged in')
        return redirect('signin')  # Redirect to sign-in page if user is not logged in

    if request.method == 'POST':
        try:
            # ✅ Convert selected item IDs from string to integer
            selected_item_ids = list(map(int, request.POST.getlist('selected_items')))
            customer_id = request.session['customer_id']

            with transaction.atomic():
                # ✅ Fetch the customer
                customer = Customer.objects.get(user_id=customer_id)

                # ✅ Filter cart items based on selected food IDs and customer
                cart_items = Cart.objects.filter(customer=customer, food__food_id__in=selected_item_ids)

                if not cart_items.exists():
                    messages.error(request, 'No valid items in cart.')
                    return redirect('cart')  # Redirect back to the cart page if no valid items

                # ✅ Calculate total price
                total = sum(item.food.price * item.quantity for item in cart_items)

                # ✅ Create order
                order = Order.objects.create(
                    customer=customer,
                    total_price=total,
                    status="Placed",
                )

                # ✅ Create OrderItems
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        food=item.food,
                        quantity=item.quantity,
                    )

                # ✅ Clear ordered items from the cart
                cart_items.delete()

                messages.success(request, 'Order placed successfully!')
                return redirect('order_confirmation', order_id=order.order_id)

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('cart')  # Redirect back to the cart page if an error occurs

    # ❌ If not POST
    messages.error(request, 'Invalid request method')
    return redirect('cart')

@csrf_exempt
def delete_cart_items(request):
    if request.method == 'POST':
        item_ids_str = request.POST.get('item_ids')
        if not item_ids_str:
            return JsonResponse({'status': 'error', 'message': 'No items provided.'})

        try:
            item_ids = json.loads(item_ids_str)
            if not item_ids:
                return JsonResponse({'status': 'error', 'message': 'No valid items in cart.'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'})

        Cart.objects.filter(food__food_id__in=item_ids).delete()
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

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
    order.status = 'Confirmed'
    order.save()
    messages.success(request, 'Order confirmed successfully!')
    return redirect('order_confirmation', order_id=order.order_id)

def remove_from_cart(request, food_id):
    if 'customer_id' not in request.session:
        return redirect('signin')

    customer = get_object_or_404(Customer, user_id=request.session['customer_id'])
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

    # Fetch order history and paginate
    orders_list = Order.objects.filter(customer=customer).order_by('-timestamp')
    paginator = Paginator(orders_list, 1)  # Show 1 order per page
    page = request.GET.get('page', 1)

    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)

    # Fetch other necessary data
    payment_methods = PaymentMethod.objects.filter(customer=customer)
    delivery_addresses = DeliveryAddress.objects.filter(customer=customer)
    preferences = Preferences.objects.filter(customer=customer).first()

    return render(request, 'profile.html', {
        'customer': customer,
        'username': customer.username,
        'orders': orders,
        'payment_methods': payment_methods,
        'delivery_addresses': delivery_addresses,
        'preferences': preferences,
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

@login_required
def profile_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'profile.html', {'customer': request.user, 'orders': orders})

def logout(request):
    if 'customer_id' in request.session:
        del request.session['customer_id']
    return redirect('home')