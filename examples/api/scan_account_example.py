"""
Example: Using the MT5 API Scanner Endpoint
Shows how clients can scan their account for rule violations
"""
import requests
import json
from typing import Optional


class MT5Scanner:
    """Client for MT5 API with rule scanning"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.token: Optional[str] = None
    
    def login(self, account: int, password: str, server: str) -> dict:
        """Login to MT5 and get session token"""
        response = requests.post(
            f"{self.api_url}/login",
            json={
                "account_number": account,
                "password": password,
                "server": server
            }
        )
        response.raise_for_status()
        data = response.json()
        self.token = data['session_token']
        return data
    
    def scan_account(self, firm_name: Optional[str] = None) -> dict:
        """
        Scan account for rule violations
        
        Args:
            firm_name: Optional propfirm name (e.g., "FTMO", "5ers")
            
        Returns:
            Violation report with severity levels
        """
        if not self.token:
            raise Exception("Not logged in. Call login() first.")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {}
        if firm_name:
            params['firm_name'] = firm_name
        
        response = requests.post(
            f"{self.api_url}/scan",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def logout(self):
        """Logout and invalidate session"""
        if not self.token:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.api_url}/logout", headers=headers)
        response.raise_for_status()
        self.token = None


def print_violations(report: dict):
    """Pretty print violation report"""
    print("\n" + "="*80)
    print("📊 RULE VIOLATION REPORT")
    print("="*80)
    print(f"Timestamp: {report['scan_timestamp']}")
    print(f"Firm: {report.get('firm_name', 'All')}")
    print(f"Model: {report['model_used']}")
    
    print("\nAccount Summary:")
    acc = report['account_summary']
    print(f"  Balance: ${acc['balance']:,.2f}")
    print(f"  Equity: ${acc['equity']:,.2f}")
    print(f"  Profit: ${acc['profit']:,.2f}")
    print(f"  Open Positions: {acc['open_positions']}")
    
    print("\nViolations Found:")
    counts = report['violation_count']
    print(f"  🔴 Critical: {counts['critical']}")
    print(f"  🟠 High: {counts['high']}")
    print(f"  🟡 Medium: {counts['medium']}")
    print(f"  🟢 Low: {counts['low']}")
    
    if report['violations']:
        print("\nDetailed Violations:")
        print("-" * 80)
        for i, v in enumerate(report['violations'], 1):
            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
            print(f"{i}. {emoji.get(v['severity'], '⚪')} [{v['severity']}] {v['category']}")
            print(f"   Type: {v['rule_type']}")
            print(f"   Description: {v['description']}")
            if v['current_value'] is not None:
                print(f"   Current: {v['current_value']} | Threshold: {v['threshold_value']}")
            print(f"   Recommendation: {v['recommendation']}")
            print()
    
    print(f"\nSummary: {report['summary']}")
    print("="*80)


def main():
    """Example usage"""
    
    # Initialize client
    scanner = MT5Scanner("http://localhost:8000")
    
    # Your MT5 credentials
    ACCOUNT = 12345678  # Replace with your account
    PASSWORD = "your_password"  # Replace with your password
    SERVER = "MetaQuotes-Demo"  # Replace with your server
    
    try:
        # Login
        print("🔐 Logging in to MT5...")
        login_result = scanner.login(ACCOUNT, PASSWORD, SERVER)
        print(f"✅ Connected to {login_result['server']}")
        print(f"   Account: {login_result['account_number']}")
        print(f"   Token expires in: {login_result['expires_in']}s")
        
        # Scan for violations
        print("\n🤖 Scanning account for rule violations...")
        print("   (Using your local Ollama + propfirm database)")
        
        # Option 1: Scan for specific firm
        report = scanner.scan_account(firm_name="FTMO")
        
        # Option 2: Scan all rules
        # report = scanner.scan_account()
        
        # Display results
        print_violations(report)
        
        # Save to file
        with open('my_violation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        print("\n💾 Report saved to: my_violation_report.json")
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error: {e}")
        if e.response is not None:
            print(f"   {e.response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Always logout
        try:
            scanner.logout()
            print("\n👋 Logged out")
        except:
            pass


if __name__ == "__main__":
    main()
