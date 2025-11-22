"""
Example usage and testing of the cTrader client
Run this to test your API connection and see live data
"""
from src.ctrader_client import CTraderClient
from src.config import Config
from datetime import datetime


def test_rest_api():
    """Test REST API functionality"""
    print("=" * 60)
    print("Testing cTrader REST API")
    print("=" * 60)
    
    try:
        Config.validate()
        client = CTraderClient()
        
        # Test 1: Get account info
        print("\n1. Account Information:")
        print("-" * 40)
        balance = client.get_balance()
        equity = client.get_equity()
        margin_used = client.get_margin_used()
        margin_free = client.get_margin_free()
        unrealised_pnl = client.get_unrealised_pnl()
        
        print(f"Balance:         ${balance:,.2f}")
        print(f"Equity:          ${equity:,.2f}")
        print(f"Margin Used:     ${margin_used:,.2f}")
        print(f"Margin Free:     ${margin_free:,.2f}")
        print(f"Unrealised P&L:  ${unrealised_pnl:,.2f}")
        
        # Test 2: Get open positions
        print("\n2. Open Positions:")
        print("-" * 40)
        positions = client.get_open_positions()
        
        if positions:
            for i, pos in enumerate(positions, 1):
                print(f"\nPosition {i}:")
                print(f"  Symbol:       {pos.symbol}")
                print(f"  Side:         {pos.side.upper()}")
                print(f"  Volume:       {pos.volume:.2f} lots")
                print(f"  Entry Price:  {pos.entry_price:.5f}")
                print(f"  Current Price: {pos.current_price:.5f}")
                print(f"  P&L:          ${pos.profit_loss:,.2f} ({pos.profit_loss_percent:.2f}%)")
        else:
            print("No open positions")
        
        # Test 3: Get today's realised P&L
        print("\n3. Today's Performance:")
        print("-" * 40)
        today_pl = client.get_today_pl()
        print(f"Realised P&L Today: ${today_pl:,.2f}")
        print(f"Total P&L Today:    ${today_pl + unrealised_pnl:,.2f}")
        
        # Test 4: Get complete snapshot
        print("\n4. Complete Account Snapshot:")
        print("-" * 40)
        snapshot = client.get_account_snapshot()
        print(f"Timestamp:        {snapshot.timestamp}")
        print(f"Balance:          ${snapshot.balance:,.2f}")
        print(f"Equity:           ${snapshot.equity:,.2f}")
        print(f"Total P&L:        ${snapshot.total_profit_loss:,.2f}")
        print(f"Daily Loss %:     {snapshot.daily_loss_percent:.2f}%")
        print(f"Open Positions:   {len(snapshot.positions)}")
        
        print("\n" + "=" * 60)
        print("✓ All REST API tests passed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nPlease check your .env configuration:")
        print("  - CTRADER_CLIENT_ID")
        print("  - CTRADER_CLIENT_SECRET")
        print("  - CTRADER_ACCESS_TOKEN")
        print("  - ACCOUNT_ID")
        return False


async def test_websocket():
    """Test WebSocket streaming (async)"""
    print("\n" + "=" * 60)
    print("Testing cTrader WebSocket API")
    print("=" * 60)
    print("Connecting to WebSocket...")
    
    try:
        client = CTraderClient()
        
        # Connect and authenticate
        await client.connect()
        print("✓ WebSocket connected and authenticated")
        
        # Subscribe to account updates
        await client.subscribe_to_account()
        print("✓ Subscribed to account updates")
        
        print("\nListening for updates (press Ctrl+C to stop)...")
        
        async def print_update(data):
            """Print incoming updates"""
            payload_type = data.get("payloadType")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received message type: {payload_type}")
        
        # Listen for a few seconds
        import asyncio
        try:
            await asyncio.wait_for(
                client.listen_for_updates(print_update),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            print("\n✓ WebSocket test completed (10 second timeout)")
        
        await client.disconnect()
        
        return True
        
    except Exception as e:
        print(f"\n✗ WebSocket Error: {e}")
        print("\nNote: WebSocket streaming requires:")
        print("  - Valid OAuth credentials")
        print("  - Proper API permissions")
        print("  - Stable internet connection")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "cTrader API Client Test Suite" + " " * 18 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Test REST API
    rest_success = test_rest_api()
    
    if not rest_success:
        print("\n⚠ Skipping WebSocket test due to REST API issues")
        return
    
    # Ask user if they want to test WebSocket
    print("\n" + "-" * 60)
    response = input("\nTest WebSocket streaming? (y/n): ").lower().strip()
    
    if response == 'y':
        import asyncio
        asyncio.run(test_websocket())
    else:
        print("Skipping WebSocket test")
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
