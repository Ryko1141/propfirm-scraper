"""
Example usage and testing of the MT5 client
Run this to test your MT5 connection and see live data
"""
from src.mt5_client import MT5Client
from src.config import Config
from datetime import datetime


def test_mt5_api():
    """Test MT5 API functionality"""
    print("=" * 60)
    print("Testing MetaTrader 5 API")
    print("=" * 60)
    
    try:
        Config.validate()
        client = MT5Client()
        
        # Test 1: Connect to MT5
        print("\n1. Connecting to MT5 Terminal:")
        print("-" * 40)
        if not client.connect():
            print("✗ Failed to connect to MT5")
            return False
        print("✓ Successfully connected to MT5")
        
        # Test 2: Get account info
        print("\n2. Account Information:")
        print("-" * 40)
        account_info = client.get_account_info()
        if account_info:
            print(f"Account Number:  {account_info['login']}")
            print(f"Server:          {account_info['server']}")
            print(f"Company:         {account_info['company']}")
            print(f"Currency:        {account_info['currency']}")
            print(f"Leverage:        1:{account_info['leverage']}")
            print(f"Balance:         ${account_info['balance']:,.2f}")
            print(f"Equity:          ${account_info['equity']:,.2f}")
            print(f"Margin Used:     ${account_info['margin']:,.2f}")
            print(f"Margin Free:     ${account_info['margin_free']:,.2f}")
            print(f"Margin Level:    {account_info['margin_level']:.2f}%")
            print(f"Profit:          ${account_info['profit']:,.2f}")
        else:
            print("✗ Failed to get account info")
            return False
        
        # Test 3: Get open positions
        print("\n3. Open Positions:")
        print("-" * 40)
        positions = client.get_open_positions()
        
        if positions:
            for i, pos in enumerate(positions, 1):
                print(f"\nPosition {i}:")
                print(f"  Ticket:       {pos.position_id}")
                print(f"  Symbol:       {pos.symbol}")
                print(f"  Side:         {pos.side.upper()}")
                print(f"  Volume:       {pos.volume:.2f} lots")
                print(f"  Entry Price:  {pos.entry_price:.5f}")
                print(f"  Current Price: {pos.current_price:.5f}")
                print(f"  P&L:          ${pos.profit_loss:,.2f} ({pos.profit_loss_percent:.2f}%)")
        else:
            print("No open positions")
        
        # Test 4: Get pending orders
        print("\n4. Pending Orders:")
        print("-" * 40)
        orders = client.get_orders()
        
        if orders:
            for i, order in enumerate(orders, 1):
                print(f"\nOrder {i}:")
                print(f"  Ticket:       {order['ticket']}")
                print(f"  Symbol:       {order['symbol']}")
                print(f"  Type:         {order['type']}")
                print(f"  Volume:       {order['volume_current']:.2f} lots")
                print(f"  Price:        {order['price_open']:.5f}")
        else:
            print("No pending orders")
        
        # Test 5: Get today's realised P&L
        print("\n5. Today's Performance:")
        print("-" * 40)
        today_pl = client.get_today_pl()
        unrealised_pnl = client.get_unrealised_pnl()
        print(f"Realised P&L Today:   ${today_pl:,.2f}")
        print(f"Unrealised P&L:       ${unrealised_pnl:,.2f}")
        print(f"Total P&L Today:      ${today_pl + unrealised_pnl:,.2f}")
        
        # Test 6: Get complete snapshot
        print("\n6. Complete Account Snapshot:")
        print("-" * 40)
        snapshot = client.get_account_snapshot()
        print(f"Timestamp:        {snapshot.timestamp}")
        print(f"Balance:          ${snapshot.balance:,.2f}")
        print(f"Equity:           ${snapshot.equity:,.2f}")
        print(f"Total P&L:        ${snapshot.total_profit_loss:,.2f}")
        print(f"Daily Loss %:     {snapshot.daily_loss_percent:.2f}%")
        print(f"Open Positions:   {len(snapshot.positions)}")
        
        # Test 7: Get terminal info
        print("\n7. Terminal Information:")
        print("-" * 40)
        terminal_info = client.get_terminal_info()
        if terminal_info:
            print(f"Connected:        {terminal_info['connected']}")
            print(f"Trade Allowed:    {terminal_info['trade_allowed']}")
            print(f"Build:            {terminal_info['build']}")
            print(f"CPU Cores:        {terminal_info['cpu_cores']}")
            print(f"Memory Total:     {terminal_info['memory_total'] / (1024**3):.2f} GB")
            print(f"Memory Used:      {terminal_info['memory_used'] / (1024**3):.2f} GB")
        
        print("\n" + "=" * 60)
        print("✓ All MT5 API tests passed!")
        print("=" * 60)
        
        # Cleanup
        client.disconnect()
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nPlease check your .env configuration:")
        print("  - PLATFORM=mt5")
        print("  - ACCOUNT_ID (your MT5 account number)")
        print("  - MT5_PASSWORD")
        print("  - MT5_SERVER")
        print("\nAlso ensure:")
        print("  - MetaTrader 5 is installed")
        print("  - You have allowed automated trading in MT5")
        print("  - The MT5 terminal is not running (or allow DLL imports)")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 12 + "MetaTrader 5 Client Test Suite" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Test MT5 API
    test_mt5_api()
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
