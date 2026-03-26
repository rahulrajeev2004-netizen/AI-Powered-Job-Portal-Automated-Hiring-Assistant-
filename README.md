# Zecpath AI Development Environment

This repository contains the core AI systems for the Zecpath project, including resume parsing, applicant tracking (ATS) scoring, and AI-driven candidate screening and interviewing. 

## Project Structure

The project follows a modular architecture designed to separate concerns and scale easily:

* **`/data/`**: Stores raw and processed datasets, sample resumes, JD (Job Description) files, and system-generated outputs.
* **`/parsers/`**: Contains scripts and modules dedicated to extracting structured text and features out of unstructured files (like PDFs, DOCX). Includes OCR tools or formatting normalizers.
* **`/ats_engine/`**: The core ATS logic. This module manages applicant tracking score calculations, matching a structured parsed resume against job criteria.
* **`/screening_ai/`**: Hosts logic for candidate pre-screening interactions, rule-based text evaluation, or early-stage LLM question answering flows.
* **`/interview_ai/`**: Advanced models or pipeline configurations designed for simulated technical or behavioral interviewing.
* **`/scoring/`**: Centralized machine learning or heuristic logic that normalizes and calculates the final candidate fitness score.
* **`/utils/`**: Utilities and helper functions that span multiple modules, including our centralized `logger.py`, database connector wrappers, and any third-party API clients.
* **`/tests/`**: Automated unit and integration tests. Structured to mirror the source directories for easy test location.
* **`requirements.txt`**: Standard Python libraries required to run and test this repository (e.g., NumPy, Pandas, Scikit-learn, PyTest).

## Setup Instructions

### Environment Setup
1. **Initialize Virtual Environment**:
   ```powershell
   python -m venv env
   ```
   **Note for Windows (PowerShell) users:** If you encounter a script disabled error, adjust your execution policy or use Command Prompt, or run the activation script like this:
   ```powershell
   Set-ExecutionPolicy Unrestricted -Scope CurrentUser
   .\env\Scripts\activate
   ```
2. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

## Development and Coding Standards

### 1. Code Style
* Format code using **Black** (`black .`).
* Ensure code follows **PEP 8** standards (verifiable via `pylint`).
* Define type hints in function signatures and use comprehensive docstrings for all classes and methods.

### 2. Documentation Format
* **Docstrings**: We standardize on the reStructuredText (Sphinx) or Google docstring format outlining Parameters (`Args`), Returns (`Returns`), and Exceptions (`Raises`).
* Each folder must contain its own mini `README.md` explaining the domain-specific logic.

### 3. Logging Standard
* Do **not** use `print()` in production AI code.
* Always import the global logger from `utils.logger`:
   ```python
   from utils.logger import get_logger
   logger = get_logger(__name__)
   
   logger.info("Initializing parser module...")
   ```
* All logs are saved across rotating files in the `logs/` directory and echoed to standard output during testing.

### 4. Testing Standard
* All new logic must include a matching test file in `/tests/`.
* We use `pytest` as our testing framework. Run tests locally ensuring tests pass before submitting a pull request.
   ```powershell
   pytest
   ```
* Ensure you cover edge cases and mocked API calls (e.g., when connecting to OpenAI or HuggingFace).
.....
