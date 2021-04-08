from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),

    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),

    path("create_listing", views.create_listing, name="create_listing"),
    path("listing/<str:listing_id>", views.listing, name="listing"),

    path("watch_list", views.watchlist, name="watchlist"),
    path("categories", views.category, name="categories")
]
