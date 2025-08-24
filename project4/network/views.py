from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import  User, Post, Follow



def index(request):
    return render(request, "network/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

@csrf_exempt
def new_post(request):
    if request.method == "POST":
        data = json.loads(request.body)
        content = data.get("content", "")
        if content.strip() == "":
            return JsonResponse({"error": "Post cannot be empty."}, status=400)

        post = Post.objects.create(user=request.user, content=content)
        return JsonResponse({
            "message": "Post created successfully",
            "post": {
                "id": post.id,
                "user": post.user.username,
                "content": post.content,
                "timestamp": post.timestamp.strftime("%b %d %Y, %I:%M %p")
            }
        }, status=201)

   
    return JsonResponse({"error": "POST request required."}, status=405)
    
    
def all_posts(request):
    posts = Post.objects.all().order_by("-timestamp")  # newest first
     # Set up pagination (10 posts per page)
    paginator = Paginator(posts, 10)

    # Get the current page number from query parameters (?page=2, etc.)
    page_number = request.GET.get("page")

    # Get the posts for that page
    page_obj = paginator.get_page(page_number)
    return render(request, "network/all_posts.html", {
        "page_obj": page_obj
    })

@login_required
def following_post(request):
    following = Follow.objects.filter(follower=request.user).values_list("following", flat=True)
    posts = Post.objects.filter(user__in=following).order_by("-timestamp")

     # Set up pagination (10 posts per page)
    paginator = Paginator(posts, 10)

    # Get the current page number from query parameters (?page=2, etc.)
    page_number = request.GET.get("page")

    # Get the posts for that page
    page_obj = paginator.get_page(page_number)
    return render(request, "network/all_posts.html", {
        "page_obj": page_obj
    })


@login_required
def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=user_profile).order_by("-timestamp")

    # follower/following counts
    followers_count = user_profile.followers.count()
    following_count = user_profile.following.count()

    # is the current user already following this profile?
    is_following = Follow.objects.filter(follower=request.user, following=user_profile).exists()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)


    return render(request, "network/profile.html", {
        "user_profile": user_profile,
        "page_obj": page_obj,
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following
    })

@login_required
def toggle_follow(request, username):
    user_to_follow = get_object_or_404(User, username=username)

    if user_to_follow == request.user:
        return JsonResponse({"error": "You cannot follow yourself."}, status=400)

    follow_obj, created = Follow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )

    if not created:
        # already following → unfollow
        follow_obj.delete()
        return JsonResponse({"status": "unfollowed"})
    else:
        return JsonResponse({"status": "followed"})
    
@login_required
@csrf_exempt
def edit_post(request, post_id):
    if request.method == "PUT":
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found."}, status=404)

        # Security: Only allow the author to edit
        if post.user != request.user:
            return JsonResponse({"error": "You cannot edit someone else's post."}, status=403)

        data = json.loads(request.body)
        content = data.get("content", "").strip()

        if content == "":
            return JsonResponse({"error": "Post cannot be empty."}, status=400)

        post.content = content
        post.save()

        return JsonResponse({"message": "Post updated successfully."}, status=200)

    return JsonResponse({"error": "Invalid request method."}, status=405)

@login_required
def like_post(request, post_id):
        
        if request.method == "PUT":
            post = get_object_or_404(Post, id=post_id)
            user = request.user

            if user in post.liked_by.all():
                post.liked_by.remove(user)
                liked = False
            else:
                post.liked_by.add(user)
                liked = True

            return JsonResponse({
                "likes": post.liked_by.count(),
                "liked": liked
            })
        
        return JsonResponse({"error": "Invalid request"}, status=400)
 
