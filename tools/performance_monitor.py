# tools/performance_monitor.py
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

import redis

def analyze_performance():
    """Analyze trading performance"""
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # Get trade history
    trades = [json.loads(t) for t in r.lrange('history:execution_results', 0, -1)]
    
    if not trades:
        print("No trades found!")
        return
    
    df = pd.DataFrame(trades)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # Calculate metrics
    total_trades = len(df)
    winning_trades = len(df[df['pnl'] > 0])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    print("\n📊 Performance Metrics:")
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate: {win_rate:.2%}")
    print(f"Total P&L: ${df['pnl'].sum():.2f}")
    
    # Plot equity curve
    plt.figure(figsize=(12, 6))
    df['cumulative_pnl'].plot()
    plt.title('Equity Curve')
    plt.xlabel('Date')
    plt.ylabel('Cumulative P&L ($)')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    analyze_performance()