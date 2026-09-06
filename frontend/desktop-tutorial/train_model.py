"""Train a crop disease classifier using PlantVillage and PlantDoc."""

from **future** import annotations

import argparse
import os
import random
from collections import Counter
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import ConcatDataset, DataLoader
from torchvision import datasets, models, transforms
from torchvision.datasets import VisionDataset
from torchvision.models import ResNet18_Weights

def parse_args() -> argparse.Namespace:
parser = argparse.ArgumentParser(
description="Train the crop disease classifier"
)

```
parser.add_argument(
    "--plantvillage-dir",
    type=Path,
    default=Path("data/PlantVillage"),
)

parser.add_argument(
    "--plantdoc-dir",
    type=Path,
    default=Path("data/PlantDoc-Dataset-master"),
)

parser.add_argument(
    "--output-dir",
    type=Path,
    default=Path("models"),
)

parser.add_argument("--epochs", type=int, default=3)
parser.add_argument("--batch-size", type=int, default=32)

parser.add_argument(
    "--max-images-per-class",
    type=int,
    default=200,
    help="Maximum images per class from each dataset. "
         "Use 0 for all images.",
)

parser.add_argument("--learning-rate", type=float, default=1e-4)

parser.add_argument(
    "--plantvillage-test-ratio",
    type=float,
    default=0.2,
)

parser.add_argument("--seed", type=int, default=42)

return parser.parse_args()
```

def set_seed(seed: int) -> None:
random.seed(seed)
torch.manual_seed(seed)

```
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(seed)
```

def image_transform(training: bool) -> transforms.Compose:
operations = [
transforms.Resize((224, 224)),
]

```
if training:
    operations.extend(
        [
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
        ]
    )

operations.extend(
    [
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)

return transforms.Compose(operations)
```

def find_plantvillage_root(root: Path) -> Path:
nested_root = root / "PlantVillage"

```
if nested_root.is_dir():
    return nested_root

return root
```

def collect_samples(
root: Path,
limit: int,
seed: int,
) -> list[tuple[Path, str]]:

```
if not root.is_dir():
    raise FileNotFoundError(
        f"Dataset directory does not exist: {root}"
    )

image_folder = datasets.ImageFolder(root)

if not image_folder.classes:
    raise ValueError(
        f"No class folders found in dataset: {root}"
    )

samples = [
    (Path(path), image_folder.classes[index])
    for path, index in image_folder.samples
]

# Shuffle before limiting so that the first N files
# are not always selected.
rng = random.Random(seed)
rng.shuffle(samples)

if limit > 0:
    grouped: dict[str, list[tuple[Path, str]]] = {}

    for sample in samples:
        grouped.setdefault(sample[1], []).append(sample)

    limited_samples: list[tuple[Path, str]] = []

    for class_name, class_samples in grouped.items():
        limited_samples.extend(class_samples[:limit])

    samples = limited_samples

counts = Counter(label for _, label in samples)

print(f"\nDataset: {root}")
print(f"Images: {len(samples)}")
print(f"Classes: {len(counts)}")

for class_name, count in sorted(counts.items()):
    print(f"  {class_name}: {count}")

return samples
```

class LabelledImages(VisionDataset):

```
def __init__(
    self,
    samples: list[tuple[Path, str]],
    class_to_index: dict[str, int],
    transform,
):
    super().__init__(root=".", transform=transform)

    self.samples = []

    for path, label in samples:

        if label not in class_to_index:
            raise ValueError(
                f"Unknown class '{label}' for image: {path}"
            )

        self.samples.append(
            (str(path), class_to_index[label])
        )

def __getitem__(self, index: int):
    from PIL import Image

    path, target = self.samples[index]

    try:
        with Image.open(path) as image:
            image = image.convert("RGB")
            image = self.transform(image)

    except Exception as exc:
        raise RuntimeError(
            f"Failed to read image: {path}"
        ) from exc

    return image, target

def __len__(self) -> int:
    return len(self.samples)
```

def split_by_class(
samples: list[tuple[Path, str]],
ratio: float,
seed: int,
) -> tuple[
list[tuple[Path, str]],
list[tuple[Path, str]]
]:

```
if not 0 < ratio < 1:
    raise ValueError(
        "plantvillage-test-ratio must be between 0 and 1"
    )

grouped: dict[str, list[tuple[Path, str]]] = {}

for sample in samples:
    grouped.setdefault(sample[1], []).append(sample)

rng = random.Random(seed)

train: list[tuple[Path, str]] = []
test: list[tuple[Path, str]] = []

for class_name, items in grouped.items():

    items = items.copy()
    rng.shuffle(items)

    if len(items) <= 1:
        train.extend(items)
        continue

    test_count = max(
        1,
        round(len(items) * ratio),
    )

    # Prevent an entire class from ending up in test.
    test_count = min(
        test_count,
        len(items) - 1,
    )

    test.extend(items[:test_count])
    train.extend(items[test_count:])

return train, test
```

def build_datasets(args: argparse.Namespace):

```
village_root = find_plantvillage_root(
    args.plantvillage_dir
)

village = collect_samples(
    village_root,
    args.max_images_per_class,
    args.seed,
)

doc_train_root = args.plantdoc_dir / "train"
doc_test_root = args.plantdoc_dir / "test"

doc_train = collect_samples(
    doc_train_root,
    args.max_images_per_class,
    args.seed + 1,
)

doc_test = collect_samples(
    doc_test_root,
    args.max_images_per_class,
    args.seed + 2,
)

# Combine class names from all datasets.
classes = sorted(
    {
        label
        for _, label in (
            village + doc_train + doc_test
        )
    }
)

if len(classes) < 2:
    raise ValueError(
        f"At least two classes are required. Found: {classes}"
    )

class_to_index = {
    label: index
    for index, label in enumerate(classes)
}

print("\nFinal classes:")
for index, class_name in enumerate(classes):
    print(f"{index}: {class_name}")

village_train, village_test = split_by_class(
    village,
    args.plantvillage_test_ratio,
    args.seed,
)

train_dataset = ConcatDataset(
    [
        LabelledImages(
            village_train,
            class_to_index,
            image_transform(True),
        ),
        LabelledImages(
            doc_train,
            class_to_index,
            image_transform(True),
        ),
    ]
)

test_dataset = ConcatDataset(
    [
        LabelledImages(
            village_test,
            class_to_index,
            image_transform(False),
        ),
        LabelledImages(
            doc_test,
            class_to_index,
            image_transform(False),
        ),
    ]
)

if len(train_dataset) == 0:
    raise ValueError("Training dataset is empty.")

if len(test_dataset) == 0:
    raise ValueError("Test dataset is empty.")

return classes, train_dataset, test_dataset
```

def train_epoch(
model,
loader,
device,
optimizer,
loss_function,
) -> float:

```
model.train()

loss_sum = 0.0

for images, labels in loader:

    images = images.to(device)
    labels = labels.to(device)

    optimizer.zero_grad(set_to_none=True)

    outputs = model(images)
    loss = loss_function(outputs, labels)

    loss.backward()
    optimizer.step()

    loss_sum += loss.item() * images.size(0)

return loss_sum / len(loader.dataset)
```

def evaluate(
model,
loader,
device,
) -> float:

```
model.eval()

correct = 0
total = 0

with torch.no_grad():

    for images, labels in loader:

        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        predictions = outputs.argmax(dim=1)

        correct += (
            predictions == labels
        ).sum().item()

        total += labels.size(0)

if total == 0:
    return 0.0

return correct / total
```

def main() -> None:

```
args = parse_args()

if args.epochs <= 0:
    raise ValueError("epochs must be greater than 0")

if args.batch_size <= 0:
    raise ValueError("batch-size must be greater than 0")

if args.learning_rate <= 0:
    raise ValueError("learning-rate must be greater than 0")

if args.max_images_per_class < 0:
    raise ValueError(
        "max-images-per-class must be zero or greater"
    )

set_seed(args.seed)

# Avoid excessive CPU thread usage.
if not torch.cuda.is_available():
    torch.set_num_threads(
        max(1, min(4, os.cpu_count() or 1))
    )

classes, train_data, test_data = build_datasets(args)

print("\n" + "=" * 60)
print(
    f"Training images : {len(train_data)}"
)
print(
    f"Testing images  : {len(test_data)}"
)
print(
    f"Number of classes: {len(classes)}"
)
print("=" * 60)

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

print(f"Using device: {device}")

train_loader = DataLoader(
    train_data,
    batch_size=args.batch_size,
    shuffle=True,
    num_workers=0,
)

test_loader = DataLoader(
    test_data,
    batch_size=args.batch_size,
    shuffle=False,
    num_workers=0,
)

# Load pretrained ResNet-18.
model = models.resnet18(
    weights=ResNet18_Weights.DEFAULT
)

# Freeze the pretrained feature extractor.
for parameter in model.parameters():
    parameter.requires_grad = False

# Replace the final classifier.
model.fc = nn.Linear(
    model.fc.in_features,
    len(classes),
)

model.to(device)

optimizer = torch.optim.Adam(
    model.fc.parameters(),
    lr=args.learning_rate,
)

loss_function = nn.CrossEntropyLoss()

best_accuracy = 0.0

for epoch in range(args.epochs):

    loss = train_epoch(
        model,
        train_loader,
        device,
        optimizer,
        loss_function,
    )

    accuracy = evaluate(
        model,
        test_loader,
        device,
    )

    print(
        f"Epoch {epoch + 1}/{args.epochs} "
        f"| loss={loss:.4f} "
        f"| accuracy={accuracy:.2%}"
    )

    best_accuracy = max(
        best_accuracy,
        accuracy,
    )

# Prepare output directory.
args.output_dir.mkdir(
    parents=True,
    exist_ok=True,
)

# Move model to CPU for deployment.
model.to("cpu")
model.eval()

# Export TorchScript.
example_input = torch.zeros(
    1,
    3,
    224,
    224,
)

with torch.no_grad():
    traced_model = torch.jit.trace(
        model,
        example_input,
    )

model_path = (
    args.output_dir / "crop_model.pt"
)

traced_model.save(str(model_path))

# Save class mapping.
classes_path = (
    args.output_dir / "classes.txt"
)

classes_path.write_text(
    "\n".join(classes) + "\n",
    encoding="utf-8",
)

print("\nTraining complete.")
print(f"Best accuracy : {best_accuracy:.2%}")
print(f"Model saved   : {model_path}")
print(f"Classes saved : {classes_path}")
```

if **name** == "**main**":
main()
