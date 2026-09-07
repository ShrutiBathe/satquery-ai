from models.vqa.inference import run_vqa


IMAGE_PATH = "test_image.jpg"


result = run_vqa(
    image_path=IMAGE_PATH,
    query="What is visible in this image?"
)

print("\n===== SATQUERY VQA TEST =====")
print("Success:", result["success"])
print("Answer:", result["answer"])
print("Confidence:", result["confidence"])
print("Error:", result["error"])
print("=============================\n")