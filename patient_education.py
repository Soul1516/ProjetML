"""
Système d'Éducation et Sensibilisation Patient
Objectif Métier: Patient
Inclut sensibilisation, conseils, journées internationales, quiz, motivation
"""

import random
from datetime import datetime
from typing import Dict, List, Tuple


class PatientEducation:
    """Système d'éducation et sensibilisation pour les patients"""
    
    def __init__(self):
        self.class_names_fr = {
            'glioma': 'Gliome',
            'meningioma': 'Méningiome',
            'pituitary': 'Tumeur Pituitaire',
            'notumor': 'Pas de Tumeur'
        }
        
        # Journées internationales de santé
        self.international_days = {
            'february': {
                '4': {
                    'name': 'Journée Mondiale contre le Cancer',
                    'description': 'Sensibilisation à la prévention et au dépistage du cancer'
                },
                '15': {
                    'name': 'Journée Internationale du Cancer de l\'Enfant',
                    'description': 'Soutien aux enfants atteints de cancer et à leurs familles'
                }
            },
            'march': {
                '22': {
                    'name': 'Journée Mondiale de l\'Eau',
                    'description': 'Importance de l\'hydratation pour la santé cérébrale'
                }
            },
            'april': {
                '7': {
                    'name': 'Journée Mondiale de la Santé',
                    'description': 'Promotion de la santé et du bien-être global'
                },
                '11': {
                    'name': 'Journée Mondiale de la Maladie de Parkinson',
                    'description': 'Sensibilisation aux troubles neurologiques'
                }
            },
            'may': {
                '25': {
                    'name': 'Journée Mondiale de la Sclérose en Plaques',
                    'description': 'Soutien aux personnes atteintes de SEP'
                }
            },
            'june': {
                '8': {
                    'name': 'Journée Mondiale des Tumeurs Cérébrales',
                    'description': 'Sensibilisation aux tumeurs cérébrales et à leurs traitements'
                }
            },
            'october': {
                '29': {
                    'name': 'Journée Mondiale de l\'Accident Vasculaire Cérébral',
                    'description': 'Prévention et reconnaissance des signes d\'AVC'
                }
            }
        }
        
        # Quiz de sensibilisation
        self.quiz_questions = [
            {
                'question': 'Quel est le principal facteur de risque modifiable pour les tumeurs cérébrales?',
                'options': [
                    'L\'exposition aux radiations',
                    'Le tabagisme',
                    'L\'âge avancé',
                    'Aucun facteur modifiable connu'
                ],
                'correct': 3,
                'explanation': 'Contrairement à d\'autres cancers, il n\'y a pas de facteurs de risque modifiables clairement établis pour la plupart des tumeurs cérébrales primaires.'
            },
            {
                'question': 'Quel symptôme est le plus fréquent dans les tumeurs cérébrales?',
                'options': [
                    'Maux de tête persistants',
                    'Convulsions',
                    'Troubles de la vision',
                    'Tous les symptômes ci-dessus peuvent survenir'
                ],
                'correct': 3,
                'explanation': 'Les symptômes varient selon la localisation de la tumeur. Maux de tête, convulsions, et troubles visuels sont tous des signes possibles.'
            },
            {
                'question': 'Quelle est la différence principale entre un gliome et un méningiome?',
                'options': [
                    'Le gliome est toujours malin, le méningiome toujours bénin',
                    'Le gliome provient des cellules gliales, le méningiome des méninges',
                    'Ils nécessitent le même traitement',
                    'Aucune différence'
                ],
                'correct': 1,
                'explanation': 'Les gliomes proviennent des cellules gliales du cerveau, tandis que les méningiomes se développent à partir des méninges (membranes entourant le cerveau).'
            },
            {
                'question': 'Quand faut-il consulter un médecin pour des maux de tête?',
                'options': [
                    'Jamais, les maux de tête sont normaux',
                    'Seulement si très intenses',
                    'Si nouveaux, persistants, ou accompagnés d\'autres symptômes neurologiques',
                    'Une fois par an pour contrôle'
                ],
                'correct': 2,
                'explanation': 'Des maux de tête nouveaux, persistants, ou accompagnés de symptômes neurologiques (nausées, troubles visuels, convulsions) nécessitent une évaluation médicale.'
            },
            {
                'question': 'Quelle est l\'importance du dépistage précoce?',
                'options': [
                    'Peu importante, les tumeurs cérébrales sont toujours fatales',
                    'Très importante, un traitement précoce améliore le pronostic',
                    'Seulement pour certains types de tumeurs',
                    'Le dépistage n\'est pas recommandé'
                ],
                'correct': 1,
                'explanation': 'Un diagnostic et un traitement précoces peuvent significativement améliorer le pronostic et la qualité de vie, même si le pronostic varie selon le type de tumeur.'
            }
        ]
    
    def get_patient_summary(self, prediction: Dict) -> str:
        """Génère un résumé patient-friendly des résultats"""
        predicted_stage = prediction.get('predicted_stage', 'unknown')
        confidence = prediction.get('confidence', 0.0)
        stage_fr = self.class_names_fr.get(predicted_stage, predicted_stage)
        
        summary = f"""
## 📊 Résultats de Votre Analyse

### Prédiction Principale
**Type détecté:** {stage_fr}
**Niveau de confiance:** {confidence*100:.1f}%

### ⚠️ Important à Comprendre

"""
        if predicted_stage == 'notumor':
            summary += """
✅ **Bonne nouvelle:** Aucune tumeur n'a été détectée dans votre IRM.

Cependant, si vous présentez des symptômes persistants, il est important de:
- Consulter votre médecin pour une évaluation clinique complète
- Considérer d'autres causes possibles de vos symptômes
- Maintenir un suivi médical régulier
"""
        else:
            summary += f"""
🔍 **Résultat de l'analyse IA:** Le système a détecté des caractéristiques suggérant un **{stage_fr.lower()}**.

### ⚠️ Ce que cela signifie:

1. **Ce n'est PAS un diagnostic définitif**
   - L'IA est un outil d'aide, pas un médecin
   - Seul un radiologue ou neurochirurgien peut confirmer le diagnostic
   - Une biopsie peut être nécessaire pour confirmation

2. **Prochaines étapes recommandées:**
   - Consultation avec votre médecin traitant
   - Discussion avec un spécialiste (neurochirurgien, oncologue)
   - Examens complémentaires si nécessaire

3. **Niveau de confiance:**
   - Confiance de {confidence*100:.1f}% signifie que le système est {'très confiant' if confidence > 0.7 else 'modérément confiant' if confidence > 0.5 else 'peu confiant'}
   - {'Un second avis est fortement recommandé' if confidence < 0.5 else 'Les résultats sont relativement fiables mais nécessitent validation médicale'}

### 💡 Rappel Important

Cette analyse est un **outil d'aide à la décision**. Elle ne remplace jamais:
- L'expertise d'un médecin qualifié
- Un examen clinique complet
- Votre jugement et celui de votre équipe médicale
"""
        
        return summary
    
    def get_educational_content(self, topic: str) -> Dict:
        """Retourne du contenu éducatif selon le sujet"""
        content = {
            'general': {
                'title': 'Comprendre les Tumeurs Cérébrales',
                'content': """
### Qu'est-ce qu'une Tumeur Cérébrale?

Une tumeur cérébrale est une masse de cellules anormales qui se développe dans le cerveau. 
Il existe deux types principaux:

1. **Tumeurs primaires:** Se développent directement dans le cerveau
2. **Tumeurs secondaires (métastases):** Provenant d'un cancer ailleurs dans le corps

### Symptômes Courants

- Maux de tête persistants ou nouveaux
- Convulsions
- Troubles de la vision
- Problèmes d'équilibre
- Changements de personnalité
- Troubles de la mémoire

### Importance du Diagnostic Précoce

Un diagnostic précoce permet:
- Un meilleur pronostic
- Plus d'options de traitement
- Une meilleure qualité de vie
                """,
                'resources': [
                    'Association pour la Recherche sur les Tumeurs Cérébrales (ARTC)',
                    'Ligue contre le Cancer',
                    'Institut National du Cancer (INCa)'
                ]
            },
            'glioma': {
                'title': 'Comprendre les Gliomes',
                'content': """
### Qu'est-ce qu'un Gliome?

Les gliomes sont des tumeurs qui se développent à partir des cellules gliales, 
qui soutiennent les neurones dans le cerveau.

### Types de Gliomes

- **Astrocytomes:** Les plus communs
- **Oligodendrogliomes:** Moins fréquents
- **Glioblastomes:** Les plus agressifs (grade IV)

### Traitements

- Chirurgie (si possible)
- Radiothérapie
- Chimiothérapie
- Thérapies ciblées

### Pronostic

Varie selon le grade (I à IV) et la localisation. 
Les gliomes de bas grade ont généralement un meilleur pronostic.
                """,
                'resources': [
                    'Société Française de Neurochirurgie',
                    'Groupe de Recherche sur les Gliomes'
                ]
            },
            'meningioma': {
                'title': 'Comprendre les Méningiomes',
                'content': """
### Qu'est-ce qu'un Méningiome?

Les méningiomes sont des tumeurs qui se développent à partir des méninges, 
les membranes qui entourent le cerveau et la moelle épinière.

### Caractéristiques

- **Souvent bénins** (non cancéreux)
- Croissance lente
- Peuvent être asymptomatiques pendant des années

### Traitements

- **Surveillance active:** Si petite taille et asymptomatique
- **Chirurgie:** Si symptomatique ou croissance
- **Radiothérapie:** Si résection incomplète

### Pronostic

Généralement excellent, surtout pour les méningiomes bénins.
                """,
                'resources': [
                    'Association des Méningiomes',
                    'Société Française de Neurochirurgie'
                ]
            },
            'pituitary': {
                'title': 'Comprendre les Tumeurs Pituitaires',
                'content': """
### Qu'est-ce qu'une Tumeur Pituitaire?

Les tumeurs pituitaires (adénomes) se développent dans l'hypophyse, 
une petite glande à la base du cerveau qui contrôle les hormones.

### Types

- **Fonctionnels:** Produisent des hormones en excès
- **Non-fonctionnels:** Ne produisent pas d'hormones

### Symptômes

- Troubles hormonaux
- Problèmes visuels (compression du chiasma optique)
- Maux de tête
- Fatigue

### Traitements

- **Médicaments:** Pour les tumeurs fonctionnelles
- **Chirurgie:** Approche transsphénoïdale (par le nez)
- **Radiothérapie:** Si nécessaire

### Pronostic

Très bon avec traitement approprié.
                """,
                'resources': [
                    'Association Française des Maladies de l\'Hypophyse',
                    'Société Française d\'Endocrinologie'
                ]
            },
            'prevention': {
                'title': 'Prévention et Bien-être Cérébral',
                'content': """
### Prévention des Tumeurs Cérébrales

Malheureusement, il n'y a pas de méthode prouvée pour prévenir les tumeurs cérébrales primaires.
Cependant, vous pouvez:

### Mode de Vie Sain

- **Alimentation équilibrée:** Fruits, légumes, grains entiers
- **Exercice régulier:** Au moins 30 min/jour
- **Sommeil suffisant:** 7-9 heures par nuit
- **Gestion du stress:** Méditation, yoga, relaxation

### Réduction des Risques

- Éviter l'exposition aux radiations inutiles
- Protéger la tête lors d'activités à risque
- Limiter l'exposition aux produits chimiques toxiques

### Dépistage

- Consulter rapidement en cas de symptômes nouveaux
- Examens réguliers si antécédents familiaux
- Surveillance après exposition aux radiations
                """,
                'resources': [
                    'Programme National Nutrition Santé (PNNS)',
                    'Santé Publique France'
                ]
            }
        }
        
        return content.get(topic, content['general'])
    
    def get_quiz(self, num_questions: int = 5) -> List[Dict]:
        """Retourne un quiz de sensibilisation"""
        return random.sample(self.quiz_questions, min(num_questions, len(self.quiz_questions)))
    
    def check_quiz_answer(self, question: Dict, answer_idx: int) -> Tuple[bool, str]:
        """Vérifie une réponse au quiz"""
        is_correct = answer_idx == question['correct']
        explanation = question['explanation']
        return is_correct, explanation
    
    def get_daily_tip(self) -> str:
        """Retourne un conseil du jour"""
        tips = [
            "💧 Buvez au moins 1.5L d'eau par jour pour maintenir une bonne hydratation cérébrale.",
            "🧠 Faites des exercices de mémoire: lisez, apprenez, jouez à des jeux de réflexion.",
            "😴 Le sommeil est essentiel: 7-9 heures par nuit permettent au cerveau de se régénérer.",
            "🥗 Une alimentation riche en oméga-3 (poissons, noix) favorise la santé cérébrale.",
            "🚶‍♂️ L'exercice physique améliore la circulation sanguine vers le cerveau.",
            "🧘‍♀️ La méditation et la relaxation réduisent le stress, bénéfique pour le cerveau.",
            "📱 Limitez le temps d'écran avant le coucher pour un meilleur sommeil.",
            "👥 Maintenez des relations sociales: elles stimulent le cerveau et réduisent l'isolement.",
            "🎵 La musique peut améliorer la fonction cognitive et l'humeur.",
            "📚 L'apprentissage continu maintient le cerveau actif et en bonne santé."
        ]
        return random.choice(tips)
    
    def get_motivational_message(self) -> str:
        """Retourne un message de motivation"""
        messages = [
            "🌟 Chaque jour est une nouvelle opportunité de prendre soin de votre santé.",
            "💪 Vous êtes plus fort que vous ne le pensez. Continuez à vous battre!",
            "🌈 Après la pluie vient le soleil. Gardez espoir et restez positif.",
            "🤝 Vous n'êtes pas seul. Une communauté de soutien vous entoure.",
            "🎯 Chaque petit pas vers la santé compte. Célébrez vos progrès!",
            "❤️ Prenez soin de vous. Votre bien-être est une priorité.",
            "🌱 La guérison est un processus. Soyez patient et bienveillant envers vous-même.",
            "✨ Votre force intérieure est remarquable. Continuez à briller!"
        ]
        return random.choice(messages)
    
    def get_today_awareness(self) -> Dict:
        """Retourne la journée internationale du jour si applicable"""
        today = datetime.now()
        month = today.strftime('%B').lower()
        day = str(today.day)
        
        if month in self.international_days and day in self.international_days[month]:
            return {
                'name': self.international_days[month][day]['name'],
                'message': self.international_days[month][day]['description']
            }
        return None
