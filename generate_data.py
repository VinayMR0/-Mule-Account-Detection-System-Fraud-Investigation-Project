import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# -----------------------------
# SETTINGS
# -----------------------------
np.random.seed(42)
random.seed(42)

NUM_ACCOUNTS = 1000
NUM_TRANSACTIONS = 10000

# -----------------------------
# 1. CREATE ACCOUNTS
# -----------------------------
accounts = []

cities = [
    "Bengaluru",
    "Mumbai",
    "Delhi",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Kolkata",
    "Ahmedabad"
]

customer_types = ["Individual", "Business"]
kyc_statuses = ["Verified", "Verified", "Verified", "Pending"]

for i in range(NUM_ACCOUNTS):

    account_id = f"ACC{100000 + i}"

    account_age_days = np.random.randint(10, 2500)

    customer_type = random.choice(customer_types)

    city = random.choice(cities)

    kyc_status = random.choice(kyc_statuses)

    accounts.append([
        account_id,
        account_age_days,
        customer_type,
        city,
        kyc_status
    ])

accounts_df = pd.DataFrame(
    accounts,
    columns=[
        "account_id",
        "account_age_days",
        "customer_type",
        "city",
        "kyc_status"
    ]
)

# -----------------------------
# 2. CREATE TRANSACTIONS
# -----------------------------
transactions = []

transaction_types = [
    "UPI",
    "IMPS",
    "NEFT",
    "CARD",
    "BANK_TRANSFER"
]

start_date = datetime(2026, 1, 1)

account_ids = accounts_df["account_id"].tolist()

for i in range(NUM_TRANSACTIONS):

    sender = random.choice(account_ids)

    receiver = random.choice(account_ids)

    # Make sure sender and receiver are different
    while receiver == sender:
        receiver = random.choice(account_ids)

    amount = round(
        np.random.lognormal(mean=7, sigma=1.2),
        2
    )

    # Keep amounts realistic
    amount = min(amount, 200000)

    transaction_time = (
        start_date +
        timedelta(
            days=random.randint(0, 180),
            minutes=random.randint(0, 1439)
        )
    )

    transaction_type = random.choice(transaction_types)

    device_id = f"DEV{random.randint(1000, 1300)}"

    transactions.append([
        f"TXN{1000000 + i}",
        sender,
        receiver,
        amount,
        transaction_time,
        transaction_type,
        device_id
    ])

transactions_df = pd.DataFrame(
    transactions,
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

# -----------------------------
# 3. SAVE DATA
# -----------------------------

accounts_df.to_csv(
    "data/accounts.csv",
    index=False
)

transactions_df.to_csv(
    "data/transactions.csv",
    index=False
)

print("Data generation completed!")

print(
    f"Accounts created: {len(accounts_df)}"
)

print(
    f"Transactions created: {len(transactions_df)}"
)

print("\nSample Accounts:")
print(accounts_df.head())

print("\nSample Transactions:")
print(transactions_df.head())