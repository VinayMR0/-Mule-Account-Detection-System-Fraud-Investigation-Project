# 🚨 Mule Account Detection System

A rule-based fraud detection and investigation system designed to identify potentially suspicious **mule accounts** by analysing transaction behaviour, fund movement, account characteristics, and counterparty relationships.

The project generates synthetic banking data, applies fraud detection rules, calculates an explainable risk score, and provides an interactive Streamlit dashboard for investigation.

---

## 🎯 Project Objective

Mule accounts are bank accounts used to receive and transfer funds associated with fraudulent or suspicious activities.

This project aims to identify potential mule accounts by detecting behavioural patterns such as:

- Multiple unique senders
- Multiple beneficiaries
- High transaction velocity
- Rapid movement of incoming funds
- Recently created accounts showing suspicious activity
- Shared devices associated with suspicious accounts
- Unusual transaction and fund-flow patterns


