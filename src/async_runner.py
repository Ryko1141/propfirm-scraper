"""
Async runner for real-time WebSocket streaming
This is an advanced alternative to the polling-based runner
"""
import asyncio
from datetime import datetime
from src.config import Config
from src.ctrader_client import CTraderClient
from src.rules import RiskRuleEngine
from src.notifier import Notifier


class AsyncRiskMonitor:
    """Real-time monitoring service using WebSocket streaming"""
    
    def __init__(self):
        """Initialize the async risk monitor"""
        Config.validate()
        
        self.client = CTraderClient()
        self.rule_engine = RiskRuleEngine()
        self.notifier = Notifier()
        self.running = False
    
    async def handle_account_update(self, data: dict):
        """
        Handle incoming WebSocket updates from cTrader
        
        Args:
            data: WebSocket message containing account/position updates
        """
        try:
            payload_type = data.get("payloadType")
            
            # Handle different message types
            if payload_type == 2126:  # ProtoOASpotEvent (price update)
                # Price updates - might trigger position P&L changes
                pass
            
            elif payload_type == 2132:  # ProtoOAExecutionEvent (order/position event)
                # Position opened, closed, or modified
                print(f"Execution event received: {data}")
                await self.check_rules()
            
            elif payload_type == 2142:  # ProtoOAAccountAuthRes
                print("Account authenticated via WebSocket")
            
            else:
                print(f"Received message type {payload_type}")
                
        except Exception as e:
            print(f"Error handling update: {e}")
    
    async def check_rules(self):
        """Perform a risk check using current account state"""
        try:
            # Get snapshot using REST (WebSocket doesn't provide full snapshot)
            snapshot = self.client.get_account_snapshot()
            violations = self.rule_engine.evaluate(snapshot)
            
            if violations:
                self.notifier.send_violations(violations)
            
            print(f"[{snapshot.timestamp}] Check complete - Equity: ${snapshot.equity:.2f}, P&L: ${snapshot.total_profit_loss:.2f}, Violations: {len(violations)}")
            
        except Exception as e:
            print(f"Error during check: {e}")
    
    async def periodic_check(self, interval: int = 60):
        """
        Perform periodic checks in addition to event-driven checks
        
        Args:
            interval: Time between checks in seconds
        """
        while self.running:
            await self.check_rules()
            await asyncio.sleep(interval)
    
    async def start(self):
        """Start the async monitoring service"""
        self.running = True
        self.notifier.send_status("Async risk monitor started (WebSocket mode)")
        
        print("Starting async risk monitor with WebSocket streaming...")
        
        try:
            # Connect to WebSocket
            await self.client.connect()
            await self.client.subscribe_to_account()
            
            # Run both event listener and periodic checker concurrently
            await asyncio.gather(
                self.client.listen_for_updates(self.handle_account_update),
                self.periodic_check(interval=60)
            )
            
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            self.notifier.send_status(f"Monitor error: {str(e)}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the monitoring service"""
        self.running = False
        await self.client.disconnect()
        self.notifier.send_status("Async risk monitor stopped")
        print("Async risk monitor stopped")


def main():
    """Entry point for async application"""
    monitor = AsyncRiskMonitor()
    
    try:
        asyncio.run(monitor.start())
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
