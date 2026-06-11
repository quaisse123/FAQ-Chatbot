"""
main.py
Task 4 - Détection d'objets et suivi simple

Ce script réalise :
- Entrée vidéo (webcam ou fichier) via OpenCV
- Détection d'objets en temps réel avec YOLO (configuration par défaut : yolov3-tiny)
- Suivi simple d'objets par association IoU (tracker léger, inspiré de SORT)

Usage:
  python main.py --source 0
  python main.py --source video.mp4 --yolo_cfg yolov3-tiny.cfg --yolo_weights yolov3-tiny.weights --yolo_names coco.names

Notes:
- Téléchargez `yolov3-tiny.cfg`, `yolov3-tiny.weights` et `coco.names` dans le dossier du script
  ou indiquez leurs chemins via les arguments.
- Appuyez sur 'q' pour quitter la fenêtre.

Code volontairement simple et commenté pour faciliter la compréhension.
"""

from typing import List, Tuple
import argparse
import time
import os
import sys

import cv2
import numpy as np


def load_yolo(cfg_path: str, weights_path: str, names_path: str):
	"""Charge le réseau YOLO et la liste des classes depuis des fichiers.
	Lève FileNotFoundError si un fichier est manquant.
	Retourne (net, classes, output_layer_names).
	"""
	if not os.path.isfile(cfg_path):
		raise FileNotFoundError(f"Fichier cfg introuvable: {cfg_path}")
	if not os.path.isfile(weights_path):
		raise FileNotFoundError(f"Fichier weights introuvable: {weights_path}")
	if not os.path.isfile(names_path):
		raise FileNotFoundError(f"Fichier coco names introuvable: {names_path}")

	net = cv2.dnn.readNetFromDarknet(cfg_path, weights_path)
	net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
	net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

	with open(names_path, 'r', encoding='utf-8') as f:
		classes = [line.strip() for line in f.readlines()]

	# compatibilité entre versions d'OpenCV
	try:
		output_layer_names = net.getUnconnectedOutLayersNames()
	except Exception:
		layer_names = net.getLayerNames()
		output_layer_names = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

	return net, classes, output_layer_names


def detect_objects(frame: np.ndarray, net, output_layer_names: List[str], conf_threshold: float = 0.4,
				   nms_threshold: float = 0.4) -> List[Tuple[int, int, int, int, float, int]]:
	"""Détecte des objets dans `frame`.
	Retourne une liste de tuples (x1, y1, x2, y2, confidence, class_id).
	"""
	H, W = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
	net.setInput(blob)
	outs = net.forward(output_layer_names)

	boxes = []
	confidences = []
	class_ids = []

	for out in outs:
		for detection in out:
			scores = detection[5:]
			if scores.size == 0:
				continue
			class_id = int(np.argmax(scores))
			conf = float(scores[class_id])
			if conf > conf_threshold:
				cx = int(detection[0] * W)
				cy = int(detection[1] * H)
				w = int(detection[2] * W)
				h = int(detection[3] * H)
				x = int(cx - w / 2)
				y = int(cy - h / 2)
				boxes.append([x, y, w, h])
				confidences.append(conf)
				class_ids.append(class_id)

	results = []
	if len(boxes) > 0:
		idxs = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
		if isinstance(idxs, (list, tuple, np.ndarray)) and len(idxs) > 0:
			if isinstance(idxs, np.ndarray):
				idxs = idxs.flatten().tolist()
			else:
				try:
					idxs = [i[0] for i in idxs]
				except Exception:
					idxs = list(idxs)

			for i in idxs:
				x, y, w, h = boxes[i]
				x1, y1, x2, y2 = max(0, x), max(0, y), min(W - 1, x + w), min(H - 1, y + h)
				results.append((x1, y1, x2, y2, confidences[i], class_ids[i]))

	return results


def iou(boxA: List[int], boxB: List[int]) -> float:
	# box format: x1,y1,x2,y2
	xA = max(boxA[0], boxB[0])
	yA = max(boxA[1], boxB[1])
	xB = min(boxA[2], boxB[2])
	yB = min(boxA[3], boxB[3])
	interW = max(0, xB - xA)
	interH = max(0, yB - yA)
	interArea = interW * interH
	areaA = max(0, boxA[2] - boxA[0]) * max(0, boxA[3] - boxA[1])
	areaB = max(0, boxB[2] - boxB[0]) * max(0, boxB[3] - boxB[1])
	union = areaA + areaB - interArea
	return float(interArea) / union if union > 0 else 0.0


class SimpleIoUTracker2:
	"""Tracker simple: appariement IoU glouton + vieillissement des pistes."""

	def __init__(self, max_lost: int = 7, iou_threshold: float = 0.3):
		self.next_id = 1
		self.tracks = {}  # id -> {'bbox':[x1,y1,x2,y2], 'lost':int, 'conf':float, 'class_id':int}
		self.max_lost = max_lost
		self.iou_threshold = iou_threshold

	def update(self, detections: List[Tuple[int, int, int, int, float, int]]):
		# detections: list of (x1,y1,x2,y2,conf,class_id)
		if len(self.tracks) == 0:
			for det in detections:
				x1, y1, x2, y2, conf, cls = det
				self.tracks[self.next_id] = {'bbox': [x1, y1, x2, y2], 'lost': 0, 'conf': conf, 'class_id': cls}
				self.next_id += 1
			return self.get_tracks()

		track_ids = list(self.tracks.keys())
		iou_matrix = np.zeros((len(track_ids), len(detections)), dtype=np.float32)
		for t_idx, tid in enumerate(track_ids):
			tb = self.tracks[tid]['bbox']
			for d_idx, det in enumerate(detections):
				db = det[0:4]
				iou_matrix[t_idx, d_idx] = iou(tb, db)

		matched_tracks = set()
		matched_dets = set()

		# greedy matching by highest IoU
		while True:
			if iou_matrix.size == 0:
				break
			t, d = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
			if iou_matrix[t, d] < self.iou_threshold:
				break
			tid = track_ids[t]
			det = detections[d]
			x1, y1, x2, y2, conf, cls = det
			self.tracks[tid]['bbox'] = [x1, y1, x2, y2]
			self.tracks[tid]['conf'] = conf
			self.tracks[tid]['class_id'] = cls
			self.tracks[tid]['lost'] = 0
			matched_tracks.add(t)
			matched_dets.add(d)
			iou_matrix[t, :] = -1
			iou_matrix[:, d] = -1

		# create new tracks for unmatched detections
		for d_idx, det in enumerate(detections):
			if d_idx in matched_dets:
				continue
			x1, y1, x2, y2, conf, cls = det
			self.tracks[self.next_id] = {'bbox': [x1, y1, x2, y2], 'lost': 0, 'conf': conf, 'class_id': cls}
			self.next_id += 1

		# increase lost counter for unmatched tracks
		for t_idx, tid in enumerate(track_ids):
			if t_idx in matched_tracks:
				continue
			self.tracks[tid]['lost'] += 1

		# remove stale tracks
		remove_ids = [tid for tid, v in self.tracks.items() if v['lost'] > self.max_lost]
		for rid in remove_ids:
			del self.tracks[rid]

		return self.get_tracks()

	def get_tracks(self):
		out = []
		for tid, v in self.tracks.items():
			out.append((tid, v['bbox'], v['class_id'], v['conf']))
		return out


def color_for_id(idx: int) -> Tuple[int, int, int]:
	# couleur déterministe pour un id (BGR)
	r = (37 * idx) % 255
	g = (17 * idx) % 255
	b = (29 * idx) % 255
	return int(b), int(g), int(r)


def draw_label(img, text, left, top, bg_color=(0, 128, 255)):
	(w, h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
	cv2.rectangle(img, (left, top - h - baseline), (left + w, top + baseline), bg_color, -1)
	cv2.putText(img, text, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


def main():
	parser = argparse.ArgumentParser(description='Detection + Tracking simple (YOLO + IoU)')
	parser.add_argument('--source', default='0', help='0 pour webcam ou chemin fichier')
	parser.add_argument('--yolo_cfg', default='yolov3-tiny.cfg', help='fichier cfg YOLO')
	parser.add_argument('--yolo_weights', default='yolov3-tiny.weights', help='fichier weights YOLO')
	parser.add_argument('--yolo_names', default='coco.names', help='fichier noms COCO')
	parser.add_argument('--confidence', type=float, default=0.4)
	parser.add_argument('--nms', type=float, default=0.4)
	parser.add_argument('--max_lost', type=int, default=7)
	parser.add_argument('--iou_threshold', type=float, default=0.3)
	args = parser.parse_args()

	try:
		net, classes, out_names = load_yolo(args.yolo_cfg, args.yolo_weights, args.yolo_names)
	except FileNotFoundError as e:
		print(e)
		print('Téléchargez les fichiers YOLO (cfg, weights, names) et relancez. Voir README.md')
		return

	tracker = SimpleIoUTracker2(max_lost=args.max_lost, iou_threshold=args.iou_threshold)

	source = args.source
	if source.isdigit():
		source = int(source)
	cap = cv2.VideoCapture(source)
	if not cap.isOpened():
		print('Impossible d\'ouvrir la source', source)
		return

	prev_time = time.time()
	while True:
		ret, frame = cap.read()
		if not ret:
			break

		detections = detect_objects(frame, net, out_names, conf_threshold=args.confidence, nms_threshold=args.nms)

		tracks = tracker.update(detections)

		# afficher détections (label + confiance)
		for (x1, y1, x2, y2, conf, cls_id) in detections:
			label = classes[cls_id] if cls_id < len(classes) else str(cls_id)
			cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 180, 255), 2)
			draw_label(frame, f"{label} {conf:.2f}", x1, max(15, y1))

		# afficher pistes (ID)
		for (tid, bbox, cls_id, conf) in tracks:
			x1, y1, x2, y2 = [int(v) for v in bbox]
			col = color_for_id(tid)
			cv2.rectangle(frame, (x1, y1), (x2, y2), col, 2)
			draw_label(frame, f"ID:{tid}", x1, y2 + 15, bg_color=col)

		# FPS
		now = time.time()
		fps = 1.0 / (now - prev_time + 1e-6)
		prev_time = now
		cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

		cv2.imshow('Detection & Tracking', frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

	cap.release()
	cv2.destroyAllWindows()


if __name__ == '__main__':
	main()

