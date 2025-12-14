"""
Système d'Authentification par Rôles
Gestion des accès Patient vs Personnel Médical
"""

import hashlib
from typing import Optional, Dict


class RoleBasedAuth:
    """Gestion de l'authentification basée sur les rôles"""
    
    # Utilisateurs par défaut (en production, utiliser une base de données)
    DEFAULT_USERS = {
        'medecin': {
            'password_hash': hashlib.sha256('medecin123'.encode()).hexdigest(),
            'role': 'medical',
            'name': 'Dr. Amani Hassani',
            'email': 'amani.hassani@hospital.fr'
        },
        'patient': {
            'password_hash': hashlib.sha256('patient123'.encode()).hexdigest(),
            'role': 'patient',
            'name': 'Patient',
            'email': 'patient@example.com'
        },
        'admin': {
            'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
            'role': 'admin',
            'name': 'Administrateur',
            'email': 'admin@hospital.fr'
        }
    }
    
    def hash_password(self, password: str) -> str:
        """Hash un mot de passe"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authentifie un utilisateur et retourne les infos utilisateur"""
        if username in self.DEFAULT_USERS:
            user = self.DEFAULT_USERS[username]
            password_hash = self.hash_password(password)
            
            if password_hash == user['password_hash']:
                return {
                    'name': user['name'],
                    'email': user['email'],
                    'role': user['role'],
                    'username': username
                }
        return None
    
    def get_user_by_token(self, token: str) -> Optional[Dict]:
        """Récupère un utilisateur par token (simplifié pour démo)"""
        # En production, utiliser JWT ou sessions sécurisées
        # Pour la démo, on utilise simplement le username comme token
        if token in self.DEFAULT_USERS:
            user = self.DEFAULT_USERS[token]
            return {
                'name': user['name'],
                'email': user['email'],
                'role': user['role'],
                'username': token
            }
        return None
    
    def has_access(self, user_role: str, required_role: str) -> bool:
        """Vérifie si l'utilisateur a accès à une fonctionnalité"""
        if not user_role:
            return False
        
        # Admin a accès à tout
        if user_role == 'admin':
            return True
        
        # Vérification spécifique
        if required_role == 'medical':
            return user_role in ['medical', 'admin']
        elif required_role == 'patient':
            return user_role in ['patient', 'medical', 'admin']
        
        return False
