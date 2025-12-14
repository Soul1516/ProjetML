# 🏥 Système de Détection de Tumeurs Cérébrales

## 🚀 Démarrage Rapide

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Lancement
```bash
streamlit run app.py
```

### 3. Utilisation
1. Ouvrir `http://localhost:8501`
2. Télécharger une image IRM
3. Cliquer "Analyser"
4. Voir les résultats !

---

## 📊 Ce que fait le système

| Entrée | Sortie |
|--------|--------|
| Image IRM du cerveau | Classification : Gliome, Méningiome, Pituitaire, ou Pas de tumeur |
| | Niveau de confiance (%) |
| | Évaluation du risque |

---

## 🧠 Les 4 Types de Tumeurs

| Type | Description | Risque |
|------|-------------|--------|
| 🔴 **Gliome** | Tumeur agressive | Élevé |
| 🟡 **Méningiome** | Souvent bénigne | Moyen |
| 🟡 **Pituitaire** | Traitable | Moyen |
| 🟢 **Pas de tumeur** | Normal | Faible |

---

## 📁 Fichiers Importants

| Fichier | Rôle |
|---------|------|
| `app.py` | Application web |
| `warm_start_rlt_model.pkl` | Modèle IA (50 arbres) |
| `scaler.pkl` | Normaliseur |
| `feature_extractor.py` | Analyse d'image |
| `model_predictor.py` | Prédiction |

---

## ⚠️ Attention

**Ceci n'est PAS un outil de diagnostic médical.**  
Consultez toujours un médecin pour un vrai diagnostic.

---

## 🔧 Problèmes Courants

| Problème | Solution |
|----------|----------|
| Module non trouvé | `pip install -r requirements.txt` |
| Application lente | Supprimer `__pycache__` et redémarrer |
| Mauvaise prédiction | Vérifier la qualité de l'image IRM |

---

*Pour plus de détails, voir `DOCUMENTATION_FR.md`*
