# scripts/convert_visdrone_to_yolo.py
import os
import cv2
from pathlib import Path

def convert_one(ann_file, img_dir, ann_dir, out_label_dir):
    """Convert one VisDrone annotation file to YOLO format."""
    img_path = os.path.join(img_dir, ann_file.replace('.txt', '.jpg'))
    if not os.path.exists(img_path):
        return

    img = cv2.imread(img_path)
    if img is None:
        return
    h, w = img.shape[:2]

    yolo_lines = []
    with open(os.path.join(ann_dir, ann_file), 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 6:
                continue
            x1, y1, box_w, box_h = map(int, parts[:4])
            cls_id = int(parts[5]) - 1  # VisDrone: 1-10, YOLO: 0-9

            # Filter ignored regions and invalid boxes.
            if cls_id < 0 or cls_id >= 10 or box_w <= 0 or box_h <= 0:
                continue

            # Normalize to YOLO xywh format.
            xc = (x1 + box_w / 2) / w
            yc = (y1 + box_h / 2) / h
            bw = box_w / w
            bh = box_h / h

            yolo_lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

    out_path = os.path.join(out_label_dir, ann_file)
    with open(out_path, 'w') as f:
        f.write("\n".join(yolo_lines))

def convert_dataset(visdrone_root, split='train'):
    img_dir = os.path.join(visdrone_root, f'VisDrone2019-DET-{split}/images')
    ann_dir = os.path.join(visdrone_root, f'VisDrone2019-DET-{split}/annotations')
    out_label_dir = os.path.join(visdrone_root, f'VisDrone2019-DET-{split}/labels')
    Path(out_label_dir).mkdir(exist_ok=True)

    for ann_file in os.listdir(ann_dir):
        if ann_file.endswith('.txt'):
            convert_one(ann_file, img_dir, ann_dir, out_label_dir)
    print(f"Converted {split} set. Labels saved to {out_label_dir}")

if __name__ == '__main__':
    visdrone_root = 'data'
    convert_dataset(visdrone_root, 'train')
    convert_dataset(visdrone_root, 'val')
