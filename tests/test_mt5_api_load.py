"""
MT5 REST API Load/Soak Test - 100 Concurrent Accounts
Tests API stability and performance with many simultaneous connections
"""
import asyncio
import aiohttp
import random
import time
from datetime import datetime
from typing import List, Dict
import statistics


class MT5ApiLoadTester:
    """Load tester for MT5 REST API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": []
        }
        
    async def simulate_account(self, session: aiohttp.ClientSession, account_num: int, 
                               credentials: Dict, stagger_delay: float):
        """Simulate a single MT5 account connection and operations"""
        
        # Stagger the start times
        await asyncio.sleep(stagger_delay)
        
        account_id = f"Account_{account_num}"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {account_id}: Starting...")
        
        token = None
        account_results = {
            "account_id": account_id,
            "login_success": False,
            "operations": [],
            "errors": []
        }
        
        try:
            # 1. Login
            start_time = time.time()
            async with session.post(
                f"{self.base_url}/api/v1/login",
                json=credentials
            ) as resp:
                elapsed = time.time() - start_time
                self.results["total_requests"] += 1
                self.results["response_times"].append(elapsed)
                
                if resp.status == 200:
                    data = await resp.json()
                    token = data.get("access_token")
                    account_results["login_success"] = True
                    self.results["successful_requests"] += 1
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {account_id}: ✓ Login successful ({elapsed:.2f}s)")
                else:
                    self.results["failed_requests"] += 1
                    error_msg = f"Login failed: {resp.status}"
                    account_results["errors"].append(error_msg)
                    self.results["errors"].append(f"{account_id}: {error_msg}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {account_id}: ✗ Login failed")
                    return account_results
            
            # Headers for authenticated requests
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. Get Account Info
            start_time = time.time()
            async with session.get(f"{self.base_url}/api/v1/account", headers=headers) as resp:
                elapsed = time.time() - start_time
                self.results["total_requests"] += 1
                self.results["response_times"].append(elapsed)
                
                if resp.status == 200:
                    self.results["successful_requests"] += 1
                    account_results["operations"].append(("account_info", elapsed, True))
                else:
                    self.results["failed_requests"] += 1
                    account_results["operations"].append(("account_info", elapsed, False))
            
            # 3. Get Balance
            start_time = time.time()
            async with session.get(f"{self.base_url}/api/v1/balance", headers=headers) as resp:
                elapsed = time.time() - start_time
                self.results["total_requests"] += 1
                self.results["response_times"].append(elapsed)
                
                if resp.status == 200:
                    self.results["successful_requests"] += 1
                    account_results["operations"].append(("balance", elapsed, True))
                else:
                    self.results["failed_requests"] += 1
                    account_results["operations"].append(("balance", elapsed, False))
            
            # 4. Get Positions
            start_time = time.time()
            async with session.get(f"{self.base_url}/api/v1/positions", headers=headers) as resp:
                elapsed = time.time() - start_time
                self.results["total_requests"] += 1
                self.results["response_times"].append(elapsed)
                
                if resp.status == 200:
                    self.results["successful_requests"] += 1
                    account_results["operations"].append(("positions", elapsed, True))
                else:
                    self.results["failed_requests"] += 1
                    account_results["operations"].append(("positions", elapsed, False))
            
            # 5. Get Orders
            start_time = time.time()
            async with session.get(f"{self.base_url}/api/v1/orders", headers=headers) as resp:
                elapsed = time.time() - start_time
                self.results["total_requests"] += 1
                self.results["response_times"].append(elapsed)
                
                if resp.status == 200:
                    self.results["successful_requests"] += 1
                    account_results["operations"].append(("orders", elapsed, True))
                else:
                    self.results["failed_requests"] += 1
                    account_results["operations"].append(("orders", elapsed, False))
            
            # 6. Get Snapshot
            start_time = time.time()
            async with session.get(f"{self.base_url}/api/v1/snapshot", headers=headers) as resp:
                elapsed = time.time() - start_time
                self.results["total_requests"] += 1
                self.results["response_times"].append(elapsed)
                
                if resp.status == 200:
                    self.results["successful_requests"] += 1
                    account_results["operations"].append(("snapshot", elapsed, True))
                else:
                    self.results["failed_requests"] += 1
                    account_results["operations"].append(("snapshot", elapsed, False))
            
            # Random delay to simulate real usage
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # 7. Logout
            start_time = time.time()
            async with session.post(f"{self.base_url}/api/v1/logout", headers=headers) as resp:
                elapsed = time.time() - start_time
                self.results["total_requests"] += 1
                self.results["response_times"].append(elapsed)
                
                if resp.status == 200:
                    self.results["successful_requests"] += 1
                    account_results["operations"].append(("logout", elapsed, True))
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {account_id}: ✓ Completed all operations")
                else:
                    self.results["failed_requests"] += 1
                    account_results["operations"].append(("logout", elapsed, False))
        
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            account_results["errors"].append(error_msg)
            self.results["errors"].append(f"{account_id}: {error_msg}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {account_id}: ✗ Error - {str(e)}")
        
        return account_results
    
    async def run_soak_test(self, num_accounts: int, credentials: Dict, 
                           max_stagger_seconds: float = 10.0):
        """
        Run soak test with multiple concurrent accounts
        
        Args:
            num_accounts: Number of accounts to simulate
            credentials: MT5 login credentials (account_id, password, server)
            max_stagger_seconds: Maximum delay to stagger account startups
        """
        print("=" * 80)
        print(f"MT5 REST API Soak Test - {num_accounts} Concurrent Accounts")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Stagger Range: 0 - {max_stagger_seconds}s")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        start_time = time.time()
        
        # Create session with connection pooling
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Create tasks with staggered delays
            tasks = []
            for i in range(num_accounts):
                stagger_delay = random.uniform(0, max_stagger_seconds)
                task = asyncio.create_task(
                    self.simulate_account(session, i + 1, credentials, stagger_delay)
                )
                tasks.append(task)
            
            # Wait for all accounts to complete
            account_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed_time = time.time() - start_time
        
        # Print results
        print()
        print("=" * 80)
        print("Test Results")
        print("=" * 80)
        print(f"Total Runtime: {elapsed_time:.2f}s")
        print(f"Total Requests: {self.results['total_requests']}")
        print(f"Successful: {self.results['successful_requests']}")
        print(f"Failed: {self.results['failed_requests']}")
        print(f"Success Rate: {(self.results['successful_requests'] / self.results['total_requests'] * 100):.2f}%")
        print()
        
        if self.results['response_times']:
            print("Response Time Statistics:")
            print(f"  Min: {min(self.results['response_times']):.3f}s")
            print(f"  Max: {max(self.results['response_times']):.3f}s")
            print(f"  Mean: {statistics.mean(self.results['response_times']):.3f}s")
            print(f"  Median: {statistics.median(self.results['response_times']):.3f}s")
            if len(self.results['response_times']) > 1:
                print(f"  Std Dev: {statistics.stdev(self.results['response_times']):.3f}s")
        
        if self.results['errors']:
            print()
            print(f"Errors ({len(self.results['errors'])}):")
            for error in self.results['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.results['errors']) > 10:
                print(f"  ... and {len(self.results['errors']) - 10} more")
        
        print("=" * 80)
        
        return self.results


async def main():
    """Run the soak test"""
    
    # MT5 credentials - REPLACE WITH YOUR ACTUAL CREDENTIALS
    credentials = {
        "account_id": 1512191081,  # Your MT5 account number
        "password": "your_password_here",  # Your MT5 password
        "server": "FTMO-Demo"  # Your MT5 server
    }
    
    # Note: Update credentials above before running!
    print("\n⚠️  WARNING: Update credentials in the script before running!")
    print("Edit test_mt5_api_load.py and set your account_id, password, and server\n")
    
    # Uncomment to run the test:
    # tester = MT5ApiLoadTester(base_url="http://localhost:8000")
    # await tester.run_soak_test(
    #     num_accounts=100,
    #     credentials=credentials,
    #     max_stagger_seconds=10.0
    # )


if __name__ == "__main__":
    asyncio.run(main())
