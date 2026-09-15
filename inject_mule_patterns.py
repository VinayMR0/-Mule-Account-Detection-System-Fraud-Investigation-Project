import pandas as pd
import numpy as np
import random
from datetime import timedelta

# ---------------------------------
# LOAD EXISTING DATA
# ---------------------------------

accounts = pd.read_csv("data/accounts.csv")
transactions = pd.read_csv("data/transactions.csv")

transactions["transaction_time"] = pd.to_datetime(
    transactions["transaction_time"]
)

random.seed(42)
np.random.seed(42)

# ---------------------------------
# SELECT POTENTIAL MULE ACCOUNTS
# ---------------------------------

account_ids = accounts["account_id"].tolist()

mule_accounts = random.sample(account_ids, 30)

print("Mule accounts selected:", mule_accounts)

# ---------------------------------
# CREATE SUSPICIOUS TRANSACTIONS
# ---------------------------------

new_transactions = []

transaction_counter = 2000000

for mule in mule_accounts:

    # ---------------------------------
    # PATTERN 1:
    # Multiple different accounts
    # sending money to mule
    # ---------------------------------

    senders = random.sample(
        [x for x in account_ids if x != mule],
        random.randint(8, 15)
    )

    base_time = pd.Timestamp("2026-06-15") + pd.Timedelta(
        days=random.randint(0, 20)
    )

    total_received = 0

    for sender in senders:

        amount = random.randint(3000, 15000)

        transaction_time = (
            base_time +
            pd.Timedelta(minutes=random.randint(1, 180))
        )

        new_transactions.append([
            f"TXN{transaction_counter}",
            sender,
            mule,
            amount,
            transaction_time,
            random.choice(["UPI", "IMPS", "BANK_TRANSFER"]),
            f"DEV{random.randint(1000, 1300)}"
        ])

        transaction_counter += 1
        total_received += amount

    # ---------------------------------
    # PATTERN 2:
    # Rapid outgoing transfer
    # ---------------------------------

    receiver = random.choice(
        [x for x in account_ids if x != mule]
    )

    outgoing_amount = round(
        total_received * random.uniform(0.75, 0.95),
        2
    )

    outgoing_time = base_time + pd.Timedelta(
        minutes=random.randint(10, 30)
    )

    new_transactions.append([
        f"TXN{transaction_counter}",
        mule,
        receiver,
        outgoing_amount,
        outgoing_time,
        "IMPS",
        f"DEV{random.randint(1000, 1300)}"
    ])

    transaction_counter += 1

# ---------------------------------
# ADD SUSPICIOUS TRANSACTIONS
# ---------------------------------

suspicious_df = pd.DataFrame(
    new_transactions,
    columns=[
        "transaction_id",
        "sender_account",
        "receiver_account",
        "amount",
        "transaction_time",
        "transaction_type",
        "device_id"
    ]
)

transactions = pd.concat(
    [transactions, suspicious_df],
    ignore_index=True
)

# ---------------------------------
# ADD GROUND TRUTH LABEL
# ---------------------------------

accounts["is_mule"] = accounts["account_id"].isin(
    mule_accounts
)

# ---------------------------------
# SAVE UPDATED DATA
# ---------------------------------

transactions.to_csv(
    "data/transactions.csv",
    index=False
)

accounts.to_csv(
    "data/accounts.csv",
    index=False
)

print("\nMule behaviour injected successfully!")

print(
    "Total transactions:",
    len(transactions)
)

print(
    "Mule accounts:",
    accounts["is_mule"].sum()
)

print("\nUpdated files:")
print("data/accounts.csv")
print("data/transactions.csv")