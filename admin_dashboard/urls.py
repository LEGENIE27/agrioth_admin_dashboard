# admin_dashboard/admin_dashboard/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login / Logout
    # Le template de login utilisé est dashboard/templates/registration/login.html
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Dashboard app (les vues sont protégées par @login_required)
    path('dashboard/', include('dashboard.urls')),

    # Faire en sorte que la page racine affiche la page de connexion
    # (cela garantit que http://127.0.0.1:8000/ affiche la page de login)
    path('', auth_views.LoginView.as_view(template_name='registration/login.html'), name='root_login'),
]
