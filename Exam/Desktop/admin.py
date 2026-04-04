from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(OrderLocation)
admin.site.register(OrderDetails)
admin.site.register(Order)