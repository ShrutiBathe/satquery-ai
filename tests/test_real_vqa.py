from models.vqa.inference import run_vqa


IMAGE_PATH = "tests/real_satellite.jpg"

questions = [
    "What is the main water feature visible in this satellite image?",
    "Are there any large developed or built-up areas visible?",
    "What types of land-cover patterns are visible in this image?",
    "Describe the main geographic features visible in this satellite image."
]


print("\n========== SATQUERY VQA EVALUATION ==========\n")

for i, question in enumerate(questions, start=1):

    print(f"Question {i}: {question}")

    result = run_vqa(
        image_path=IMAGE_PATH,
        query=question
    )

    print("Success:", result["success"])
    print("Answer:", result["answer"])
    print("Confidence:", result["confidence"])
    print("Error:", result["error"])
    print("-" * 60)

print("\n=============================================\n")