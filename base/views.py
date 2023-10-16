from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm,MyUserCreationForm
from django.http import Http404
# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
def loginPage(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
            print(f"user is: {user}")
        except:
            print(f"user not found")
            messages.error(request, "User does not exist.")
        finally:
            user = authenticate(request, email=email, password=password )
            if user is not None:
                login(request,user)
                return redirect('home')
            else:
                messages.error(request, "Credential Failed!")

        # print("Horayyyyy")
    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    page = 'register'
    form = MyUserCreationForm()
    print(form)
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            # print(user)
            login(request, user)
            return redirect('home')
        else:
            print('MOMOMOMOM')
            messages.error(request, "Ann error occurred.")
            return redirect('register')
    context = {'page': page, "form": form}
    return render(request, 'base/login_register.html', context)

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains = q) | 
        Q(name__icontains = q) | 
        Q(description__icontains = q)
        )

    topics = Topic.objects.all()
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains = q))
    context = {"rooms": rooms, "topics":topics, "room_count":room_count, "room_messages":room_messages}
    return render(request, 'base/home.html', context)

def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()
    if request.method == "POST":
        message = Message.objects.create(
            user = request.user,
            room=room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
    
    context = {'room': room, 'room_messages':room_messages, "participants":participants}
    return render(request, 'base/room.html', context)

def userProfile(request, pk):
    user = User.objects.get(id = pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {"me":user, 'rooms':rooms, "room_messages":room_messages, "topics":topics}
    return render(request, 'base/profile.html', context)

@login_required(login_url='/login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all().order_by('-id')[:2]
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description'),

        )

        # form = RoomForm(request.POST)
        # if form.is_valid():
        #     room = form.save(commit=False)
        #     room.host = request.user
        #     room.save()
        return redirect('home')
        
    context = {'form': form, 'topics':topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='/login')
def updateRoom(request, pk):
    room = Room.objects.get(id = pk)
    form = RoomForm(instance=room)
    # topics = Topic.objects.all().order_by('-id')[:2]
    topics = Topic.objects.all().order_by('-id')

    
    if request.user != room.host:
        return HttpResponse("You are not allowed here!")

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        # form = RoomForm(request.POST, instance=room)
        # if form.is_valid():
        #     form.save()
        return redirect('home')
    context = {'room': room, 'form': form, 'topics':topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='/login')
def deleteRoom(request, pk):
    room = Room.objects.get(id = pk)
    if request.user != room.host:
        return HttpResponse("You are not allowed here!")

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    context = {'obj': room}
    return render(request, 'base/delete.html', context)

@login_required(login_url='/login')
def deleteMessage(request, pk):
    try:
        message = Message.objects.get(id = pk)
    except:
        # raise Http404("Message does not exist!")
        if 'HTTP_REFERER' in request.META:
        # Use the 'HTTP_REFERER' header to get the previous URL
            previous_url = request.META['HTTP_REFERER']
            # Redirect to the previous URL
            return HttpResponseRedirect(previous_url)
        else:
            # If the 'HTTP_REFERER' header is not available, you can provide a default URL to redirect to
            # For example, you can redirect to the homepage
            return HttpResponseRedirect('home')
        # return HttpResponse("Message does not exist!")

    # if message is None:
    #     raise Http404("Message does not exist!")

    if request.user != message.user:
        return HttpResponse("You are not allowed here!")

    if request.method == 'POST':
        message.delete()
        return redirect('room', message.room.id)
    context = {'obj': message}
    return render(request, 'base/delete.html', context)

@login_required(login_url='/login')
def updateUser(request):
    # if request.user != room.host:
    #     return HttpResponse("You are not allowed here!")
    user = request.user
    form = UserForm(instance=user)
    context = {'form':form}

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk = user.id)

    return render(request, 'base/update-user.html',context)

def topicPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(
        Q(name__icontains = q) 
        )
    context = {'topics':topics}
    return render(request, 'base/topics.html', context)

def activityPage(request):
    messagess = Message.objects.all()
    context = {'messagess':messagess}
    return render(request, 'base/activity.html', context)
