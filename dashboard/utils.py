from .services.node_api import MongoDBService, NodeAPIService
import os

def get_api_service():
    # Utiliser MongoDB directement par défaut
    use_direct_mongo = os.environ.get('USE_DIRECT_MONGO', 'True').lower() == 'true'
    
    if use_direct_mongo:
        try:
            return MongoDBService()
        except Exception as e:
            print(f"Erreur de connexion à MongoDB: {e}")
            print("Fallback vers NodeAPIService")
            return NodeAPIService()
    else:
        return NodeAPIService()