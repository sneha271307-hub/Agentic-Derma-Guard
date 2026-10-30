"""Train the Diagnosis Agent (EfficientNet-B0). Run in Colab/GPU. Never touches the 2,000 validation images.

  python scripts/train_diagnosis.py --train-dir /data/train --labels-csv /data/train_labels.csv \
         --id-col image_id --label-col dx --epochs 10
Saves ../models/best_model.pth (picked by macro-F1 on an internal 10% hold-out of the TRAIN set).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agents.diagnosis_agent import build_model   # noqa: E402
from config import CLASSES, IMG_SIZE             # noqa: E402

MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]


class DS(Dataset):
    def __init__(self, items, tf):
        self.items, self.tf = items, tf

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        p, y = self.items[i]
        return self.tf(Image.open(p).convert("RGB")), y


def find(root: Path, iid: str):
    for e in (".jpg", ".jpeg", ".png"):
        if (root / f"{iid}{e}").exists():
            return root / f"{iid}{e}"
    hits = list(root.rglob(f"{iid}.*"))
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-dir", required=True)
    ap.add_argument("--labels-csv", required=True)
    ap.add_argument("--id-col", default="image_id")
    ap.add_argument("--label-col", default="dx")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "models" / "best_model.pth"))
    a = ap.parse_args()

    df = pd.read_csv(a.labels_csv)
    df[a.label_col] = df[a.label_col].astype(str).str.strip().str.lower()
    c2i = {c: i for i, c in enumerate(CLASSES)}
    root, items = Path(a.train_dir), []
    for _, r in df.iterrows():
        p = find(root, str(r[a.id_col]))
        if p is not None:
            items.append((p, c2i[r[a.label_col]]))
    print(f"{len(items)} training images")

    ys = [y for _, y in items]
    tr, va = train_test_split(items, test_size=0.1, stratify=ys, random_state=42)

    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(IMG_SIZE, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(), transforms.RandomVerticalFlip(),
        transforms.RandomRotation(30), transforms.ColorJitter(0.2, 0.2, 0.2, 0.02),
        transforms.ToTensor(), transforms.Normalize(MEAN, STD)])
    eval_tf = transforms.Compose([transforms.Resize((IMG_SIZE, IMG_SIZE)),
                                  transforms.ToTensor(), transforms.Normalize(MEAN, STD)])
    tl = DataLoader(DS(tr, train_tf), batch_size=a.batch_size, shuffle=True, num_workers=2)
    vl = DataLoader(DS(va, eval_tf), batch_size=64, num_workers=2)

    counts = np.bincount([y for _, y in tr], minlength=len(CLASSES)).astype(float)
    w = torch.tensor((counts.sum() / (len(CLASSES) * np.maximum(counts, 1))) ** 0.5, dtype=torch.float32)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = build_model(pretrained=True).to(dev)
    crit = nn.CrossEntropyLoss(weight=w.to(dev))
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs)
    scaler = torch.cuda.amp.GradScaler(enabled=dev == "cuda")

    best = -1.0
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    for ep in range(1, a.epochs + 1):
        model.train()
        for x, y in tl:
            x, y = x.to(dev), y.to(dev)
            opt.zero_grad()
            with torch.autocast(device_type=dev, enabled=dev == "cuda"):
                loss = crit(model(x), y)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
        sched.step()
        model.eval()
        P, T = [], []
        with torch.no_grad():
            for x, y in vl:
                P += model(x.to(dev)).argmax(1).cpu().tolist()
                T += y.tolist()
        f1 = f1_score(T, P, average="macro")
        acc = float(np.mean(np.array(P) == np.array(T)))
        print(f"epoch {ep}/{a.epochs}  loss {loss.item():.3f}  holdout acc {acc:.3f}  macro-F1 {f1:.3f}")
        if f1 > best:
            best = f1
            torch.save({"state_dict": model.state_dict(), "classes": CLASSES, "img_size": IMG_SIZE}, a.out)
            print("  saved", a.out)


if __name__ == "__main__":
    main()
