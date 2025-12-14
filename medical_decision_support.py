"""
Système d'Aide à la Décision Médicale
Objectif Métier: Médecin
Utilise Mistral LLM avec prompt engineering pour l'analyse clinique
"""

import os
from typing import Dict, List, Optional
from datetime import datetime


class MedicalDecisionSupport:
    """Système d'aide à la décision pour les médecins"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('MISTRAL_API_KEY', '')
        self.has_llm = bool(self.api_key)
        
        # Recommandations basées sur les types de tumeurs
        self.clinical_guidelines = {
            'glioma': {
                'imaging': [
                    "IRM avec contraste (T1, T2, FLAIR, DWI)",
                    "Spectroscopie IRM pour caractérisation métabolique",
                    "Perfusion IRM pour évaluation de la vascularisation",
                    "IRM fonctionnelle si localisation éloquente"
                ],
                'referrals': [
                    "Neurochirurgien (évaluation chirurgicale)",
                    "Oncologue médical (traitement systémique)",
                    "Radiothérapeute (planification radiothérapie)",
                    "Neurologue (prise en charge symptomatique)"
                ],
                'monitoring': [
                    "Surveillance IRM tous les 3 mois la première année",
                    "Évaluation clinique mensuelle",
                    "Suivi neuropsychologique si nécessaire",
                    "Surveillance des effets secondaires du traitement"
                ],
                'next_steps': [
                    "Biopsie stéréotaxique pour confirmation histologique",
                    "Évaluation de la résécabilité chirurgicale",
                    "Détermination du grade (I-IV selon WHO)",
                    "Planification multidisciplinaire du traitement"
                ],
                'urgency': 'high',
                'risk_factors': [
                    "Âge > 60 ans",
                    "Taille tumorale > 5cm",
                    "Localisation éloquente",
                    "Symptômes neurologiques sévères"
                ]
            },
            'meningioma': {
                'imaging': [
                    "IRM avec contraste (T1, T2)",
                    "IRM 3D haute résolution pour planification chirurgicale",
                    "Angio-IRM pour évaluation vasculaire",
                    "Scanner osseux si extension osseuse suspectée"
                ],
                'referrals': [
                    "Neurochirurgien (évaluation résection)",
                    "Radiothérapeute (si contre-indication chirurgicale)",
                    "Neurologue (suivi clinique)"
                ],
                'monitoring': [
                    "Surveillance IRM tous les 6 mois si asymptomatique",
                    "Surveillance annuelle si petite taille (< 2cm)",
                    "Évaluation clinique trimestrielle"
                ],
                'next_steps': [
                    "Évaluation de la résécabilité complète (Simpson grade)",
                    "Détermination du grade histologique (I-III)",
                    "Planification chirurgicale si symptomatique",
                    "Surveillance active si asymptomatique et petite taille"
                ],
                'urgency': 'medium',
                'risk_factors': [
                    "Taille > 3cm",
                    "Œdème périlésionnel",
                    "Symptômes neurologiques",
                    "Localisation parasagittale ou base du crâne"
                ]
            },
            'pituitary': {
                'imaging': [
                    "IRM hypophysaire haute résolution (séquences coronales et sagittales)",
                    "IRM avec contraste dynamique",
                    "Évaluation de l'extension suprasellaire",
                    "Angio-IRM pour relation avec carotides"
                ],
                'referrals': [
                    "Endocrinologue (évaluation hormonale complète)",
                    "Neurochirurgien (approche transsphénoïdale)",
                    "Ophtalmologiste (évaluation du champ visuel)",
                    "Radiothérapeute (si résection incomplète)"
                ],
                'monitoring': [
                    "Dosages hormonaux complets (prolactine, GH, ACTH, TSH, FSH, LH)",
                    "Champ visuel mensuel si compression chiasma",
                    "IRM de contrôle 3 mois post-opératoire",
                    "Surveillance endocrinienne à vie"
                ],
                'next_steps': [
                    "Bilan hormonal complet (matin, à jeun)",
                    "Évaluation ophtalmologique (acuité, champ visuel)",
                    "Détermination du type (fonctionnel vs non-fonctionnel)",
                    "Planification chirurgicale si nécessaire"
                ],
                'urgency': 'medium',
                'risk_factors': [
                    "Compression du chiasma optique",
                    "Déficit hormonal",
                    "Taille > 1cm (macroadénome)",
                    "Symptômes visuels"
                ]
            },
            'notumor': {
                'imaging': [
                    "Pas d'imagerie supplémentaire nécessaire si clinique rassurante",
                    "IRM de contrôle dans 6-12 mois si symptômes persistants",
                    "Évaluation alternative selon symptômes"
                ],
                'referrals': [
                    "Neurologue (si symptômes persistants)",
                    "Psychiatre (si troubles fonctionnels suspectés)"
                ],
                'monitoring': [
                    "Suivi clinique selon symptômes",
                    "Réassurance du patient"
                ],
                'next_steps': [
                    "Réassurance du patient",
                    "Traitement symptomatique si nécessaire",
                    "Suivi clinique selon évolution"
                ],
                'urgency': 'low',
                'risk_factors': []
            }
        }
    
    def get_clinical_recommendations(self, prediction: Dict, patient_info: Dict) -> Dict:
        """
        Génère des recommandations cliniques basées sur la prédiction
        
        Args:
            prediction: Résultat de prédiction du modèle
            patient_info: Informations du patient (âge, symptômes, etc.)
        
        Returns:
            Dict avec recommandations structurées
        """
        predicted_stage = prediction.get('predicted_stage', 'notumor')
        confidence = prediction.get('confidence', 0.0)
        
        # Récupérer les guidelines de base
        guidelines = self.clinical_guidelines.get(predicted_stage, self.clinical_guidelines['notumor']).copy()
        
        # Adapter selon la confiance
        if confidence < 0.5:
            guidelines['next_steps'].insert(0, 
                "⚠️ Confiance faible - Confirmation par biopsie ou second avis recommandé")
        
        # Adapter selon l'âge du patient
        age = patient_info.get('age')
        if age:
            if age > 60 and predicted_stage == 'glioma':
                guidelines['next_steps'].append(
                    "Considérer l'âge avancé dans la planification thérapeutique")
            elif age < 18:
                guidelines['referrals'].append("Pédiatre spécialisé en neuro-oncologie")
        
        # Adapter selon les symptômes
        symptoms = patient_info.get('symptoms', [])
        if 'Convulsions' in symptoms:
            guidelines['next_steps'].append("Évaluation EEG et traitement antiépileptique")
        if any('visuel' in s.lower() for s in symptoms):
            guidelines['referrals'].append("Ophtalmologiste (évaluation urgente)")
        
        return guidelines
    
    def get_llm_analysis(self, prediction: Dict, patient_info: Dict, context: str = "") -> str:
        """
        Analyse LLM avancée utilisant Mistral avec prompt engineering
        
        Args:
            prediction: Résultat de prédiction
            patient_info: Informations patient
            context: Contexte supplémentaire (masque, image, etc.)
        
        Returns:
            Analyse textuelle générée par LLM
        """
        if not self.has_llm:
            return "⚠️ Clé API Mistral non configurée. Configurez MISTRAL_API_KEY pour activer l'analyse LLM."
        
        try:
            from mistralai import Mistral
            
            client = Mistral(api_key=self.api_key)
            
            # Prompt engineering pour analyse médicale
            prompt = self._build_medical_prompt(prediction, patient_info, context)
            
            # Appel à l'API Mistral
            response = client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Basse température pour plus de cohérence médicale
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            return "⚠️ Bibliothèque mistralai non installée. Installez avec: pip install mistralai"
        except Exception as e:
            return f"⚠️ Erreur lors de l'analyse LLM: {str(e)}"
    
    def _get_system_prompt(self) -> str:
        """Prompt système pour guider le LLM"""
        return """Tu es un assistant médical spécialisé en neuro-oncologie. 
Tu fournis des analyses cliniques structurées, factuelles et basées sur les preuves.
Tu es prudent, mentionnes toujours les limitations de l'IA, et recommandes toujours 
la consultation d'un professionnel de santé qualifié pour un diagnostic définitif.
Tu utilises un langage médical approprié mais accessible."""
    
    def _build_medical_prompt(self, prediction: Dict, patient_info: Dict, context: str) -> str:
        """Construit le prompt médical structuré"""
        predicted_stage = prediction.get('predicted_stage', 'unknown')
        confidence = prediction.get('confidence', 0.0)
        probabilities = prediction.get('probabilities', {})
        
        prompt = f"""Analyse clinique d'un cas de tumeur cérébrale suspectée.

PRÉDICTION DU MODÈLE IA:
- Type prédit: {predicted_stage}
- Confiance: {confidence*100:.1f}%
- Distribution des probabilités:
"""
        for tumor_type, prob in probabilities.items():
            prompt += f"  - {tumor_type}: {prob*100:.1f}%\n"
        
        prompt += f"\nINFORMATIONS PATIENT:\n"
        if patient_info.get('age'):
            prompt += f"- Âge: {patient_info['age']} ans\n"
        if patient_info.get('gender'):
            prompt += f"- Sexe: {patient_info['gender']}\n"
        if patient_info.get('symptoms'):
            prompt += f"- Symptômes: {', '.join(patient_info['symptoms'])}\n"
        if patient_info.get('medical_history'):
            prompt += f"- Antécédents: {patient_info['medical_history']}\n"
        
        if context:
            prompt += f"\nCONTEXTE TECHNIQUE:\n{context}\n"
        
        prompt += """
TÂCHE:
Fournis une analyse clinique structurée incluant:
1. Interprétation de la prédiction (forces et limitations)
2. Facteurs de risque identifiés
3. Recommandations d'imagerie complémentaire
4. Spécialistes à consulter
5. Prochaines étapes cliniques
6. Points d'attention particuliers

Sois précis, factuel, et mentionne toujours que l'IA est un outil d'aide à la décision.
"""
        return prompt


class EthicalAIDisclaimer:
    """Disclaimer éthique pour l'utilisation de l'IA en médecine"""
    
    def __init__(self):
        self.disclaimer_text = self._generate_disclaimer()
    
    def get_disclaimer(self) -> str:
        """Retourne le disclaimer complet"""
        return self.disclaimer_text
    
    def _generate_disclaimer(self) -> str:
        """Génère le texte du disclaimer"""
        return """
## ⚠️ Avertissement Éthique et Légal - Intelligence Artificielle en Médecine

### 🎯 Objectif de l'Application

Cette application est un **outil d'aide à la décision** conçu pour assister les professionnels de santé dans l'analyse d'images IRM cérébrales. Elle ne remplace **JAMAIS** le jugement clinique d'un médecin qualifié.

### ⚖️ Limitations et Responsabilités

1. **Précision du Modèle**
   - Le modèle a une précision d'environ 78%
   - Des erreurs de classification sont possibles
   - Les résultats doivent être interprétés dans le contexte clinique global

2. **Pas de Diagnostic Définitif**
   - L'IA ne peut pas établir un diagnostic médical définitif
   - Tous les résultats doivent être validés par un radiologue ou neurochirurgien qualifié
   - Une biopsie histologique reste nécessaire pour confirmer le type de tumeur

3. **Responsabilité Médicale**
   - Le médecin traitant reste entièrement responsable des décisions cliniques
   - L'utilisation de cet outil n'exonère pas de la responsabilité médicale
   - Les recommandations générées sont indicatives, non prescriptives

4. **Données et Confidentialité**
   - Les images uploadées sont traitées localement ou via des API sécurisées
   - Respect du RGPD et des réglementations sur les données de santé
   - Aucune donnée n'est stockée sans consentement explicite

5. **Biais et Équité**
   - Le modèle peut présenter des biais liés aux données d'entraînement
   - Les performances peuvent varier selon les populations
   - Une vigilance particulière est requise pour les cas atypiques

### 📋 Bonnes Pratiques d'Utilisation

✅ **À FAIRE:**
- Utiliser comme outil complémentaire à l'expertise médicale
- Valider tous les résultats avec des méthodes diagnostiques standard
- Documenter l'utilisation de l'IA dans le dossier médical
- Former le personnel aux limitations de l'IA
- Maintenir une supervision humaine constante

❌ **À ÉVITER:**
- Remplacer l'expertise médicale par l'IA
- Prendre des décisions uniquement basées sur les prédictions IA
- Ignorer les signes cliniques contradictoires
- Utiliser sans formation appropriée
- Partager des données sans consentement

### 🔬 Validation et Certification

- Ce système n'est **PAS** un dispositif médical certifié
- Il est destiné à la recherche et au développement
- Une validation clinique approfondie est nécessaire avant utilisation en routine
- Conformité aux normes ISO 13485 et FDA (si applicable) requise pour usage clinique

### 📞 Contact et Support

Pour toute question éthique ou technique:
- Consulter la documentation complète (`DOCUMENTATION_FR.md`)
- Contacter l'équipe de développement
- Référencer les guidelines médicales officielles

### 📅 Dernière Mise à Jour

*Disclaimer généré le {date}*
""".format(date=datetime.now().strftime("%d/%m/%Y"))

