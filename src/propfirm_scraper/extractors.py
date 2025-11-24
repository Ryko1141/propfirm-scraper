"""
Extraction utilities for finding specific rule types in text.
"""

import re


def extract_account_sizes(text):
    """Extract all account size options mentioned."""
    sizes = []
    patterns = [
        r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:account|balance|capital)',
        r'(?:account|balance|capital)[:\s]+\$(\d{1,3}(?:,\d{3})*)',
        r'\$(\d+)k\s*(?:account|balance)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value = match.group(1)
            if 'k' in match.group(0).lower():
                value = str(int(value) * 1000)
            sizes.append(value.replace(',', ''))
    
    return sorted(set(sizes), key=lambda x: int(x))


def extract_profit_targets(text):
    """Extract profit target percentages."""
    targets = []
    patterns = [
        r'(?:profit target|target profit|profit goal)[:\s]+(\d+)%',
        r'(\d+)%\s+(?:profit target|profit)',
        r'achieve.*?(\d+)%.*?profit',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            targets.append(match.group(1))
    
    return list(set(targets))


def extract_drawdown_limits(text):
    """Extract daily loss and max drawdown limits."""
    rules = {'daily_loss': [], 'max_drawdown': [], 'trailing_drawdown': []}
    
    # Daily loss - more flexible patterns
    daily_patterns = [
        r'daily loss limit[:\s]+is[:\s]+(\d+)%',
        r'daily loss limit[:\s]+(\d+)%',
        r'(\d+)%\s+daily loss',
        r'daily[:\s]+(?:loss|drawdown)[^\d]+(\d+)%',
    ]
    
    for pattern in daily_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            rules['daily_loss'].append(match.group(1))
    
    # Max drawdown - more flexible patterns
    max_patterns = [
        r'max(?:imum)?[:\s]+(?:loss|drawdown)[^\d]+(\d+)%',
        r'(\d+)%\s+max(?:imum)?[:\s]+(?:loss|drawdown)',
        r'overall[:\s]+drawdown[^\d]+(\d+)%',
    ]
    
    for pattern in max_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            rules['max_drawdown'].append(match.group(1))
    
    # Trailing drawdown
    if 'trailing' in text.lower() and 'drawdown' in text.lower():
        pattern = r'trailing[:\s]+(\d+)%'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            rules['trailing_drawdown'].append(match.group(1))
    
    return rules


def extract_prohibited_strategies(text):
    """Extract all prohibited trading strategies."""
    prohibited = []
    strategies = [
        'copy trading', 'tick scalping', 'HFT', 'high frequency trading',
        'martingale', 'grid trading', 'arbitrage', 'gambling',
        'hedging', 'news trading', 'account rolling', 'one sided betting',
        'hyperactivity', 'latency trading', 'quick strike', 'all in one'
    ]
    
    text_lower = text.lower()
    
    for strategy in strategies:
        # Check for prohibited/restricted mentions
        pattern1 = rf'(?:prohibit|forbidden|not allowed|restricted|banned)[^.{{}}]+{re.escape(strategy.lower())}'
        pattern2 = rf'{re.escape(strategy.lower())}[^.{{}}]+(?:prohibit|forbidden|not allowed|restricted|banned)'
        
        if re.search(pattern1, text_lower, re.DOTALL) or re.search(pattern2, text_lower, re.DOTALL):
            prohibited.append(strategy)
    
    return prohibited


def extract_profit_split(text):
    """Extract profit split percentage."""
    pattern = r'(?:profit split|reward share|profit share)[:\s]+(\d+)%'
    matches = re.finditer(pattern, text, re.IGNORECASE)
    splits = [match.group(1) for match in matches]
    return splits[0] if splits else None


def extract_min_trading_days(text):
    """Extract minimum trading days requirement."""
    pattern = r'(?:minimum|min)[:\s]+(\d+)\s+(?:trading )?days?'
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def extract_leverage(text):
    """Extract leverage ratio."""
    pattern = r'(?:leverage|leverage ratio)[:\s]+1:(\d+)'
    match = re.search(pattern, text, re.IGNORECASE)
    return f"1:{match.group(1)}" if match else None


def identify_challenge_type(text, title, url):
    """Identify which challenge/account type this page describes."""
    # Handle both 'body' and 'html' field names
    text_combined = (str(text) + " " + str(title) + " " + str(url)).lower()
    
    challenge_types = []
    
    if '1-step' in text_combined or 'one step' in text_combined:
        challenge_types.append('1_step')
    if '2-step' in text_combined or 'two step' in text_combined:
        challenge_types.append('2_step')
    if 'lite' in text_combined and 'challenge' in text_combined:
        challenge_types.append('lite')
    if 'instant' in text_combined:
        challenge_types.append('instant')
    
    return challenge_types if challenge_types else ['general']
