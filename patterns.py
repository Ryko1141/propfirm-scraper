"""
Regex patterns for extracting trading rules.
"""

# Account size patterns
ACCOUNT_SIZE_PATTERNS = [
    r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:account|balance|capital)',
    r'(?:account|balance|capital)[:\s]+\$(\d{1,3}(?:,\d{3})*)',
    r'\$(\d+)k\s*(?:account|balance)',
]

# Profit target patterns
PROFIT_TARGET_PATTERNS = [
    r'(?:profit target|target profit|profit goal)[:\s]+(\d+)%',
    r'(\d+)%\s+(?:profit target|target)',
]

# Daily loss patterns
DAILY_LOSS_PATTERNS = [
    r'(?:daily (?:loss|drawdown) limit|daily limit)[:\s]+(\d+)%',
    r'(\d+)%\s+daily (?:loss|drawdown)',
]

# Max drawdown patterns
MAX_DRAWDOWN_PATTERNS = [
    r'(?:max(?:imum)? (?:loss|drawdown)|overall drawdown)[:\s]+(\d+)%',
    r'(\d+)%\s+(?:max(?:imum)? (?:loss|drawdown)|overall)',
]

# Trailing drawdown patterns
TRAILING_DRAWDOWN_PATTERNS = [
    r'trailing[:\s]+(\d+)%',
]

# Profit split patterns
PROFIT_SPLIT_PATTERNS = [
    r'(?:profit split|reward share|profit share)[:\s]+(\d+)%',
]

# Minimum trading days patterns
MIN_TRADING_DAYS_PATTERNS = [
    r'(?:minimum|min)[:\s]+(\d+)\s+(?:trading )?days?',
]

# Leverage patterns
LEVERAGE_PATTERNS = [
    r'(?:leverage|leverage ratio)[:\s]+1:(\d+)',
]

# Prohibited strategies (exact keywords to search for)
PROHIBITED_STRATEGIES = [
    'copy trading',
    'tick scalping',
    'HFT',
    'high frequency trading',
    'martingale',
    'grid trading',
    'arbitrage',
    'gambling',
    'hedging',
    'news trading',
    'account rolling',
    'one sided betting',
    'hyperactivity',
    'latency trading',
    'quick strike',
]

# Challenge type keywords
CHALLENGE_TYPE_KEYWORDS = {
    '1_step': ['1-step', 'one step', '1 step'],
    '2_step': ['2-step', 'two step', '2 step'],
    'lite': ['lite challenge', 'lite account'],
    'instant': ['instant', 'instant funding', 'instant account'],
}
