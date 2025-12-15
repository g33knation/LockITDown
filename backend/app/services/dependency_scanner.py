import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini (re-using key from env)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class DependencyScanner:
    @staticmethod
    def scan_dependencies(filename: str, content: str) -> list:
        """
        Scans dependency files (requirements.txt, package.json) using Gemini
        to identify insecure or outdated packages.
        """
        if not GOOGLE_API_KEY:
            return []

        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            
            prompt = f"""
            You are a software security expert. Analyze the following dependency file ({filename}) for security vulnerabilities.
            
            Content:
            {content}
            
            Task:
            Identify any packages that have **KNOWN HIGH-RISK VULNERABILITIES** (CVEs) or are significantly outdated and dangerous.
            Ignore standard/safe packages. Only report real threats.
            
            Output JSON ONLY list of objects. If none, return [].
            Format:
            [
                {{
                    "package": "package_name",
                    "version": "version_string",
                    "severity": "HIGH" | "CRITICAL",
                    "issue": "Brief description of vulnerability (e.g. CVE-2023-XXXX)"
                }}
            ]
            """
            
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            results = json.loads(response.text.strip())
            
            # Map to standard vulnerability format
            vulns = []
            for item in results:
                # Find line number (simple substring match)
                line_no = 1
                for i, line in enumerate(content.splitlines()):
                    if item['package'] in line:
                        line_no = i + 1
                        break
                
                vulns.append({
                    "id": f"dep-{item['package']}",
                    "line": line_no,
                    "content": f"{item['package']} {item.get('version', '')}",
                    "type": "Insecure Dependency",
                    "severity": item.get('severity', "HIGH"),
                    "description": item.get('issue', "Potential security risk")
                })
                
            return vulns
            
        except Exception as e:
            print(f"Dependency Scan Error: {e}")
            return []
