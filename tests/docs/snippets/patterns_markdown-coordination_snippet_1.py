# Source: patterns/markdown-coordination.md
# Line: 262
# Valid syntax: True
# Has imports: True
# Has assignments: True

import pandas as pd
manifest = pd.read_csv("data/processed/alice/manifest.csv")
train_segments = manifest[manifest["split"] == "train"]