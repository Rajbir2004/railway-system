from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.models import User
from .models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
import datetime
import random

def nav(request):
    return render(request, 'carousel.html')

def About(request):
    return render(request, 'about.html')

def Contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        try:
            send_mail(
                f'New Contact Message from {name}',
                f'You have received a new message from your website contact form:\n\n'
                f'Name: {name}\n'
                f'Email: {email}\n\n'
                f'Message:\n{message}',
                settings.DEFAULT_FROM_EMAIL,
                ['rajbir6484@gmail.com'],
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent successfully!')
        except Exception as e:
            messages.error(request, 'Failed to send message. Please try again later.')
            print("Contact form error:", e)
            
    return render(request, 'contact.html')

def Login_customer(request):
    error = False
    error2 = False
    error3 = False
    if request.method == "POST":
        n = request.POST.get('uname')
        p = request.POST.get('pwd')
        user = authenticate(username=n, password=p)
        if user:
            login(request, user)
            if user.is_staff:
                error2 = True
            else:
                error = True
        else:
            error3 = True

    d = {'error': error, 'error2': error2, 'error3': error3}
    return render(request, 'login_customer.html', d)

def Register_customer(request):
    error = False
    if request.method == "POST":
        n = request.POST.get('uname')
        f = request.POST.get('fname')
        l = request.POST.get('lname')
        e = request.POST.get('email')
        a = request.POST.get('add')
        m = request.POST.get('mobile')
        g = request.POST.get('male')
        d_birth = request.POST.get('birth')
        p = request.POST.get('pwd')
        
        if User.objects.filter(username=n).exists():
            error = "Username already exists. Please choose a different one."
            return render(request, 'register_customer.html', {'error': error})
            
        # Store user data in session instead of saving to database immediately
        request.session['registration_data'] = {
            'uname': n,
            'fname': f,
            'lname': l,
            'email': e,
            'add': a,
            'mobile': m,
            'male': g,
            'birth': d_birth,
            'pwd': p
        }
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        request.session['registration_otp'] = otp
        
        # Send Email with timeout protection
        try:
            send_mail(
                'Your Railway Booking System OTP',
                f'Hello {f},\n\nYour OTP for registration is: {otp}\n\nWelcome aboard!',
                settings.DEFAULT_FROM_EMAIL,
                [e],
                fail_silently=True, # Prevent hanging if SMTP is slow
            )
        except Exception as ex:
            print("Failed to send OTP email:", ex)
            # We still proceed to verify_otp because the session has the data
            
        return redirect('verify_otp')
        
    d = {'error': error}
    return render(request, 'register_customer.html', d)

def Verify_OTP(request):
    error = False
    if 'registration_data' not in request.session:
        return redirect('register_customer')
        
    if request.method == "POST":
        entered_otp = request.POST.get('otp')
        real_otp = request.session.get('registration_otp')
        
        if entered_otp == real_otp:
            # OTP is correct, now we create the user
            data = request.session.get('registration_data')
            
            # Create the active user
            user = User.objects.create_user(
                first_name=data['fname'], 
                last_name=data['lname'], 
                username=data['uname'], 
                password=data['pwd'], 
                email=data['email']
            )
            # user.is_active is True by default
            
            # Create profile
            Register.objects.create(
                user=user, 
                add=data['add'], 
                mobile=data['mobile'], 
                gender=data['male'], 
                dob=data['birth']
            )
            
            # Clean up session
            del request.session['registration_otp']
            del request.session['registration_data']
            
            # Log them in automatically
            login(request, user)
            return redirect('dashboard')
        else:
            error = True
            
    return render(request, 'verify_otp.html', {'error': error})

@login_required(login_url='login_customer')
def Search_Train(request):
    data = Add_route.objects.values('route').distinct()
    error = False
    route1 = []
    route = ""
    fare3 = 0
    coun = 1
    if request.method == "POST":
        f = request.POST.get("fcity")
        t = request.POST.get("tcity")
        da = request.POST.get("date")
        data1 = Add_route.objects.filter(route=f)
        data2 = Add_route.objects.filter(route=t)
        
        for i in data1:
            for j in data2:
                if i.train.train_no == j.train.train_no:
                    route1.append(Add_Train.objects.filter(train_no=i.train.train_no))
        
        fare1 = data1.first().fare if data1.exists() else 0
        fare2 = data2.first().fare if data2.exists() else 0
        fare3 = abs(fare2 - fare1)
        if 0 < fare3 < 5:
            fare3 = 5
            
        route = f + " to " + t
        request.session['search_date'] = da
        request.session['search_fare'] = fare3
        request.session['search_route'] = route
        error = True

    d = {"data2": data, 'route1': route1, 'fare3': fare3, "error": error, 'coun': coun, 'route': route}
    return render(request, 'search_train.html', d)

@login_required(login_url='login_customer')
def Dashboard(request):
    return render(request, 'dashboard.html')

def Logout(request):
    logout(request)
    return redirect('nav')

@login_required(login_url='login_customer')
def Book_detail(request, coun, pid, route1):
    data2 = Add_Train.objects.get(id=pid)
    user1 = Register.objects.get(user=request.user)
    pro = Passenger.objects.filter(user=user1)
    book = Book_ticket.objects.filter(user=user1)
    
    total = sum([i.fare for i in pro if i.status != "set" and i.fare])
    
    search_date = request.session.get('search_date', str(datetime.date.today()))
    search_fare = request.session.get('search_fare', 0)
    
    error = False
    housefull = False
    
    if request.method == "POST":
        if data2.seats > 0:
            f = request.POST.get("name")
            t = request.POST.get("age")
            da = request.POST.get("gender")
            
            # Decrement seats
            data2.seats -= 1
            data2.save()
            
            passenger = Passenger.objects.create(user=user1, train=data2, route=route1, name=f, gender=da, age=t, fare=search_fare, date1=search_date)
            
            # FIX: Save search_fare instead of 'total' which was the previous sum
            Book_ticket.objects.create(user=user1, route=route1, fare=search_fare, passenger=passenger, date2=search_date)
            
            if passenger:
                error = True
        else:
            housefull = True
            
    d = {'data2': data2, 'pro': pro, 'total': total, 'book': book, 'error': error, 'housefull': housefull, 'route1': route1, 'coun': coun, 'pid': pid}
    return render(request, 'book_detail.html', d)

@login_required(login_url='login_customer')
def Delete_passenger(request, pid, bid, route1):
    passenger = Passenger.objects.get(id=pid)
    # Increment seats back
    train = passenger.train
    train.seats += 1
    train.save()
    
    passenger.delete()
    messages.info(request, 'Passenger Deleted Successfully')
    return redirect('book_detail', coun=1, pid=bid, route1=route1)

@login_required(login_url='login_customer')
def Card_Detail(request, total, coun, route1, pid):
    data2 = Add_Train.objects.get(id=pid)
    user1 = Register.objects.get(user=request.user)
    pro = Passenger.objects.filter(user=user1)
    book = Book_ticket.objects.filter(user=user1)
    
    error = False
    count = ""
    if request.method == "POST":
        error = True
        just_booked = []
        for i in pro:
            count = i.name
            if i.status != "set":
                i.status = "set"
                i.save()
                just_booked.append(i)
                
        # Send Email E-Ticket
        if just_booked:
            try:
                html_message = render_to_string('email_ticket.html', {
                    'pro': just_booked, 
                    'total': total, 
                    'route1': route1, 
                    'data2': data2,
                    'user': request.user
                })
                send_mail(
                    'Your Railway E-Ticket Confirmation',
                    'Thank you for booking with us! Please view this email in an HTML-compatible client to see your e-ticket.',
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    fail_silently=True,
                    html_message=html_message
                )
            except Exception as e:
                print("Failed to send ticket email:", e)
                
        return redirect('my_booking')

    d = {'user': user1, 'data2': data2, 'pro': pro, 'total': total, 'book': book, 'error': error, 'route1': route1, 'count': count}
    return render(request, 'card_detail.html', d)

@login_required(login_url='login_customer')
def my_booking(request):
    user1 = Register.objects.get(user=request.user)
    pro = Passenger.objects.filter(user=user1)
    book = Book_ticket.objects.filter(user=user1)
    d = {'user': user1, 'pro': pro, 'book': book}
    return render(request, 'my_booking.html', d)

@login_required(login_url='login_customer')
def view_ticket(request, pid):
    book = Book_ticket.objects.get(id=pid)
    return render(request, 'view_ticket.html', {'book': book, 'passenger': book.passenger})

@login_required(login_url='login_customer')
def viewbookings(request):
    book = Book_ticket.objects.all()
    return render(request, 'viewbookings.html', {'book': book})

@login_required(login_url='login_customer')
def delte_my_booking(request, pid):
    Passenger.objects.filter(id=pid).delete()
    return redirect('my_booking')

@login_required(login_url='login_customer')
def deletebooking(request, pid):
    Passenger.objects.filter(id=pid).delete()
    return redirect('viewbookings')

@login_required(login_url='login_customer')
def Add_train(request):
    error = False
    if request.method == "POST":
        n = request.POST.get('busname')
        no = request.POST.get('bus_no')
        f = request.POST.get('fcity')
        to = request.POST.get('tcity')
        de = request.POST.get('dtime')
        a = request.POST.get('atime')
        t = request.POST.get('ttime')
        d = request.POST.get('dis')
        seats = request.POST.get('seats', 100)
        i = request.FILES.get('img')
        Add_Train.objects.create(trainname=n, train_no=no, from_city=f, to_city=to, departuretime=de, arrivaltime=a, trevaltime=t, distance=d, img=i, seats=seats)
        error = True
    return render(request, 'add_train.html', {"error": error})

@login_required(login_url='login_customer')
def view_train(request):
    data = Add_Train.objects.all()
    return render(request, "view_train.html", {"data": data})

@login_required(login_url='login_customer')
def add_route(request):
    error = False
    data = Add_Train.objects.all()
    if request.method == "POST":
        b = request.POST.get('bus')
        r = request.POST.get('route')
        f = request.POST.get('fare')
        d = request.POST.get('dis')
        bus1 = Add_Train.objects.get(id=b)
        Add_route.objects.create(train=bus1, route=r, distance=d, fare=f)
        error = True
    return render(request, 'add_route.html', {"data": data, "error": error})

@login_required(login_url='login_customer')
def Edit_route(request, pid):
    error = False
    data = Add_route.objects.get(id=pid)
    data2 = Add_Train.objects.all()
    if request.method == "POST":
        b = request.POST.get('bus')
        r = request.POST.get('route')
        f = request.POST.get('fare')
        d = request.POST.get('dis')
        data.train = Add_Train.objects.get(id=b)
        data.route = r
        data.fare = f
        data.distance = d
        data.save()
        error = True
    return render(request, 'editroute.html', {"data": data, "data2": data2, "error": error})

@login_required(login_url='login_customer')
def edit(request, pid):
    error = False
    data1 = Add_Train.objects.get(id=pid)
    if request.method == "POST":
        data1.trainname = request.POST.get('busname')
        data1.train_no = request.POST.get('bus_no')
        data1.departuretime = request.POST.get('dtime')
        data1.arrivaltime = request.POST.get('atime')
        data1.trevaltime = request.POST.get('ttime')
        data1.from_city = request.POST.get('fcity')
        data1.to_city = request.POST.get('tcity')
        data1.distance = request.POST.get('dis')
        data1.seats = request.POST.get('seats', 100)
        data1.save()
        error = True
    return render(request, 'edittrain.html', {'data': data1, 'error': error})

@login_required(login_url='login_customer')
def delete(request, pid):
    Add_Train.objects.filter(id=pid).delete()
    return redirect('view_train')

@login_required(login_url='login_customer')
def delete_route(request, pid):
    Add_route.objects.filter(id=pid).delete()
    return redirect('availableroute')

@login_required(login_url='login_customer')
def displayroute(request):
    data = Add_route.objects.all()
    data2 = Add_Train.objects.all()
    return render(request, "availableroute.html", {'data': data, 'data2': data2})

@login_required(login_url='login_customer')
def admindashboard(request):
    if not request.user.is_staff:
        return redirect('login_customer')
        
    total_users = User.objects.filter(is_staff=False).count()
    total_trains = Add_Train.objects.count()
    total_routes = Add_route.objects.count()
    
    # Calculate revenue from Book_ticket (sum of fare)
    total_revenue = sum([t.fare for t in Book_ticket.objects.all() if t.fare])
    
    d = {
        'total_users': total_users,
        'total_trains': total_trains,
        'total_routes': total_routes,
        'total_revenue': total_revenue
    }
    return render(request, 'admindashboard.html', d)

@login_required(login_url='login_customer')
def change_image(request, pid):
    train = Add_Train.objects.get(id=pid)
    error = ""
    if request.method == "POST":
        try:
            train.img = request.FILES['newpic']
            train.save()
            error = "no"
        except:
            error = "yes"
    return render(request, 'change_image.html', {'error': error, 'train': train})

@login_required(login_url='login_customer')
def view_regusers(request):
    data = Register.objects.filter(user__is_staff=False)
    return render(request, "view_regusers.html", {"data": data})

@login_required(login_url='login_customer')
def delete_user(request, pid):
    User.objects.filter(id=pid).delete()
    return redirect('view_regusers')

from django.http import HttpResponse
from django.template.loader import get_template

@login_required(login_url='login_customer')
def download_ticket(request, pid):
    book = Book_ticket.objects.get(id=pid)
    context = {'book': book, 'passenger': book.passenger}
    return render(request, 'ticket_pdf.html', context)