"""
SatQuery AI - Pre-packaged High-Fidelity Satellite Sample Data
Generates realistic procedural remote sensing imagery (Optical RGB, SAR Backscatter,
Bi-temporal pairs, bounding boxes, and ground-truth segmentation masks)
for zero-friction hackathon evaluation.
"""

from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from datetime import date

import config.settings as cfg
from utils.image_utils import create_annotated_bboxes, create_change_heatmap, create_segmentation_overlay


def _create_synthetic_terrain(width: int = 512, height: int = 512, seed: int = 42) -> np.ndarray:
    """Generate smooth base elevation/terrain noise."""
    np.random.seed(seed)
    # Multi-octave Perlin-like fractal terrain approximation
    grid = np.random.uniform(0.2, 0.8, (16, 16))
    img_coarse = Image.fromarray((grid * 255).astype(np.uint8)).resize((width, height), resample=Image.Resampling.BICUBIC)
    arr = np.array(img_coarse, dtype=np.float32) / 255.0
    return arr


def generate_change_detection_scenario() -> Dict[str, Any]:
    """
    Scenario 1: Bi-temporal Urban Growth & Industrial Construction (2024 vs 2026)
    """
    w, h = 600, 600
    
    # Baseline Image A (2024 - Semi-arid land with minor road)
    base_arr = _create_synthetic_terrain(w, h, seed=101)
    img_a = Image.new("RGB", (w, h), color=(140, 130, 110))
    draw_a = ImageDraw.Draw(img_a)

    # Add terrain variation
    for y in range(0, h, 8):
        for x in range(0, w, 8):
            factor = base_arr[y, x]
            r = int(140 * factor + 40)
            g = int(130 * factor + 35)
            b = int(105 * factor + 30)
            draw_a.rectangle([x, y, x + 8, y + 8], fill=(r, g, b))

    # River / Coastline on East edge
    draw_a.polygon([(520, 0), (600, 0), (600, 600), (480, 600), (510, 300)], fill=(32, 68, 108))

    # Single rural highway in 2024
    draw_a.line([(0, 280), (490, 310)], fill=(80, 80, 85), width=7)

    # Post-Event Image B (2026 - Major new industrial park, secondary roads, grid blocks)
    img_b = img_a.copy()
    draw_b = ImageDraw.Draw(img_b)

    # New grid road network
    draw_b.line([(220, 50), (220, 550)], fill=(65, 65, 70), width=9)
    draw_b.line([(360, 50), (360, 550)], fill=(65, 65, 70), width=9)
    draw_b.line([(50, 150), (450, 150)], fill=(65, 65, 70), width=8)
    draw_b.line([(50, 420), (450, 420)], fill=(65, 65, 70), width=8)

    # New industrial warehouses & bright roofs
    warehouses = [
        [100, 180, 190, 250],
        [240, 170, 340, 260],
        [240, 320, 330, 400],
        [110, 330, 200, 400],
        [380, 180, 460, 290]
    ]
    for x0, y0, x1, y1 in warehouses:
        # Building roof with bright reflective texture
        draw_b.rectangle([x0, y0, x1, y1], fill=(215, 222, 235), outline=(40, 45, 55), width=2)
        # Shadow
        draw_b.polygon([(x1, y0 + 10), (x1 + 14, y0 + 20), (x1 + 14, y1 + 10), (x1, y1)], fill=(40, 40, 45))

    # Land cleared for development
    draw_b.rectangle([80, 450, 430, 560], fill=(168, 158, 138), outline=(130, 120, 100), width=1)

    # Generate real change heatmap & composite overlay
    heatmap, overlay = create_change_heatmap(img_a, img_b, sensitivity=1.4)

    return {
        "id": "scenario_change_detection",
        "title": "Urban & Industrial Expansion",
        "category": cfg.WORKFLOW_CHANGE,
        "mode": cfg.MODE_COMPARE,
        "default_query": "What changed between 2024 and 2026?",
        "suggested_queries": [
            "What changed between 2024 and 2026?",
            "Highlight newly built industrial structures",
            "Quantify the area of newly developed land",
            "Did the water boundary shift?"
        ],
        "image_a": img_a,
        "image_b": img_b,
        "image_a_name": "Sentinel2_AOI_20240615_T43RER.tif",
        "image_b_name": "Sentinel2_AOI_20260320_T43RER.tif",
        "image_a_date": date(2024, 6, 15),
        "image_b_date": date(2026, 3, 20),
        "sensor_a": "Sentinel-2 MSI (10m Optical)",
        "sensor_b": "Sentinel-2 MSI (10m Optical)",
        "detected_task": {
            "id": cfg.WORKFLOW_CHANGE,
            "title": "Bi-Temporal Change Detection",
            "reason": "Natural language query inquires about structural and surface modifications between temporal dates (2024 to 2026).",
            "input_modality": "Bi-Temporal Optical Multi-Spectral",
            "model_pipeline": "Siamese ResNet-50 + Differential Feature Attention"
        },
        "answer": (
            "Analysis reveals significant anthropogenic expansion between June 2024 and March 2026. "
            "A total of 5 major industrial logistics warehouses (approx. 43,200 m²) and a dual-arterial "
            "asphalt grid network (3.4 km) were constructed in the central quadrant. "
            "Additionally, 18.5 hectares of previously vacant shrubland have been cleared for ongoing phase-2 construction. "
            "No significant morphological alteration was detected along the eastern coastline."
        ),
        "confidence": 0.93,
        "confidence_breakdown": {
            "spatial": 0.95,
            "semantic": 0.92,
            "sensor": 0.96
        },
        "metrics": {
            "New Built Structures": {"value": "5 Facilities", "unit": "Count"},
            "Total Built-up Footprint": {"value": "43,200", "unit": "m²"},
            "New Road Infrastructure": {"value": "3.4", "unit": "km"},
            "Cleared Land Parcel": {"value": "18.5", "unit": "Hectares"},
            "Shoreline Displacement": {"value": "< 0.5", "unit": "meters (Negligible)"}
        },
        "summary_bullets": [
            "5 newly constructed logistics warehouses identified in central sector.",
            "3.4 km of newly surfaced dual-arterial road grid detected.",
            "18.5 hectares of vacant shrubland cleared for civil development.",
            "Eastern water body boundary remained stable (< 0.5m variation)."
        ],
        "visual_evidence": {
            "type": "change_detection",
            "image_a": img_a,
            "image_b": img_b,
            "heatmap": heatmap,
            "overlay": overlay,
            "labels": [
                {"name": "New Infrastructure / Buildings", "color": "#F43F5E", "count": 5},
                {"name": "Land Preparation / Clearing", "color": "#F59E0B", "count": 1},
                {"name": "Stable Natural Features", "color": "#10B981", "count": "N/A"}
            ]
        }
    }


def generate_grounding_scenario() -> Dict[str, Any]:
    """
    Scenario 2: Fuel Storage Tank & Logistics Facility Visual Grounding
    """
    w, h = 600, 600
    np.random.seed(202)

    # Industrial port satellite scene
    img = Image.new("RGB", (w, h), color=(105, 112, 120))
    draw = ImageDraw.Draw(img)

    # Asphalt apron & docking roads
    draw.rectangle([0, 0, w, h], fill=(85, 92, 100))
    draw.line([(0, 180), (w, 180)], fill=(45, 50, 58), width=24)
    draw.line([(0, 420), (w, 420)], fill=(45, 50, 58), width=24)
    draw.line([(290, 0), (290, h)], fill=(45, 50, 58), width=24)

    # Circular Fuel Storage Tanks
    tanks = [
        (80, 80, 55),
        (200, 80, 55),
        (80, 280, 55),
        (200, 280, 55),
        (80, 480, 55),
        (200, 480, 55)
    ]
    for cx, cy, radius in tanks:
        # Outer bund wall
        draw.ellipse([cx - radius - 8, cy - radius - 8, cx + radius + 8, cy + radius + 8], fill=(60, 65, 72), outline=(130, 135, 145))
        # Floating roof tank
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(225, 230, 238), outline=(30, 35, 45), width=2)
        # Shadow
        draw.arc([cx - radius, cy - radius, cx + radius, cy + radius], start=30, end=150, fill=(35, 40, 48), width=6)

    # Rectangular Warehouses & Cargo sheds
    sheds = [
        [340, 80, 540, 160],
        [340, 220, 550, 310],
        [340, 360, 520, 450],
        [340, 490, 540, 570]
    ]
    for x0, y0, x1, y1 in sheds:
        draw.rectangle([x0, y0, x1, y1], fill=(160, 175, 195), outline=(30, 35, 45), width=2)
        # Roof corrugation pattern
        for y_line in range(y0 + 10, y1, 12):
            draw.line([(x0, y_line), (x1, y_line)], fill=(135, 150, 170), width=1)

    # Grounding bounding box annotations
    bboxes = []
    for idx, (cx, cy, r) in enumerate(tanks, start=1):
        x0 = (cx - r - 10) / w
        y0 = (cy - r - 10) / h
        x1 = (cx + r + 10) / w
        y1 = (cy + r + 10) / h
        bboxes.append({
            "box": [y0, x0, y1, x1],
            "label": f"Storage Tank #{idx}",
            "score": round(0.92 + (idx % 5) * 0.015, 3),
            "color": "#00F0FF"
        })

    for idx, (x0, y0, x1, y1) in enumerate(sheds, start=1):
        bboxes.append({
            "box": [y0 / h, x0 / w, y1 / h, x1 / w],
            "label": f"Warehouse #{idx}",
            "score": round(0.90 + (idx % 4) * 0.02, 3),
            "color": "#38BDF8"
        })

    annotated_img = create_annotated_bboxes(img, bboxes)

    # Create binary mask for storage tanks
    mask = np.zeros((h, w), dtype=np.uint8)
    for cx, cy, r in tanks:
        y, x = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        mask[dist_from_center <= r] = 255
    seg_overlay = create_segmentation_overlay(img, mask, color_hex="#00F0FF", alpha=0.5)

    return {
        "id": "scenario_visual_grounding",
        "title": "Fuel Depot & Logistics Grounding",
        "category": cfg.WORKFLOW_GROUNDING,
        "mode": cfg.MODE_SINGLE,
        "default_query": "Where are the fuel storage tanks and warehouse facilities?",
        "suggested_queries": [
            "Where are the fuel storage tanks?",
            "Locate all warehouse structures",
            "Detect containment berms around liquid tanks",
            "Count the circular storage units"
        ],
        "image_a": img,
        "image_b": None,
        "image_a_name": "WorldView3_Refinery_0.3m_AOI.tif",
        "image_b_name": None,
        "sensor_a": "WorldView-3 (0.3m High-Resolution Optical)",
        "detected_task": {
            "id": cfg.WORKFLOW_GROUNDING,
            "title": "Visual Grounding & Localization",
            "reason": "Natural language query requests exact spatial location and coordinates of specific target classes ('fuel storage tanks', 'warehouses').",
            "input_modality": "High-Resolution Monomodal Optical",
            "model_pipeline": "Open-Vocabulary Grounding DINO + SAM (Segment Anything Remote Sensing)"
        },
        "answer": (
            "SatQuery successfully localized 6 floating-roof petrochemical storage tanks and 4 industrial warehouse units. "
            "The storage tanks are situated in the western quadrant arranged in three doublets within protective concrete bund berms. "
            "The warehouses occupy the eastern sector along primary transit corridors. "
            "All coordinates and polygon boundaries have been projected with 96% localization confidence."
        ),
        "confidence": 0.94,
        "confidence_breakdown": {
            "spatial": 0.97,
            "semantic": 0.94,
            "sensor": 0.98
        },
        "metrics": {
            "Detected Storage Tanks": {"value": "6 Units", "unit": "Cylindrical Vessels"},
            "Detected Warehouses": {"value": "4 Units", "unit": "Industrial Sheds"},
            "Average Tank Diameter": {"value": "38.5", "unit": "Meters"},
            "Estimated Total Capacity": {"value": "180,000", "unit": "m³ (Equivalent Crude)"},
            "Localization Precision": {"value": "0.32", "unit": "Meters (Sub-pixel)"}
        },
        "summary_bullets": [
            "6 circular storage tanks detected with sub-meter spatial precision.",
            "4 high-bay distribution warehouses localized along east boundary.",
            "Secondary containment berms confirmed intact around all tanks.",
            "Zero structural defects or perimeter intrusions observed."
        ],
        "visual_evidence": {
            "type": "grounding",
            "image_a": img,
            "annotated_bboxes": annotated_img,
            "seg_overlay": seg_overlay,
            "bboxes": bboxes,
            "labels": [
                {"name": "Fuel Storage Tank", "color": "#00F0FF", "count": 6},
                {"name": "Industrial Warehouse", "color": "#38BDF8", "count": 4}
            ]
        }
    }


def generate_optical_sar_scenario() -> Dict[str, Any]:
    """
    Scenario 3: Monsoon Flood Inundation (Cloudy Optical vs Weather-Invariant SAR)
    """
    w, h = 600, 600
    np.random.seed(303)

    # Base Optical image: lush river basin partially covered by heavy monsoon cloud wisps
    img_opt = Image.new("RGB", (w, h), color=(60, 110, 50))
    draw_opt = ImageDraw.Draw(img_opt)

    # Agricultural plots
    for y in range(0, h, 20):
        for x in range(0, w, 20):
            shade = int(np.random.uniform(50, 85))
            draw_opt.rectangle([x, y, x + 20, y + 20], fill=(45, shade + 35, 35))

    # Winding swollen river & flooded lowlands
    draw_opt.polygon([(100, 0), (220, 0), (320, 250), (450, 400), (520, 600), (350, 600), (220, 380), (140, 200)], fill=(30, 65, 95))

    # Dense clouds and cloud shadows obscuring 45% of optical scene
    draw_opt.ellipse([150, 120, 480, 380], fill=(240, 245, 255), outline=None)
    draw_opt.ellipse([260, 180, 540, 440], fill=(230, 235, 248), outline=None)

    # SAR Image (Sentinel-1 C-Band VV polarization backscatter)
    # Calibrated backscatter: open water has specular reflection -> dark black (very low dB)
    # Cloud cover is transparent to radar!
    sar_arr = np.random.normal(90, 15, (h, w)).astype(np.float32)

    # Water flooded areas: specular reflection -> very dark (dB < -20)
    flood_mask = np.zeros((h, w), dtype=bool)
    y, x = np.ogrid[:h, :w]
    # Synthetic river curve + flooded floodplain
    flood_mask |= ((x > 120 + 0.5 * y) & (x < 360 + 0.35 * y))
    flood_mask |= ((y > 320) & (x > 200) & (x < 480))
    sar_arr[flood_mask] = np.random.normal(25, 6, np.sum(flood_mask))

    # Urban settlements: double-bounce bright scattering -> high pixel values
    urban_mask = (x > 480) & (y < 240)
    sar_arr[urban_mask] = np.random.normal(225, 20, np.sum(urban_mask))

    sar_arr = np.clip(sar_arr, 0, 255).astype(np.uint8)
    img_sar = Image.fromarray(sar_arr, mode="L").convert("RGB")

    # Generate fused flooded area overlay
    flood_binary = (sar_arr < 45).astype(np.uint8)
    fused_overlay = create_segmentation_overlay(img_opt, flood_binary, color_hex="#00F0FF", alpha=0.55)

    return {
        "id": "scenario_optical_sar",
        "title": "Monsoon Flood Inundation Fusion",
        "category": cfg.WORKFLOW_OPTICAL_SAR,
        "mode": cfg.MODE_OPTICAL_SAR,
        "default_query": "Map flood extents and compare optical cloud obstruction with SAR radar backscatter.",
        "suggested_queries": [
            "Map flood extents through cloud obstruction",
            "Compare optical visibility vs SAR radar backscatter",
            "Identify submerged agricultural land parcels",
            "Detect isolated urban settlements"
        ],
        "image_a": img_opt,
        "image_b": img_sar,
        "image_a_name": "Sentinel2_Optical_RGB_CloudCover.tif",
        "image_b_name": "Sentinel1_SAR_C-Band_VV_Backscatter.tif",
        "sensor_a": "Sentinel-2 MSI (Optical Multispectral)",
        "sensor_b": "Sentinel-1 SAR (C-Band Synthetic Aperture Radar)",
        "detected_task": {
            "id": cfg.WORKFLOW_OPTICAL_SAR,
            "title": "Multimodal Optical + SAR Fusion",
            "reason": "Query requires piercing through optical cloud obscuration by fusing synthetic aperture radar dielectric backscatter with multispectral baseline imagery.",
            "input_modality": "Optical RGB + Dual-Polarized SAR (VV/VH)",
            "model_pipeline": "Cross-Attention Cross-Sensor Transformer (Co-Transformer SAR+MSI)"
        },
        "answer": (
            "Multimodal sensor fusion overcomes 48.2% optical cloud obscuration. "
            "Sentinel-1 SAR radar backscatter reveals severe specular attenuation (-24.1 dB), indicating active standing floodwaters "
            "covering 62.4 hectares of agricultural lowlands. "
            "The residential cluster on the northeastern ridge exhibits strong corner-reflector double-bounce (+6.8 dB), "
            "confirming it remains unflooded and suitable for emergency relief logistics."
        ),
        "confidence": 0.91,
        "confidence_breakdown": {
            "spatial": 0.93,
            "semantic": 0.89,
            "sensor": 0.96
        },
        "metrics": {
            "Optical Cloud Obscuration": {"value": "48.2", "unit": "% Scene Area"},
            "Total Inundated Area": {"value": "62.4", "unit": "Hectares"},
            "Flooded Cropland Proportion": {"value": "74.1", "unit": "% of Sector Basin"},
            "Radar Water Backscatter": {"value": "-24.1", "unit": "dB (Specular Flat Water)"},
            "Dry Habitation Cluster": {"value": "Intact", "unit": "Confirmed Safe"}
        },
        "summary_bullets": [
            "SAR C-Band radar successfully penetrated dense cloud cover obscuring 48.2% of the scene.",
            "62.4 hectares of catastrophic agricultural flood inundation mapped.",
            "Northeastern township confirmed dry via double-bounce radar return (+6.8 dB).",
            "Emergency transport corridor along east embankment remains open."
        ],
        "visual_evidence": {
            "type": "optical_sar",
            "image_a": img_opt,
            "image_b": img_sar,
            "fused_overlay": fused_overlay,
            "labels": [
                {"name": "Submerged / Standing Floodwater", "color": "#00F0FF", "count": "62.4 Ha"},
                {"name": "Dry Agricultural Land", "color": "#10B981", "count": "38.0 Ha"},
                {"name": "Optical Cloud Obscuration", "color": "#F8FAFC", "count": "48.2%"}
            ]
        }
    }


def generate_vqa_scenario() -> Dict[str, Any]:
    """
    Scenario 4: Coastal Harbor Maritime Infrastructure & Vessel Activity VQA
    """
    w, h = 600, 600
    np.random.seed(404)

    # Deep blue ocean with coastal quay
    img = Image.new("RGB", (w, h), color=(25, 55, 95))
    draw = ImageDraw.Draw(img)

    # Concrete Pier & Quay on left side
    draw.polygon([(0, 0), (240, 0), (240, 360), (380, 360), (380, 480), (0, 480), (0, 600)], fill=(120, 125, 135))

    # Gantry cranes along the pier
    cranes = [(80, 100), (80, 220), (200, 380), (320, 420)]
    for cx, cy in cranes:
        draw.rectangle([cx - 8, cy - 8, cx + 8, cy + 8], fill=(225, 140, 30))

    # Cargo vessels berthed
    vessels = [
        [(255, 60), (285, 60), (295, 260), (245, 260)],  # Big container ship
        [(395, 380), (415, 380), (420, 520), (390, 520)]  # Feeder vessel
    ]
    for poly in vessels:
        draw.polygon(poly, fill=(195, 205, 215), outline=(30, 40, 50), width=2)

    # Generate attention/saliency map
    sal_arr = np.zeros((h, w), dtype=np.float32)
    y, x = np.ogrid[:h, :w]
    for poly in vessels:
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        sal_arr += np.exp(-(dist ** 2) / (2 * (65 ** 2)))
    sal_arr = np.clip(sal_arr, 0.0, 1.0)

    attention_overlay = create_segmentation_overlay(img, sal_arr, color_hex="#38BDF8", alpha=0.6)

    return {
        "id": "scenario_vqa",
        "title": "Harbor Maritime Traffic & Port Operations",
        "category": cfg.WORKFLOW_VQA,
        "mode": cfg.MODE_SINGLE,
        "default_query": "What maritime vessels and port infrastructure are active in this harbor scene?",
        "suggested_queries": [
            "What maritime vessels and port infrastructure are active?",
            "Are there cargo container ships berthed at the pier?",
            "How many ship-to-shore gantry cranes are installed?",
            "Is there any oil slick or marine pollution visible?"
        ],
        "image_a": img,
        "image_b": None,
        "image_a_name": "Pleiades_Harbor_0.5m_T43R.tif",
        "image_b_name": None,
        "sensor_a": "Pléiades Neo (0.3m Very High Resolution Optical)",
        "detected_task": {
            "id": cfg.WORKFLOW_VQA,
            "title": "Visual Question Answering (VQA)",
            "reason": "Natural language query seeks high-level multi-object scene comprehension, infrastructure inventory, and vessel status.",
            "input_modality": "Very High Resolution Optical Remote Sensing",
            "model_pipeline": "Remote-Sensing Vision-Language Transformer (RS-VLM Multi-Task)"
        },
        "answer": (
            "The scene captures an active deep-water container terminal with two berthed commercial vessels. "
            "A 200m Panamax-class container vessel is berthed along Quay 1, with active cargo handling. "
            "A secondary feeder freighter (135m) is moored at the southern pier. "
            "Four rail-mounted gantry cranes are deployed along the quay aprons. "
            "Water clarity in the mooring basin is high with zero observable petrochemical sheen or surface pollution."
        ),
        "confidence": 0.95,
        "confidence_breakdown": {
            "spatial": 0.96,
            "semantic": 0.94,
            "sensor": 0.97
        },
        "metrics": {
            "Berthed Commercial Vessels": {"value": "2 Ships", "unit": "Panamax & Feeder"},
            "Gantry Cranes Installed": {"value": "4 Units", "unit": "Operational"},
            "Main Berth Length": {"value": "480", "unit": "Meters"},
            "Surface Pollution Detected": {"value": "0.0", "unit": "% (None Detected)"}
        },
        "summary_bullets": [
            "2 commercial cargo vessels actively docked at primary terminal quays.",
            "4 rail-mounted gantry container cranes identified along aprons.",
            "Clear navigation channel with no unauthorized watercraft detected.",
            "Zero marine fuel sheen or turbidity anomalies in the basin."
        ],
        "visual_evidence": {
            "type": "vqa",
            "image_a": img,
            "attention_overlay": attention_overlay,
            "labels": [
                {"name": "Panamax Container Vessel", "color": "#38BDF8", "count": 1},
                {"name": "Feeder Cargo Ship", "color": "#00F0FF", "count": 1},
                {"name": "Gantry Crane Infrastructure", "color": "#F59E0B", "count": 4}
            ]
        }
    }


def get_all_scenarios() -> Dict[str, Any]:
    """Retrieve all bundled demo scenarios."""
    return {
        "change_detection": generate_change_detection_scenario(),
        "grounding": generate_grounding_scenario(),
        "optical_sar": generate_optical_sar_scenario(),
        "vqa": generate_vqa_scenario()
    }
