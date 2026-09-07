import torch
from transformers import AutoProcessor, AutoModelForImageTextToText

MODEL_ID = "HuggingFaceTB/SmolVLM-500M-Instruct"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading VQA model on {DEVICE}...")

processor = AutoProcessor.from_pretrained(MODEL_ID)

model = AutoModelForImageTextToText.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16 if DEVICE == "cuda" else torch.float32,
)

model = model.to(DEVICE)
model.eval()

print("VQA model loaded.")