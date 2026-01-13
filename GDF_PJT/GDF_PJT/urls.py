from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # App views
    path('Login/', views.Login_view, name='Login'),
    path('Home/',views.Home_view, name='Home'),
    path('Logout/', views.Sair_View, name='Logout'),
    path('Dashboard/', views.Dashboard_View, name='Dashboard'),
    
    path('',views.Login_view),
]
