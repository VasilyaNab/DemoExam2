from django.db import models

class User(models.Model):
    role = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100)
    login = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"{self.surname} {self.name} {self.patronymic}"


class Category(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name


class Product(models.Model):
    article = models.CharField(max_length=10)
    name = models.CharField(max_length=50)
    price = models.IntegerField()
    supplier = models.CharField(max_length=50)
    seller = models.CharField( max_length=30)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True,null=True)
    discount = models.IntegerField()
    count = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to="./Images", blank=True, null=True)
    def __str__(self) -> str:
        return self.article

class OrderLocation(models.Model):
    location = models.TextField()

class OrderDetails(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey("Order", on_delete=models.CASCADE)
    count = models.IntegerField(default=1)

class Order(models.Model):
    orders = models.ManyToManyField(Product, through=OrderDetails)
    date = models.DateField()
    date_delivery =  models.DateField()
    location = models.ForeignKey(OrderLocation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.IntegerField()
    status = models.CharField(max_length=50)