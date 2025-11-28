"""
Compliance Review API built on Guardian's rule engine.

This FastAPI service lets users submit account metrics for a prop compliance
review using the latest rules stored in the Guardian database. It also exposes
soft-rule insights to help users avoid common pitfalls beyond hard limits.
"""
from datetime import datetime
import sqlite3
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.config import AccountManager, FIRM_RULES, PropRules
from src.models import AccountSnapshot, Position
from src.rules import check_account_rules

app = FastAPI(title="Guardian Compliance API", version="1.0.0")

account_manager = AccountManager()


class PositionInput(BaseModel):
    """Pydantic model for incoming position data."""

    position_id: str = Field(..., description="Position identifier")
    symbol: str = Field(..., description="Trading symbol")
    volume: float = Field(..., description="Lots size (positive for buy, negative for sell)")
    entry_price: float = Field(..., description="Position entry price")
    current_price: float = Field(..., description="Current market price")
    profit_loss: float = Field(..., description="Unrealized profit/loss in account currency")
    side: str = Field(..., description="Trade direction: buy or sell")


class AccountDataInput(BaseModel):
    """User-supplied account state used for compliance evaluation."""

    balance: float = Field(..., description="Current account balance")
    equity: float = Field(..., description="Current account equity")
    starting_balance: Optional[float] = Field(None, description="Starting balance for total drawdown calculations")
    day_start_balance: Optional[float] = Field(None, description="Balance at start of trading day")
    day_start_equity: Optional[float] = Field(None, description="Equity at start of trading day")
    margin_used: float = Field(0.0, description="Margin currently used")
    margin_available: float = Field(0.0, description="Available margin")
    total_profit_loss: float = Field(0.0, description="Realized profit/loss for the day")
    positions: List[PositionInput] = Field(default_factory=list, description="Open positions to assess")


class ComplianceRequest(BaseModel):
    """API request for a compliance review."""

    firm: str = Field(..., description="Prop firm name as stored in the database")
    program_id: Optional[str] = Field(None, description="Program identifier used to fetch rules from the database")
    account_id: Optional[str] = Field(None, description="Optional account identifier for client-side tracking")
    account: AccountDataInput = Field(..., description="Account data used for evaluation")
    include_soft_rules: bool = Field(True, description="Whether to return soft-rule insights alongside the review")


class BreachResponse(BaseModel):
    """Serialized rule breach."""

    level: str
    code: str
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None


class SoftRuleInsight(BaseModel):
    """Soft rule guidance pulled from the rules database."""

    rule_type: str
    description: str
    challenge_type: Optional[str] = None
    severity: Optional[str] = None
    extraction_method: Optional[str] = None
    confidence_score: Optional[float] = None
    conditions: Optional[str] = None


class ComplianceResponse(BaseModel):
    """API response summarizing compliance status and insights."""

    account_id: Optional[str]
    firm: str
    program_id: Optional[str]
    rules_source: str
    status: str
    hard_breaches: List[BreachResponse]
    warnings: List[BreachResponse]
    soft_rule_insights: List[SoftRuleInsight] = Field(default_factory=list)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Simple health endpoint."""

    return {"status": "ok"}


def _load_ruleset(firm: str, program_id: Optional[str]) -> tuple[PropRules, str]:
    """Return the rule set for a firm/program with its source."""

    normalized_firm = firm.strip()

    if program_id:
        rules = account_manager.get_rules_by_program_id(normalized_firm, program_id)
        if rules:
            return rules, "database"

    rules = FIRM_RULES.get(normalized_firm.lower())
    if rules:
        return rules, "predefined"

    raise HTTPException(status_code=404, detail=f"No rules found for firm '{firm}'")


def _build_snapshot(account: AccountDataInput) -> AccountSnapshot:
    """Transform incoming account data into an AccountSnapshot."""

    positions = [
        Position(
            position_id=pos.position_id,
            symbol=pos.symbol,
            volume=pos.volume,
            entry_price=pos.entry_price,
            current_price=pos.current_price,
            profit_loss=pos.profit_loss,
            side=pos.side,
        )
        for pos in account.positions
    ]

    return AccountSnapshot(
        timestamp=datetime.utcnow(),
        balance=account.balance,
        equity=account.equity,
        margin_used=account.margin_used,
        margin_available=account.margin_available,
        positions=positions,
        total_profit_loss=account.total_profit_loss,
        starting_balance=account.starting_balance,
        day_start_balance=account.day_start_balance,
        day_start_equity=account.day_start_equity,
    )


def _get_soft_rules(firm: str, program_id: Optional[str]) -> List[SoftRuleInsight]:
    """Fetch soft-rule insights for a firm from the database."""

    db_path = Path(account_manager.db_path)
    if not db_path.exists():
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM prop_firm WHERE name = ? COLLATE NOCASE", (firm,))
    firm_row = cursor.fetchone()
    if not firm_row:
        conn.close()
        return []

    firm_id = firm_row["id"]
    query = [
        "SELECT rule_type, details, challenge_type, severity, extraction_method, confidence_score, conditions",
        "FROM firm_rule",
        "WHERE firm_id = ?",
        "AND (rule_category = 'soft_rule' OR severity = 'optional')",
    ]
    params: list = [firm_id]

    if program_id:
        query.append("AND challenge_type = ?")
        params.append(program_id)

    query.append("ORDER BY extracted_at DESC")

    cursor.execute("\n".join(query), params)
    rows = cursor.fetchall()
    conn.close()

    insights: List[SoftRuleInsight] = []
    for row in rows:
        insights.append(
            SoftRuleInsight(
                rule_type=row["rule_type"],
                description=row["details"] or "",
                challenge_type=row["challenge_type"],
                severity=row["severity"],
                extraction_method=row["extraction_method"],
                confidence_score=row["confidence_score"],
                conditions=row["conditions"],
            )
        )

    return insights


@app.post("/compliance/review", response_model=ComplianceResponse, tags=["compliance"])
def review_compliance(request: ComplianceRequest) -> ComplianceResponse:
    """Evaluate an account against prop firm rules and return insights."""

    rules, source = _load_ruleset(request.firm, request.program_id)
    snapshot = _build_snapshot(request.account)
    breaches = check_account_rules(snapshot, rules, starting_balance=request.account.starting_balance)

    hard_breaches = [b for b in breaches if b.level == "HARD"]
    warnings = [b for b in breaches if b.level == "WARN"]

    if hard_breaches:
        status = "non_compliant"
    elif warnings:
        status = "needs_attention"
    else:
        status = "compliant"

    soft_insights = _get_soft_rules(request.firm, request.program_id) if request.include_soft_rules else []

    return ComplianceResponse(
        account_id=request.account_id,
        firm=request.firm,
        program_id=request.program_id,
        rules_source=source,
        status=status,
        hard_breaches=[BreachResponse(**b.__dict__) for b in hard_breaches],
        warnings=[BreachResponse(**b.__dict__) for b in warnings],
        soft_rule_insights=soft_insights,
    )


@app.get(
    "/firms/{firm}/soft-rules",
    response_model=List[SoftRuleInsight],
    tags=["insights"],
)
def soft_rules(firm: str, program_id: Optional[str] = None) -> List[SoftRuleInsight]:
    """Return soft-rule insights for a firm/program."""

    insights = _get_soft_rules(firm, program_id)
    if not insights:
        raise HTTPException(status_code=404, detail="No soft rules found for the requested firm")

    return insights


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8010,
        log_level="info",
    )
