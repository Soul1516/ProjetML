# 🏥 Documentation Complète - Système de Détection de Tumeurs Cérébrales

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Le Notebook d'Entraînement](#le-notebook-dentraînement)
3. [L'Extracteur de Caractéristiques](#lextracteur-de-caractéristiques)
4. [Le Prédicteur de Modèle](#le-prédicteur-de-modèle)
5. [L'Application Chatbot](#lapplication-chatbot)
6. [Guide d'Utilisation](#guide-dutilisation)
7. [Dépannage](#dépannage)

---

## 🎯 Vue d'ensemble

### Qu'est-ce que ce projet ?

Ce projet est un **système d'aide au diagnostic médical** qui analyse des images IRM du cerveau pour :
- **Détecter** la présence de tumeurs cérébrales
- **Classifier** le type de tumeur (gliome, méningiome, pituitaire, ou pas de tumeur)
- **Évaluer le risque** pour le patient

### Les 4 Classes de Tumeurs

| Classe | Description | Niveau de Risque |
|--------|-------------|------------------|
| **Gliome** | Tumeur agressive des cellules gliales | 🔴 Élevé |
| **Méningiome** | Tumeur des méninges, souvent bénigne | 🟡 Moyen |
| **Pituitaire** | Tumeur de l'hypophyse, souvent traitable | 🟡 Moyen |
| **Pas de tumeur** | Cerveau normal, pas de tumeur détectée | 🟢 Faible |

### Architecture du Système

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Image IRM      │ --> │  Extraction de   │ --> │  Prédiction     │
│  (Upload)       │     │  Caractéristiques│     │  (Modèle RLT)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          v
                                                 ┌─────────────────┐
                                                 │  Résultat +     │
                                                 │  Niveau Risque  │
                                                 └─────────────────┘
```

---

## 📓 Le Notebook d'Entraînement

### Fichier : `notebookfee462a95e (2).ipynb`

### Objectif
Entraîner un modèle de Machine Learning capable de classifier les tumeurs cérébrales avec ~78% de précision.

### Étapes d'Entraînement

#### 1. Chargement des Données
```
Training/
├── glioma/      (images de gliomes)
├── meningioma/  (images de méningiomes)
├── pituitary/   (images de tumeurs pituitaires)
└── notumor/     (images sans tumeur)
```

#### 2. Prétraitement des Images
- **Redimensionnement** : Toutes les images sont redimensionnées à 256x256 pixels
- **Normalisation** : Les valeurs de pixels sont normalisées (moyenne=0, écart-type=1)
- **Segmentation Watershed** : Détection automatique des régions tumorales

#### 3. Extraction des Caractéristiques (Radiomics)
Le système extrait **6 caractéristiques clés** de chaque image :

| Caractéristique | Description | Importance |
|-----------------|-------------|------------|
| `diagnostics_Image-original_Mean` | Luminosité moyenne de l'image | Moyenne |
| `diagnostics_Mask-original_VoxelNum` | Nombre de pixels dans le masque (taille de la région) | ⭐ Très importante |
| `diagnostics_Mask-original_VolumeNum` | Nombre de régions connectées | ⭐ Très importante |
| `original_shape_Elongation` | Forme : ronde (0.5) vs allongée (1.0) | Importante |
| `original_shape_MajorAxisLength` | Longueur du plus grand axe | Importante |
| `original_shape_MinorAxisLength` | Longueur du plus petit axe | Importante |

#### 4. Entraînement du Modèle "Warm Start RLT"
- **Type** : Ensemble de 50 arbres de décision
- **Méthode** : Reinforcement Learning Trees (RLT)
- **Précision** : ~78%

#### 5. Fichiers Générés

| Fichier | Contenu |
|---------|---------|
| `warm_start_rlt_model.pkl` | Le modèle entraîné (50 arbres) |
| `scaler.pkl` | Le normaliseur pour les 6 caractéristiques |
| `selected_features.json` | Liste des caractéristiques sélectionnées |

---

## 🔬 L'Extracteur de Caractéristiques

### Fichier : `feature_extractor.py`

### Classe : `RadiomicsFeatureExtractor`

### Comment ça marche ?

#### Étape 1 : Chargement de l'Image
```python
# L'image est chargée et convertie en niveaux de gris
image = Image.open(chemin_image).convert('L')
```

#### Étape 2 : Prétraitement
```python
# Redimensionnement à 256x256
image = cv2.resize(image, (256, 256))

# Normalisation
moyenne = image.mean()
ecart_type = image.std()
image_normalisee = (image - moyenne) / ecart_type
```

#### Étape 3 : Segmentation Watershed

**Objectif** : Trouver la région tumorale (zones brillantes)

```
Image Originale     -->    Masque Watershed
┌─────────────┐           ┌─────────────┐
│   ░░░░░░░   │           │   ░░░░░░░   │
│  ░░████░░░  │    -->    │   ░████░░   │
│  ░░████░░░  │           │   ░████░░   │
│   ░░░░░░░   │           │   ░░░░░░░   │
└─────────────┘           └─────────────┘
      Tumeur                  Masque
```

**Algorithme** :
1. Créer un masque du cerveau (seuil Otsu)
2. Identifier les zones claires (> 85e percentile) = tumeur potentielle
3. Identifier les zones sombres (< 30e percentile) = fond
4. Appliquer l'algorithme Watershed pour séparer les régions

#### Étape 4 : Extraction des Caractéristiques PyRadiomics
```python
# Utilisation de la bibliothèque PyRadiomics
caracteristiques = extractor.execute(image_sitk, masque_sitk)
```

### Valeurs Typiques par Classe

| Caractéristique | Gliome | Méningiome | Pituitaire | Pas de tumeur |
|-----------------|--------|------------|------------|---------------|
| VoxelNum | 3,400-5,100 | 2,800-5,200 | 4,400-6,500 | 10,000-40,000 |
| VolumeNum | 5-29 | 4-20 | 9-30 | 1-2 |
| MajorAxis | 240-277 | 200-260 | 255-335 | 215-260 |
| MinorAxis | 200-228 | 150-220 | 220-280 | 155-225 |

---

## 🤖 Le Prédicteur de Modèle

### Fichier : `model_predictor.py`

### Classe : `CancerStagePredictor`

### Comment fonctionne la prédiction ?

#### Méthode 1 : Prédiction par Arbres (40%)

Le modèle contient **50 arbres de décision**. Chaque arbre :
1. Prend les 6 caractéristiques en entrée
2. Parcourt ses branches selon les valeurs
3. Retourne une probabilité pour chaque classe

```
                    Arbre de Décision
                          │
              ┌───────────┴───────────┐
        VoxelNum <= 5000?       VoxelNum > 5000?
              │                       │
        ┌─────┴─────┐           ┌─────┴─────┐
   Elongation?   Elongation?   Tumeur      Pas de
        │            │                     tumeur
      Gliome    Méningiome
```

#### Méthode 2 : Score par Caractéristiques (60%)

Basé sur les plages de valeurs typiques de chaque classe :

```python
# Exemple : Si VoxelNum > 10,000 → probablement "Pas de tumeur"
# Exemple : Si MajorAxis > 280 → probablement "Pituitaire"
```

#### Combinaison Finale

```
Probabilité Finale = 40% × Prédiction_Arbres + 60% × Score_Caractéristiques
```

### Exemple de Sortie

```
=== Analyse des Caractéristiques ===
  VoxelNum: 4500
  VolumeNum: 15
  MajorAxis: 245.3
  MinorAxis: 198.7
  Elongation: 0.81

=== Scores par Caractéristiques ===
  meningioma: 8
  glioma: 6
  pituitary: 4
  notumor: 2

=== Prédiction Finale ===
  PRÉDIT: meningioma (67.3%)
```

---

## 💬 L'Application Chatbot

### Fichier : `app.py`

### Technologies Utilisées
- **Streamlit** : Interface web interactive
- **Mistral AI** : LLM pour analyse clinique avancée (Objectif Métier: Médecin)
- **OpenAI/LangChain** (optionnel) : Réponses conversationnelles avancées

### Modules Principaux

#### 1. Système d'Aide à la Décision Médicale (`medical_decision_support.py`)
**Objectif Métier: Médecin**

- **Recommandations cliniques structurées** basées sur le type de tumeur
- **Analyse LLM avancée** utilisant Mistral avec prompt engineering
- **Guidelines cliniques** pour chaque type de tumeur:
  - Recommandations d'imagerie
  - Spécialistes à consulter
  - Surveillance recommandée
  - Prochaines étapes cliniques
- **Adaptation contextuelle** selon l'âge, symptômes, et confiance du modèle

#### 2. Système d'Éducation Patient (`patient_education.py`)
**Objectif Métier: Patient**

- **Résumés patient-friendly** des résultats d'analyse
- **Contenu éducatif** sur les tumeurs cérébrales
- **Quiz de sensibilisation** pour tester les connaissances
- **Messages de motivation** quotidiens
- **Conseils du jour** pour la santé cérébrale
- **Calendrier des journées internationales** de santé
- **Ressources** et liens utiles

#### 3. Disclaimer Éthique (`EthicalAIDisclaimer`)
- **Avertissements légaux** et éthiques
- **Limitations du modèle** et responsabilités
- **Bonnes pratiques** d'utilisation
- **Conformité** RGPD et réglementations médicales

### Interface Utilisateur

```
┌─────────────────────────────────────────────────────────────┐
│  🏥 Assistant d'Analyse de Tumeurs Cérébrales              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  👤 Informations Patient (Optionnel)                        │
│  ┌─────────────┐  ┌─────────────┐                           │
│  │ Âge: [  ]   │  │ Sexe: [▼]  │                           │
│  └─────────────┘  └─────────────┘                           │
│  Symptômes: [ ] Maux de tête  [ ] Convulsions               │
│                                                              │
│  📤 Télécharger des Images                                  │
│  ┌─────────────────────────────────────────┐                │
│  │  Glisser-déposer vos images IRM ici     │                │
│  └─────────────────────────────────────────┘                │
│                                                              │
│  [🔍 Analyser les Images]                                   │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  📊 Résultats                                               │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ Image Orig.  │  │ Avec Masque  │                         │
│  └──────────────┘  └──────────────┘                         │
│                                                              │
│  Stade Prédit: MÉNINGIOME                                   │
│  Confiance: 67.3%                                           │
│  ⚠️ Risque: Moyen - Méningiome suspecté (généralement bénin)│
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  💬 Chat                                                    │
│  Vous: Que signifie ce résultat ?                          │
│  Bot: Le méningiome est une tumeur qui se développe...     │
└─────────────────────────────────────────────────────────────┘
```

### Fonctionnalités

#### Interface Médecin (Onglet 1)
1. **Formulaire Patient** : Âge, sexe, symptômes, historique médical
2. **Upload d'Images** : JPG, PNG, TIFF supportés
3. **Visualisation du Masque** : Voir la région détectée en rouge
4. **Statistiques** : Taille de la région, couverture cérébrale
5. **Graphique de Probabilités** : Distribution pour chaque classe
6. **Aide à la Décision Clinique** :
   - Recommandations d'imagerie
   - Spécialistes à consulter
   - Surveillance recommandée
   - Prochaines étapes
7. **Analyse LLM Mistral** : Analyse clinique avancée avec prompt engineering

#### Interface Patient (Onglet 2)
1. **Mes Résultats** : Résumé patient-friendly des prédictions
2. **Éducation** : Contenu éducatif sur les tumeurs cérébrales
3. **Quiz** : Quiz de sensibilisation interactif
4. **Motivation** : Messages motivants et conseils du jour
5. **Calendrier** : Journées internationales de santé

#### À Propos (Onglet 3)
1. **Disclaimer Éthique** : Avertissements et responsabilités
2. **Documentation** : Liens vers la documentation complète
3. **Configuration LLM** : Informations sur Mistral AI

---

## 📖 Guide d'Utilisation

### Installation

```bash
# 1. Créer un environnement virtuel
python -m venv .venv

# 2. Activer l'environnement
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. (Optionnel) Configurer la clé API Mistral
# Windows:
set MISTRAL_API_KEY=votre_cle_api
# Mac/Linux:
export MISTRAL_API_KEY=votre_cle_api
```

### Configuration Mistral AI

Pour activer l'analyse LLM avancée:

1. **Obtenir une clé API** : Créez un compte sur [Mistral AI](https://mistral.ai)
2. **Configurer la clé** :
   - Via variable d'environnement : `MISTRAL_API_KEY`
   - Via interface : Entrez la clé dans l'onglet Médecin
3. **Modèle utilisé** : `mistral-large-latest`
4. **Coûts** : Consultez la tarification Mistral AI

### Lancement de l'Application

```bash
streamlit run app.py
```

L'application sera accessible à : `http://localhost:8501`

### Étapes d'Analyse

#### Pour les Médecins (Onglet 1)

1. **Configurer Mistral API** (optionnel mais recommandé)
2. **Remplir les informations patient** : Âge, sexe, symptômes, historique
3. **Télécharger** une ou plusieurs images IRM
4. **Cliquer** sur "🔍 Analyser les Images"
5. **Examiner** les résultats :
   - Image originale vs masque de segmentation
   - Classe prédite et niveau de confiance
   - Statistiques de segmentation
6. **Consulter l'aide à la décision** :
   - Recommandations d'imagerie complémentaire
   - Spécialistes à consulter
   - Surveillance recommandée
   - Prochaines étapes cliniques
7. **Lire l'analyse LLM** (si Mistral configuré) pour une interprétation approfondie

#### Pour les Patients (Onglet 2)

1. **Consulter "Mes Résultats"** après analyse dans l'onglet Médecin
2. **Lire le contenu éducatif** sur les différents types de tumeurs
3. **Tester ses connaissances** avec le quiz de sensibilisation
4. **Consulter les conseils du jour** et messages de motivation
5. **Découvrir les journées internationales** de santé

---

## 🔧 Dépannage

### Problème : "Module not found"

```bash
# Solution : Installer les dépendances manquantes
pip install pyradiomics simpleitk scikit-image opencv-python
```

### Problème : Prédiction incorrecte

**Causes possibles** :
1. **Image de mauvaise qualité** : Utilisez des IRM haute résolution
2. **Mauvais type d'image** : Le modèle est entraîné sur des IRM cérébrales T1
3. **Orientation incorrecte** : L'image doit être orientée correctement

### Problème : Le masque couvre toute l'image

**Cause** : La segmentation n'a pas trouvé de tumeur distincte
**Solution** : Cela peut indiquer "Pas de tumeur" - c'est normal pour les cas sains

### Problème : Application lente

**Solution** :
```bash
# Vider le cache et redémarrer
# Windows:
rmdir /s /q __pycache__
streamlit run app.py
```

---

## 📁 Structure des Fichiers

```
ml/
├── app.py                    # Application Streamlit principale
├── feature_extractor.py      # Extraction des caractéristiques
├── model_predictor.py        # Prédiction avec le modèle
├── warm_start_rlt_model.pkl  # Modèle entraîné (50 arbres)
├── scaler.pkl                # Normaliseur pour les caractéristiques
├── selected_features.json    # Liste des caractéristiques
├── requirements.txt          # Dépendances Python
├── Training/                 # Images d'entraînement
│   ├── glioma/
│   ├── meningioma/
│   ├── pituitary/
│   └── notumor/
└── Testing/                  # Images de test
    ├── glioma/
    ├── meningioma/
    ├── pituitary/
    └── notumor/
```

---

## ⚠️ Avertissement Médical

**Ce système est un outil d'aide à la décision et NE REMPLACE PAS un diagnostic médical professionnel.**

- Les résultats doivent être confirmés par un radiologue qualifié
- Le modèle a une précision d'environ 78%, ce qui signifie qu'il peut se tromper
- Toujours consulter un médecin pour un diagnostic définitif

---

## 📞 Support

Pour toute question ou problème :
1. Vérifier la section [Dépannage](#dépannage)
2. Consulter les logs dans le terminal
3. Redémarrer l'application après modifications

---

## 🆕 Nouvelles Fonctionnalités (Version 2.0)

### 🎯 Objectifs Métier

#### 👨‍⚕️ Objectif Métier: Médecin

**Système d'Aide à la Décision Clinique**

Le système fournit aux médecins:

1. **Recommandations Structurées**
   - Basées sur les guidelines cliniques
   - Adaptées au type de tumeur détecté
   - Personnalisées selon l'âge et les symptômes du patient

2. **Analyse LLM avec Mistral**
   - **Modèle**: `mistral-large-latest`
   - **Prompt Engineering**: Prompts spécialisés pour l'analyse médicale
   - **Température**: 0.3 (cohérence médicale)
   - **Analyse contextuelle** incluant:
     - Interprétation de la prédiction
     - Facteurs de risque
     - Recommandations d'imagerie
     - Spécialistes à consulter
     - Prochaines étapes cliniques

3. **Guidelines par Type de Tumeur**
   - **Gliome**: Imagerie avancée, références multidisciplinaires
   - **Méningiome**: Évaluation résécabilité, surveillance
   - **Pituitaire**: Bilan hormonal, évaluation ophtalmologique
   - **Pas de tumeur**: Réassurance, suivi selon symptômes

#### 👤 Objectif Métier: Patient

**Système d'Éducation et Sensibilisation**

1. **Résumés Patient-Friendly**
   - Explications simples et accessibles
   - Mise en contexte des résultats
   - Prochaines étapes claires

2. **Contenu Éducatif**
   - Informations sur chaque type de tumeur
   - Symptômes et traitements
   - Ressources et liens utiles

3. **Quiz de Sensibilisation**
   - 5+ questions sur la santé cérébrale
   - Explications détaillées
   - Apprentissage interactif

4. **Motivation et Bien-être**
   - Messages motivants quotidiens
   - Conseils santé cérébrale
   - Calendrier des journées internationales

### ⚖️ Éthique et Conformité

**Disclaimer Éthique Complet**

- Avertissements légaux et responsabilités
- Limitations du modèle (78% précision)
- Bonnes pratiques d'utilisation
- Conformité RGPD
- Validation et certification

### 🔧 Configuration Technique

**Mistral AI Integration**

```python
# Configuration via variable d'environnement
export MISTRAL_API_KEY="votre_cle"

# Ou via interface Streamlit
# Onglet Médecin > Mistral API Key
```

**Prompt Engineering**

Le système utilise des prompts spécialisés:
- **System Prompt**: Définit le rôle (assistant médical spécialisé)
- **User Prompt**: Structure les données (prédiction, patient, contexte)
- **Temperature**: 0.3 pour cohérence médicale
- **Max Tokens**: 1000 pour analyses complètes

### 📊 Architecture des Modules

```
app.py
├── medical_decision_support.py
│   ├── MedicalDecisionSupport
│   │   ├── get_clinical_recommendations()
│   │   └── get_llm_analysis() [Mistral]
│   └── EthicalAIDisclaimer
│       └── get_disclaimer()
└── patient_education.py
    └── PatientEducation
        ├── get_patient_summary()
        ├── get_educational_content()
        ├── get_quiz()
        └── get_motivational_message()
```

---

*Documentation générée pour le projet de détection de tumeurs cérébrales*
*Version 2.0 - Décembre 2024*
*Ajout: Système d'aide à la décision médicale + Éducation patient + Éthique IA*
