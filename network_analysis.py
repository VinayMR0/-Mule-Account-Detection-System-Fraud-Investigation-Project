import pandas as pd

# ============================================================
# LOAD DATA
# ============================================================

transactions = pd.read_csv("data/transactions.csv")

transactions["transaction_time"] = pd.to_datetime(
    transactions["transaction_time"]
)

print("=" * 60)
print("MULE NETWORK & FUND-FLOW ANALYSIS")
print("=" * 60)

# ============================================================
# BASIC NETWORK EDGES
# ============================================================

network_edges = (
    transactions
    .groupby(["sender_account", "receiver_account"])
    .agg(
        transaction_count=("transaction_id", "count"),
        total_amount=("amount", "sum"),
        average_amount=("amount", "mean")
    )
    .reset_index()
)

network_edges.to_csv(
    "data/account_network.csv",
    index=False
)

# ============================================================
# ACCOUNT-LEVEL NETWORK FEATURES
# ============================================================

accounts = set(
    transactions["sender_account"]
).union(
    set(transactions["receiver_account"])
)

results = []

for account in accounts:

    incoming = transactions[
        transactions["receiver_account"] == account
    ].copy()

    outgoing = transactions[
        transactions["sender_account"] == account
    ].copy()

    # --------------------------------------------------------
    # BASIC NETWORK METRICS
    # --------------------------------------------------------

    unique_senders = incoming[
        "sender_account"
    ].nunique()

    unique_receivers = outgoing[
        "receiver_account"
    ].nunique()

    total_received = incoming["amount"].sum()
    total_sent = outgoing["amount"].sum()

    incoming_count = len(incoming)
    outgoing_count = len(outgoing)

    # --------------------------------------------------------
    # PASS-THROUGH RATIO
    # --------------------------------------------------------

    if total_received > 0:
        pass_through_ratio = total_sent / total_received
    else:
        pass_through_ratio = 0

    # --------------------------------------------------------
    # RAPID FUND MOVEMENT
    # --------------------------------------------------------

    rapid_movements = 0

    for _, in_txn in incoming.iterrows():

        future_outgoing = outgoing[
            (outgoing["transaction_time"] >= in_txn["transaction_time"]) &
            (
                outgoing["transaction_time"]
                <= in_txn["transaction_time"]
                + pd.Timedelta(minutes=30)
            )
        ]

        if len(future_outgoing) > 0:
            rapid_movements += len(future_outgoing)

    # --------------------------------------------------------
    # NETWORK SCORE
    # --------------------------------------------------------

    score = 0
    reasons = []

    # Multiple incoming sources
    if unique_senders >= 10:
        score += 20
        reasons.append(
            "10+ incoming counterparties"
        )

    elif unique_senders >= 5:
        score += 10
        reasons.append(
            "Multiple incoming counterparties"
        )

    # Multiple outgoing destinations
    if unique_receivers >= 8:
        score += 20
        reasons.append(
            "8+ outgoing counterparties"
        )

    elif unique_receivers >= 4:
        score += 10
        reasons.append(
            "Multiple outgoing counterparties"
        )

    # --------------------------------------------------------
    # PASS-THROUGH BEHAVIOUR
    # --------------------------------------------------------

    if (
        total_received >= 30000
        and pass_through_ratio >= 0.70
    ):
        score += 25
        reasons.append(
            "High pass-through of received funds"
        )

    # --------------------------------------------------------
    # RAPID MOVEMENT
    # --------------------------------------------------------

    if rapid_movements >= 3:
        score += 25
        reasons.append(
            "Repeated rapid incoming-to-outgoing movement"
        )

    elif rapid_movements >= 1:
        score += 10
        reasons.append(
            "Rapid incoming-to-outgoing movement"
        )

    # --------------------------------------------------------
    # INTERMEDIARY PATTERN
    # --------------------------------------------------------

    if (
        unique_senders >= 5
        and unique_receivers >= 4
        and pass_through_ratio >= 0.50
    ):
        score += 15
        reasons.append(
            "Potential intermediary account"
        )

    score = min(score, 100)

    # --------------------------------------------------------
    # RISK LEVEL
    # --------------------------------------------------------

    if score >= 70:
        risk_level = "HIGH"

    elif score >= 40:
        risk_level = "MEDIUM"

    else:
        risk_level = "LOW"

    results.append({
        "account_id": account,
        "unique_senders": unique_senders,
        "unique_receivers": unique_receivers,
        "incoming_count": incoming_count,
        "outgoing_count": outgoing_count,
        "total_received": round(total_received, 2),
        "total_sent": round(total_sent, 2),
        "pass_through_ratio": round(
            pass_through_ratio, 2
        ),
        "rapid_movements": rapid_movements,
        "network_risk_score": score,
        "network_risk_level": risk_level,
        "network_risk_reasons": " | ".join(reasons)
    })

# ============================================================
# SAVE RESULTS
# ============================================================

network_risk = pd.DataFrame(results)

network_risk = network_risk.sort_values(
    "network_risk_score",
    ascending=False
)

network_risk.to_csv(
    "data/network_risk_scores.csv",
    index=False
)

# ============================================================
# DISPLAY SCORE DISTRIBUTION
# ============================================================

print("\nNETWORK RISK DISTRIBUTION")
print("-" * 40)

print(
    network_risk["network_risk_level"]
    .value_counts()
)

# ============================================================
# DISPLAY TOP ACCOUNTS
# ============================================================

print("\nTOP NETWORK RISK ACCOUNTS")
print("-" * 40)

columns = [
    "account_id",
    "unique_senders",
    "unique_receivers",
    "total_received",
    "total_sent",
    "pass_through_ratio",
    "rapid_movements",
    "network_risk_score",
    "network_risk_level"
]

print(
    network_risk[columns]
    .head(20)
    .to_string(index=False)
)

print("\n" + "=" * 60)
print("NETWORK ANALYSIS COMPLETED")
print("=" * 60)

print("\nFiles created:")
print("1. data/account_network.csv")
print("2. data/network_risk_scores.csv")