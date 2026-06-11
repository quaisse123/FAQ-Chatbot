TASK 4 - Détection d'objets et suivi (simple)

Ce dépôt contient `main.py` : un script simple (documenté en français) qui réalise la détection
et le suivi d'objets en temps réel via OpenCV et YOLO.

Prérequis
---------
- Python 3.8+
- Installer les dépendances :

```bash
pip install -r requirements.txt
```

Modèle YOLO (fichiers à fournir)
--------------------------------
Le script attend les fichiers suivants dans le dossier courant (ou indiquez un chemin via les arguments):
- `yolov3-tiny.cfg`
- `yolov3-tiny.weights` (≈ 34MB)
- `coco.names`

Sources possibles :
- cfg: https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg
- weights: https://pjreddie.com/media/files/yolov3-tiny.weights
- names: https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names

Exemples de téléchargement (Linux/macOS) :

```bash
curl -L -o yolov3-tiny.cfg https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg
curl -L -o yolov3-tiny.weights https://pjreddie.com/media/files/yolov3-tiny.weights
curl -L -o coco.names https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names
```

Utilisation
----------
Lancer la webcam (index 0) :

```bash
python main.py --source 0
```

Lancer sur une vidéo :

```bash
python main.py --source path/to/video.mp4
```

Options utiles
--------------
- `--yolo_cfg`, `--yolo_weights`, `--yolo_names` : chemins vers les fichiers YOLO
- `--confidence` : seuil de confiance (par défaut 0.4)
- `--nms` : seuil NMS (par défaut 0.4)
- `--max_lost` : nombre d'images avant suppression d'une piste (par défaut 7)
- `--iou_threshold` : seuil d'appariement IoU pour le tracker (par défaut 0.3)

Remarques
--------
- Le tracker implémenté est volontairement simple (IoU + appariement glouton). Il donne
  des IDs stables dans de nombreux cas mais n'a pas la précision d'algorithmes complets
  comme SORT/DeepSORT.
- Ce script est conçu pour l'apprentissage et pour être lisible/modifiable.

