from datetime import timedelta

from django.utils import timezone
from django.conf import settings
from django.shortcuts import render, redirect
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import login_required

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash

from django.contrib import messages
from django_password_history.models import UserPasswordHistory

from accounts.DummyCustomer import DummyCustomer

from .models import *
from .forms import *
from .filters import OrderFilter
from .AppUtils import *

#################################
from django.db import connection
import mysql.connector
from django.utils.crypto import pbkdf2

# Change this in order to protect / enrisk the website
secured = False

#################################

# Create your views here.
def registerPage(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = CreateUserForm()

    if request.method == 'POST':
        form = CreateUserForm(request.POST)

        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('username')
            messages.success(request, f'Account was created for {user}')
            current_user = User.objects.filter(username=user).last()
            user_history = UserPasswordHistory(user=current_user)
            user_history.save()
            user_history.store_password()

            return redirect('login')

    context = {'form': form}
    return render(request, 'accounts/register.html', context)

def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')

        if secured==False:
            if username != None and password != None:
                #TODO: change credentials of db here to presentation's db
                conn = mysql.connector.connect(host = "127.0.0.1", user="root", password = "1234", database = "communication")
                cursor = conn.cursor()
                # with connection.cursor() as cursor:

                """
                Scenario in order to exploit this:
                1. Hacker creates a new user directly in the db (malicious username input: " or "1" = "1"; INSERT INTO auth_user values("sha1$1$<selected salt>$<hash match to password and selected salt>" <last_login>, <is_superuser>, <username>, <last_name>, <email>, <is_staff>, <is_active>, <date_joined>, "hacker");#
                   In that situation he knows the salt, because he creates it on its own.
                2. The hacker then connects to the system with his fake user.
                """

                query = f"SELECT password FROM auth_user WHERE username=\"{username}\""

                row = None

                first = True

                for result in cursor.execute(query, multi=True):
                    if result.with_rows:
                        print("Rows produced by statement '{}':".format(result.statement))
                        fetched = result.fetchall()
                        print(fetched)

                        if first:
                            row = fetched[0]
                            first = False
                    else:
                        print("Number of rows affected by statement '{}': {}".format(result.statement, result.rowcount))

                # row = [result.fetchone() for result in cursor.execute(query, multi=True)]
                # cursor.execute(query, multi=True)
                # row = cursor.fetchone()[0]
                row = row[0]
                passwordDbParts    = row.split("$", maxsplit = 3)
                encryptionType     = passwordDbParts[0]
                numberOfIterations = passwordDbParts[1]
                salt               = passwordDbParts[2]
                expectedHash       = passwordDbParts[3]
                encryptionType = eval("hashlib." + encryptionType.replace("pbkdf2_", ""))
                hash = pbkdf2(password, salt, int(numberOfIterations), digest=encryptionType)
                hash = base64.b64encode(hash).decode('ascii').strip()
                if (hash == expectedHash):
                    user = authenticate(request, username = username, password = password)
                    login(request, user)
                    return redirect('home')
        else:
            if request.method == 'POST':
                # Lock users:
                failed_attempts_count = None
                if User.objects.filter(username=username).exists():
                    user = User.objects.filter(username=username).last()
                    min_lock_time = timezone.now() - timedelta(seconds=settings.LOGIN_FAILURE_COUNTING_DURATION)
                    failed_attempts_count = user.failed_login_attempts.filter(time__gte=min_lock_time).count()
                    if failed_attempts_count > settings.LOGIN_MAX_RETRIES:
                        messages.error(request, 'This user is locked due to 3 failed login attempts.')
                        return render(request, 'accounts/login.html', {})
        
                user = authenticate(request, username=username, password=password)
        
                if user is not None:
                    login(request, user)
                    return redirect('home')
                else:
                    if User.objects.filter(username=username).exists():
                        user = User.objects.filter(username=username).last()
                        FailedLoginAttempt.create_record(user)
                        if failed_attempts_count:
                            messages.error(request, f'Wrong Password ({failed_attempts_count}/{settings.LOGIN_MAX_RETRIES})')
                        else:
                            messages.error(request, 'Wrong Password')
                    else:
                        messages.error(request, "User doesn't exist")

        context = {}
        return render(request, 'accounts/login.html', context)

@login_required(login_url='login')
def change_password_page(request):
    current_user = request.user
    if not current_user.is_authenticated:
        return redirect('login')
    form = ChangePasswordForm()

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get('password1')
            user_history = UserPasswordHistory.objects.filter(user=current_user).last()
            if user_history:
                if user_history.password_is_used(password):
                    form = ChangePasswordForm()
                    context = {
                        'form': form,
                        'username': current_user.username,
                        'errors': 'You have used this password at the past.'
                    }
                    return render(request, 'accounts/change_password.html', context)
            else:
                user_history = UserPasswordHistory(user=current_user)
                user_history.save()

            current_user.set_password(password)
            user_history.store_password()
            current_user.save()
            update_session_auth_hash(request, current_user)
            messages.success(request, f'Password changed for {current_user.username}')
            return redirect('home')

    context = {'form': form, 'username': current_user.username}
    return render(request, 'accounts/change_password.html', context)


def logoutUser(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def home(request):
    orders = Order.objects.all()
    customers = None
    patternToSearch = request.POST.get("search-bar")

    if patternToSearch == None:
        customers = Customer.objects.filter(creator_id = request.user.id)
    else:
        current_user = request.user

        if secured == False: 
            if patternToSearch != None:
                # To exploit this input field, enter "%'#" in the search bar (without the quotes)
                sql = f"SELECT * FROM accounts_customer WHERE name LIKE '%{patternToSearch}%' AND creator_id = {current_user.id};"

            try:
                #TODO: change credentials of db here to presentation's db
                conn = mysql.connector.connect(host = "127.0.0.1", user="root", password = "1234", database = "communication")
                cursor = conn.cursor()
                customers = []

                # Allows multi query, this way we can use UNION in our SQL Injection
                iterable = cursor.execute(sql, multi=True)
                iterable = cursor.fetchall()
                for result in iterable:
                    # currentResult = result.fetchall()
                    currentResult = result

                    # currentCustomer = Customer()
                    currentCustomer = DummyCustomer()

                    currentCustomer.id    = currentResult[0]
                    currentCustomer.name  = currentResult[1]
                    currentCustomer.phone = currentResult[2]
                    currentCustomer.email = currentResult[3]
                    currentCustomer.date_created = currentResult[4]
                    currentCustomer.creator_id = currentResult[5]

                    customers.append(currentCustomer)

            except Exception as e:
                print(e)
        
        # NOTE: This solution already handles the trying of sqli with parameters
        else:
            customers = Customer.objects.filter(creator_id = current_user.id)
            customers = [customer for customer in customers if patternToSearch in customer.name]

    total_customers = len(customers)
    total_orders = orders.count()
    connected = orders.filter(status='Connected').count()
    pending = orders.filter(status='Pending').count()

    context = {'orders': orders, 'customers': customers, 
    'total_customers': total_customers, 'total_orders': total_orders,
    'connected': connected, 'pending': pending, "secured" : secured }

    return render(request, 'accounts/dashboard.html', context)

@login_required(login_url='login')
def networkplans(request):
    plans = Plan.objects.all()
    return render(request, 'accounts/networkplans.html', {'plans': plans})

def customer(request, pk):
    secured = True

    if secured==False:
        # what happens if pk will be equas to  ---> ' or '1'='1 <--- ???????
        # CLUE: customer = Customer.objects.raw("SELECT * FROM USERS WHERE id='' or '1'='1'")
        # Further explanation: https://docs.djangoproject.com/en/4.0/topics/db/sql/#passing-parameters-into-raw
        customer = Customer.objects.raw("SELECT * FROM USERS WHERE id='" + pk + "'")
    else:
        customer = Customer.objects.get(id=pk)
    orders = customer.order_set.all()
    orders_count = orders.count()

    myFilter = OrderFilter(request.GET, queryset=orders)
    orders = myFilter.qs

    context = {'customer': customer, 'orders': orders, 'orders_count':orders_count, 'myFilter': myFilter}
    return render(request, 'accounts/customer.html', context)

@login_required(login_url='login')
def createOrder(request, pk):
    OrderFormSet = inlineformset_factory(Customer, Order, fields=('plan', 'status'), extra=3, can_delete=False)
    customer = Customer.objects.get(id=pk)
    formset = OrderFormSet(queryset=Order.objects.none(), instance=customer)
    if request.method == 'POST':
        #print('Printing POST', request.POST)
        #form = OrderForm(request.POST)
        formset = OrderFormSet(request.POST, instance=customer)
        if formset.is_valid():
            formset.save()
            return redirect('/')

    context = {'formset': formset}
    return render(request, 'accounts/order_form.html', context)

@login_required(login_url='login')
def updateOrder(request, pk):
    form = OrderForm()

    order = Order.objects.get(id=pk)
    form = OrderForm(instance=order)
    if request.method == 'POST':
        #print('Printing POST', request.POST)
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('/')

    context = {'form': form}
    return render(request, 'accounts/update_order.html', context)


@login_required(login_url='login')
def create_customer(request):
    form = CreateCustomerForm()

    if request.method == 'POST':
        form = CreateCustomerForm(request.POST)
        if form.is_valid():
            userId = request.user.id
            customerName = form.cleaned_data["name"]
            print(customerName)
            form.save()

            customersToSet = Customer.objects.get(name=customerName)
            customersToSet.creator_id = userId
            customersToSet.save()

            return redirect('/')

    context = {'form': form}
    return render(request, 'accounts/create_customer.html', context)

@login_required(login_url='login')
def deleteOrder(request, pk):
    order = Order.objects.get(id=pk)
    if request.method == "POST":
        order.delete()
        return redirect('/')

    context = {'item': order}


    return render(request,'accounts/delete.html', context)

@login_required(login_url='login')
def deleteCustomer(request, pk):
    customer = Customer.objects.get(id=pk)
    if request.method == "POST":
        Order.objects.filter(customer=customer).delete()
        customer.delete()
        return redirect('/')

    context = {'item': customer}


    return render(request,'accounts/delete_customer.html', context)