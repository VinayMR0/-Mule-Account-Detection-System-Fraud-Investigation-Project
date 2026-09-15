import pandas as pd
import numpy as np

# ---------------------------------------
# LOAD DATA
# ---------------------------------------

accounts = pd.read_csv("data/accounts.csv")

transactions = pd.read_csv(
    "data/transactions.csv",
    parse_dates=["transaction_time"]
)

print("Data loaded successfully!")
print(f"Accounts: {len(accounts)}")
print(f"Transactions: {len(transactions)}")


# ---------------------------------------
# 1. INCOMING TRANSACTIONS
# ---------------------------------------

incoming = (
    transactions
    .groupby("receiver_account")
    .agg(
        incoming_count=("transaction_id", "count"),
        unique_senders=("sender_account", "nunique"),
        total_received=("amount", "sum")
    )
    .reset_index()
)

incoming.rename(
    columns={"receiver_account": "account_id"},
    inplace=True
)


# ---------------------------------------
# 2. OUTGOING TRANSACTIONS
# ---------------------------------------

outgoing = (
    transactions
    .groupby("sender_account")
    .agg(
        outgoing_count=("transaction_id", "count"),
        unique_receivers=("receiver_account", "nunique"),
        total_sent=("amount", "sum")
    )
    .reset_index()
)

outgoing.rename(
    columns={"sender_account": "account_id"},
    inplace=True
)


# ---------------------------------------
# 3. TRANSACTION VELOCITY
# ---------------------------------------

transaction_counts = (
    transactions
    .groupby("receiver_account")
    .size()
    .reset_index(name="transaction_velocity")
)

transaction_counts.rename(
    columns={"receiver_account": "account_id"},
    inplace=True
)


# ---------------------------------------
# 4. DEVICE ANALYSIS
# ---------------------------------------

device_analysis = (
    transactions
    .groupby("receiver_account")["device_id"]
    .nunique()
    .reset_index(name="unique_devices")
)

device_analysis.rename(
    columns={"receiver_account": "account_id"},
    inplace=True
)


# ---------------------------------------
# 5. MERGE ALL FEATURES
# ---------------------------------------

risk_data = accounts.copy()

risk_data = risk_data.merge(
    incoming,
    on="account_id",
    how="left"
)

risk_data = risk_data.merge(
    outgoing,
    on="account_id",
    how="left"
)

risk_data = risk_data.merge(
    transaction_counts,
    on="account_id",
    how="left"
)

risk_data = risk_data.merge(
    device_analysis,
    on="account_id",
    how="left"
)


# ---------------------------------------
# FILL MISSING VALUES
# ---------------------------------------

numeric_columns = [
    "incoming_count",
    "unique_senders",
    "total_received",
    "outgoing_count",
    "unique_receivers",
    "total_sent",
    "transaction_velocity",
    "unique_devices"
]

risk_data[numeric_columns] = (
    risk_data[numeric_columns]
    .fillna(0)
)


# ---------------------------------------
# 6. RISK SCORING
# ---------------------------------------

risk_data["risk_score"] = 0

# Multiple unique senders
risk_data.loc[
    risk_data["unique_senders"] >= 10,
    "risk_score"
] += 20

# High incoming transaction count
risk_data.loc[
    risk_data["incoming_count"] >= 12,
    "risk_score"
] += 15

# High transaction velocity
risk_data.loc[
    risk_data["transaction_velocity"] >= 15,
    "risk_score"
] += 15

# Multiple devices
risk_data.loc[
    risk_data["unique_devices"] >= 4,
    "risk_score"
] += 10

# New account
risk_data.loc[
    risk_data["account_age_days"] <= 90,
    "risk_score"
] += 10

# High number of outgoing transactions
risk_data.loc[
    risk_data["outgoing_count"] >= 10,
    "risk_score"
] += 10


# ---------------------------------------
# 7. RAPID FUND MOVEMENT
# ---------------------------------------

rapid_transfer_accounts = set()

for account in transactions["receiver_account"].unique():

    incoming_txns = transactions[
        transactions["receiver_account"] == account
    ].sort_values("transaction_time")

    outgoing_txns = transactions[
        transactions["sender_account"] == account
    ].sort_values("transaction_time")

    for _, incoming_txn in incoming_txns.iterrows():

        later_outgoing = outgoing_txns[
            (outgoing_txns["transaction_time"] >
             incoming_txn["transaction_time"]) &
            (outgoing_txns["transaction_time"] <=
             incoming_txn["transaction_time"] +
             pd.Timedelta(minutes=30))
        ]

        if len(later_outgoing) > 0:

            rapid_transfer_accounts.add(account)

            break


risk_data.loc[
    risk_data["account_id"].isin(rapid_transfer_accounts),
    "risk_score"
] += 25


# ---------------------------------------
# CAP SCORE AT 100
# ---------------------------------------

risk_data["risk_score"] = (
    risk_data["risk_score"]
    .clip(upper=100)
)


# ---------------------------------------
# 8. RISK LEVEL
# ---------------------------------------

def classify_risk(score):

    if score >= 60:
        return "HIGH"

    elif score >= 30:
        return "MEDIUM"

    else:
        return "LOW"


risk_data["risk_level"] = (
    risk_data["risk_score"]
    .apply(classify_risk)
)


# ---------------------------------------
# 9. SORT BY RISK
# ---------------------------------------

risk_data = risk_data.sort_values(
    "risk_score",
    ascending=False
)


# ---------------------------------------
# 10. SAVE RESULTS
# ---------------------------------------

risk_data.to_csv(
    "data/mule_risk_scores.csv",
    index=False
)


# ---------------------------------------
# 11. DISPLAY RESULTS
# ---------------------------------------

print("\n--------------------------------")
print("MULE ACCOUNT DETECTION COMPLETE")
print("--------------------------------")

print(
    "\nRisk distribution:"
)

print(
    risk_data["risk_level"]
    .value_counts()
)

print(
    "\nTop 20 highest-risk accounts:"
)

print(
    risk_data[
        [
            "account_id",
            "risk_score",
            "risk_level",
            "unique_senders",
            "incoming_count",
            "outgoing_count",
            "unique_devices"
        ]
    ].head(20).to_string(index=False)
)

print(
    "\nResults saved to:"
)

print(
    "data/mule_risk_scores.csv"
)