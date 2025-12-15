from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from pydantic import BaseModel
import shutil
import os
import tempfile
from app.services.scanner import ScanService
from app.services.fixer import FixService
from app.services.dependency_scanner import DependencyScanner
from app.services.ast_scanner import ASTScanner

router = APIRouter()

# Store uploaded file path temporarily for MVP (Not production safe!)
# In a real app, manage sessions or IDs.
CURRENT_FILE_PATH = None

class FixRequest(BaseModel):
    vulnerability_id: str
    line: int
    content: str # Original content
    
class ApplyFixRequest(BaseModel):
    line: int
    new_content: str
    file_path: str

class ScanPathRequest(BaseModel):
    path: str

class VerifyVulnRequest(BaseModel):
    content: str
    type: str

import subprocess

@router.post("/verify-vuln")
async def verify_vuln(request: VerifyVulnRequest):
    result = FixService.verify_vulnerability(request.dict())
    return result

@router.post("/scan-path")
async def scan_path(request: ScanPathRequest):
    if not os.path.exists(request.path) or not os.path.isdir(request.path):
        raise HTTPException(status_code=400, detail="Invalid directory path")
    
    results = []
    
    # Walk directory
    ignored_dirs = {'.git', '.venv', 'venv', 'env', 'node_modules', '__pycache__', '.idea', '.vscode', 'lib', 'site-packages', 'build', 'dist'}
    
    for root, dirs, files in os.walk(request.path):
        # Modify dirs in-place to skip ignored directories (case-insensitive)
        original_dirs = list(dirs)
        dirs[:] = [d for d in dirs if d.lower() not in ignored_dirs]
        
        print(f"Scanning: {root}")
        
        for file in files:
            file_path = os.path.join(root, file)
            file_lower = file.lower()
            
            # 1. Code Files
            if file.endswith(('.py', '.js', '.ts', '.tsx', '.jsx')):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    vulns = ScanService.scan_content(content)
                    
                    # Enhanced Analysis: Run AST Scanner for Python files
                    if file.endswith('.py'):
                        try:
                            ast_vulns = ASTScanner.scan_content(content)
                            # Dedup logic could go here, for now just append
                            vulns.extend(ast_vulns)
                        except Exception as ast_err:
                            print(f"AST Scan Error {file}: {ast_err}")

                    if vulns:
                        results.append({
                            "filename": file,
                            "filepath": os.path.abspath(file_path),
                            "vulnerabilities": vulns,
                            "content": content
                        })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

            # 2. Dependency Files
            elif file_lower in ['requirements.txt', 'package.json']:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    vulns = DependencyScanner.scan_dependencies(file, content)
                    if vulns:
                        results.append({
                            "filename": file,
                            "filepath": os.path.abspath(file_path),
                            "vulnerabilities": vulns,
                            "content": content
                        })
                except Exception as e:
                    print(f"Error scanning dependency {file_path}: {e}")
                    
    return {"files": results}

@router.get("/browse")
async def browse_folder():
    """
    Opens a native Windows folder picker dialog on the server side (user's machine).
    Returns the selected path.
    """
    try:
        # PowerShell command to open FolderBrowserDialog
        ps_script = """
        Add-Type -AssemblyName System.Windows.Forms
        $f = New-Object System.Windows.Forms.FolderBrowserDialog
        $f.Description = "Select a project directory to scan"
        $f.ShowNewFolderButton = $true
        if ($f.ShowDialog() -eq 'OK') {
            Write-Output $f.SelectedPath
        }
        """
        
        # Run PowerShell command
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        path = result.stdout.strip()
        if path:
            return {"path": path}
        else:
            return {"path": ""} # User cancelled
            
    except Exception as e:
        print(f"Browse Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Legacy upload endpoint kept for reference or removal
@router.post("/upload")
async def upload_file(files: List[UploadFile] = File(...)):
    # ... legacy implementation ...
    return {"files": []} 


@router.post("/generate-fix")
async def generate_fix(request: FixRequest):
    # In a real scenario, we might re-read the file or send more context to the AI
    # Here we just use the fix service mock
    result = FixService.generate_fix({
        "content": request.content
    })
    return result

@router.post("/apply-fix")
async def apply_fix(request: ApplyFixRequest):
    # We now allow edits to any file path provided by scan-path
    if not os.path.exists(request.file_path):
         raise HTTPException(status_code=400, detail="File not found")

    success = FixService.apply_fix(request.file_path, request.line, request.new_content)
    
    if success:
        return {"status": "success", "message": "Fix applied"}
    else:
        raise HTTPException(status_code=500, detail="Failed to apply fix")
