"""
Universal template structure for prop firm rule extraction.
"""

UNIVERSAL_TEMPLATE = {
    "firm_name": "",
    "website": "",
    "scraped_date": "",
    
    "general_rules": {
        "prohibited_strategies": [],
        "payout_rules": {
            "min_payout": None,
            "payout_frequency": None,
            "payout_methods": []
        },
        "trading_restrictions": {
            "news_trading": None,
            "weekend_holding": None,
            "ea_allowed": None,
        },
        "soft_rules": []
    },
    
    "challenge_types": {
        "example_1_step": {
            "name": "1-Step Challenge",
            "account_sizes": [],
            "profit_targets": [],
            "daily_loss_limit": None,
            "max_drawdown": None,
            "trailing_drawdown": None,
            "min_trading_days": None,
            "max_trading_days": None,
            "leverage": None,
            "profit_split": None,
            "refundable_fee": None,
            "trading_period": None
        },
        "example_2_step": {
            "name": "2-Step Challenge",
            "phases": {
                "phase_1": {
                    "profit_target": None,
                    "daily_loss_limit": None,
                    "max_drawdown": None,
                    "min_trading_days": None,
                    "max_trading_days": None
                },
                "phase_2": {
                    "profit_target": None,
                    "daily_loss_limit": None,
                    "max_drawdown": None,
                    "min_trading_days": None,
                    "max_trading_days": None
                },
                "funded": {
                    "daily_loss_limit": None,
                    "max_drawdown": None,
                    "profit_split": None
                }
            },
            "account_sizes": [],
            "leverage": None,
            "refundable_fee": None
        }
    }
}


def create_challenge_template(challenge_name="New Challenge"):
    """Create a new challenge template with default structure."""
    return {
        "name": challenge_name,
        "account_sizes": [],
        "profit_targets": [],
        "daily_loss_limit": None,
        "max_drawdown": None,
        "trailing_drawdown": None,
        "min_trading_days": None,
        "max_trading_days": None,
        "leverage": None,
        "profit_split": None,
        "refundable_fee": None,
        "trading_period": None,
        "sources": []
    }


def create_phase_template(phase_name="Phase"):
    """Create a phase template for multi-step challenges."""
    return {
        "name": phase_name,
        "profit_target": None,
        "daily_loss_limit": None,
        "max_drawdown": None,
        "min_trading_days": None,
        "max_trading_days": None
    }
