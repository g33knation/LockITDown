# LockITDown - Code Security Auditor

An intelligent, local-first security scanner for your codebases.

## Features

-   **Smart Scanning**: Detects hardcoded secrets (AWS keys, passwords) and insecure functions (`eval`, `exec`).
-   **Deep Analysis**: Uses AST (Abstract Syntax Tree) to understand code structure, not just text matching.
-   **Dependency Audit**: Checks `requirements.txt` and `package.json` for insecure libraries using AI.
-   **AI Verification**: "Second Opinion" button to have AI confirm if a bug is real or false positive.
-   **Auto-Fix**: One-click fixes for found vulnerabilities (powered by Gemini).
-   **Local & Secure**: Runs on `localhost`. Your code stays on your machine (except for snippets sent to AI for verification/fixing).

## Getting Started

### Prerequisites
-   Python 3.8+
-   Node.js & npm

### 1. Backend Setup
```bash
cd backend
# Create .env file with your GOOGLE_API_KEY
pip install -r requirements.txt
uvicorn main:app --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Usage
1.  Open `http://localhost:5173`.
2.  Click **Browse** to select a project folder.
3.  Click **Scan**.
4.  Review findings and use **Verify** or **Fix It**.

---
*Generated for LockITDown MVP.*
