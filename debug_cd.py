"""
Diagnostic script: test ChangeFormer inference directly.
Inspects raw logits to understand why the model returns all-zero masks.
"""
import sys
import numpy as np
from pathlib import Path

# Find the most recent uploaded change-detection pair
upload_dir = Path("backend/runtime/uploads")
if not upload_dir.exists():
    print(f"Upload dir not found at {upload_dir.resolve()}")
    # Try to find any processed before/after pair
    processed_dirs = list(Path(".").rglob("processed/before.png"))
    if processed_dirs:
        before_path = processed_dirs[-1]
        after_path = before_path.parent / "after.png"
        print(f"Found processed pair:\n  Before: {before_path}\n  After:  {after_path}")
    else:
        print("No processed image pairs found. Checking outputs...")
        # Look for raw uploaded images
        upload_dirs = sorted(upload_dir.parent.parent.rglob("image_a*"))
        print(f"Found uploads: {upload_dirs}")
        sys.exit(1)
else:
    # Find the latest analysis dir
    analysis_dirs = sorted(upload_dir.iterdir(), reverse=True)
    if not analysis_dirs:
        print("No analysis directories found.")
        sys.exit(1)
    latest = analysis_dirs[0]
    before_candidates = list(latest.glob("image_a*"))
    after_candidates = list(latest.glob("image_b*"))
    if not before_candidates or not after_candidates:
        print(f"No image pair in {latest}")
        sys.exit(1)
    before_path = before_candidates[0]
    after_path = after_candidates[0]
    print(f"Using uploaded pair from {latest.name}:")
    print(f"  Before: {before_path}")
    print(f"  After:  {after_path}")

# Also check the processed directory
processed_candidates = list(Path(".").rglob("processed/before.png"))
if processed_candidates:
    before_path = processed_candidates[-1]
    after_path = before_path.parent / "after.png"
    print(f"\nUsing PROCESSED pair (this is what the model actually sees):")
    print(f"  Before: {before_path}")
    print(f"  After:  {after_path}")

from PIL import Image

# Load and inspect the images
img_before = Image.open(before_path)
img_after = Image.open(after_path)
print(f"\nBefore image: size={img_before.size}, mode={img_before.mode}")
print(f"After  image: size={img_after.size}, mode={img_after.mode}")

arr_before = np.array(img_before)
arr_after = np.array(img_after)
print(f"\nBefore array: shape={arr_before.shape}, dtype={arr_before.dtype}, range=[{arr_before.min()}, {arr_before.max()}]")
print(f"After  array: shape={arr_after.shape}, dtype={arr_after.dtype}, range=[{arr_after.min()}, {arr_after.max()}]")

# Check if images are identical
if arr_before.shape == arr_after.shape:
    diff = np.abs(arr_before.astype(float) - arr_after.astype(float))
    print(f"\nPixel difference: mean={diff.mean():.2f}, max={diff.max():.2f}, nonzero_pixels={np.count_nonzero(diff.sum(axis=-1) if diff.ndim==3 else diff)}")
    if diff.max() == 0:
        print("*** CRITICAL: Before and After images are IDENTICAL! ***")
else:
    print(f"\nImages have different shapes: {arr_before.shape} vs {arr_after.shape}")

# Now run the model
print("\n--- Running ChangeFormer model ---")
try:
    from models.change_detection.inference import get_model
    import torch
    
    model = get_model()
    print(f"Model loaded on device: {model.device}")
    print(f"Model image_size: {model.image_size}")
    
    # Run prediction
    mask = model.predict(str(before_path), str(after_path))
    print(f"\nRaw mask: shape={mask.shape}, unique_values={np.unique(mask)}, nonzero={np.count_nonzero(mask)}")
    
    # Also check raw logits
    before_img = model._load_image(str(before_path))
    after_img = model._load_image(str(after_path))
    print(f"\nModel-loaded before: shape={before_img.shape}, dtype={before_img.dtype}, range=[{before_img.min()}, {before_img.max()}]")
    print(f"Model-loaded after:  shape={after_img.shape}, dtype={after_img.dtype}, range=[{after_img.min()}, {after_img.max()}]")
    
    before_tensor = model._preprocess(before_img)
    after_tensor = model._preprocess(after_img)
    print(f"\nBefore tensor: shape={before_tensor.shape}, range=[{before_tensor.min():.4f}, {before_tensor.max():.4f}]")
    print(f"After  tensor: shape={after_tensor.shape}, range=[{after_tensor.min():.4f}, {after_tensor.max():.4f}]")
    
    # Raw forward pass
    with torch.no_grad():
        output = model.model.net_G(before_tensor, after_tensor)
    
    if isinstance(output, (list, tuple)):
        print(f"\nModel returned {len(output)} outputs")
        for i, o in enumerate(output):
            print(f"  Output[{i}]: shape={o.shape}, range=[{o.min():.4f}, {o.max():.4f}]")
        prediction = output[-1]
    else:
        prediction = output
        print(f"\nModel output: shape={prediction.shape}, range=[{prediction.min():.4f}, {prediction.max():.4f}]")
    
    # Check logits per class
    print(f"\nFinal logits shape: {prediction.shape}")
    if prediction.shape[1] == 2:
        logits_unchanged = prediction[0, 0]  # class 0: unchanged
        logits_changed = prediction[0, 1]     # class 1: changed
        print(f"  Class 0 (unchanged): mean={logits_unchanged.mean():.4f}, max={logits_unchanged.max():.4f}")
        print(f"  Class 1 (changed):   mean={logits_changed.mean():.4f}, max={logits_changed.max():.4f}")
        
        # Check argmax
        argmax = torch.argmax(prediction, dim=1).squeeze(0)
        print(f"  Argmax unique values: {torch.unique(argmax).tolist()}")
        print(f"  Pixels predicted as changed: {(argmax == 1).sum().item()} / {argmax.numel()}")
        
        # Check softmax probabilities
        probs = torch.softmax(prediction, dim=1)
        change_prob = probs[0, 1]
        print(f"\n  Change probability: mean={change_prob.mean():.4f}, max={change_prob.max():.4f}")
        print(f"  Pixels with change_prob > 0.3: {(change_prob > 0.3).sum().item()}")
        print(f"  Pixels with change_prob > 0.5: {(change_prob > 0.5).sum().item()}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
