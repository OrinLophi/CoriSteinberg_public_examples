# Mobile Automation & AI Tooling — Portfolio Examples

This repository contains a selection of production and framework-level code from my work in mobile application cybersecurity automation. The files here represent a cross-section of a larger platform I designed and built at NowSecure: shared base libraries, cross-platform automation templates, and AI-powered data tooling.

---

## What This Repo Demonstrates

These aren't isolated scripts. They represent pieces of a coherent framework built to scale across a distributed team of nine engineers operating on Android and iOS, across hundreds of applications and clients.

The platform I built included:

- **Shared base libraries** with typed data models, standardized error taxonomy, and reusable element interaction utilities (Android/Python and iOS/Swift)
- **Templated automation projects** generated via CLI tooling — engineers bootstrapped new projects from versioned templates rather than starting from scratch
- **Structured telemetry (RunData)** embedded within scripts themselves, enabling consistent measurement and quality tracking across all automations
- **AI-powered screenshot analysis** integrated into the assessment data pipeline, surfacing results through the API for the first time
- **Case studies** — three essays on systems thinking and design.

---

## Files

### `screenshotanalysis.py`
**AI-powered mobile app authentication analysis**

Orchestrates screenshot-based login verification across mobile application security assessments. Retrieves app data from a configurable API endpoint, submits screenshots to an AI analysis workflow, and outputs structured results as CSV and JSON.

Key design decisions:
- Two-pass architecture: pulls assessment index first, then enriches in batches — avoids overloading the upstream API
- Checkpointing via JSON output — runs are resumable if interrupted
- Retry logic with graceful failure handling and per-app error logging
- LLM prompt logic and OpenAI integration live in the orchestration layer (Retool workflow triggered via webhook); this script handles batching, retry, and output formatting

> Built as a production POC in a single day. Webhook endpoints are configurable via environment variables; in a production system these would be fully externalized.

---

### `models.py` + `workflow.py` + `standard_functions.py` (Android / Python Appium)
**Cross-platform Android automation framework — shared base library and workflow template**

`models.py` is the shared base library imported by all Android automation scripts. It provides:
- `RunData` — a typed dataclass capturing login success, error codes, actions completed, and platform metadata. Written to the platform via `driver.log_event()` at session end, enabling consistent measurement across all automations
- `ErrorCodes` — a standardized enum taxonomy covering all known failure states, with human-readable descriptions
- Reusable element interaction utilities: `wait_for`, `wait_exist`, `tap_if_exists`, `force_tap_elem`, `scroll`, `permission`, `handle_chrome`
- Login validation logic including `login_success_fallback` — XML tree traversal with keyword matching for cases where primary element detection fails
- Credential loading via `load_creds` — dynamic config ingestion supporting multiple data structures

`workflow.py` is the automation template. Engineers filled in `{{CODE}}` with app-specific interaction logic. Everything else — session launch, error handling, RunData logging, session teardown — was inherited from the framework.

---

### `IOS_AutomationUITests.swift` + `workFlow.swift` (iOS / XCUITest)
**Cross-platform iOS automation framework — shared base library and workflow template**

The Swift equivalent of the Android framework, designed to share the same data model conventions and error taxonomy across platforms.

`IOS_AutomationUITests.swift` provides:
- `RunData` struct — mirrors the Android RunData model for cross-platform consistency
- `FieldsConfig` — typed credential ingestion from platform config
- XCTest extensions: `waitForElementToAppear`, `takeScreenshot`, `arbitraryWait`, `confirm_login`
- `confirm_login` — multi-stage login validation with configurable success/error elements, fallback keyword scanning, and secure text field detection
- OSLog extensions for structured logging to the platform
- XCUIApplication extensions: `tapByVector`, `tapCoordinate`, `showDebugTree`
- Quiescence swizzle — disables XCTest's idle-waiting behavior for apps with persistent animations

`workFlow.swift` is the iOS automation template, structured to mirror the Android workflow pattern. Credential injection, session management, and RunData logging are handled by the framework.

---

## Design Philosophy

**Standardization over heroics.** The goal was to make every engineer on the team produce consistent, measurable output — not to write impressive one-off scripts. The framework handled the hard parts so engineers could focus on app-specific logic.

**Data as a first-class output.** RunData wasn't an afterthought. It was designed into the framework from the start so that every automation produced structured telemetry, enabling quality tracking and performance measurement at scale.

**Build for the failure case.** Error taxonomy, retry logic, fallback validation, and checkpointing were all built in because production automation fails in ways you don't predict. The framework anticipated that.

---

## Background

These files are sanitized samples from production work at NowSecure, a mobile application cybersecurity company. Sensitive credentials, client identifiers, and proprietary API endpoints have been removed or replaced with placeholders.

---

*More examples available on request. Additional tooling — including data pipeline infrastructure, GraphQL extraction scripts, and AI prompt engineering frameworks — available for discussion in context.*
