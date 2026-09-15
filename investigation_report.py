import pandas as pd
from datetime import timedelta

# ============================================================
# LOAD DATA
# ============================================================

accounts = pd.read_csv("data/accounts.csv")
transactions = pd.read_csv("data/transactions.csv")
risk_scores = pd.read_csv("data/mule_risk_scores.csv")

# Convert transaction_time to datetime
transactions["transaction_time"] = pd.to_datetime(
    transactions["transaction_time"]
)

# Select the highest-risk account
top_account = risk_scores.sort_values(
    by="risk_score",
    ascending=False
).iloc[0]

account_id = top_account["account_id"]

print("=" * 60)
print("FRAUD INVESTIGATION REPORT")
print("=" * 60)

print(f"\nAccount ID     : {account_id}")
print(f"Risk Score     : {top_account['risk_score']}/100")
print(f"Risk Level     : {top_account['risk_level']}")

# ============================================================
# ACCOUNT INFORMATION
# ============================================================

account_info = accounts[
    accounts["account_id"] == account_id
].iloc[0]

print("\nACCOUNT INFORMATION")
print("-" * 40)

print(f"Account Age    : {account_info['account_age_days']} days")
print(f"KYC Status     : {account_info['kyc_status']}")
print(f"City           : {account_info['city']}")

# ============================================================
# TRANSACTION ANALYSIS
# ============================================================

incoming = transactions[
    transactions["receiver_account"] == account_id
].copy()

outgoing = transactions[
    transactions["sender_account"] == account_id
].copy()

# Sort transactions chronologically
incoming = incoming.sort_values("transaction_time")
outgoing = outgoing.sort_values("transaction_time")

total_received = incoming["amount"].sum()
total_sent = outgoing["amount"].sum()

unique_senders = incoming["sender_account"].nunique()
unique_receivers = outgoing["receiver_account"].nunique()

# Devices associated with the account
account_transactions = transactions[
    (transactions["sender_account"] == account_id) |
    (transactions["receiver_account"] == account_id)
]

unique_devices = account_transactions["device_id"].nunique()

print("\nTRANSACTION ANALYSIS")
print("-" * 40)

print(f"Incoming Transactions : {len(incoming)}")
print(f"Unique Senders        : {unique_senders}")
print(f"Total Received        : ₹{total_received:,.2f}")

print(f"\nOutgoing Transactions : {len(outgoing)}")
print(f"Unique Receivers      : {unique_receivers}")
print(f"Total Sent            : ₹{total_sent:,.2f}")

print(f"\nAssociated Devices    : {unique_devices}")

# ============================================================
# TRANSACTION TYPES
# ============================================================

print("\nTRANSACTION TYPES")
print("-" * 40)

transaction_type_counts = account_transactions[
    "transaction_type"
].value_counts()

for transaction_type, count in transaction_type_counts.items():
    print(f"{transaction_type:<18}: {count}")

# ============================================================
# RAPID FUND MOVEMENT ANALYSIS
# ============================================================

rapid_transfers = []

for _, inc in incoming.iterrows():

    possible_outgoing = outgoing[
        (outgoing["transaction_time"] >= inc["transaction_time"]) &
        (
            outgoing["transaction_time"]
            <= inc["transaction_time"] + timedelta(minutes=30)
        )
    ]

    for _, out in possible_outgoing.iterrows():

        rapid_transfers.append({
            "incoming_transaction": inc["transaction_id"],
            "incoming_time": inc["transaction_time"],
            "incoming_amount": inc["amount"],
            "outgoing_transaction": out["transaction_id"],
            "outgoing_time": out["transaction_time"],
            "outgoing_amount": out["amount"],
            "receiver": out["receiver_account"]
        })

print("\nRAPID FUND MOVEMENT")
print("-" * 40)

print(f"Rapid transfer events : {len(rapid_transfers)}")

# ============================================================
# RISK INDICATORS
# ============================================================

print("\nRISK INDICATORS")
print("-" * 40)

risk_reasons = []

if unique_senders >= 10:
    risk_reasons.append(
        "High number of unique incoming senders"
    )

if len(incoming) >= 12:
    risk_reasons.append(
        "High incoming transaction volume"
    )

if len(incoming) >= 15:
    risk_reasons.append(
        "High transaction velocity"
    )

if unique_devices >= 4:
    risk_reasons.append(
        "Multiple devices associated with account"
    )

if account_info["account_age_days"] <= 90:
    risk_reasons.append(
        "Recently opened account"
    )

if len(outgoing) >= 10:
    risk_reasons.append(
        "High outgoing transaction volume"
    )

if len(rapid_transfers) > 0:
    risk_reasons.append(
        "Rapid movement of funds after incoming transactions"
    )

if not risk_reasons:
    risk_reasons.append(
        "No major risk indicators identified"
    )

for i, reason in enumerate(risk_reasons, 1):
    print(f"{i}. {reason}")

# ============================================================
# FUND FLOW ANALYSIS
# ============================================================

print("\nFUND FLOW ANALYSIS")
print("-" * 40)

if total_received > 0:

    outgoing_ratio = (total_sent / total_received) * 100

    print(f"Received : ₹{total_received:,.2f}")
    print(f"Sent     : ₹{total_sent:,.2f}")
    print(f"Outflow / Inflow Ratio : {outgoing_ratio:.2f}%")

else:

    outgoing_ratio = 0

    print("No incoming funds identified.")

# ============================================================
# TOP INCOMING SENDERS
# ============================================================

print("\nTOP INCOMING SENDERS")
print("-" * 40)

if not incoming.empty:

    top_senders = (
        incoming.groupby("sender_account")["amount"]
        .agg(["count", "sum"])
        .sort_values("sum", ascending=False)
        .head(5)
    )

    for sender, row in top_senders.iterrows():

        print(
            f"{sender} | "
            f"Transactions: {int(row['count'])} | "
            f"Amount: ₹{row['sum']:,.2f}"
        )

else:

    print("No incoming transactions.")

# ============================================================
# TOP OUTGOING RECEIVERS
# ============================================================

print("\nTOP OUTGOING RECEIVERS")
print("-" * 40)

if not outgoing.empty:

    top_receivers = (
        outgoing.groupby("receiver_account")["amount"]
        .agg(["count", "sum"])
        .sort_values("sum", ascending=False)
        .head(5)
    )

    for receiver, row in top_receivers.iterrows():

        print(
            f"{receiver} | "
            f"Transactions: {int(row['count'])} | "
            f"Amount: ₹{row['sum']:,.2f}"
        )

else:

    print("No outgoing transactions.")

# ============================================================
# INVESTIGATION ASSESSMENT
# ============================================================

print("\nINVESTIGATION ASSESSMENT")
print("-" * 40)

risk_level = top_account["risk_level"]

if risk_level == "HIGH":

    assessment = (
        "The account exhibits multiple high-risk behavioural "
        "indicators consistent with potential mule-account "
        "activity. Further investigation is recommended."
    )

    recommended_action = (
        "HIGH-RISK REVIEW / ACCOUNT RESTRICTION "
        "AS PER APPLICABLE POLICY"
    )

elif risk_level == "MEDIUM":

    assessment = (
        "The account exhibits several suspicious behavioural "
        "indicators and requires enhanced review."
    )

    recommended_action = "ENHANCED REVIEW"

else:

    assessment = (
        "The account currently shows limited indicators "
        "of suspicious activity."
    )

    recommended_action = "ROUTINE MONITORING"

print(assessment)

print("\nRECOMMENDED ACTION")
print("-" * 40)
print(recommended_action)

# ============================================================
# CREATE INVESTIGATION REPORT
# ============================================================

report = pd.DataFrame([{

    "account_id": account_id,

    "risk_score": top_account["risk_score"],
    "risk_level": risk_level,

    "account_age_days": account_info["account_age_days"],
    "kyc_status": account_info["kyc_status"],
    "city": account_info["city"],

    "incoming_transactions": len(incoming),
    "unique_senders": unique_senders,
    "total_received": round(total_received, 2),

    "outgoing_transactions": len(outgoing),
    "unique_receivers": unique_receivers,
    "total_sent": round(total_sent, 2),

    "outflow_inflow_ratio": round(outgoing_ratio, 2),

    "unique_devices": unique_devices,

    "rapid_transfer_events": len(rapid_transfers),

    "risk_indicators": " | ".join(risk_reasons),

    "investigation_assessment": assessment,

    "recommended_action": recommended_action

}])

# ============================================================
# SAVE CSV REPORT
# ============================================================

report.to_csv(
    "data/investigation_report.csv",
    index=False
)

# ============================================================
# SAVE RAPID TRANSFER DETAILS
# ============================================================

if rapid_transfers:

    rapid_df = pd.DataFrame(rapid_transfers)

    rapid_df.to_csv(
        "data/rapid_fund_movements.csv",
        index=False
    )

# ============================================================
# FINAL MESSAGE
# ============================================================

print("\n" + "=" * 60)
print("INVESTIGATION REPORT GENERATED SUCCESSFULLY")
print("=" * 60)

print("\nFiles created:")

print("1. data/investigation_report.csv")

if rapid_transfers:
    print("2. data/rapid_fund_movements.csv")

print("\nInvestigation completed for:")
print(f"Account: {account_id}")
print(f"Risk Level: {risk_level}")
print(f"Risk Score: {top_account['risk_score']}/100")

print("=" * 60)