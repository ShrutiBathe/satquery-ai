from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image

MODEL_ID = "HuggingFaceTB/SmolVLM-500M-Instruct"
IMAGE_PATH = "data/sentinel2_rgb_visual.tif"

print("Loading processor...")
processor = AutoProcessor.from_pretrained(MODEL_ID)

print("Loading model...")
model = AutoModelForImageTextToText.from_pretrained(MODEL_ID)

print("Loading satellite GeoTIFF...")
image = Image.open(IMAGE_PATH).convert("RGB")

print("Image loaded:", image.size)

question = "What is visible in this satellite image? Describe the major land features."

messages = [
    {
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "text", "text": question},
        ],
    }
]

prompt = processor.apply_chat_template(
    messages,
    add_generation_prompt=True,
)

inputs = processor(
    text=prompt,
    images=[image],
    return_tensors="pt",
)

print("Running VLM inference...")

generated_ids = model.generate(
    **inputs,
    max_new_tokens=150,
)

answer = processor.batch_decode(
    generated_ids,
    skip_special_tokens=True,
)[0]

print("\n==============================")
print("SATELLITE VLM ANSWER")
print("==============================")
print(answer)