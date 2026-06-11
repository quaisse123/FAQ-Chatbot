# CodeAlpha — Plan des Tâches AI

> Guide simple et clair pour les 3 premières tâches

---

## TÂCHE 1 — Chatbot for FAQs

> Créer un chatbot qui répond aux questions fréquentes en trouvant la question la plus similaire à celle de l'utilisateur.

---

### Étape 1 : Préparer les FAQs

> **Énoncé** : Collecter des questions fréquentes liées à un sujet ou produit, et associer à chacune une réponse.

Créer une liste de paires question/réponse sur un thème de ton choix (école, produit, service...). Plus il y a de questions, meilleur sera le chatbot.

---

### Étape 2 : Installer les librairies NLP

> **Énoncé** : Utiliser des librairies NLP pour traiter et comparer du texte de façon mathématique.

Installer les outils nécessaires pour vectoriser le texte et calculer des similarités entre phrases.

---

### Étape 3 : Vectoriser les questions

> **Énoncé** : Transformer les questions textuelles en vecteurs numériques pour pouvoir les comparer entre elles.

Utiliser TF-IDF pour représenter chaque question comme un vecteur. Entraîner le vectoriseur sur la liste de questions préparée.

---

### Étape 4 : Trouver la meilleure réponse

> **Énoncé** : Comparer la question de l'utilisateur aux FAQs et retourner la réponse la plus pertinente.

Transformer la question de l'utilisateur avec le même vectoriseur, puis calculer la similarité cosinus avec toutes les FAQs. Retourner la réponse associée à la question la plus proche.

---

### Étape 5 : Créer une boucle de conversation

> **Énoncé** : Rendre le chatbot interactif en permettant à l'utilisateur de poser plusieurs questions à la suite.

Mettre le tout dans une boucle qui attend l'entrée de l'utilisateur, calcule la réponse et l'affiche, jusqu'à ce que l'utilisateur décide de quitter.

---

### Étape 6 (Optionnel) : Ajouter une interface graphique

> **Énoncé** : Créer une interface web ou desktop simple pour remplacer le terminal.

Utiliser Streamlit ou Tkinter pour afficher un champ de saisie et les réponses du bot dans une UI propre.

---

## TÂCHE 2 — Language Translation Tool

> Créer un outil de traduction de texte avec sélection de langue source et cible, en utilisant une API gratuite.

---

### Étape 1 : Choisir une API de traduction gratuite

> **Énoncé** : Identifier une solution de traduction qui ne nécessite ni clé API ni inscription.

Utiliser `deep-translator`, une librairie Python basée sur Google Translate, entièrement gratuite et sans configuration d'authentification.

---

### Étape 2 : Installer la librairie

> **Énoncé** : Installer l'outil de traduction dans l'environnement Python.

Installer `deep-translator` via pip en une seule commande.

---

### Étape 3 : Traduire un texte

> **Énoncé** : Effectuer une première traduction simple pour valider que tout fonctionne correctement.

Appeler le traducteur avec une langue source, une langue cible et un texte d'exemple. Vérifier que le résultat est correct.

---

### Étape 4 : Récupérer les langues disponibles

> **Énoncé** : Lister toutes les langues supportées pour permettre à l'utilisateur de choisir.

Récupérer dynamiquement la liste des langues disponibles et l'afficher à l'utilisateur comme options de sélection.

---

### Étape 5 : Construire l'interface utilisateur

> **Énoncé** : Permettre à l'utilisateur de saisir un texte, choisir les langues et voir la traduction s'afficher.

Créer un formulaire simple (terminal, Tkinter ou Streamlit) avec un champ texte, un sélecteur de langue source, un sélecteur de langue cible et un bouton de traduction.

---

### Étape 6 (Optionnel) : Ajouter la synthèse vocale

> **Énoncé** : Lire la traduction à voix haute après l'affichage pour améliorer l'expérience utilisateur.

Utiliser `pyttsx3` ou `gTTS` pour convertir le texte traduit en audio et le jouer automatiquement.

---

## TÂCHE 3 — Object Detection and Tracking

> Détecter et suivre des objets en temps réel à partir d'une webcam ou d'un fichier vidéo, avec affichage des boîtes et des IDs.

---

### Étape 1 : Installer les librairies

> **Énoncé** : Mettre en place l'environnement avec les outils de vision par ordinateur et de détection d'objets.

Installer `ultralytics` pour YOLOv8 et `opencv-python` pour la gestion de la vidéo.

---

### Étape 2 : Charger le modèle pré-entraîné

> **Énoncé** : Utiliser un modèle YOLO déjà entraîné sur des milliers d'images pour éviter tout entraînement manuel.

Charger YOLOv8n (nano), le modèle le plus léger. Il se télécharge automatiquement au premier appel, aucune configuration manuelle.

---

### Étape 3 : Lancer la détection sur webcam

> **Énoncé** : Activer la caméra et détecter les objets en temps réel avec affichage des boîtes englobantes.

Appeler la méthode de tracking du modèle en pointant sur la webcam. L'affichage s'ouvre automatiquement avec les labels et boîtes dessinés sur chaque frame.

---

### Étape 4 : Tester sur un fichier vidéo

> **Énoncé** : Remplacer la webcam par une vidéo locale pour analyser un enregistrement existant.

Changer la source de webcam vers un fichier `.mp4` ou `.avi`. Le reste du pipeline reste identique.

---

### Étape 5 : Lire les données de détection

> **Énoncé** : Accéder aux informations brutes de détection pour les utiliser ou les sauvegarder.

Parcourir les résultats frame par frame pour récupérer les coordonnées des boîtes, les noms des objets détectés et leurs IDs de suivi.

---

### Étape 6 (Optionnel) : Filtrer par type d'objet

> **Énoncé** : Limiter la détection à certaines catégories d'objets pour un résultat plus ciblé.

Spécifier les classes d'objets à détecter (personnes, voitures, animaux...) en passant leurs identifiants COCO au modèle.

---

*CodeAlpha Internship — AI Track | www.codealpha.tech*