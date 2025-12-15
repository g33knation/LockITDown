from typing import List, Dict
import re

class ScanService:
    @staticmethod
    def scan_content(content: str) -> list:
        vulnerabilities = []
        lines = content.split('\n')
        
        # Regex Patterns for Common Secrets & Insecure Functions
        patterns = [
            # AWS Access Key ID (AKI...) - Case Sensitive (Uppercase)
            {"name": "AWS Access Key", "pattern": r"(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])", "type": "Secret", "severity": "CRITICAL"},
            # Generic API Key - Case Insensitive
            {"name": "Hardcoded API Key", "pattern": r"(?i)(api_key|apikey|secret|token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]", "type": "Secret", "severity": "HIGH"},
            # Hardcoded Password - Case Insensitive
            {"name": "Hardcoded Password", "pattern": r"(?i)(password|passwd|pwd)\s*=\s*['\"][^'\"]{3,}['\"]", "type": "Secret", "severity": "HIGH"},
            # Insecure function: eval() - Negative lookbehind for word char or dot (excludes .eval, literal_eval)
            {"name": "Insecure Function (eval)", "pattern": r"(?<![\w.])eval\(", "type": "Insecure Code", "severity": "MEDIUM"},
             # Insecure function: exec() - Negative lookbehind (excludes .exec for JS, os.exec)
            {"name": "Insecure Function (exec)", "pattern": r"(?<![\w.])exec\(", "type": "Insecure Code", "severity": "MEDIUM"},
        ]

        for i, line in enumerate(lines):
            for p in patterns:
                match = re.search(p["pattern"], line)
                if match:
                    # Filter out commented lines (basic check)
                    stripped = line.strip()
                    if stripped.startswith('#') or stripped.startswith('//'):
                        continue
                    
                    # Filter out matches that obey 'Safe' rules (e.g. literal_eval, .exec)
                    # We rely on regex boundaries now: (?<![\w.]) matches only standalone calls
                    
                    # Filter out matches inside strings (Heuristic: Odd number of quotes before match)
                    # ONLY apply this for Code Execution checks (eval, exec).
                    # Secrets (passwords, keys) ARE usually inside strings, so we must allow them.
                    if p['type'] == 'Insecure Code':
                        start_idx = match.start()
                        prefix = line[:start_idx]
                        if prefix.count('"') % 2 == 1 or prefix.count("'") % 2 == 1:
                            continue

                    print(f"DEBUG: Vuln found [{p['name']}]: {stripped} (Matched: {match.group(0)})")
                        
                    vulnerabilities.append({
                        "id": f"vuln-{i}-{p['name'].replace(' ', '')}",
                        "line": i + 1,
                        "content": line,
                        "type": p["name"],
                        "severity": p["severity"]
                    })
                    
        return vulnerabilities
