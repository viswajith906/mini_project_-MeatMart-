from django.db import models
from django.conf import settings
from django.utils import timezone

class User(models.Model):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('shop', 'Shop Owner'),
    )
    
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)   # << ADD THIS
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"

class Shop(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shop_image = models.ImageField(upload_to='shop_images/', blank=True, null=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    shop_image = models.ImageField(upload_to='shops/', null=True, blank=True)
    location = models.CharField(max_length=100)
   
    phone_number = models.CharField(max_length=15)
    payment_phone_number = models.CharField(
    "Online Payment Phone",
    max_length=20,
    blank=True,
    default=""
)

    product_image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    product_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
class Order(models.Model):
    STATUS_CHOICES = (
        ('placed', 'Placed'),
        ('cancelled', 'Cancelled'),
         ('delivered', 'Delivered'),   # <- add this
    )

    shop = models.ForeignKey('Shop', on_delete=models.CASCADE)
    customer = models.ForeignKey('User', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='placed')
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)   # <- add this
    notified_to_shop = models.BooleanField(default=False)
    is_seen = models.BooleanField(default=False)



    def __str__(self):
        return f"Order #{self.id} - {self.shop.name} - {self.customer.username} ({self.quantity} Kg)"

class Feedback(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE)
    customer = models.ForeignKey('User', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(1,6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for Order {self.order.id} - {self.rating}★"

class Delivery(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    delivery_address = models.TextField()
    delivery_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('out_for_delivery', 'Out for Delivery'),
            ('delivered', 'Delivered'),
        ],
        default='pending'
    )
    delivery_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Delivery for Order {self.order.id} - {self.delivery_status}"

