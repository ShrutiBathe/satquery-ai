import os
import torch

from .model import model, processor, DEVICE
from .preprocessing import load_vqa_image

def build_vqa_prompt(query: str) -> str:
    """
    Build a standardized prompt for SatQuery remote-sensing VQA.
    """

    return f"""
You are SatQuery, an AI assistant specialized in remote-sensing
and satellite image analysis.

Analyze the provided satellite image carefully.

Rules:
1. Answer the user's question directly.
2. Use only information visually supported by the image.
3. Do not invent objects, features, or locations.
4. Do not assume false-color imagery represents natural RGB colors.
5. Avoid unnecessary speculation.
6. If something is uncertain, clearly say that it is uncertain.
7. Keep the answer concise and informative.
8. When possible, mention the approximate location of the feature
   in the image (center, left, right, upper, lower, etc.).

User question:
{query}
"""



def run_vqa(
    image_path: str,
    query: str
) -> dict:

    # -------------------------
    # Input validation
    # -------------------------

    if not image_path:
        return {
            "success": False,
            "answer": "",
            "confidence": None,
            "evidence": [],
            "output_paths": [],
            "statistics": {},
            "error": "image_path is required"
        }

    if not os.path.exists(image_path):
        return {
            "success": False,
            "answer": "",
            "confidence": None,
            "evidence": [],
            "output_paths": [],
            "statistics": {},
            "error": f"Image not found: {image_path}"
        }

    if not query or not query.strip():
        return {
            "success": False,
            "answer": "",
            "confidence": None,
            "evidence": [],
            "output_paths": [],
            "statistics": {},
            "error": "query is required"
        }

    try:

        # -------------------------
        # Load image
        # -------------------------

        image = load_vqa_image(image_path)

        # -------------------------
        # Create conversation
        # -------------------------

        prompt_text = build_vqa_prompt(query)

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt_text}
                ]
            }
        ]
        # -------------------------
        # Prepare model input
        # -------------------------

        prompt = processor.apply_chat_template(
            messages,
            add_generation_prompt=True
        )

        inputs = processor(
            text=prompt,
            images=[image],
            return_tensors="pt"
        )

        inputs = inputs.to(DEVICE)

        # -------------------------
        # Model inference
        # -------------------------

        with torch.no_grad():

            generated_ids = model.generate(
                **inputs,
                max_new_tokens=256
            )

        # -------------------------
        # Decode answer
        # -------------------------

            generated_text = processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
            )[0]

            # Keep only the assistant's response
            if "Assistant:" in generated_text:
             answer = generated_text.split("Assistant:", 1)[1].strip()
            else:
                answer = generated_text.strip()

        return {
            "success": True,
            "answer": answer,
            "confidence": None,
            "evidence": [],
            "output_paths": [],
            "statistics": {},
            "error": None
        }

    except Exception as e:

        return {
            "success": False,
            "answer": "",
            "confidence": None,
            "evidence": [],
            "output_paths": [],
            "statistics": {},
            "error": str(e)
        }