# Walkthrough

<p align="left">
  <img src="https://img.shields.io/badge/Build_Trace-BT--006-blue?style=for-the-badge" alt="Build Trace ID" />
  <img src="https://img.shields.io/badge/Module-Core-0052cc?style=for-the-badge" alt="Module Type" />
</p>

---

## Purpose
Allows the researcher to step sequentially through the reasoning chain that advanced the investigation.

## Why It Exists

> [!NOTE]
> Designed to teach the user *how* to think about the investigation.

Rather than just showing the final graph, the walkthrough reconstructs the logic step-by-step, explicitly focusing on the **"Why Did We Move Here?"** transitions.

## Research Significance

> [!IMPORTANT]
> **Strict Reasoning Enforcement:** Enforces the strict ordering of the E → C → I → H → X framework. It ensures moving from an Inference to a Hypothesis is viewed as a structured bet, not a proven fact. It explicitly flags future steps as `PENDING` to prevent hallucinating results.

## Key Interactions
- **Step Rail Navigation:** Utilizes the Left Rail for step navigation and tracking progress.
- **Trace Visualization:** Uses the Center Graph to display tracing context dynamically.
- **Dossier Integration:** Shares the Node Dossier logic for deep-dive context without redundant code.

## Implementation Path
`src/features/core/walkthrough/`
