"""
SatQuery AI - Export and Report Generation Utilities
Exports analysis results to formatted Markdown, JSON, and text summaries.
"""

import json
from datetime import datetime
from typing import Dict, Any


def generate_markdown_report(result: Dict[str, Any], query: str, task: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
    """Generate comprehensive analysis report in Markdown."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    confidence_pct = int(result.get("confidence", 0.90) * 100)
    
    report = f"""# SatQuery AI — Geospatial Analysis Intelligence Report
**Platform:** Multi-Sensor Earth Observation Intelligence  
**Generated At:** {timestamp}  
**Report Reference:** {result.get("analysis_id", "ANL-EXPORT")}

---

## 1. Executive Summary
- **Natural Language Query:** *"{query}"*
- **Autonomous Routed Workflow:** **{task.get("title", "Multimodal Remote Sensing")}**
- **Decision Confidence:** **{confidence_pct}%** ({'High' if confidence_pct >= 85 else 'Moderate'} Confidence)
- **Primary AI Insight:**  
  > {result.get("answer", "No answer generated.")}

---

## 2. Key Findings & Detected Quantities
"""
    for bullet in result.get("summary_bullets", []):
        report += f"- {bullet}\n"

    metrics = result.get("metrics", {})
    if metrics:
        report += "\n### Quantitative Metrics Table\n"
        report += "| Metric Indicator | Quantified Value | Measurement Units |\n"
        report += "| :--- | :--- | :--- |\n"
        for k, v in metrics.items():
            report += f"| {k} | {v.get('value', 'N/A')} | {v.get('unit', '')} |\n"

    report += f"""
---

## 3. Confidence Decomposition
- **Spatial Grounding Accuracy:** {int(result.get("confidence_breakdown", {}).get("spatial", 0.92) * 100)}%
- **Semantic Alignment:** {int(result.get("confidence_breakdown", {}).get("semantic", 0.90) * 100)}%
- **Sensor Data Integrity:** {int(result.get("confidence_breakdown", {}).get("sensor", 0.95) * 100)}%

---

## 4. Agentic Execution Trace
"""
    for idx, trace in enumerate(result.get("analysis_trace", []), 1):
        if isinstance(trace, dict):
            stage = trace.get("stage", "Stage")
            details = trace.get("details", "")
            latency = trace.get("latency", "N/A")
        else:
            # Backend may currently return trace entries as plain strings.
            stage = "Stage"
            details = str(trace)
            latency = "N/A"

        report += (
            f"{idx}. **{stage}**: {details} "
            f"*(Latency: {latency})*\n"
        )
    return report.strip()


def generate_json_report(result: Dict[str, Any], query: str, task: Dict[str, Any]) -> str:
    """Generate structured JSON representation of the analysis."""
    payload = {
        "system_spec": "Autonomous Earth Observation Intelligence",
        "system": "SatQuery AI",
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "routed_task": task,
        "result": {
            "answer": result.get("answer"),
            "confidence": result.get("confidence"),
            "confidence_breakdown": result.get("confidence_breakdown"),
            "metrics": result.get("metrics"),
            "summary_bullets": result.get("summary_bullets")
        },
        "execution_trace": result.get("analysis_trace", [])
    }
    return json.dumps(payload, indent=2)
