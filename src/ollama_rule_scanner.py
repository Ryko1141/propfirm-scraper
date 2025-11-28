"""
Ollama-Powered Account Rule Violation Scanner
Analyzes MT5 account data and checks database for rule violations using LLM
"""
import asyncio
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import sqlite3
from dataclasses import dataclass, asdict


@dataclass
class RuleViolation:
    """Rule violation detected by scanner"""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    rule_type: str  # hard_rule, soft_rule
    category: str  # daily_drawdown, total_drawdown, lot_size, etc.
    description: str
    current_value: Optional[float]
    threshold_value: Optional[float]
    firm_name: Optional[str]
    recommendation: str
    timestamp: str


class OllamaRuleScanner:
    """Scan account data for rule violations using Ollama LLM"""
    
    def __init__(self, 
                 ollama_url: str = "http://localhost:11434",
                 model: str = "qwen2.5-coder:14b",
                 db_path: str = "propfirm_scraper.db"):
        """
        Initialize Ollama rule scanner
        
        Args:
            ollama_url: Ollama API base URL
            model: Model name (qwen2.5-coder, llama3.2, mistral, etc.)
            db_path: Path to propfirm database
        """
        self.ollama_url = ollama_url
        self.model = model
        self.db_path = db_path
        
    def _query_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Query Ollama API"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent analysis
                    "top_p": 0.9
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            print(f"   Sending request to Ollama (model: {self.model})...")
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120  # Increased timeout for larger models
            )
            response.raise_for_status()
            
            result = response.json()
            llm_response = result.get("response", "")
            
            print(f"   Received response ({len(llm_response)} chars)")
            
            if not llm_response:
                print("   ⚠️  Warning: Empty response from Ollama")
            
            return llm_response
            
        except requests.exceptions.Timeout:
            print(f"   ❌ Ollama request timed out after 120 seconds")
            return ""
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Ollama API error: {e}")
            return ""
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return ""
    
    def _get_firm_rules_from_db(self, firm_name: Optional[str] = None) -> List[Dict]:
        """Retrieve rules from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if firm_name:
                query = """
                    SELECT fr.*, pf.name as firm_name
                    FROM firm_rule fr
                    JOIN prop_firm pf ON fr.firm_id = pf.id
                    WHERE LOWER(pf.name) LIKE LOWER(?)
                    ORDER BY fr.severity DESC, fr.rule_type
                """
                cursor.execute(query, (f"%{firm_name}%",))
            else:
                query = """
                    SELECT fr.*, pf.name as firm_name
                    FROM firm_rule fr
                    JOIN prop_firm pf ON fr.firm_id = pf.id
                    ORDER BY pf.name, fr.severity DESC, fr.rule_type
                """
                cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            rules = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return rules
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return []
    
    def _get_rule_documents(self, firm_name: Optional[str] = None) -> List[Dict]:
        """Retrieve rule documentation from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if firm_name:
                query = """
                    SELECT hd.title, hd.body_text, pf.name as firm_name, hd.url
                    FROM help_document hd
                    JOIN prop_firm pf ON hd.firm_id = pf.id
                    WHERE LOWER(pf.name) LIKE LOWER(?)
                    AND hd.is_current = 1
                    AND (LOWER(hd.title) LIKE '%rule%' 
                         OR LOWER(hd.title) LIKE '%drawdown%'
                         OR LOWER(hd.title) LIKE '%violation%'
                         OR LOWER(hd.body_text) LIKE '%maximum loss%'
                         OR LOWER(hd.body_text) LIKE '%daily loss%')
                    LIMIT 10
                """
                cursor.execute(query, (f"%{firm_name}%",))
            else:
                query = """
                    SELECT hd.title, hd.body_text, pf.name as firm_name, hd.url
                    FROM help_document hd
                    JOIN prop_firm pf ON hd.firm_id = pf.id
                    WHERE hd.is_current = 1
                    AND (LOWER(hd.title) LIKE '%rule%' 
                         OR LOWER(hd.title) LIKE '%drawdown%'
                         OR LOWER(hd.title) LIKE '%violation%')
                    LIMIT 20
                """
                cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            docs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return docs
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return []
    
    def _fallback_rule_analysis(self, account_data: Dict, db_rules: List[Dict]) -> List[RuleViolation]:
        """
        Fallback rule-based analysis when LLM fails
        Simple threshold checking without AI interpretation
        """
        violations = []
        balance = account_data.get('balance', 0)
        equity = account_data.get('equity', 0)
        profit = account_data.get('profit', 0)
        positions = account_data.get('positions', [])
        
        # Check daily drawdown
        daily_loss_pct = abs(profit / balance * 100) if balance > 0 else 0
        
        for rule in db_rules:
            rule_type = rule.get('rule_type', '').lower()
            value_str = rule.get('value', '')
            
            # Daily loss rule
            if 'daily' in rule_type and 'loss' in rule_type:
                try:
                    threshold = float(value_str.rstrip('%'))
                    if daily_loss_pct >= threshold * 0.8:  # 80% threshold
                        severity = "CRITICAL" if daily_loss_pct >= threshold else "HIGH"
                        violations.append(RuleViolation(
                            severity=severity,
                            rule_type=rule.get('rule_category', 'hard_rule'),
                            category='daily_drawdown',
                            description=f"Daily loss at {daily_loss_pct:.2f}%, approaching {threshold}% limit",
                            current_value=daily_loss_pct,
                            threshold_value=threshold,
                            firm_name=rule.get('firm_name'),
                            recommendation="Close losing positions or reduce exposure",
                            timestamp=datetime.now().isoformat()
                        ))
                except (ValueError, AttributeError):
                    pass
            
            # Stop loss rule
            if 'stop' in rule_type and 'loss' in rule_type:
                positions_without_sl = [p for p in positions if p.get('sl', 0) == 0]
                if positions_without_sl:
                    violations.append(RuleViolation(
                        severity="MEDIUM",
                        rule_type='soft_rule',
                        category='stop_loss',
                        description=f"{len(positions_without_sl)} position(s) missing stop loss",
                        current_value=len(positions_without_sl),
                        threshold_value=0,
                        firm_name=rule.get('firm_name'),
                        recommendation="Add stop loss orders to all positions",
                        timestamp=datetime.now().isoformat()
                    ))
            
            # Position count rule
            if 'position' in rule_type and 'max' in rule_type:
                try:
                    max_positions = int(value_str.split()[0])
                    if len(positions) > max_positions:
                        violations.append(RuleViolation(
                            severity="MEDIUM",
                            rule_type='soft_rule',
                            category='position_count',
                            description=f"Too many positions: {len(positions)} > {max_positions}",
                            current_value=len(positions),
                            threshold_value=max_positions,
                            firm_name=rule.get('firm_name'),
                            recommendation="Reduce number of open positions",
                            timestamp=datetime.now().isoformat()
                        ))
                except (ValueError, AttributeError, IndexError):
                    pass
        
        return violations
    
    def scan_account(self, account_data: Dict, firm_name: Optional[str] = None) -> Dict:
        """
        Scan account data for rule violations
        
        Args:
            account_data: Account snapshot from MT5 API
            firm_name: Prop firm name (optional, for targeted rule checking)
            
        Returns:
            Comprehensive violation report
        """
        print("=" * 80)
        print("🔍 Ollama Rule Violation Scanner")
        print("=" * 80)
        print(f"Model: {self.model}")
        print(f"Firm: {firm_name or 'All firms'}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get rules from database
        print("📚 Loading rules from database...")
        db_rules = self._get_firm_rules_from_db(firm_name)
        rule_docs = self._get_rule_documents(firm_name)
        print(f"   Found {len(db_rules)} structured rules")
        print(f"   Found {len(rule_docs)} rule documents")
        print()
        
        # Prepare context for LLM
        account_summary = f"""
Account Information:
- Balance: ${account_data.get('balance', 0):,.2f}
- Equity: ${account_data.get('equity', 0):,.2f}
- Profit/Loss: ${account_data.get('profit', 0):,.2f}
- Margin Used: ${account_data.get('margin', 0):,.2f}
- Margin Free: ${account_data.get('margin_free', 0):,.2f}
- Margin Level: {account_data.get('margin_level', 0):.2f}%
- Open Positions: {len(account_data.get('positions', []))}
"""
        
        # Add position details
        if account_data.get('positions'):
            account_summary += "\nOpen Positions:\n"
            for pos in account_data.get('positions', []):
                account_summary += f"  - {pos.get('symbol')}: {pos.get('volume')} lots, P/L: ${pos.get('profit', 0):.2f}\n"
        
        # Format database rules
        rules_context = "\n\nDatabase Rules:\n"
        for rule in db_rules[:20]:  # Limit to avoid token overflow
            rules_context += f"""
Rule Type: {rule.get('rule_type')}
Category: {rule.get('rule_category')}
Firm: {rule.get('firm_name')}
Value: {rule.get('value')}
Details: {rule.get('details', 'N/A')}
Severity: {rule.get('severity')}
---
"""
        
        # Add relevant documentation snippets
        docs_context = "\n\nRelevant Documentation:\n"
        for doc in rule_docs[:5]:  # Limit context
            body_preview = doc.get('body_text', '')[:500]
            docs_context += f"""
Document: {doc.get('title')}
Firm: {doc.get('firm_name')}
Content: {body_preview}...
---
"""
        
        # System prompt for rule analysis
        system_prompt = """You are an expert prop trading rule compliance analyst. 
Your job is to analyze trading account data and identify rule violations.

Analyze the account data against the provided rules and identify:
1. HARD RULE violations (immediate account failure)
2. SOFT RULE violations (warnings, best practices)

For each violation, provide:
- Severity (CRITICAL, HIGH, MEDIUM, LOW)
- Category (e.g., daily_drawdown, lot_size, position_count)
- Description of the violation
- Current value vs threshold
- Recommendation for remediation

Respond in JSON format:
{
  "violations": [
    {
      "severity": "CRITICAL",
      "rule_type": "hard_rule",
      "category": "daily_drawdown",
      "description": "...",
      "current_value": 150.00,
      "threshold_value": 100.00,
      "recommendation": "..."
    }
  ],
  "summary": "Brief summary of findings"
}
"""
        
        # Query LLM for analysis
        print("🤖 Analyzing account with Ollama LLM...")
        analysis_prompt = f"""
{account_summary}
{rules_context}
{docs_context}

Please analyze this trading account for rule violations. Consider both hard rules (immediate failures) 
and soft rules (warnings, best practices). Provide detailed analysis in JSON format.
"""
        
        llm_response = self._query_ollama(analysis_prompt, system_prompt)
        
        # Parse LLM response
        violations = []
        summary = "Analysis complete"
        
        if not llm_response or llm_response.strip() == "":
            # Empty response from LLM
            summary = "LLM returned empty response. Performing rule-based analysis..."
            violations = self._fallback_rule_analysis(account_data, db_rules)
        else:
            try:
                # Try to extract JSON from response
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = llm_response[json_start:json_end]
                    analysis = json.loads(json_str)
                    
                    for v in analysis.get('violations', []):
                        violations.append(RuleViolation(
                            severity=v.get('severity', 'MEDIUM'),
                            rule_type=v.get('rule_type', 'unknown'),
                            category=v.get('category', 'general'),
                            description=v.get('description', ''),
                            current_value=v.get('current_value'),
                            threshold_value=v.get('threshold_value'),
                            firm_name=firm_name,
                            recommendation=v.get('recommendation', ''),
                            timestamp=datetime.now().isoformat()
                        ))
                    
                    summary = analysis.get('summary', 'Analysis complete')
                else:
                    print("⚠️  No JSON found in response, using fallback analysis")
                    summary = "JSON parsing failed. Using rule-based analysis..."
                    violations = self._fallback_rule_analysis(account_data, db_rules)
                    
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON decode error: {e}, using fallback analysis")
                summary = f"JSON parsing failed: {str(e)}. Using rule-based analysis..."
                violations = self._fallback_rule_analysis(account_data, db_rules)
            except Exception as e:
                print(f"⚠️  Unexpected error: {e}, using fallback analysis")
                summary = f"Unexpected error: {str(e)}. Using rule-based analysis..."
                violations = self._fallback_rule_analysis(account_data, db_rules)
        
        # Generate report
        report = {
            "scan_timestamp": datetime.now().isoformat(),
            "firm_name": firm_name,
            "model_used": self.model,
            "account_summary": {
                "balance": account_data.get('balance'),
                "equity": account_data.get('equity'),
                "profit": account_data.get('profit'),
                "open_positions": len(account_data.get('positions', []))
            },
            "rules_checked": len(db_rules),
            "documents_analyzed": len(rule_docs),
            "violations": [asdict(v) for v in violations],
            "violation_count": {
                "critical": len([v for v in violations if v.severity == "CRITICAL"]),
                "high": len([v for v in violations if v.severity == "HIGH"]),
                "medium": len([v for v in violations if v.severity == "MEDIUM"]),
                "low": len([v for v in violations if v.severity == "LOW"])
            },
            "hard_rules_violated": len([v for v in violations if v.rule_type == "hard_rule"]),
            "soft_rules_violated": len([v for v in violations if v.rule_type == "soft_rule"]),
            "summary": summary,
            "llm_raw_response": llm_response
        }
        
        return report
    
    def print_report(self, report: Dict):
        """Print formatted violation report"""
        print()
        print("=" * 80)
        print("📊 RULE VIOLATION REPORT")
        print("=" * 80)
        print(f"Timestamp: {report['scan_timestamp']}")
        print(f"Firm: {report['firm_name'] or 'All'}")
        print(f"Model: {report['model_used']}")
        print()
        
        print("Account Summary:")
        print(f"  Balance: ${report['account_summary']['balance']:,.2f}")
        print(f"  Equity: ${report['account_summary']['equity']:,.2f}")
        print(f"  Profit: ${report['account_summary']['profit']:,.2f}")
        print(f"  Open Positions: {report['account_summary']['open_positions']}")
        print()
        
        print("Analysis:")
        print(f"  Rules Checked: {report['rules_checked']}")
        print(f"  Documents Analyzed: {report['documents_analyzed']}")
        print()
        
        print("Violations Found:")
        print(f"  🔴 Critical: {report['violation_count']['critical']}")
        print(f"  🟠 High: {report['violation_count']['high']}")
        print(f"  🟡 Medium: {report['violation_count']['medium']}")
        print(f"  🟢 Low: {report['violation_count']['low']}")
        print(f"  Hard Rules: {report['hard_rules_violated']}")
        print(f"  Soft Rules: {report['soft_rules_violated']}")
        print()
        
        if report['violations']:
            print("Detailed Violations:")
            print("-" * 80)
            for i, v in enumerate(report['violations'], 1):
                severity_icon = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🟢"
                }.get(v['severity'], "⚪")
                
                print(f"{i}. {severity_icon} [{v['severity']}] {v['category']}")
                print(f"   Type: {v['rule_type']}")
                print(f"   Description: {v['description']}")
                if v['current_value'] is not None:
                    print(f"   Current: {v['current_value']} | Threshold: {v['threshold_value']}")
                print(f"   Recommendation: {v['recommendation']}")
                print()
        
        print("Summary:")
        print(report['summary'])
        print()
        print("=" * 80)
    
    def save_report(self, report: Dict, filename: Optional[str] = None):
        """Save report to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rule_violation_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Report saved to: {filename}")


async def scan_mt5_account(api_url: str = "http://localhost:8000",
                           token: Optional[str] = None,
                           firm_name: Optional[str] = None,
                           ollama_model: str = "llama3.2"):
    """
    Scan MT5 account via REST API and check for rule violations
    
    Args:
        api_url: MT5 REST API base URL
        token: Session token (if None, will attempt to use test credentials)
        firm_name: Prop firm name
        ollama_model: Ollama model to use
    """
    # Initialize scanner
    scanner = OllamaRuleScanner(model=ollama_model)
    
    # Get account snapshot from API
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        response = requests.get(f"{api_url}/api/v1/snapshot", headers=headers, timeout=10)
        response.raise_for_status()
        
        account_data = response.json()
        
    except Exception as e:
        print(f"❌ Failed to get account data: {e}")
        print("💡 Make sure MT5 API is running and you have a valid session token")
        return
    
    # Scan for violations
    report = scanner.scan_account(account_data, firm_name)
    
    # Print and save report
    scanner.print_report(report)
    scanner.save_report(report)
    
    return report


def main():
    """Main entry point for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scan MT5 account for rule violations using Ollama")
    parser.add_argument("--api-url", default="http://localhost:8000", help="MT5 API URL")
    parser.add_argument("--token", help="MT5 API session token")
    parser.add_argument("--firm", help="Prop firm name (e.g., FTMO, MyForexFunds)")
    parser.add_argument("--model", default="llama3.2", help="Ollama model (llama3.2, mistral, etc.)")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama API URL")
    
    args = parser.parse_args()
    
    # Check if Ollama is running
    try:
        response = requests.get(f"{args.ollama_url}/api/tags", timeout=5)
        response.raise_for_status()
        print(f"✅ Ollama is running at {args.ollama_url}")
    except Exception as e:
        print(f"❌ Ollama not accessible: {e}")
        print("💡 Make sure Ollama is installed and running: ollama serve")
        return
    
    # Run scan
    asyncio.run(scan_mt5_account(
        api_url=args.api_url,
        token=args.token,
        firm_name=args.firm,
        ollama_model=args.model
    ))


if __name__ == "__main__":
    main()
