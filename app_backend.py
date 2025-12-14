"""
API Flask Backend pour l'Application d'Analyse de Tumeurs Cérébrales
Accès basé sur les rôles avec panneaux Médecin et Patient
"""

from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import base64
import numpy as np
from PIL import Image
import io
import pandas as pd
from pathlib import Path
import tempfile

from auth import RoleBasedAuth
from feature_extractor import RadiomicsFeatureExtractor
from model_predictor import CancerStagePredictor
from medical_decision_support import MedicalDecisionSupport, EthicalAIDisclaimer
from patient_education import PatientEducation


def convert_numpy_types(obj):
    """Convertit récursivement les types numpy en types Python natifs pour la sérialisation JSON"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, pd.Series):
        return convert_numpy_types(obj.to_dict())
    elif isinstance(obj, pd.DataFrame):
        return convert_numpy_types(obj.to_dict('records'))
    else:
        return obj


app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
CORS(app, supports_credentials=True)

# Initialize components
auth = RoleBasedAuth()
feature_extractor = RadiomicsFeatureExtractor()
predictor = CancerStagePredictor(model_dir='output')
medical_support = MedicalDecisionSupport(api_key=os.getenv('MISTRAL_API_KEY', ''))
patient_education = PatientEducation()
ethical_disclaimer = EthicalAIDisclaimer()

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tif', 'tiff', 'bmp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def image_to_base64(image_array):
    """Convertit un tableau numpy d'image en chaîne base64"""
    if image_array is None:
        print("Avertissement: image_array est None dans image_to_base64")
        return None
    try:
        # Handle different image array shapes
        if len(image_array.shape) == 3:
            img = Image.fromarray(image_array.astype(np.uint8))
        elif len(image_array.shape) == 2:
            img = Image.fromarray(image_array.astype(np.uint8), mode='L').convert('RGB')
        else:
            print(f"Avertissement: Forme d'image inattendue: {image_array.shape}")
            return None
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Erreur lors de la conversion de l'image en base64: {e}")
        import traceback
        traceback.print_exc()
        return None


@app.route('/')
def index():
    """Sert le fichier HTML principal"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/login', methods=['POST'])
def login():
    """Gère la connexion de l'utilisateur"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user_info = auth.authenticate(username, password)
    if user_info:
        session['user'] = user_info
        return jsonify({
            'success': True,
            'user': user_info
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Nom d\'utilisateur ou mot de passe invalide'
        }), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    """Gère la déconnexion de l'utilisateur"""
    session.pop('user', None)
    return jsonify({'success': True})


@app.route('/api/user', methods=['GET'])
def get_user():
    """Obtient les informations de l'utilisateur actuel"""
    user = session.get('user')
    if user:
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'user': None})


@app.route('/api/analyze', methods=['POST'])
def analyze_image():
    """Analyse l'image IRM et retourne la prédiction"""
    try:
        print("=== Point de terminaison d'analyse appelé ===")
        user = session.get('user')
        if not user:
            print("Erreur: Non authentifié")
            return jsonify({'error': 'Non authentifié'}), 401
        
        if not auth.has_access(user['role'], 'medical'):
            print(f"Erreur: Accès refusé pour le rôle {user['role']}")
            return jsonify({'error': 'Accès refusé'}), 403
        
        if 'image' not in request.files:
            print("Erreur: Aucun fichier image dans la requête")
            return jsonify({'error': 'Aucun fichier image fourni'}), 400
        
        files = request.files.getlist('image')
        if not files or all(f.filename == '' for f in files):
            print("Erreur: Aucun fichier image valide")
            return jsonify({'error': 'Aucun fichier image valide fourni'}), 400
        
        # Obtenir les informations du patient depuis le formulaire
        patient_info = {
            'age': request.form.get('age', type=int),
            'gender': request.form.get('gender'),
            'symptoms': request.form.getlist('symptoms'),
            'medical_history': request.form.get('medical_history')
        }
        
        all_results = []
        recommendations = None
        
        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                print(f"Avertissement: Fichier invalide: {file.filename}")
                continue
            
            try:
                # Sauvegarder le fichier téléchargé temporairement
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                    file.save(tmp_file.name)
                    tmp_path = tmp_file.name
                
                try:
                    # Obtenir la visualisation du masque
                    print(f"Traitement de l'image: {file.filename}")
                    original, mask, overlay = feature_extractor.get_mask_visualization(tmp_path, label='unknown')
                    
                    if original is None or overlay is None:
                        print(f"Avertissement: Échec de la génération de la visualisation pour {file.filename}")
                        continue  # Ignorer ce fichier et continuer avec le suivant
                    
                    # Extraire les caractéristiques
                    print(f"Extraction des caractéristiques de {file.filename}")
                    features = feature_extractor.extract_features(tmp_path, label='unknown')
                    
                    if not features:
                        print(f"Avertissement: Échec de l'extraction des caractéristiques de {file.filename}")
                        continue  # Ignorer ce fichier et continuer avec le suivant
                    
                    features_df = pd.DataFrame([features])
                    
                    # Obtenir la prédiction
                    print(f"Génération de la prédiction pour {file.filename}")
                    prediction = predictor.predict(features_df, patient_info=patient_info if patient_info.get('age') else None)
                    
                    if not prediction:
                        print(f"Avertissement: Échec de la génération de la prédiction pour {file.filename}")
                        continue  # Ignorer ce fichier et continuer avec le suivant

                    print(f"Prédiction réussie: {prediction.get('predicted_stage', 'inconnu')}")

                    # Calculer les statistiques du masque
                    mask_stats = {}
                    if mask is not None:
                        total_pixels = mask.shape[0] * mask.shape[1]
                        mask_pixels = np.sum(mask > 0)
                        mask_stats = {
                            'mask_area_pixels': int(mask_pixels),
                            'mask_percentage': round(mask_pixels / total_pixels * 100, 2),
                            'has_region': bool(mask_pixels > 100)
                        }
                    
                    # Obtenir les recommandations cliniques (seulement pour la première image)
                    if len(all_results) == 0:
                        recommendations = medical_support.get_clinical_recommendations(prediction, patient_info)
                    
                    # Convertir les images en base64
                    result = {
                        'filename': file.filename,
                        'prediction': prediction,
                        'mask_stats': mask_stats,
                        'images': {
                            'original': image_to_base64(original),
                            'overlay': image_to_base64(overlay)
                        }
                    }
                    
                    all_results.append(result)
                    
                finally:
                    # Nettoyer le fichier temporaire
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        
            except Exception as e:
                print(f"Erreur lors du traitement de {file.filename}: {e}")
                import traceback
                traceback.print_exc()
                # Ne peut pas utiliser 'continue' ici car nous sommes en dehors d'une boucle.
                # Au lieu de cela, ignorer l'ajout à all_results, donc la vérification ci-dessous déclenchera une erreur si vide.

        if not all_results:
            print("Erreur: Aucun résultat généré")
            return jsonify({'error': 'Échec du traitement des images. Veuillez vérifier que les images sont des scans IRM valides.'}), 500
        
        # Ajouter les recommandations au premier résultat
        if all_results and recommendations:
            all_results[0]['recommendations'] = recommendations
        
        # Convertir les types numpy en types Python natifs pour la sérialisation JSON
        all_results = convert_numpy_types(all_results)
        
        print(f"Succès: Retour de {len(all_results)} résultat(s)")
        return jsonify({'success': True, 'results': all_results})
        
    except Exception as e:
        print(f"Erreur fatale dans analyze_image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500


@app.route('/api/patient/education', methods=['GET'])
def get_patient_education():
    """Obtient le contenu éducatif pour les patients"""
    user = session.get('user')
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    topic = request.args.get('topic', 'general')
    content = patient_education.get_educational_content(topic)
    
    return jsonify({
        'success': True,
        'content': content
    })


@app.route('/api/patient/quiz', methods=['GET'])
def get_quiz():
    """Obtient les questions du quiz"""
    user = session.get('user')
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    num_questions = request.args.get('num', 5, type=int)
    questions = patient_education.get_quiz(num_questions)
    
    return jsonify({
        'success': True,
        'questions': questions
    })


@app.route('/api/patient/motivation', methods=['GET'])
def get_motivation():
    """Obtient le message de motivation"""
    user = session.get('user')
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    message = patient_education.get_motivational_message()
    tip = patient_education.get_daily_tip()
    
    return jsonify({
        'success': True,
        'message': message,
        'tip': tip
    })


@app.route('/api/patient/international-days', methods=['GET'])
def get_international_days():
    """Obtient les journées internationales de sensibilisation"""
    user = session.get('user')
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    month = request.args.get('month')
    if month and month in patient_education.international_days:
        days = patient_education.international_days[month]
        return jsonify({
            'success': True,
            'days': days
        })
    
    return jsonify({
        'success': True,
        'days': {}
    })


@app.route('/api/disclaimer', methods=['GET'])
def get_disclaimer():
    """Obtient l'avertissement éthique sur l'IA"""
    disclaimer = ethical_disclaimer.get_disclaimer()
    return jsonify({
        'success': True,
        'disclaimer': disclaimer
    })


@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    """Point de terminaison du chatbot Mistral (réservé pour une implémentation future)"""
    user = session.get('user')
    if not user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    # Espace réservé pour l'intégration du chatbot Mistral
    return jsonify({
        'success': False,
        'message': 'Fonctionnalité chatbot à venir. L\'intégration Mistral sera implémentée ici.'
    })


if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    print("=" * 60)
    print("Plateforme d'Analyse de Tumeurs Cérébrales")
    print("=" * 60)
    print("Démarrage du serveur Flask...")
    print("Accédez à l'application sur: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
