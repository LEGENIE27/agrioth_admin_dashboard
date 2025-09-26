from venv import logger
import requests
import json
from django.conf import settings
from django.core.cache import cache
from requests.exceptions import RequestException
from pymongo import MongoClient
from bson import ObjectId
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MongoDBService:
    def __init__(self):
        # Récupérer l'URL de connexion depuis les variables d'environnement
        self.connection_string = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/agrioth')
        self.client = None
        self.db = None
        
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client.get_database()  # Utilise la base de données par défaut de l'URI
            
            # Test de connexion
            self.client.admin.command('ismaster')
            print("Connexion à MongoDB établie avec succès")
        except Exception as e:
            print(f"Erreur de connexion à MongoDB: {e}")
            raise
    
    def get_users(self):
        try:
            if self.db is None:
                return []
                
            users = list(self.db.users.find({}))
            
            # Formater les données pour les rendre sérialisables
            formatted_users = []
            for user in users:
                formatted_user = {
                    'id': str(user.get('_id', '')),
                    'phoneNumber': user.get('phoneNumber', ''),
                    'firstname': user.get('firstname', ''),
                    'lastname': user.get('lastname', ''),
                    'region': user.get('region', ''),
                    'status': user.get('status', ''),
                    'createdAt': user.get('createdAt', '')  # Ne pas convertir en ISO
                }
                formatted_users.append(formatted_user)
            
            return formatted_users
        except Exception as e:
            print(f"Erreur lors de la récupération des utilisateurs: {e}")
            return []
    
    def create_user(self, user_data):
        """
        Crée un nouvel utilisateur dans la base de données MongoDB
        """
        try:
            if self.db is None:
                # Tentative de reconnexion si la base de données n'est pas accessible
                self.__init__()
                if self.db is None:
                    return {'error': 'Impossible de se connecter à la base de données'}
            
            # Ajouter un timestamp si non fourni
            if 'createdAt' not in user_data:
                user_data['createdAt'] = datetime.now()
            
            # Insertion du nouvel utilisateur
            result = self.db.users.insert_one(user_data)
            
            if result.inserted_id:
                return {'success': True, 'inserted_id': str(result.inserted_id)}
            else:
                return {'error': "Échec de l'insertion"}
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            return {'error': str(e)}
    
    def update_user(self, user_id, user_data):
        """
        Met à jour un utilisateur existant dans la base de données MongoDB
        """
        try:
            if self.db is None:
                return {'error': 'Impossible de se connecter à la base de données'}
            
            # Ajouter un timestamp de mise à jour
            user_data['updatedAt'] = datetime.now()
            
            # Mise à jour de l'utilisateur
            result = self.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': user_data}
            )
            
            if result.modified_count > 0:
                return {'success': True, 'modified_count': result.modified_count}
            else:
                return {'error': "Aucune modification effectuée ou utilisateur non trouvé"}
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'utilisateur: {e}")
            return {'error': str(e)}
    
    def delete_user(self, user_id):
        """
        Supprime un utilisateur de la base de données MongoDB
        """
        try:
            if self.db is None:
                return {'error': 'Impossible de se connecter à la base de données'}
            
            # Suppression de l'utilisateur
            result = self.db.users.delete_one({'_id': ObjectId(user_id)})
            
            if result.deleted_count > 0:
                return {'success': True, 'deleted_count': result.deleted_count}
            else:
                return {'error': "Aucun utilisateur supprimé ou utilisateur non trouvé"}
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'utilisateur: {e}")
            return {'error': str(e)}
    
    def create_box(self, box_data):
        """
        Crée une nouvelle boîte dans la base de données MongoDB
        """
        try:
            if self.db is None:
                # Tentative de reconnexion si la base de données n'est pas accessible
                self.__init__()
                if self.db is None:
                    return {'error': 'Impossible de se connecter à la base de données'}

            # Vérifier si la collection boxes existe, sinon la créer
            if 'boxes' not in self.db.list_collection_names():
                self.db.create_collection('boxes')

            # Convertir l'ID utilisateur en ObjectId si nécessaire
            if 'user_id' in box_data:
                box_data['user'] = ObjectId(box_data['user_id'])
                del box_data['user_id']

            # Ajouter les timestamps
            box_data['createdAt'] = datetime.now()
            box_data['lastActivity'] = datetime.now()

            # Insertion de la nouvelle boîte
            result = self.db.boxes.insert_one(box_data)

            if result.inserted_id:
                return {'success': True, 'inserted_id': str(result.inserted_id)}
            else:
                return {'error': "Échec de l'insertion de la boîte"}

        except Exception as e:
            logger.error(f"Erreur lors de la création de la boîte: {e}")
            return {'error': str(e)}
    
    def get_boxes(self):
        try:
            if self.db is None:
                return []
                
            # Vérifier si la collection boxes existe
            if 'boxes' not in self.db.list_collection_names():
                print("La collection 'boxes' n'existe pas dans la base de données")
                return []
                
            boxes = list(self.db.boxes.find({}))
            
            # Formater les données pour les rendre sérialisables
            formatted_boxes = []
            for box in boxes:
                # Gérer le champ user qui peut être un ObjectId ou un document populé
                user_info = box.get('user', {})
                if isinstance(user_info, ObjectId):
                    # Si c'est un ObjectId, on récupère les infos de l'utilisateur
                    user = self.db.users.find_one({'_id': user_info})
                    user_info = {
                        'id': str(user.get('_id', '')),
                        'firstname': user.get('firstname', ''),
                        'lastname': user.get('lastname', ''),
                        'phoneNumber': user.get('phoneNumber', ''),
                        'status': user.get('status', '')  # Ajout du statut utilisateur
                    } if user else {}
                
                formatted_box = {
                    'id': str(box.get('_id', '')),
                    'status': box.get('status', ''),
                    'user': user_info,
                    'lastActivity': box.get('lastActivity', ''),  # Ne pas convertir en ISO
                    'createdAt': box.get('createdAt', '')  # Ne pas convertir en ISO
                }
                formatted_boxes.append(formatted_box)
            
            return formatted_boxes
        except Exception as e:
            print(f"Erreur lors de la récupération des boîtes: {e}")
            return []
    
    def get_user_stats(self):
        try:
            if self.db is None:
                return {'total': 0, 'active': 0, 'pending_box': 0, 'suspended': 0}
                
            # Utiliser l'agrégation MongoDB pour des statistiques précises
            pipeline = [
                {
                    '$group': {
                        '_id': '$status',
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            stats = list(self.db.users.aggregate(pipeline))
            
            # Convertir en format plus utilisable
            result = {'total': 0, 'active': 0, 'pending_box': 0, 'suspended': 0}
            for stat in stats:
                result['total'] += stat['count']
                if stat['_id'] == 'active':
                    result['active'] = stat['count']
                elif stat['_id'] == 'pending_box':
                    result['pending_box'] = stat['count']
                elif stat['_id'] == 'suspended':
                    result['suspended'] = stat['count']
            
            return result
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques utilisateurs: {e}")
            users = self.get_users()
            return {
                'total': len(users),
                'active': len([u for u in users if u.get('status') == 'active']),
                'pending_box': len([u for u in users if u.get('status') == 'pending_box']),
                'suspended': len([u for u in users if u.get('status') == 'suspended']),
            }
    
    def get_box_stats(self):
        try:
            if self.db is None:
                return {'total': 0, 'active': 0, 'inactive': 0, 'maintenance': 0}
                
            # Vérifier si la collection boxes existe
            if 'boxes' not in self.db.list_collection_names():
                return {'total': 0, 'active': 0, 'inactive': 0, 'maintenance': 0}
                
            # Utiliser l'agrégation MongoDB pour des statistiques précises
            pipeline = [
                {
                    '$group': {
                        '_id': '$status',
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            stats = list(self.db.boxes.aggregate(pipeline))
            
            # Convertir en format plus utilisable
            result = {'total': 0, 'active': 0, 'inactive': 0, 'maintenance': 0}
            for stat in stats:
                result['total'] += stat['count']
                if stat['_id'] == 'active':
                    result['active'] = stat['count']
                elif stat['_id'] == 'inactive':
                    result['inactive'] = stat['count']
                elif stat['_id'] == 'maintenance':
                    result['maintenance'] = stat['count']
            
            return result
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques des boîtes: {e}")
            boxes = self.get_boxes()
            return {
                'total': len(boxes),
                'active': len([b for b in boxes if b.get('status') == 'active']),
                'inactive': len([b for b in boxes if b.get('status') == 'inactive']),
                'maintenance': len([b for b in boxes if b.get('status') == 'maintenance']),
            }
    
    def get_subscriptions(self):
        try:
            if self.db is None:
                return []
                
            # Vérifier si la collection subscriptions existe
            if 'subscriptions' not in self.db.list_collection_names():
                print("La collection 'subscriptions' n'existe pas dans la base de données")
                return []
                
            subscriptions = list(self.db.subscriptions.find({}))
            
            formatted_subscriptions = []
            for sub in subscriptions:
                # Récupérer les informations de l'utilisateur
                user_info = {}
                if 'user' in sub:
                    user = self.db.users.find_one({'_id': ObjectId(sub['user'])})
                    if user:
                        user_info = {
                            'id': str(user.get('_id', '')),
                            'firstname': user.get('firstname', ''),
                            'lastname': user.get('lastname', ''),
                            'phoneNumber': user.get('phoneNumber', ''),
                            'status': user.get('status', '')  # Ajout du statut utilisateur
                        }
                
                formatted_sub = {
                    'id': str(sub.get('_id', '')),
                    'user': user_info,
                    'plan': sub.get('plan', ''),
                    'status': sub.get('status', ''),
                    'startDate': sub.get('startDate', ''),  # Ne pas convertir en ISO
                    'endDate': sub.get('endDate', ''),  # Ne pas convertir en ISO
                    'price': sub.get('price', 0),
                    'paymentMethod': sub.get('paymentMethod', ''),
                    'createdAt': sub.get('createdAt', ''),  # Ne pas convertir en ISO
                    'updatedAt': sub.get('updatedAt', '')  # Ne pas convertir en ISO
                }
                formatted_subscriptions.append(formatted_sub)
            
            return formatted_subscriptions
        except Exception as e:
            print(f"Erreur lors de la récupération des abonnements: {e}")
            return []
    
    def create_subscription(self, subscription_data):
        """
        Crée un nouvel abonnement dans la base de données MongoDB
        """
        try:
            if self.db is None:
                # Tentative de reconnexion si la base de données n'est pas accessible
                self.__init__()
                if self.db is None:
                    return {'error': 'Impossible de se connecter à la base de données'}
            
            # Vérifier si la collection subscriptions existe, sinon la créer
            if 'subscriptions' not in self.db.list_collection_names():
                self.db.create_collection('subscriptions')
            
            # Convertir l'ID utilisateur en ObjectId si nécessaire
            if 'user_id' in subscription_data:
                subscription_data['user'] = ObjectId(subscription_data['user_id'])
                del subscription_data['user_id']
            
            # Convertir les dates en objets datetime si elles sont fournies sous forme de chaînes
            if 'startDate' in subscription_data and isinstance(subscription_data['startDate'], str):
                subscription_data['startDate'] = datetime.fromisoformat(subscription_data['startDate'].replace('Z', '+00:00'))
            
            if 'endDate' in subscription_data and isinstance(subscription_data['endDate'], str):
                subscription_data['endDate'] = datetime.fromisoformat(subscription_data['endDate'].replace('Z', '+00:00'))
            
            # Ajouter les timestamps
            subscription_data['createdAt'] = datetime.now()
            subscription_data['updatedAt'] = datetime.now()
            
            # Insertion du nouvel abonnement
            result = self.db.subscriptions.insert_one(subscription_data)
            
            if result.inserted_id:
                return {'success': True, 'inserted_id': str(result.inserted_id)}
            else:
                return {'error': "Échec de l'insertion de l'abonnement"}
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'abonnement: {e}")
            return {'error': str(e)}
    
    def update_subscription(self, subscription_id, subscription_data):
        """
        Met à jour un abonnement existant dans la base de données MongoDB
        """
        try:
            if self.db is None:
                return {'error': 'Impossible de se connecter à la base de données'}
            
            # Vérifier si la collection subscriptions existe
            if 'subscriptions' not in self.db.list_collection_names():
                return {'error': "La collection 'subscriptions' n'existe pas"}
            
            # Convertir l'ID utilisateur en ObjectId si nécessaire
            if 'user_id' in subscription_data:
                subscription_data['user'] = ObjectId(subscription_data['user_id'])
                del subscription_data['user_id']
            
            # Convertir les dates en objets datetime si elles sont fournies sous forme de chaînes
            if 'startDate' in subscription_data and isinstance(subscription_data['startDate'], str):
                subscription_data['startDate'] = datetime.fromisoformat(subscription_data['startDate'].replace('Z', '+00:00'))
            
            if 'endDate' in subscription_data and isinstance(subscription_data['endDate'], str):
                subscription_data['endDate'] = datetime.fromisoformat(subscription_data['endDate'].replace('Z', '+00:00'))
            
            # Ajouter un timestamp de mise à jour
            subscription_data['updatedAt'] = datetime.now()
            
            # Mise à jour de l'abonnement
            result = self.db.subscriptions.update_one(
                {'_id': ObjectId(subscription_id)},
                {'$set': subscription_data}
            )
            
            if result.modified_count > 0:
                return {'success': True, 'modified_count': result.modified_count}
            else:
                return {'error': "Aucune modification effectuée ou abonnement non trouvé"}
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'abonnement: {e}")
            return {'error': str(e)}
    
    def delete_subscription(self, subscription_id):
        """
        Supprime un abonnement de la base de données MongoDB
        """
        try:
            if self.db is None:
                return {'error': 'Impossible de se connecter à la base de données'}
            
            # Vérifier si la collection subscriptions existe
            if 'subscriptions' not in self.db.list_collection_names():
                return {'error': "La collection 'subscriptions' n'existe pas"}
            
            # Suppression de l'abonnement
            result = self.db.subscriptions.delete_one({'_id': ObjectId(subscription_id)})
            
            if result.deleted_count > 0:
                return {'success': True, 'deleted_count': result.deleted_count}
            else:
                return {'error': "Aucun abonnement supprimé ou abonnement non trouvé"}
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'abonnement: {e}")
            return {'error': str(e)}
    
    def get_subscription_by_id(self, subscription_id):
        """
        Récupère un abonnement spécifique par son ID
        """
        try:
            if self.db is None:
                return None
            
            # Vérifier si la collection subscriptions existe
            if 'subscriptions' not in self.db.list_collection_names():
                return None
                
            subscription = self.db.subscriptions.find_one({'_id': ObjectId(subscription_id)})
            
            if subscription:
                # Récupérer les informations de l'utilisateur
                user_info = {}
                if 'user' in subscription:
                    user = self.db.users.find_one({'_id': ObjectId(subscription['user'])})
                    if user:
                        user_info = {
                            'id': str(user.get('_id', '')),
                            'firstname': user.get('firstname', ''),
                            'lastname': user.get('lastname', ''),
                            'phoneNumber': user.get('phoneNumber', ''),
                            'status': user.get('status', '')  # Ajout du statut utilisateur
                        }
                
                formatted_sub = {
                    'id': str(subscription.get('_id', '')),
                    'user': user_info,
                    'plan': subscription.get('plan', ''),
                    'status': subscription.get('status', ''),
                    'startDate': subscription.get('startDate', ''),
                    'endDate': subscription.get('endDate', ''),
                    'price': subscription.get('price', 0),
                    'paymentMethod': subscription.get('paymentMethod', ''),
                    'createdAt': subscription.get('createdAt', ''),
                    'updatedAt': subscription.get('updatedAt', '')
                }
                return formatted_sub
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération de l'abonnement {subscription_id}: {e}")
            return None
    
    def get_feedbacks(self):
        try:
            if self.db is None:
                return []
                
            # Vérifier si la collection feedbacks existe
            if 'feedbacks' not in self.db.list_collection_names():
                print("La collection 'feedbacks' n'existe pas dans la base de données")
                return []
                
            feedbacks = list(self.db.feedbacks.find({}))
            
            formatted_feedbacks = []
            for feedback in feedbacks:
                # Récupérer les informations de l'utilisateur
                user_info = {}
                if 'user' in feedback:
                    user = self.db.users.find_one({'_id': ObjectId(feedback['user'])})
                    if user:
                        user_info = {
                            'id': str(user.get('_id', '')),
                            'firstname': user.get('firstname', ''),
                            'lastname': user.get('lastname', ''),
                            'phoneNumber': user.get('phoneNumber', ''),
                            'status': user.get('status', '')  # Ajout du statut utilisateur
                        }
                
                formatted_feedback = {
                    'id': str(feedback.get('_id', '')),
                    'user': user_info,
                    'rating': feedback.get('rating', 0),
                    'message': feedback.get('message', ''),  # Utiliser 'message' au lieu de 'comment'
                    'category': feedback.get('category', ''),
                    'createdAt': feedback.get('createdAt', ''),  # Ne pas convertir en ISO
                    'updatedAt': feedback.get('updatedAt', '')  # Ne pas convertir en ISO
                }
                formatted_feedbacks.append(formatted_feedback)
            
            return formatted_feedbacks
        except Exception as e:
            print(f"Erreur lors de la récupération des feedbacks: {e}")
            return []
    
    def get_subscription_stats(self):
        try:
            if self.db is None:
                return {'total': 0, 'active': 0, 'expired': 0, 'canceled': 0}
                
            # Vérifier si la collection subscriptions existe
            if 'subscriptions' not in self.db.list_collection_names():
                return {'total': 0, 'active': 0, 'expired': 0, 'canceled': 0}
                
            # Utiliser l'agrégation MongoDB pour des statistiques précises
            pipeline = [
                {
                    '$group': {
                        '_id': '$status',
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            stats = list(self.db.subscriptions.aggregate(pipeline))
            
            # Convertir en format plus utilisable
            result = {'total': 0, 'active': 0, 'expired': 0, 'canceled': 0}
            for stat in stats:
                result['total'] += stat['count']
                if stat['_id'] == 'active':
                    result['active'] = stat['count']
                elif stat['_id'] == 'expired':
                    result['expired'] = stat['count']
                elif stat['_id'] == 'canceled':
                    result['canceled'] = stat['count']
            
            return result
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques d'abonnements: {e}")
            subscriptions = self.get_subscriptions()
            return {
                'total': len(subscriptions),
                'active': len([s for s in subscriptions if s.get('status') == 'active']),
                'expired': len([s for s in subscriptions if s.get('status') == 'expired']),
                'canceled': len([s for s in subscriptions if s.get('status') == 'canceled']),
            }
    
    def get_feedback_stats(self):
        try:
            if self.db is None:
                return {'total': 0, 'positive': 0, 'neutral': 0, 'negative': 0}
                
            # Vérifier si la collection feedbacks existe
            if 'feedbacks' not in self.db.list_collection_names():
                return {'total': 0, 'positive': 0, 'neutral': 0, 'negative': 0}
                
            # Utiliser l'agrégation MongoDB pour des statistiques précises
            pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'total': {'$sum': 1},
                        'positive': {
                            '$sum': {'$cond': [{'$gte': ['$rating', 4]}, 1, 0]}
                        },
                        'neutral': {
                            '$sum': {'$cond': [
                                {'$and': [
                                    {'$gte': ['$rating', 3]},
                                    {'$lt': ['$rating', 4]}
                                ]}, 1, 0]
                            }
                        },
                        'negative': {
                            '$sum': {'$cond': [{'$lt': ['$rating', 3]}, 1, 0]}
                        }
                    }
                }
            ]
            
            stats = list(self.db.feedbacks.aggregate(pipeline))
            
            if stats:
                return {
                    'total': stats[0]['total'],
                    'positive': stats[0]['positive'],
                    'neutral': stats[0]['neutral'],
                    'negative': stats[0]['negative']
                }
            else:
                return {'total': 0, 'positive': 0, 'neutral': 0, 'negative': 0}
        except Exception as e:
            print(f"Erreur lors du calcul des statistiques de feedbacks: {e}")
            feedbacks = self.get_feedbacks()
            return {
                'total': len(feedbacks),
                'positive': len([f for f in feedbacks if f.get('rating', 0) >= 4]),
                'neutral': len([f for f in feedbacks if 3 <= f.get('rating', 0) < 4]),
                'negative': len([f for f in feedbacks if f.get('rating', 0) < 3]),
            }
    
    def get_recent_activity(self, limit=10):
        try:
            if self.db is None:
                return []
                
            # Vérifier si la collection activities existe
            if 'activities' not in self.db.list_collection_names():
                return []
                
            # Cette méthode suppose que vous avez a collection pour les activités
            activities = list(self.db.activities.find({}).sort('timestamp', -1).limit(limit))
            
            formatted_activities = []
            for activity in activities:
                formatted_activity = {
                    'id': str(activity.get('_id', '')),
                    'type': activity.get('type', ''),
                    'description': activity.get('description', ''),
                    'timestamp': activity.get('timestamp', ''),  # Ne pas convertir en ISO
                    'user': activity.get('user', '')
                }
                formatted_activities.append(formatted_activity)
            
            return formatted_activities
        except Exception as e:
            print(f"Erreur lors de la récupération des activités: {e}")
            return []
    
    def get_user_by_id(self, user_id):
        try:
            if self.db is None:
                return None
                
            user = self.db.users.find_one({'_id': ObjectId(user_id)})
            if user:
                return {
                    'id': str(user.get('_id', '')),
                    'phoneNumber': user.get('phoneNumber', ''),
                    'firstname': user.get('firstname', ''),
                    'lastname': user.get('lastname', ''),
                    'region': user.get('region', ''),
                    'status': user.get('status', ''),
                    'createdAt': user.get('createdAt', '')  # Ne pas convertir en ISO
                }
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération de l'utilisateur {user_id}: {e}")
            return None
    
    def get_box_by_id(self, box_id):
        try:
            if self.db is None:
                return None
                
            # Vérifier si la collection boxes existe
            if 'boxes' not in self.db.list_collection_names():
                return None
                
            box = self.db.boxes.find_one({'_id': ObjectId(box_id)})
            if box:
                # Gérer le champ user qui peut être un ObjectId ou un document populé
                user_info = box.get('user', {})
                if isinstance(user_info, ObjectId):
                    user = self.db.users.find_one({'_id': user_info})
                    user_info = {
                        'id': str(user.get('_id', '')),
                        'firstname': user.get('firstname', ''),
                        'lastname': user.get('lastname', ''),
                        'phoneNumber': user.get('phoneNumber', ''),
                        'status': user.get('status', '')  # Ajout du statut utilisateur
                    } if user else {}
                
                return {
                    'id': str(box.get('_id', '')),
                    'status': box.get('status', ''),
                    'user': user_info,
                    'lastActivity': box.get('lastActivity', ''),  # Ne pas convertir en ISO
                    'createdAt': box.get('createdAt', '')  # Ne pas convertir en ISO
                }
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération de la boîte {box_id}: {e}")
            return None
    
    def update_user_status(self, user_id, status):
        try:
            if self.db is None:
                return False, "Base de données non connectée"
                
            if status not in ['pending_box', 'active', 'suspended']:
                return False, "Statut invalide"
            
            result = self.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'status': status}}
            )
            
            return result.modified_count > 0, "Statut mis à jour avec succès" if result.modified_count > 0 else "Aucune modification"
        except Exception as e:
            print(f"Erreur lors de la mise à jour du statut utilisateur: {e}")
            return False, f"Erreur: {str(e)}"
    
    def update_box_status(self, box_id, status):
        try:
            if self.db is None:
                return False, "Base de données non connectée"
                
            # Vérifier si la collection boxes existe
            if 'boxes' not in self.db.list_collection_names():
                return False, "La collection 'boxes' n'existe pas"
                
            if status not in ['active', 'inactive', 'maintenance']:
                return False, "Statut invalide"
            
            result = self.db.boxes.update_one(
                {'_id': ObjectId(box_id)},
                {'$set': {'status': status}}
            )
            return result.modified_count > 0, "Statut mis à jour avec succès" if result.modified_count > 0 else "Aucune modification"
        except Exception as e:
            print(f"Erreur lors de la mise à jour du statut de la boîte: {e}")
            return False, f"Erreur: {str(e)}"
    
    def get_user_boxes(self, user_id):
        try:
            if self.db is None:
                return []
                
            # Vérifier si la collection boxes existe
            if 'boxes' not in self.db.list_collection_names():
                return []
                
            boxes = list(self.db.boxes.find({'user': ObjectId(user_id)}))
            
            formatted_boxes = []
            for box in boxes:
                formatted_box = {
                    'id': str(box.get('_id', '')),
                    'status': box.get('status', ''),
                    'lastActivity': box.get('lastActivity', ''),  # Ne pas convertir en ISO
                    'createdAt': box.get('createdAt', '')  # Ne pas convertir en ISO
                }
                formatted_boxes.append(formatted_box)
            
            return formatted_boxes
        except Exception as e:
            print(f"Erreur lors de la récupération des boîtes de l'utilisateur {user_id}: {e}")
            return []
    
    def search_users(self, query):
        try:
            if self.db is None:
                return []
                
            # Recherche par nom, prénom, téléphone ou région
            users = list(self.db.users.find({
                '$or': [
                    {'firstname': {'$regex': query, '$options': 'i'}},
                    {'lastname': {'$regex': query, '$options': 'i'}},
                    {'phoneNumber': {'$regex': query, '$options': 'i'}},
                    {'region': {'$regex': query, '$options': 'i'}}
                ]
            }))
            
            formatted_users = []
            for user in users:
                formatted_user = {
                    'id': str(user.get('_id', '')),
                    'phoneNumber': user.get('phoneNumber', ''),
                    'firstname': user.get('firstname', ''),
                    'lastname': user.get('lastname', ''),
                    'region': user.get('region', ''),
                    'status': user.get('status', ''),
                    'createdAt': user.get('createdAt', '')  # Ne pas convertir en ISO
                }
                formatted_users.append(formatted_user)
            
            return formatted_users
        except Exception as e:
            print(f"Erreur lors de la recherche d'utilisateurs: {e}")
            return []
    
    def search_boxes(self, query):
        try:
            if self.db is None:
                return []
                
            # Vérifier si la collection boxes existe
            if 'boxes' not in self.db.list_collection_names():
                return []
                
            # Recherche par nom, localisation ou statut
            boxes = list(self.db.boxes.find({
                '$or': [
                    {'name': {'$regex': query, '$options': 'i'}},
                    {'location': {'$regex': query, '$options': 'i'}},
                    {'status': {'$regex': query, '$options': 'i'}}
                ]
            }))
            
            formatted_boxes = []
            for box in boxes:
                # Gérer le champ user qui peut être un ObjectId ou un document populé
                user_info = box.get('user', {})
                if isinstance(user_info, ObjectId):
                    user = self.db.users.find_one({'_id': user_info})
                    user_info = {
                        'id': str(user.get('_id', '')),
                        'firstname': user.get('firstname', ''),
                        'lastname': user.get('lastname', ''),
                        'phoneNumber': user.get('phoneNumber', ''),
                        'status': user.get('status', '')  # Ajout du statut utilisateur
                    } if user else {}
                
                formatted_box = {
                    'id': str(box.get('_id', '')),
                    'status': box.get('status', ''),
                    'user': user_info,
                    'lastActivity': box.get('lastActivity', ''),  # Ne pas convertir en ISO
                    'createdAt': box.get('createdAt', '')  # Ne pas convertir en ISO
                }
                formatted_boxes.append(formatted_box)
            
            return formatted_boxes
        except Exception as e:
            print(f"Erreur lors de la recherche de boîtes: {e}")
            return []


# Ancienne classe conservée pour référence (peut être supprimée)
class NodeAPIService:
    def __init__(self):
        self.base_url = settings.NODE_API_URL
        self.token = settings.NODE_API_TOKEN
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}' if self.token else ''
        }
    
    def _make_request(self, method, endpoint, data=None, params=None):
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                return None
                
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"Erreur API Node.js: {e}")
            return None
    
    def get_users(self):
        return []
    
    def get_boxes(self):
        return []
    
    def get_user_stats(self):
        users = self.get_users()
        return {
            'total': len(users),
            'active': len([u for u in users if u.get('status') == 'active']),
            'pending': len([u for u in users if u.get('status') == 'pending_box']),
        }
    
    def get_box_stats(self):
        boxes = self.get_boxes()
        return {
            'total': len(boxes),
            'active': len([b for b in boxes if b.get('status') == 'active']),
        }

# Fonction utilitaire pour obtenir le service approprié
def get_db_service():
    # Retourne toujours MongoDBService puisque nous utilisons directement MongoDB
    return MongoDBService()