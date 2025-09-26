from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .utils import get_api_service
import logging
import json

# Configuration du logging
logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_staff

@login_required
@user_passes_test(is_admin)
def dashboard_home(request):
    try:
        api_service = get_api_service()
        
        # Stats existantes
        user_stats = api_service.get_user_stats()
        box_stats = api_service.get_box_stats()
        subscription_stats = api_service.get_subscription_stats()
        feedback_stats = api_service.get_feedback_stats()

        # 🔹 Ajout pour graphiques
        users = api_service.get_users() or []
        boxes = api_service.get_boxes() or []

        def default_serializer(o):
            try:
                return o.isoformat()
            except Exception:
                return str(o)

        context = {
            'user_stats': user_stats,
            'box_stats': box_stats,
            'subscription_stats': subscription_stats,
            'feedback_stats': feedback_stats,
            'users_json': json.dumps(users, default=default_serializer),
            'boxes_json': json.dumps(boxes, default=default_serializer),
        }
        
        return render(request, 'dashboard/home.html', context)
    
    except Exception as e:
        logger.error(f"Erreur dans dashboard_home: {e}")
        messages.error(request, "Erreur de connexion à la base de données")
        return render(request, 'dashboard/home.html', {
            'user_stats': {'total': 0, 'active': 0, 'pending': 0, 'suspended': 0},
            'box_stats': {'total': 0, 'active': 0, 'inactive': 0, 'maintenance': 0},
            'subscription_stats': {'total': 0, 'active': 0, 'expired': 0, 'canceled': 0},
            'feedback_stats': {'total': 0, 'positive': 0, 'neutral': 0, 'negative': 0},
            'users_json': '[]',
            'boxes_json': '[]'
        })

@login_required
@user_passes_test(is_admin)
def user_list(request):
    try:
        api_service = get_api_service()
        users = api_service.get_users()
        boxes = api_service.get_boxes() or []
        
        # Préparer les données pour l'affichage des boxes attribuées
        for user in users:
            user['assigned_boxes'] = []
            # Si l'API retourne directement les boxes de l'utilisateur
            if 'boxes' in user and user['boxes']:
                user['assigned_boxes'] = user['boxes']
            # Sinon, nous devrons implémenter une logique de matching
            # basée sur les IDs de boxes stockés dans l'utilisateur
        
        # Filtrer les boxes disponibles (non attribuées ou pouvant être réattribuées)
        available_boxes = [box for box in boxes if box.get('status') in ['active', 'available']]
        
        context = {
            'users': users,
            'available_boxes': available_boxes,
        }
        
        return render(request, 'dashboard/users.html', context)
    
    except Exception as e:
        logger.error(f"Erreur dans user_list: {e}")
        messages.error(request, "Erreur de connexion à la base de données")
        return render(request, 'dashboard/users.html', {'users': [], 'available_boxes': []})

@login_required
@user_passes_test(is_admin)
def add_user(request):
    if request.method == 'POST':
        try:
            api_service = get_api_service()
            
            # Récupération des données du formulaire
            firstname = request.POST.get('firstname')
            lastname = request.POST.get('lastname')
            phoneNumber = request.POST.get('phoneNumber')
            region = request.POST.get('region')
            status = request.POST.get('status')
            
            # Création de l'utilisateur via l'API
            user_data = {
                'firstname': firstname,
                'lastname': lastname,
                'phoneNumber': phoneNumber,
                'region': region,
                'status': status
            }
            
            result = api_service.create_user(user_data)
            
            if result and 'error' not in result:
                messages.success(request, 'Utilisateur ajouté avec succès!')
            else:
                error_msg = result.get('error', 'Erreur inconnue lors de l\'ajout')
                messages.error(request, f'Erreur: {error_msg}')
                
        except Exception as e:
            logger.error(f"Erreur dans add_user: {e}")
            messages.error(request, f'Erreur lors de l\'ajout: {str(e)}')
        
        return redirect('user_list')
    
    # Si la méthode n'est pas POST, rediriger vers la liste
    return redirect('user_list')

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    if request.method == 'POST':
        try:
            api_service = get_api_service()
            
            # Récupération des données du formulaire
            firstname = request.POST.get('firstname')
            lastname = request.POST.get('lastname')
            phoneNumber = request.POST.get('phoneNumber')
            region = request.POST.get('region')
            status = request.POST.get('status')
            
            # Mise à jour de l'utilisateur via l'API
            user_data = {
                'firstname': firstname,
                'lastname': lastname,
                'phoneNumber': phoneNumber,
                'region': region,
                'status': status
            }
            
            result = api_service.update_user(user_id, user_data)
            
            if result and 'error' not in result:
                messages.success(request, 'Utilisateur modifié avec succès!')
            else:
                error_msg = result.get('error', 'Erreur inconnue lors de la modification')
                messages.error(request, f'Erreur: {error_msg}')
                
        except Exception as e:
            logger.error(f"Erreur dans edit_user: {e}")
            messages.error(request, f'Erreur lors de la modification: {str(e)}')
        
        return redirect('user_list')
    
    # Si la méthode n'est pas POST, rediriger vers la liste
    return redirect('user_list')

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    if request.method == 'POST':
        try:
            api_service = get_api_service()
            result = api_service.delete_user(user_id)
            
            if result and 'error' not in result:
                messages.success(request, 'Utilisateur supprimé avec succès!')
            else:
                error_msg = result.get('error', 'Erreur inconnue lors de la suppression')
                messages.error(request, f'Erreur: {error_msg}')
                
        except Exception as e:
            logger.error(f"Erreur dans delete_user: {e}")
            messages.error(request, f'Erreur lors de la suppression: {str(e)}')
        
        return redirect('user_list')
    
    # Si la méthode n'est pas POST, rediriger vers la liste
    return redirect('user_list')

@login_required
@user_passes_test(is_admin)
def box_list(request):
    try:
        api_service = get_api_service()
        boxes = api_service.get_boxes()
        
        context = {
            'boxes': boxes,
        }
        
        return render(request, 'dashboard/boxes.html', context)
    
    except Exception as e:
        logger.error(f"Erreur dans box_list: {e}")
        messages.error(request, "Erreur de connexion à la base de données")
        return render(request, 'dashboard/boxes.html', {'boxes': []})

@login_required
@user_passes_test(is_admin)
def user_detail(request, user_id):
    try:
        api_service = get_api_service()
        user = api_service.get_user_by_id(user_id)
        context = {'user': user}
        return render(request, 'dashboard/user_detail.html', context)
    
    except Exception as e:
        logger.error(f"Erreur dans user_detail: {e}")
        messages.error(request, "Erreur de récupération des détails de l'utilisateur")
        return redirect('user_list')

@login_required
@user_passes_test(is_admin)
def subscription_list(request):
    try:
        api_service = get_api_service()
        subscriptions = api_service.get_subscriptions()
        users = api_service.get_users()  # Ajout de cette ligne pour récupérer les utilisateurs

        context = {
            'subscriptions': subscriptions,
            'users': users,  # Ajout de cette ligne pour passer les utilisateurs au template
        }
        return render(request, 'dashboard/subscriptions.html', context)

    except Exception as e:
        logger.error(f"Erreur dans subscription_list: {e}")
        messages.error(request, "Erreur de connexion à la base de données")
        return render(request, 'dashboard/subscriptions.html', {
            'subscriptions': [],
            'users': []  # Ajout d'une liste vide en cas d'erreur
        })

@login_required
@user_passes_test(is_admin)
def subscription_create(request):
    if request.method == 'POST':
        try:
            api_service = get_api_service()
            
            # Récupération des données du formulaire
            subscription_data = {
                'user_id': request.POST.get('user_id'),
                'plan': request.POST.get('plan'),
                'status': request.POST.get('status'),
                'startDate': request.POST.get('startDate'),
                'endDate': request.POST.get('endDate'),
                'price': request.POST.get('price'),
                'paymentMethod': request.POST.get('paymentMethod')
            }
            
            # Création de l'abonnement via l'API
            result = api_service.create_subscription(subscription_data)
            
            if result and 'error' not in result:
                messages.success(request, 'Abonnement créé avec succès!')
                return redirect('subscription_list')
            else:
                error_msg = result.get('error', 'Erreur inconnue lors de la création')
                messages.error(request, f'Erreur: {error_msg}')
                
        except Exception as e:
            logger.error(f"Erreur dans subscription_create: {e}")
            messages.error(request, f'Erreur lors de la création: {str(e)}')
            return render(request, 'dashboard/subscription_form.html', {'form_data': request.POST})
    
    # Si la méthode n'est pas POST, afficher le formulaire vide
    try:
        api_service = get_api_service()
        users = api_service.get_users() or []
        return render(request, 'dashboard/subscription_form.html', {
            'users': users,
            'form_data': {},
            'action': 'create'
        })
    except Exception as e:
        logger.error(f"Erreur dans subscription_create (GET): {e}")
        messages.error(request, "Erreur de connexion à la base de données")
        return redirect('subscription_list')

@login_required
@user_passes_test(is_admin)
def subscription_update(request, subscription_id):
    if request.method == 'POST':
        try:
            api_service = get_api_service()
            
            # Récupération des données du formulaire
            subscription_data = {
                'user_id': request.POST.get('user_id'),
                'plan': request.POST.get('plan'),
                'status': request.POST.get('status'),
                'startDate': request.POST.get('startDate'),
                'endDate': request.POST.get('endDate'),
                'price': request.POST.get('price'),
                'paymentMethod': request.POST.get('paymentMethod')
            }
            
            # Mise à jour de l'abonnement via l'API
            result = api_service.update_subscription(subscription_id, subscription_data)
            
            if result and 'error' not in result:
                messages.success(request, 'Abonnement modifié avec succès!')
                return redirect('subscription_list')
            else:
                error_msg = result.get('error', 'Erreur inconnue lors de la modification')
                messages.error(request, f'Erreur: {error_msg}')
                
        except Exception as e:
            logger.error(f"Erreur dans subscription_update: {e}")
            messages.error(request, f'Erreur lors de la modification: {str(e)}')
    
    # Récupération des données de l'abonnement pour pré-remplir le formulaire
    try:
        api_service = get_api_service()
        subscription = api_service.get_subscription_by_id(subscription_id)
        users = api_service.get_users() or []
        
        if not subscription:
            messages.error(request, 'Abonnement non trouvé')
            return redirect('subscription_list')
            
        return render(request, 'dashboard/subscription_form.html', {
            'subscription': subscription,
            'users': users,
            'form_data': subscription,
            'action': 'update'
        })
    except Exception as e:
        logger.error(f"Erreur dans subscription_update (GET): {e}")
        messages.error(request, "Erreur de connexion à la base de données")
        return redirect('subscription_list')

@login_required
@user_passes_test(is_admin)
def subscription_delete(request, subscription_id):
    if request.method == 'POST':
        try:
            api_service = get_api_service()
            
            # Suppression de l'abonnement via l'API
            result = api_service.delete_subscription(subscription_id)
            
            if result and 'error' not in result:
                messages.success(request, 'Abonnement supprimé avec succès!')
            else:
                error_msg = result.get('error', 'Erreur inconnue lors de la suppression')
                messages.error(request, f'Erreur: {error_msg}')
                
        except Exception as e:
            logger.error(f"Erreur dans subscription_delete: {e}")
            messages.error(request, f'Erreur lors de la suppression: {str(e)}')
        
        return redirect('subscription_list')
    
    # Si la méthode n'est pas POST, afficher la page de confirmation
    try:
        api_service = get_api_service()
        subscription = api_service.get_subscription_by_id(subscription_id)
        
        if not subscription:
            messages.error(request, 'Abonnement non trouvé')
            return redirect('subscription_list')
            
        return render(request, 'dashboard/subscription_confirm_delete.html', {
            'subscription': subscription
        })
    except Exception as e:
        logger.error(f"Erreur dans subscription_delete (GET): {e}")
        messages.error(request, "Erreur de connexion à la base de données")
        return redirect('subscription_list')

@login_required
@user_passes_test(is_admin)
def feedback_list(request):
    try:
        api_service = get_api_service()
        feedbacks = api_service.get_feedbacks()

        context = {
            'feedbacks': feedbacks,
        }
        return render(request, 'dashboard/feedbacks.html', context)

    except Exception as e:
        logger.error(f"Erreur dans feedback_list: {e}")
        messages.error(request, "Erreur de connexion à la base de données")
        return render(request, 'dashboard/feedbacks.html', {'feedbacks': []})

# =============================================================================
# NOUVELLES VUES POUR LA GESTION DES BOXES DES UTILISATEURS
# =============================================================================

@login_required
@user_passes_test(is_admin)
def assign_box(request, user_id):
    if request.method == 'POST':
        try:
            api_service = get_api_service()
            
            # Récupération des données du formulaire
            box_id = request.POST.get('box_id')
            assignment_notes = request.POST.get('assignment_notes', '')
            
            # Attribution de la box à l'utilisateur via l'API
            assignment_data = {
                'user_id': user_id,
                'box_id': box_id,
                'assignment_notes': assignment_notes
            }
            
            # Ici, vous devrez implémenter la méthode assign_box_to_user dans votre API service
            result = api_service.assign_box_to_user(assignment_data)
            
            if result and 'error' not in result:
                messages.success(request, 'Box attribuée avec succès!')
            else:
                error_msg = result.get('error', 'Erreur inconnue lors de l\'attribution')
                messages.error(request, f'Erreur: {error_msg}')
                
        except Exception as e:
            logger.error(f"Erreur dans assign_box: {e}")
            messages.error(request, f'Erreur lors de l\'attribution de la box: {str(e)}')
        
        return redirect('user_list')
    
    # Si la méthode n'est pas POST, rediriger vers la liste
    return redirect('user_list')

@login_required
@user_passes_test(is_admin)
def unassign_box(request, user_id, box_id):
    if request.method == 'POST':
        try:
            api_service = get_api_service()
            
            # Retrait de la box de l'utilisateur via l'API
            # Ici, vous devrez implémenter la méthode unassign_box_from_user dans votre API service
            result = api_service.unassign_box_from_user(user_id, box_id)
            
            if result and 'error' not in result:
                messages.success(request, 'Box retirée avec succès!')
            else:
                error_msg = result.get('error', 'Erreur inconnue lors du retrait')
                messages.error(request, f'Erreur: {error_msg}')
                
        except Exception as e:
            logger.error(f"Erreur dans unassign_box: {e}")
            messages.error(request, f'Erreur lors du retrait de la box: {str(e)}')
        
        return redirect('user_list')
    
    # Si la méthode n'est pas POST, rediriger vers la liste
    return redirect('user_list')

@login_required
@user_passes_test(is_admin)
def user_boxes(request, user_id):
    try:
        api_service = get_api_service()
        
        # Récupérer les informations de l'utilisateur
        user = api_service.get_user_by_id(user_id)
        
        # Récupérer les boxes attribuées à cet utilisateur
        # Ici, vous devrez implémenter la méthode get_user_boxes dans votre API service
        user_boxes = api_service.get_user_boxes(user_id) or []
        
        context = {
            'user': user,
            'user_boxes': user_boxes,
        }
        
        return render(request, 'dashboard/user_boxes.html', context)
    
    except Exception as e:
        logger.error(f"Erreur dans user_boxes: {e}")
        messages.error(request, "Erreur de récupération des boxes de l'utilisateur")
        return redirect('user_list')

# =============================================================================
# NOUVELLE VUE AJOUTÉE POUR CRÉER UNE BOX POUR UN UTILISATEUR
# =============================================================================

@login_required
@user_passes_test(is_admin)
def create_box_for_user(request, user_id):
    if request.method == 'POST':
        try:
            api_service = get_api_service()
            
            # Récupération des données du formulaire
            box_data = {
                'name': request.POST.get('name'),
                'serial_number': request.POST.get('serial_number'),
                'box_type': request.POST.get('box_type'),
                'status': request.POST.get('status'),
                'description': request.POST.get('description', ''),
                'user_id': user_id  # Associer la box à l'utilisateur
            }
            
            # Création de la box via l'API
            result = api_service.create_box(box_data)
            
            if result and 'error' not in result:
                messages.success(request, 'Box créée et attribuée à l\'utilisateur avec succès!')
            else:
                error_msg = result.get('error', 'Erreur inconnue lors de la création')
                messages.error(request, f'Erreur: {error_msg}')
                
        except Exception as e:
            logger.error(f"Erreur dans create_box_for_user: {e}")
            messages.error(request, f'Erreur lors de la création de la box: {str(e)}')
        
        return redirect('user_list')
    
    # Si la méthode n'est pas POST, rediriger vers la liste
    return redirect('user_list')