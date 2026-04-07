# Transmission d'images avec correction d'erreurs Reed-Solomon

## Description

Ce projet simule une **chaîne de transmission d'image** complète, de la compression à la reconstruction, en passant par un encodage correcteur d'erreurs et une simulation de canal bruité. Il a été conçu pour illustrer les concepts de théorie de l'information et de codage de canal dans le cadre de mon TIPE.

Chaine de traitement:
La chaîne de traitement est la suivante :

```
Image originale
      │
      ▼
Compression RLE (par canal)
      │
      ▼
Encodage Reed-Solomon RS(n, k)
      │
      ▼
Canal bruité (erreurs aléatoires)
      │
      ▼
Décodage Reed-Solomon (correction d'erreurs)
      │
      ▼
Décompression RLE
      │
      ▼
Image reconstruite
```

---

## Modules

| Fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée principal, orchestre toute la chaîne |
| `compression.py` | Compression et décompression par RLE (Run-Length Encoding) |
| `reed_solomon.py` | Encodage et décodage Reed-Solomon sur GF(256) |
| `corps_fini.py` | Arithmétique dans le corps de Galois GF(2⁸) |
| `canal_bruite.py` | Simulation d'un canal bruité (erreurs aléatoires) |
| `auxi.py` | Fonctions utilitaires (chargement, affichage, sauvegarde, encodage/décodage par blocs) |

---

## Structure du projet

```
.
├── main.py
├── auxi.py
├── compression.py
├── reed_solomon.py
├── canal_bruite.py
├── corps_fini.py
└── README.md
```
---

## Détail des composants

### Compression RLE (`compression.py`)

La compression opère **canal par canal** (R, G, B séparément) pour maximiser les répétitions de valeurs consécutives identiques.

Chaque canal est aplati en un vecteur 1D, puis encodé sous la forme de paires `(valeur, compteur)`. Les métadonnées de taille (hauteur, largeur, taille de chaque canal compressé) sont stockées en tête de flux sur 4 octets chacune (format big-endian).

**Contrainte** : le compteur est limité à 255 (1 octet) pour rester compatible avec GF(256).

### Code Reed-Solomon (`reed_solomon.py` + `corps_fini.py`)

Le code utilisé est un code **RS(n, k)** sur le corps fini GF(2⁸) :
- **n** : longueur du mot de code (max 255)
- **k** : longueur du message utile
- **n - k** : nombre de symboles de redondance, permettant de corriger jusqu'à `(n-k)/2` erreurs par bloc

L'arithmétique du corps GF(256) (addition XOR, multiplication via tables log/exp, division, inversion) est implémentée dans `corps_fini.py`. Le polynôme primitif utilisé est X⁸ + X⁷ + X² + X + 1.

La correction utilise l'algorithme de **Berlekamp-Massey** pour localiser les erreurs et l'algorithme de **Forney** pour calculer leurs magnitudes.

### Canal bruité (`canal_bruite.py`)

Simule un canal à erreurs aléatoires indépendantes : chaque octet transmis est remplacé par une valeur aléatoire avec une probabilité égale au `taux_erreur` spécifié.

### Paramètres par défaut

| Paramètre | Valeur par défaut |
|---|---|
| Code Reed-Solomon | RS(244, 212) |
| Taux d'erreur | 2% |

---

## Prérequis

- Python 3.8+
- [OpenCV](https://pypi.org/project/opencv-python/) : `pip install opencv-python`
- [NumPy](https://pypi.org/project/numpy/) : `pip install numpy`

---

## Utilisation

```bash
python main.py
```

Le programme demande interactivement :
1. Le **nom de l'image** à transmettre (avec extension, ex: `photo.jpg`)
2. Si vous souhaitez personnaliser les paramètres **n** et **k** du code Reed-Solomon
3. Si vous souhaitez personnaliser le **taux d'erreur** de la simulation
4. Si vous souhaitez **sauvegarder** l'image reconstruite

---

## Exemple de sortie

```
[INFO] Image chargée : (480, 640, 3)
[INFO] Taille initiale : 921600 octets.
[INFO] Taille après compression : 310240 octets
[INFO] Taux de compression : 33.67%
[INFO] Taille après encodage avec RS(244,212): 358160 octets
[INFO] Transmission bruitée avec taux_erreur = 2.0%
[INFO] Données décodées (RS)
[INFO] Image reconstruite :(480,640,3)
```

---

## Limites connues

- La taille maximale d'un bloc Reed-Solomon est **255 octets** (contrainte du corps GF(256)).
- La décompression applique des gardes sur les dimensions (hauteur max 1500, largeur max 1800) pour éviter les débordements en cas de corruption des métadonnées.
- Un taux d'erreur trop élevé (supérieur à `(n-k)/2n`) peut dépasser la capacité de correction du code et entraîner une image reconstruite dégradée.

