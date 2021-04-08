from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import User, Listing, Bid, Comment, WatchList
from .forms import CreateListingForm


def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(sold=False)
    })


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
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


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
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == "POST":
        form = CreateListingForm(request.POST)

        if form.is_valid():
            owner = request.user
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            bid = form.cleaned_data["bid"]
            image_url = form.cleaned_data["image_url"]
            if request.POST.get("categories") is not None:
                category = request.POST.get("categories")
            if request.POST.get("add-category") is not "":
                category = request.POST.get("add-category")
            else:
                category = "Undefined"
            Listing.objects.create(owner=owner, title=title, description=description, price=bid, image_url=image_url, category=category)
    
        return HttpResponseRedirect(reverse('index'))

    elif request.method == "GET":
        return render(request, "auctions/create_listing.html", {
            "listing_form": CreateListingForm(),
            "categories": Listing.objects.values_list('category', flat=True)
        })


@login_required
def listing(request, listing_id):
    user = request.user
    try:
        listing = Listing.objects.get(id=listing_id)
    except Listing.DoesNotExist:
        return render(request, "auctions/404.html")
    am_owner = True if (listing.owner == user) else False
    category = listing.category
    button = "unwatch" if (WatchList.objects.filter(user=user, listing_id=listing_id)) else "watch"

    if request.method == "POST":
        if request.POST.get("comment") is not None:
            comment = request.POST.get("comment")
            Comment.objects.create(user=user, listing=listing, comment=comment)

        elif request.POST.get("watch") is not None:
            WatchList.objects.create(user=user, listing_id=listing_id)
            button = "unwatch"
        elif request.POST.get("unwatch") is not None:
            WatchList.objects.get(user=user, listing_id=listing_id).delete()
            button = "watch"

        elif request.POST.get("bid") is not None:
            bid = request.POST.get("bid")
            listing.price = float(bid)
            listing.save()
            Bid.objects.create(user=user, price=bid, listing=listing)

        elif request.POST.get("close-bidding") is not None:
            highest_bidder = Bid.objects.get(price=listing.price, listing=listing).user
            listing.sold = True
            listing.winner = highest_bidder.username
            listing.save()
    
    comments = Comment.objects.filter(listing=listing.id)
    sold = listing.sold
    winner = listing.winner
    bidding_msg = "Congratulations, you are the winner!" if (str(user) == winner) else "Bidding is closed"

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "category": category,
        "comments": comments, 
        "button": button, 
        "am_owner": am_owner,
        "sold": sold,
        "bidding_msg": bidding_msg
    })


@login_required
def watchlist(request):
    user = request.user
    user_watching = WatchList.objects.filter(user=user)
    id_set = user_watching.values_list('listing_id', flat=True)
    listings = []

    for each_id in id_set:
        listings.append(Listing.objects.get(id=each_id))

    return render(request, "auctions/watchlist.html", {
        "listings": listings,
    })


def category(request):
    listings = None
    categories = Listing.objects.values_list('category', flat=True)
    category = categories.first()

    if request.method == "POST":
        category = request.POST["categories"]
        listings = Listing.objects.filter(category=category)

    return render(request, "auctions/categories.html", {
        "categories": categories,
        "category": category,
        "listings": listings
    })