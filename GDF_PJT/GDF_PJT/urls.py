from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),

    # App views
    path('Login/', views.login_view, name='Login'),
    path('Home/',views.home_view, name='Home'),
    path('Logout/', views.sair_view, name='Logout'),
    path('Dashboard/', views.index_dashboard, name='Dashboard'),
    
    path('',views.login_view),
]
