from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Shop, Order, Feedback
from .forms import UserRegistrationForm, ShopRegistrationForm, LoginForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .forms import FeedbackForm
# near other imports at top of views.py
from django.db.models import F, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from django.db.models import Q



def home(request):
    return render(request, 'mart/home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])
            user.phone_number = form.cleaned_data.get('phone_number', '') or ''
            user.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'mart/register.html', {'form': form})

def customer_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            try:
                user = User.objects.get(username=username)
                if check_password(password, user.password) and user.role == 'customer':
                    request.session['user_id'] = user.id
                    request.session['user_role'] = user.role
                    messages.success(request, 'Logged in successfully as customer!')
                    return redirect('customer_dashboard')
                else:
                    messages.error(request, 'Invalid credentials or not a customer account')
            except User.DoesNotExist:
                messages.error(request, 'User does not exist')
    else:
        form = LoginForm()
    
    return render(request, 'mart/customer_login.html', {'form': form})

def shop_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            try:
                user = User.objects.get(username=username)
                if check_password(password, user.password) and user.role == 'shop':
                    request.session['user_id'] = user.id
                    request.session['user_role'] = user.role
                    messages.success(request, 'Logged in successfully as shop owner!')
                    return redirect('shop_dashboard')
                else:
                    messages.error(request, 'Invalid credentials or not a shop account')
            except User.DoesNotExist:
                messages.error(request, 'User does not exist')
    else:
        form = LoginForm()
    
    return render(request, 'mart/shop_login.html', {'form': form})

def customer_dashboard(request):
    if 'user_id' not in request.session or request.session.get('user_role') != 'customer':
        messages.error(request, 'Please login as customer first')
        return redirect('customer_login')
    
    user = get_object_or_404(User, id=request.session['user_id'])
    
      # Read GET param 'location' (from the navbar search)
    loc = request.GET.get('location', '').strip()

    if loc:
        # filter by location or address (case-insensitive partial match)
        shops = Shop.objects.filter(
            Q(location__icontains=loc) | Q(address__icontains=loc)
        ).distinct()
    else:
        shops = Shop.objects.all()
    
    return render(request, 'mart/customer_dashboard.html', {
        'user': user,
        'shops': shops
    })


def shop_dashboard(request):
    if 'user_id' not in request.session or request.session.get('user_role') != 'shop':
        messages.error(request, 'Please login as shop owner first')
        return redirect('shop_login')
    
    user = get_object_or_404(User, id=request.session['user_id'])
    
    # Check if shop profile exists
    try:
        shop = Shop.objects.get(user=user)
        form = ShopRegistrationForm(instance=shop)
    except Shop.DoesNotExist:
        shop = None
        form = ShopRegistrationForm()
    
    if request.method == 'POST':
        form = ShopRegistrationForm(request.POST, request.FILES, instance=shop)
        if form.is_valid():
            shop = form.save(commit=False)
            shop.user = user
            shop.save()
            messages.success(request, 'Shop profile updated successfully!')
            return redirect('shop_dashboard')
    
    return render(request, 'mart/shop_dashboard.html', {
        'user': user,
        'form': form,
        'shop': shop
    })

def logout(request):
    auth_logout(request)
    if 'user_id' in request.session:
        del request.session['user_id']
    if 'user_role' in request.session:
        del request.session['user_role']
    messages.success(request, 'Logged out successfully!')
    return redirect('home')


def register_shop(request):
    if request.method == 'POST':
        form = ShopRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            shop = form.save(commit=False)
            shop.user = request.user  # link shop to the logged-in user
            shop.save()
            return redirect('shop_dashboard')  # redirect after success
    else:
        form = ShopRegistrationForm()
    
    return render(request, 'mart/shop_dashboard.html', {'form': form})

def shop_detail(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)

    # fetch feedbacks for this shop (most recent first)
    feedbacks = Feedback.objects.filter(shop=shop).select_related('customer', 'order').order_by('-created_at')

    # compute average rating (None if no feedback)
    avg_rating = feedbacks.aggregate(avg=Avg('rating'))['avg']

    # number of feedbacks
    feedback_count = feedbacks.count()

    return render(request, 'mart/shop_detail.html', {
        'shop': shop,
        'feedbacks': feedbacks,
        'avg_rating': avg_rating,
        'feedback_count': feedback_count,
    })



def place_order(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)

    if request.method == 'POST':
        # ensure customer is logged in
        if 'user_id' not in request.session or request.session.get('user_role') != 'customer':
            messages.error(request, 'Please login as customer to place an order.')
            return redirect('customer_login')

        try:
            quantity = int(request.POST.get('quantity', 0))
        except (TypeError, ValueError):
            messages.error(request, 'Invalid quantity.')
            return redirect(reverse('shop_detail', args=[shop.id]))

        if quantity <= 0:
            messages.error(request, 'Please select a valid quantity.')
            return redirect(reverse('shop_detail', args=[shop.id]))

        # Use transaction + F expressions to avoid race conditions
        with transaction.atomic():
            # lock the shop row
            shop = Shop.objects.select_for_update().get(id=shop_id)
            if shop.quantity < quantity:
                messages.error(request, 'Not enough stock available.')
                return redirect(reverse('shop_detail', args=[shop.id]))

            # subtract quantity atomically
            Shop.objects.filter(id=shop.id).update(quantity=F('quantity') - quantity)
            shop.refresh_from_db()

            total_price = (Decimal(quantity) * Decimal(str(shop.rate))).quantize(Decimal('0.01'))

            # create order record
            customer = get_object_or_404(User, id=request.session['user_id'])
            order = Order.objects.create(
                shop=shop,
                customer=customer,
                quantity=quantity,
                total_price=total_price,
                status='placed',
            )

        messages.success(request, f'Order placed successfully! Total = ₹{total_price}')
        return HttpResponseRedirect(reverse('shop_detail', args=[shop.id]) + f'?order_id={order.id}')

    return redirect('shop_detail', shop_id=shop.id)

def cancel_order(request, order_id):
    # check logged in
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to cancel orders.')
        return redirect('customer_login')

    order = get_object_or_404(Order, id=order_id)

    # only the customer who placed the order can cancel it
    if order.customer.id != request.session['user_id']:
        messages.error(request, 'You do not have permission to cancel this order.')
        return redirect('orders')

    if order.status != 'placed':
        messages.info(request, 'This order is already cancelled or cannot be cancelled.')
        return redirect('orders')

    with transaction.atomic():
        # restore shop quantity
        Shop.objects.filter(id=order.shop.id).update(quantity=F('quantity') + order.quantity)
        # mark order cancelled
        order.status = 'cancelled'
        order.cancelled_at = timezone.now()
        order.save()

    messages.success(request, f'Order #{order.id} cancelled and {order.quantity} Kg returned to stock.')
    return redirect('orders')

def cancel_order(request, order_id):
    # check logged in
    if 'user_id' not in request.session:
        messages.error(request, 'Please login to cancel orders.')
        return redirect('customer_login')

    order = get_object_or_404(Order, id=order_id)

    # only the customer who placed the order can cancel it
    if order.customer.id != request.session['user_id']:
        messages.error(request, 'You do not have permission to cancel this order.')
        return redirect('orders')

    if order.status != 'placed':
        messages.info(request, 'This order is already cancelled or cannot be cancelled.')
        return redirect('orders')

    with transaction.atomic():
        # restore shop quantity
        Shop.objects.filter(id=order.shop.id).update(quantity=F('quantity') + order.quantity)
        # mark order cancelled
        order.status = 'cancelled'
        order.cancelled_at = timezone.now()
        order.save()

    messages.success(request, f'Order #{order.id} cancelled and {order.quantity} Kg returned to stock.')
    return redirect('orders')



def orders(request):
    if 'user_id' not in request.session:
        messages.error(request, "Please login first to view orders")
        return redirect('customer_login')
    
    customer_id = request.session['user_id']
    user_orders = Order.objects.filter(customer_id=customer_id).select_related('shop').order_by('-created_at')

    return render(request, 'mart/orders.html', {'orders': user_orders})

def delivery(request):
    # only customers can see this page
    if 'user_id' not in request.session or request.session.get('user_role') != 'customer':
        messages.error(request, 'Please login as customer first')
        return redirect('customer_login')

    customer = get_object_or_404(User, id=request.session['user_id'])
    # fetch this customer's orders (most recent first)
    orders = Order.objects.filter(customer=customer).select_related('shop').order_by('-created_at')

    # build list of (order, feedback, feedback_form)
    order_items = []
    for o in orders:
        fb = None
        try:
            fb = o.feedback  # uses OneToOne reverse accessor if Feedback.order is OneToOne
        except Feedback.DoesNotExist:
            fb = None
        feedback_form = FeedbackForm() if (o.status == 'delivered' and fb is None) else None
        order_items.append({'order': o, 'feedback': fb, 'feedback_form': feedback_form})

    return render(request, 'mart/delivery.html', {'order_items': order_items})
def deliver_order(request, order_id):
    if request.method != 'POST':
        return redirect('delivery')

    if 'user_id' not in request.session:
        messages.error(request, 'Please login to confirm delivery.')
        return redirect('customer_login')

    order = get_object_or_404(Order, id=order_id)
    # only the customer who placed the order can confirm delivery
    if order.customer.id != request.session['user_id']:
        messages.error(request, 'Permission denied.')
        return redirect('delivery')

    if order.status != 'placed':
        messages.info(request, 'Order cannot be marked delivered.')
        return redirect('delivery')

    order.status = 'delivered'
    order.delivered_at = timezone.now()
    order.save()

    messages.success(request, f'Order #{order.id} marked as delivered. Thank you!')
    return redirect('delivery')
def submit_feedback(request, order_id):
    if request.method != 'POST':
        return redirect('delivery')

    if 'user_id' not in request.session:
        messages.error(request, 'Please login to submit feedback.')
        return redirect('customer_login')

    order = get_object_or_404(Order, id=order_id)
    if order.customer.id != request.session['user_id']:
        messages.error(request, 'Permission denied.')
        return redirect('delivery')

    if order.status != 'delivered':
        messages.error(request, 'You can only give feedback after the order is delivered.')
        return redirect('delivery')

    # if feedback exists, don't allow duplicate
    if hasattr(order, 'feedback'):
        messages.info(request, 'Feedback already submitted.')
        return redirect('delivery')

    form = FeedbackForm(request.POST)
    if form.is_valid():
        fb = form.save(commit=False)
        fb.order = order
        fb.shop = order.shop
        fb.customer = order.customer
        fb.save()
        messages.success(request, 'Thanks for your feedback!')
    else:
        messages.error(request, 'Please correct the feedback form errors.')

    return redirect('delivery')

def shop_delivery(request):
    # ensure logged-in shop owner
    if 'user_id' not in request.session or request.session.get('user_role') != 'shop':
        messages.error(request, 'Please login as shop owner first')
        return redirect('shop_login')

    shop_owner = get_object_or_404(User, id=request.session['user_id'])
    shop = get_object_or_404(Shop, user=shop_owner)
        # mark all unseen orders as seen when shop opens the delivery page
    Order.objects.filter(shop=shop, is_seen=False).update(is_seen=True)

    # get orders for this shop, newest first
    orders = Order.objects.filter(shop=shop).select_related('customer').order_by('-created_at')

    return render(request, 'mart/shop_delivery.html', {
        'shop': shop,
        'orders': orders
    })

def shop_feedbacks(request):
    # only shop owners can access
    if 'user_id' not in request.session or request.session.get('user_role') != 'shop':
        messages.error(request, 'Please login as shop owner first')
        return redirect('shop_login')

    shop_owner = get_object_or_404(User, id=request.session['user_id'])
    shop = get_object_or_404(Shop, user=shop_owner)

    feedbacks = Feedback.objects.filter(shop=shop).select_related('customer', 'order').order_by('-created_at')
    avg_rating = feedbacks.aggregate(avg=Avg('rating'))['avg']

    return render(request, 'mart/shop_feedbacks.html', {
        'shop': shop,
        'feedbacks': feedbacks,
        'avg_rating': avg_rating,
    })


def shop_notifications(request):
    # ensure logged-in shop owner
    if 'user_id' not in request.session or request.session.get('user_role') != 'shop':
        messages.error(request, 'Please login as shop owner first')
        return redirect('shop_login')

    shop_owner = get_object_or_404(User, id=request.session['user_id'])
    shop = get_object_or_404(Shop, user=shop_owner)

    # Mark all unseen orders for this shop as seen (so badge clears)
    Order.objects.filter(shop=shop, is_seen=False).update(is_seen=True)

    orders = Order.objects.filter(shop=shop).select_related('customer').order_by('-created_at')

    return render(request, 'mart/shop_notifications.html', {
        'shop': shop,
        'orders': orders
    })


def shop_mark_delivered(request, order_id):
    # Only allow POST from the shop page
    if request.method != 'POST':
        return redirect('shop_delivery')

    if 'user_id' not in request.session or request.session.get('user_role') != 'shop':
        messages.error(request, 'Please login as shop owner first')
        return redirect('shop_login')

    shop_owner = get_object_or_404(User, id=request.session['user_id'])
    shop = get_object_or_404(Shop, user=shop_owner)
    order = get_object_or_404(Order, id=order_id, shop=shop)

    if order.status == 'delivered':
        messages.info(request, 'Order already marked as delivered.')
        return redirect('shop_delivery')

    with transaction.atomic():
        order.status = 'delivered'
        order.delivered_at = timezone.now()
        order.save()

    messages.success(request, f'Order #{order.id} marked as delivered.')
    return redirect('shop_delivery')


@require_GET
def api_shop_unread_orders(request):
    if 'user_id' not in request.session or request.session.get('user_role') != 'shop':
        return JsonResponse({'error': 'login required as shop'}, status=403)

    shop_owner = get_object_or_404(User, id=request.session['user_id'])
    shop = get_object_or_404(Shop, user=shop_owner)

    # fetch first 10 unread orders
    unread_qs = Order.objects.filter(shop=shop, is_seen=False).order_by('-created_at')[:10]

    orders_data = [
        {
            'id': o.id,
            'customer': o.customer.username,
            'phone': o.customer.phone_number or '',
            'quantity': o.quantity,
            'total_price': str(o.total_price),
            'created_at': o.created_at.isoformat(),
        }
        for o in unread_qs
    ]

    # ✅ Fix: update using a separate query on their IDs
    ids = [o.id for o in unread_qs]
    if ids:
        Order.objects.filter(id__in=ids).update(notified_to_shop=True)

    return JsonResponse({'unread_count': len(orders_data), 'orders': orders_data})



def mark_orders_seen(request):
    # only allow shop users
    if request.session.get('user_role') != 'shop':
        return JsonResponse({'status': 'forbidden'}, status=403)

    shop_owner = get_object_or_404(User, id=request.session['user_id'])
    shop = get_object_or_404(Shop, user=shop_owner)

    Order.objects.filter(shop=shop, is_seen=False).update(is_seen=True)

    return JsonResponse({'status': 'ok'})


