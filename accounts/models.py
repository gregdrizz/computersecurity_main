from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Customer(models.Model):
    name = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    creator_id = models.IntegerField(null=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name


class FailedLoginAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='failed_login_attempts')
    time = models.DateTimeField(default=timezone.now)

    @classmethod
    def create_record(cls, user: User):
        new_record = cls(user=user)
        new_record.save()
        return new_record

    def __str__(self):
        return self.user.username + ' - ' + self.time.isoformat()


class Plan(models.Model):
    TYPE = (
        ('Annual', 'Annual'),
        ('Monthly', 'Monthly'),
    )
    name = models.CharField(max_length=200, null=True)
    price = models.FloatField(null=True)
    type = models.CharField(max_length=200, null=True, choices=TYPE)
    description = models.CharField(max_length=200, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS = (
        ('Pending', 'Pending'),
        ('Setting Up', 'Setting Up'),
        ('Connected', 'Connected')
    )

    customer = models.ForeignKey(Customer, null=True, on_delete= models.SET_NULL)
    plan = models.ForeignKey(Plan, null=True, on_delete= models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    status = models.CharField(max_length=200, null=True, choices=STATUS)
    note = models.CharField(max_length=1000, null=True)
    
    def __str__(self):
        return '{} ordered by {}'.format(self.plan.name, self.customer.name)