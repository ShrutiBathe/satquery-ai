"""
SatQuery AI - Professional Project Architecture & Team Integration Handbook PDF Generator
Smart India Hackathon 2026 | Problem Statement ID: SIH26167
Generates an executive, publication-grade PDF document for group members,
academic guides, and external hackathon evaluators.
"""

import os
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from PIL import Image as PILImage


class NumberedCanvas(canvas.Canvas):
    """Custom canvas that adds page numbers ('Page X of Y') and professional running headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0F172A"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 752, "SATQUERY AI")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawString(115, 752, "• Problem Statement ID: SIH26167 • System Architecture & Integration Guide")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(54, 744, 558, 744)

        # Footer (all pages)
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#0284C7"))
        self.drawString(54, 36, "SMART INDIA HACKATHON 2026")
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(185, 36, "| SatQuery AI Autonomous Multimodal Remote-Sensing Platform")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_str)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(54, 46, 558, 46)
        self.restoreState()


def build_pdf(output_filename: str = "SatQuery_AI_Project_Architecture_and_Integration_Guide.pdf") -> str:
    base_dir = Path(__file__).resolve().parent
    output_path = base_dir / output_filename

    # Page setup
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Palette
    C_PRIMARY = colors.HexColor("#0F172A")     # Slate 900
    C_ACCENT = colors.HexColor("#0284C7")      # Blue 600
    C_CYAN = colors.HexColor("#0891B2")        # Cyan 600
    C_PURPLE = colors.HexColor("#7C3AED")      # Purple 600
    C_SUCCESS = colors.HexColor("#059669")     # Green 600
    C_TEXT = colors.HexColor("#334155")        # Slate 700
    C_MUTED = colors.HexColor("#64748B")       # Slate 500
    C_BG_LIGHT = colors.HexColor("#F8FAFC")    # Slate 50
    C_BORDER = colors.HexColor("#E2E8F0")      # Slate 200

    # Typography Styles
    styles.add(ParagraphStyle(
        'DocSuperHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=C_ACCENT,
        textTransform='uppercase',
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=C_PRIMARY,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=C_MUTED,
        spaceAfter=14
    ))

    styles.add(ParagraphStyle(
        'SectionH1',
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=C_PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'SectionH2',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=C_CYAN,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'BodyDark',
        fontName='Helvetica',
        fontSize=9.2,
        leading=13.5,
        textColor=C_TEXT,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        'BodyDarkBold',
        fontName='Helvetica-Bold',
        fontSize=9.2,
        leading=13.5,
        textColor=C_PRIMARY,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        'CalloutText',
        fontName='Helvetica',
        fontSize=8.8,
        leading=13,
        textColor=C_TEXT
    ))

    styles.add(ParagraphStyle(
        'TableHead',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    ))

    styles.add(ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=8.2,
        leading=11,
        textColor=C_TEXT
    ))

    styles.add(ParagraphStyle(
        'TableCellBold',
        fontName='Helvetica-Bold',
        fontSize=8.2,
        leading=11,
        textColor=C_PRIMARY
    ))

    styles.add(ParagraphStyle(
        'CodeStyle',
        fontName='Courier',
        fontSize=7.8,
        leading=10.5,
        textColor=C_PRIMARY
    ))

    story = []

    # =========================================================================
    # PAGE 1: COVER & EXECUTIVE SPECIFICATION
    # =========================================================================
    story.append(Paragraph("SMART INDIA HACKATHON 2026 • PROBLEM STATEMENT ID: SIH26167", styles['DocSuperHeader']))
    story.append(Paragraph("SatQuery AI: System Architecture & Team Integration Handbook", styles['DocTitle']))
    story.append(Paragraph(
        "Interactive AI Assistant for Multimodal Remote-Sensing Image Analysis • "
        "Comprehensive Guide for Group Members, Project Mentors, and External Evaluators",
        styles['DocSubtitle']
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_ACCENT, spaceAfter=12))

    # Meta Info Card Table
    meta_data = [
        [
            Paragraph("<b>Project Name:</b> SatQuery AI", styles['TableCell']),
            Paragraph("<b>Problem Statement ID:</b> SIH26167", styles['TableCell'])
        ],
        [
            Paragraph("<b>Target Domain:</b> Space Technology / Defense / AI EO", styles['TableCell']),
            Paragraph("<b>Architecture:</b> 5-Tier Agentic Cognitive Core", styles['TableCell'])
        ],
        [
            Paragraph("<b>Frontend UI:</b> Streamlit 1.54 (Python)", styles['TableCell']),
            Paragraph("<b>Target Backend:</b> FastAPI / LangGraph Agent", styles['TableCell'])
        ],
        [
            Paragraph("<b>Core Sensors:</b> Optical MSI (Sentinel-2) + SAR (Sentinel-1)", styles['TableCell']),
            Paragraph("<b>Integration Protocol:</b> REST POST /api/v1/analyze", styles['TableCell'])
        ]
    ]
    t_meta = Table(meta_data, colWidths=[250, 254])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 14))

    # Executive Overview
    story.append(Paragraph("1. Executive Summary & Problem Context", styles['SectionH1']))
    story.append(Paragraph(
        "Earth Observation (EO) satellites continuously collect terabytes of multispectral optical and synthetic aperture radar (SAR) "
        "imagery. However, converting raw rasters into actionable geospatial intelligence currently requires deep domain expertise in GIS "
        "software (ArcGIS, QGIS), complex radiometric calibration, and manual tool chaining. Disaster responders, defense commanders, and "
        "policy analysts cannot afford hours of manual analysis during emergency operations.",
        styles['BodyDark']
    ))
    story.append(Paragraph(
        "<b>SatQuery AI</b> solves this problem statement by providing an <b>autonomous, natural-language vision-language assistant</b>. "
        "Users ask questions in plain English (e.g., <i>'Where are the fuel storage tanks?'</i> or <i>'Map flood extents through cloud cover'</i>). "
        "An intelligent agentic routing dispatcher tokenizes the inquiry, verifies spatial projections, and orchestrates specialized deep "
        "learning models—presenting verified visual bounding boxes, change heatmaps, and tri-factor confidence metrics without hallucination.",
        styles['BodyDark']
    ))

    # Key Architectural Innovations Callout Box
    key_innovations = [
        [Paragraph("<b>KEY ARCHITECTURAL HIGHLIGHTS FOR EVALUATORS & GUIDES</b>", styles['TableHead'])],
        [Paragraph(
            "<b>1. Autonomous Task Selection (Auto Detect):</b> Decouples non-expert users from GIS pipeline selection; routes questions to the optimal model dynamically.<br/>"
            "<b>2. Multimodal Optical + SAR Fusion:</b> Fuses Sentinel-2 optical reflectance with Sentinel-1 C-Band radar to achieve 100% cloud-penetrating flood and structure analysis.<br/>"
            "<b>3. Evidence-Grounded Outputs:</b> Every textual claim is tied directly to sub-pixel bounding boxes, segmentation masks, or radiometric difference tensors.<br/>"
            "<b>4. Mathematical Tri-Factor Confidence:</b> Replaces arbitrary LLM certainty with an orthogonal decomposition of spatial IoU, semantic entropy, and sensor calibration.",
            styles['CalloutText']
        )]
    ]
    t_innov = Table(key_innovations, colWidths=[504])
    t_innov.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('BACKGROUND', (0, 1), (-1, 1), C_BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, C_ACCENT),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t_innov)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: 5-TIER ENTERPRISE SYSTEM ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("2. Enterprise System Architecture (5-Tier Design)", styles['SectionH1']))
    story.append(Paragraph(
        "To ensure modularity, high testability, and clear separation of concerns across team members, "
        "SatQuery AI implements a <b>5-Tier Cognitive Pipeline</b>. The diagram below illustrates data flow from ingestion to presentation:",
        styles['BodyDark']
    ))

    # Embed High-Resolution System Architecture Graphic
    arch_img_path = base_dir / "assets" / "system_architecture.jpg"
    if arch_img_path.exists():
        story.append(RLImage(str(arch_img_path), width=7.0 * inch, height=3.94 * inch))
        story.append(Paragraph("<i>Figure 1: SatQuery AI Autonomous Multimodal System Architecture Blueprint</i>", styles['DocSubtitle']))
    story.append(Spacer(1, 8))

    # Tiered Breakdown Table
    tier_table_data = [
        [Paragraph("TIER", styles['TableHead']), Paragraph("NAME & SCOPE", styles['TableHead']), Paragraph("CORE COMPONENTS & DATA TRANSFORMATIONS", styles['TableHead'])],
        [
            Paragraph("<b>Tier 1</b>", styles['TableCellBold']),
            Paragraph("<b>Multimodal Ingestion Tier</b>", styles['TableCell']),
            Paragraph("Ingests Optical (Sentinel-2, WorldView-3), SAR Radar (Sentinel-1 VV/VH), GeoTIFF rasters, and user queries. Handles orthorectification, CRS projection (EPSG:4326), and radiometric calibration.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Tier 2</b>", styles['TableCellBold']),
            Paragraph("<b>Agentic Routing & Cognitive Dispatcher</b>", styles['TableCell']),
            Paragraph("Zero-shot NLP query classifier + spatial sanity validator. Uses a LangGraph state machine to parse intent and route inquiries to the appropriate specialist neural node.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Tier 3</b>", styles['TableCellBold']),
            Paragraph("<b>Specialist Neural Model Array</b>", styles['TableCell']),
            Paragraph("Array of 4 dedicated computer vision backbones: (1) RSVQA Engine, (2) Grounding DINO + SAM, (3) Siamese ResNet-50 Change Detector, and (4) Optical+SAR Co-Transformer.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Tier 4</b>", styles['TableCellBold']),
            Paragraph("<b>Evidence Synthesis & Calibration Tier</b>", styles['TableCell']),
            Paragraph("Converts model tensors into physical coordinates, generates radiometric change heatmaps, and computes the orthogonal Tri-Factor Confidence score.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Tier 5</b>", styles['TableCellBold']),
            Paragraph("<b>Presentation & Intelligence HUD</b>", styles['TableCell']),
            Paragraph("Reactive Streamlit user interface featuring multi-tab visual evidence viewer, 6-stage execution trace, conversational follow-up chat, and 1-click Markdown/JSON exports.", styles['TableCell'])
        ]
    ]
    t_tier = Table(tier_table_data, colWidths=[45, 135, 324])
    t_tier.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('BOX', (0, 0), (-1, -1), 1, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_tier)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: HOW THE SYSTEM WORKS (END-TO-END WORKFLOW)
    # =========================================================================
    story.append(Paragraph("3. Operational Lifecycle: How the System Works", styles['SectionH1']))
    story.append(Paragraph(
        "When an end user interacts with SatQuery AI, execution proceeds deterministically through a <b>7-stage pipeline</b> "
        "designed to prevent latency spikes and eliminate hallucinations:",
        styles['BodyDark']
    ))

    flow_steps = [
        ("Stage 1: User Ingestion & Mode Configuration", "The user uploads one or two satellite scenes (or selects pre-loaded realistic scenarios) and submits a plain-English question. The UI checks image dimensions, channels (RGB/NIR/dB), and file size (< 50MB)."),
        ("Stage 2: Query Parsing & Semantic Intent Classification", "The intent classifier extracts semantic entity tokens (e.g., 'fuel tanks', 'flooding', 'changes'). If mode is set to 'Auto Detect', the agent chooses between VQA, Grounding, Change Detection, or Optical+SAR fusion."),
        ("Stage 3: Spatial Alignment & Radiometric Normalization", "For bi-temporal comparisons, baseline Image A (T1) and post-event Image B (T2) are verified for spatial coregistration, coordinate reference system (CRS) compatibility, and resolution match."),
        ("Stage 4: Specialist Neural Pipeline Execution", "The routed specialist model processes the image tensors on the GPU backend: Grounding DINO detects bounding coordinates, Siamese ResNet extracts differential feature maps, or Co-Transformer fuses optical reflectance with radar."),
        ("Stage 5: Radiometric Thresholding & Mask Generation", "Raw neural logits are converted into human-interpretable visual evidence: binary change masks via Otsu thresholding, bounding boxes with sub-pixel coordinates, or heatmaps colored by magnitude."),
        ("Stage 6: Tri-Factor Confidence Calculation", "The platform computes the mathematical confidence score: C_total = w1*C_spatial + w2*C_semantic + w3*C_sensor. Predictions failing the confidence threshold (tau = 0.85) are flagged with caution badges."),
        ("Stage 7: Interactive Presentation & Reporting", "The Streamlit frontend renders the visual evidence in synchronized tabs (Original, Change Mask, Heatmap, Bounding Box), populates quantitative metrics, and records the 6-stage execution trace.")
    ]

    flow_table_data = [[Paragraph("STAGE", styles['TableHead']), Paragraph("WORKFLOW OPERATION & LOGIC", styles['TableHead'])]]
    for stage_title, stage_desc in flow_steps:
        flow_table_data.append([
            Paragraph(f"<b>{stage_title.split(':')[0]}</b>", styles['TableCellBold']),
            Paragraph(f"<b>{stage_title.split(':')[1]}:</b> {stage_desc}", styles['TableCell'])
        ])

    t_flow = Table(flow_table_data, colWidths=[90, 414])
    t_flow.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_CYAN),
        ('BOX', (0, 0), (-1, -1), 1, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 10))

    # Mathematical Rigor Box
    story.append(Paragraph("Mathematical Formulations (Defending Scientific Rigor)", styles['SectionH2']))
    math_table_data = [
        [Paragraph("MATHEMATICAL PRINCIPLE", styles['TableHead']), Paragraph("FORMULATION & SCIENTIFIC DEFENSE", styles['TableHead'])],
        [
            Paragraph("<b>Tri-Factor Confidence Metric</b>", styles['TableCellBold']),
            Paragraph("<b>C_total = w1·C_spatial + w2·C_semantic + w3·C_sensor</b><br/>"
                      "• <b>C_spatial:</b> Intersection over Union (IoU) of bounding box contours modulated by edge gradient sharpness (sigma_edge).<br/>"
                      "• <b>C_semantic:</b> Normalized Shannon entropy over prediction class distribution: 1 - H(P_cls)/ln(K).<br/>"
                      "• <b>C_sensor:</b> Radiometric calibration factoring atmospheric reflectance (rho_atm) and radar clutter-to-noise ratio (CNR).", styles['TableCell'])
        ],
        [
            Paragraph("<b>Bi-Temporal Radiometric Difference</b>", styles['TableCellBold']),
            Paragraph("<b>D_change(x, y) = || phi(I_T2)(x, y) - phi(I_T1)(x, y) ||_2</b><br/>"
                      "Deep feature distance extracted from Siamese ResNet-50 encoder phi(·). Invariant to seasonal illumination and sun angle variance.", styles['TableCell'])
        ]
    ]
    t_math = Table(math_table_data, colWidths=[150, 354])
    t_math.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('BOX', (0, 0), (-1, -1), 1, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_math)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4 & 5: TEAM MEMBER TASK DIVISION & INTEGRATION CONTRACT
    # =========================================================================
    story.append(Paragraph("4. Group Members: Work Division & Module Integration", styles['SectionH1']))
    story.append(Paragraph(
        "To enable seamless parallel development across your team, each member is assigned an independent, "
        "modular subsystem. Each module has clearly defined <b>Input/Output Data Contracts</b> so that when "
        "your backend service is connected, it integrates immediately into this frontend without code conflicts.",
        styles['BodyDark']
    ))

    # Tasks Matrix Table
    tasks_data = [
        [Paragraph("MODULE / SUBSYSTEM", styles['TableHead']), Paragraph("ASSIGNED ROLE", styles['TableHead']), Paragraph("KEY DELIVERABLES & MODELS", styles['TableHead']), Paragraph("INPUT / OUTPUT CONTRACT", styles['TableHead'])],
        [
            Paragraph("<b>Module 1</b><br/>NLP & Agentic Intent Router", styles['TableCellBold']),
            Paragraph("<b>Team Member 1</b><br/>(AI Orchestration)", styles['TableCell']),
            Paragraph("• Intent classifier classifying query into VQA, Grounding, Change, or Optical+SAR.<br/>• Entity extractor identifying target keywords.<br/>• LangGraph routing node.", styles['TableCell']),
            Paragraph("<b>Input:</b> Query string, available image count.<br/><b>Output:</b> detected_task object with id, title, reason, and selected model pipeline.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Module 2</b><br/>Visual Grounding & Localization", styles['TableCellBold']),
            Paragraph("<b>Team Member 2</b><br/>(Computer Vision)", styles['TableCell']),
            Paragraph("• Open-vocabulary object detector (Grounding DINO).<br/>• Zero-shot bounding boxes & sub-pixel coordinates.<br/>• Optional SAM mask generation.", styles['TableCell']),
            Paragraph("<b>Input:</b> Image A (RGB), prompt keywords.<br/><b>Output:</b> bboxes list with [ymin, xmin, ymax, xmax] normalized (0-1), labels, confidence scores.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Module 3</b><br/>Bi-Temporal Change Detection", styles['TableCellBold']),
            Paragraph("<b>Team Member 3</b><br/>(Deep Learning)", styles['TableCell']),
            Paragraph("• Siamese ResNet-50 / ChangeFormer network.<br/>• Pixel-wise differential feature extraction.<br/>• Binary change mask & continuous heatmap.", styles['TableCell']),
            Paragraph("<b>Input:</b> Image A (T1) + Image B (T2) paired rasters.<br/><b>Output:</b> Differential heatmap tensor (0-255), binary change mask, quantified delta metrics.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Module 4</b><br/>Optical + SAR Multimodal Fusion", styles['TableCellBold']),
            Paragraph("<b>Team Member 4</b><br/>(Radar & Cross-Sensor)", styles['TableCell']),
            Paragraph("• Cross-Attention Co-Transformer architecture.<br/>• Sentinel-1 C-Band backscatter calibration.<br/>• Cloud-penetrating flood/structure mapping.", styles['TableCell']),
            Paragraph("<b>Input:</b> Optical RGB raster + SAR VV/VH raster.<br/><b>Output:</b> Fused flood/feature mask, dB backscatter values, cloud obscuration percentage.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Module 5</b><br/>Remote Sensing VQA Engine", styles['TableCellBold']),
            Paragraph("<b>Team Member 5</b><br/>(Vision-Language AI)", styles['TableCell']),
            Paragraph("• Vision Transformer (ViT) + Multimodal Q-Former.<br/>• Complex spatial counting, environmental inventory, and facility description.", styles['TableCell']),
            Paragraph("<b>Input:</b> Image A raster + natural language question.<br/><b>Output:</b> Synthesized natural-language answer, summary_bullets list, confidence breakdown.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Module 6</b><br/>FastAPI Backend & Integration Client", styles['TableCellBold']),
            Paragraph("<b>Team Member 6</b><br/>(Backend & Deployment)", styles['TableCell']),
            Paragraph("• FastAPI microservice implementing POST /api/v1/analyze.<br/>• GPU inference worker deployment.<br/>• Session persistence and health probes.", styles['TableCell']),
            Paragraph("<b>Input:</b> Multipart form / JSON HTTP request.<br/><b>Output:</b> Standardized JSON payload matching frontend schema (see Section 5).", styles['TableCell'])
        ]
    ]
    t_tasks = Table(tasks_data, colWidths=[110, 85, 170, 139])
    t_tasks.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('BOX', (0, 0), (-1, -1), 1, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_tasks)
    story.append(Spacer(1, 10))

    # Integration Workflow Note
    story.append(Paragraph("How the Frontend Connects to Your Backend Models", styles['SectionH2']))
    story.append(Paragraph(
        "Currently, SatQuery AI includes a <b>High-Fidelity Simulation Engine</b> (<code>services/mock_service.py</code>) "
        "that allows you to demo and test the entire UI immediately offline. To connect your live models: "
        "<br/>1. Team Member 6 hosts the FastAPI backend server implementing the <code>POST /api/v1/analyze</code> endpoint."
        "<br/>2. Toggle <b>Demo Simulation Mode to OFF</b> in the sidebar (or configure <code>SATQUERY_BACKEND_URL</code>)."
        "<br/>3. The frontend REST client (<code>services/api_client.py</code>) dispatches the images and query, automatically unpacking the returned evidence onto the dashboard.",
        styles['BodyDark']
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 6: API JSON CONTRACT & TECHNICAL SPECIFICATIONS
    # =========================================================================
    story.append(Paragraph("5. API Contract Specifications (REST & JSON Schema)", styles['SectionH1']))
    story.append(Paragraph(
        "To ensure all group members build backend endpoints that plug directly into the frontend, "
        "implement the following standardized request and response payload schemas:",
        styles['BodyDark']
    ))

    # Request Code Snippet
    req_json = (
        "// POST /api/v1/analyze (multipart/form-data or application/json)\n"
        "{\n"
        '  "query": "Where are the fuel storage tanks and what changed between dates?",\n'
        '  "mode": "auto_detect",          // auto_detect | single_image | compare_images | optical_sar\n'
        '  "metadata_a": {\n'
        '    "sensor": "Sentinel-2 MSI",\n'
        '    "acquisition_date": "2024-06-15",\n'
        '    "crs": "EPSG:4326",\n'
        '    "resolution": "0.5m/px"\n'
        "  },\n"
        '  "metadata_b": {\n'
        '    "sensor": "Sentinel-2 MSI",\n'
        '    "acquisition_date": "2026-03-20"\n'
        "  },\n"
        '  "image_a": "<binary_stream_or_base64>",\n'
        '  "image_b": "<optional_binary_stream_or_base64>"\n'
        "}"
    )

    resp_json = (
        "// Standardized Response Payload returned to Frontend\n"
        "{\n"
        '  "status": "success",\n'
        '  "analysis_id": "SQ-84920",\n'
        '  "detected_task": {\n'
        '    "id": "change_detection",     // vqa | visual_grounding | change_detection | optical_sar_fusion\n'
        '    "title": "Bi-Temporal Change Detection",\n'
        '    "reason": "Query requests differential evaluation between 2024 and 2026.",\n'
        '    "model_pipeline": "Siamese ResNet-50 + Differential Feature Attention"\n'
        "  },\n"
        '  "answer": "Significant industrial expansion identified between 2024 and 2026...",\n'
        '  "confidence": 0.93,\n'
        '  "confidence_breakdown": { "spatial": 0.95, "semantic": 0.92, "sensor": 0.96 },\n'
        '  "summary_bullets": [\n'
        '    "5 newly constructed logistics warehouses identified.",\n'
        '    "3.4 km of asphalt road network laid."\n'
        "  ],\n"
        '  "metrics": {\n'
        '    "New Facilities": { "value": "5", "unit": "Buildings" },\n'
        '    "Built Footprint": { "value": "43,200", "unit": "m²" }\n'
        "  },\n"
        '  "analysis_trace": [\n'
        '    { "step": 1, "stage": "Query Understanding", "latency": "140ms" },\n'
        '    { "step": 2, "stage": "Specialist Inference", "latency": "1.2s" }\n'
        "  ]\n"
        "}"
    )

    t_api_code = Table([
        [Paragraph("EXPECTED API REQUEST PAYLOAD", styles['TableHead']), Paragraph("EXPECTED API RESPONSE PAYLOAD", styles['TableHead'])],
        [Paragraph(f"<pre>{req_json}</pre>", styles['CodeStyle']), Paragraph(f"<pre>{resp_json}</pre>", styles['CodeStyle'])]
    ], colWidths=[246, 258])
    t_api_code.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('BACKGROUND', (0, 1), (-1, 1), C_BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_api_code)
    story.append(Spacer(1, 10))

    # Technical Specifications Summary
    story.append(Paragraph("6. Project Technical Profile & Quick Reference", styles['SectionH1']))
    spec_table_data = [
        [Paragraph("PARAMETER", styles['TableHead']), Paragraph("SPECIFICATION", styles['TableHead']), Paragraph("NOTES / PURPOSE", styles['TableHead'])],
        [Paragraph("<b>Core Framework</b>", styles['TableCellBold']), Paragraph("Streamlit 1.54.0 (Python 3.10+)", styles['TableCell']), Paragraph("Reactive web UI, modular routing, and HUD presentation", styles['TableCell'])],
        [Paragraph("<b>Dependencies</b>", styles['TableCellBold']), Paragraph("pillow, numpy, pandas, plotly, requests", styles['TableCell']), Paragraph("Raster processing, matrix math, orbital maps, and REST client", styles['TableCell'])],
        [Paragraph("<b>Default Port</b>", styles['TableCellBold']), Paragraph("8501 (http://localhost:8501)", styles['TableCell']), Paragraph("Local workstation or cloud server container mapping", styles['TableCell'])],
        [Paragraph("<b>Startup Command</b>", styles['TableCellBold']), Paragraph("streamlit run app.py", styles['TableCell']), Paragraph("Launches application with persistent session state", styles['TableCell'])],
        [Paragraph("<b>Upload Limits</b>", styles['TableCellBold']), Paragraph("Max 50 MB per file", styles['TableCell']), Paragraph("Configured in config/settings.py via MAX_UPLOAD_SIZE_MB", styles['TableCell'])],
        [Paragraph("<b>Supported Formats</b>", styles['TableCellBold']), Paragraph(".tif, .tiff, .geotiff, .png, .jpg, .jpeg", styles['TableCell']), Paragraph("Standard satellite rasters & multi-band GeoTIFFs", styles['TableCell'])],
        [Paragraph("<b>Themes Available</b>", styles['TableCellBold']), Paragraph("Dark Orbit • Enterprise Obsidian • Light Cleanroom", styles['TableCell']), Paragraph("Configurable via single dropdown in System Settings", styles['TableCell'])]
    ]
    t_spec = Table(spec_table_data, colWidths=[110, 160, 234])
    t_spec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_CYAN),
        ('BOX', (0, 0), (-1, -1), 1, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_spec)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    return str(output_path)


if __name__ == "__main__":
    pdf_file = build_pdf()
    print(f"Successfully generated PDF: {pdf_file}")
