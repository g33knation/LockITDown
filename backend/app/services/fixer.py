import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load env vars (if not already loaded)
load_dotenv()

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class FixService:
    @staticmethod
    def generate_fix(vulnerability: dict) -> dict:
        """
        Generates a fix using Google Gemini.
        """
        original_line = vulnerability.get("content", "")
        
        if not GOOGLE_API_KEY:
            return {
                "original_snippet": original_line,
                "fixed_snippet": original_line + " # ERROR: GOOGLE_API_KEY not set",
                "explanation": "Please set GOOGLE_API_KEY in .env to use AI features."
            }

        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            
            prompt = f"""
            You are a security expert. Fix the provided insecure code snippet.
            RULES:
            1. ONLY return the secure code line. No markdown, no explanations.
            2. Replace hardcoded secrets with `os.getenv('CONSTANT_NAME')`.
            3. Do NOT wrap the `os.getenv` call in quotes. 
               Correct: `password = os.getenv('PASSWORD')`
               password = os.getenv('PASSWORD')
            4. Preserve indentation.

            Insecure Code:
            {original_line}
            
            Secure Code:
            """
            
            response = model.generate_content(prompt)
            fixed_code = response.text.strip()
            
            # Clean up potential markdown formatting
            fixed_code = fixed_code.replace('```python', '').replace('```', '').strip()
            
            print(f"DEBUG: Fix generated for '{original_line.strip()}': '{fixed_code}'")

            return {
                "original_snippet": original_line,
                "fixed_snippet": fixed_code,
                "explanation": "AI-generated secure replacement."
            }
            
        except Exception as e:
            print(f"Gemini Error: {e}")
            return {
                "original_snippet": original_line,
                "fixed_snippet": original_line + f" # Error generating fix",
                "explanation": "Failed to contact AI service."
            }

    @staticmethod
    def apply_fix(file_path: str, line_number: int, new_content: str) -> bool:
        """
        Applies the fix by replacing the specific line in the file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if 0 <= line_number - 1 < len(lines):
                # Maintain indentation
                original_indent = lines[line_number - 1][:len(lines[line_number - 1]) - len(lines[line_number - 1].lstrip())]
                lines[line_number - 1] = original_indent + new_content.strip() + '\n'
                
                # SMART IMPORT LOGIC:
                # If we introduced 'os.' and 'import os' is missing, inject it.
                if 'os.' in new_content:
                    has_os_import = any(l.strip().startswith('import os') or l.strip().startswith('from os') for l in lines)
                    if not has_os_import:
                        print("DEBUG: Injecting 'import os' for smart fix.")
                        # Insert at top, but try to skip shebang or encoding headers if possible
                        # For MVP, just index 0 or 1 if shebang
                        insert_idx = 0
                        if lines and lines[0].startswith('#!'):
                            insert_idx = 1
                        lines.insert(insert_idx, "import os\n")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return True
            return False
        except Exception as e:
            print(f"Error applying fix: {e}")
            return False

    @staticmethod
    def verify_vulnerability(vulnerability: dict) -> dict:
        """
        Asks Gemini if a vulnerability is a False Positive.
        """
        if not GOOGLE_API_KEY:
            return {"analysis": "AI not configured.", "is_false_positive": False, "confidence": 0.0}

        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            
            prompt = f"""
            You are a senior security engineer. Analyze this finding from a static analysis tool.
            
            Code Context:
            {vulnerability.get('content', '')}
            
            Vulnerability Type: {vulnerability.get('type', 'Unknown')}
            
            Task:
            Determine if this is a FALSE POSITIVE.
            1. If it's a test file, print statement, or safe usage, it's a False Positive.
            2. If it's a real hardcoded secret or dangerous function, it's a True Positive.
            
            Output JSON ONLY:
            {{
                "is_false_positive": boolean,
                "confidence": float (0.0 to 1.0),
                "reasoning": "brief explanation"
            }}
            """
            
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text.strip()) # simplistic parsing, preferably use json.loads
            
        except Exception as e:
            print(f"Verification Error: {e}")
            return {"analysis": "Error during verification.", "is_false_positive": False, "confidence": 0.0}
