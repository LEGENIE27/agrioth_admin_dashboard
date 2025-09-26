from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/edit/<str:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<str:user_id>/', views.delete_user, name='delete_user'),
    path('users/<str:user_id>/', views.user_detail, name='user_detail'),
    path('boxes/', views.box_list, name='box_list'),
    
    # URLs pour la gestion des abonnements
    path('subscriptions/', views.subscription_list, name='subscription_list'),
    path('subscriptions/add/', views.subscription_create, name='subscription_create'),
    path('subscriptions/edit/<str:subscription_id>/', views.subscription_update, name='subscription_update'),
    path('subscriptions/delete/<str:subscription_id>/', views.subscription_delete, name='subscription_delete'),
    
    path('feedbacks/', views.feedback_list, name='feedback_list'),
    
    # Nouvelles URLs pour la gestion des boxes des utilisateurs
    path('users/assign-box/<str:user_id>/', views.assign_box, name='assign_box'),
    path('users/unassign-box/<str:user_id>/<str:box_id>/', views.unassign_box, name='unassign_box'),
    path('users/boxes/<str:user_id>/', views.user_boxes, name='user_boxes'),
    # Ajout de l'URL pour créer une box pour un utilisateur
    path('users/create-box/<str:user_id>/', views.create_box_for_user, name='create_box_for_user'),
]