import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Mule Account Detection & Investigation",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .risk-high {
        padding: 12px 16px;
        border-radius: 10px;
        background: rgba(255, 75, 75, 0.14);
        border: 1px solid rgba(255, 75, 75, 0.35);
        margin-bottom: 8px;
    }

    .risk-medium {
        padding: 12px 16px;
        border-radius: 10px;
        background: rgba(255, 165, 0, 0.14);
        border: 1px solid rgba(255, 165, 0, 0.35);
        margin-bottom: 8px;
    }

    .risk-low {
        padding: 12px 16px;
        border-radius: 10px;
        background: rgba(50, 205, 50, 0.12);
        border: 1px solid rgba(50, 205, 50, 0.3);
        margin-bottom: 8px;
    }

    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin-top: 0.5rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.07);
        padding: 12px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.15);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data
def load_data():
    accounts = pd.read_csv("data/accounts.csv")
    transactions = pd.read_csv("data/transactions.csv")
    risk_scores = pd.read_csv("data/mule_risk_scores.csv")

    transactions["transaction_time"] = pd.to_datetime(
        transactions["transaction_time"],
        errors="coerce"
    )

    return accounts, transactions, risk_scores


try:
    accounts, transactions, risk_scores = load_data()
except Exception as e:
    st.error("Could not load the project data.")
    st.code(str(e))
    st.stop()

# ============================================================
# SIDEBAR FILTERS
# ============================================================
st.sidebar.title("🎛️ Investigation Controls")

risk_options = ["ALL"] + sorted(
    risk_scores["risk_level"].dropna().unique().tolist()
)

selected_risk = st.sidebar.selectbox(
    "Risk Level",
    risk_options
)

min_score, max_score = st.sidebar.slider(
    "Risk Score Range",
    min_value=0,
    max_value=100,
    value=(0, 100)
)

if transactions["transaction_time"].notna().any():
    min_date = transactions["transaction_time"].min().date()
    max_date = transactions["transaction_time"].max().date()

    selected_dates = st.sidebar.date_input(
        "Transaction Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    selected_dates = None

# Apply account/risk filters
filtered_risk = risk_scores[
    risk_scores["risk_score"].between(min_score, max_score)
].copy()

if selected_risk != "ALL":
    filtered_risk = filtered_risk[
        filtered_risk["risk_level"] == selected_risk
    ]

filtered_accounts = accounts[
    accounts["account_id"].isin(filtered_risk["account_id"])
].copy()

# Apply transaction date filter
filtered_transactions = transactions.copy()

if selected_dates and len(selected_dates) == 2:
    start_date, end_date = selected_dates

    filtered_transactions = filtered_transactions[
        (filtered_transactions["transaction_time"].dt.date >= start_date) &
        (filtered_transactions["transaction_time"].dt.date <= end_date)
    ]

# ============================================================
# HEADER
# ============================================================
st.title("🚨 Mule Account Detection & Investigation System")
st.caption("Interactive Fraud Risk Monitoring & Investigation Dashboard")

st.divider()

# ============================================================
# GLOBAL KPIs
# ============================================================
total_accounts = len(accounts)
total_transactions = len(filtered_transactions)

high_risk_count = len(
    filtered_risk[filtered_risk["risk_level"] == "HIGH"]
)
medium_risk_count = len(
    filtered_risk[filtered_risk["risk_level"] == "MEDIUM"]
)
low_risk_count = len(
    filtered_risk[filtered_risk["risk_level"] == "LOW"]
)

flagged_pct = (
    (high_risk_count / len(filtered_risk) * 100)
    if len(filtered_risk) else 0
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Accounts", f"{total_accounts:,}")
k2.metric("🔴 High Risk", f"{high_risk_count:,}")
k3.metric("🟠 Medium Risk", f"{medium_risk_count:,}")
k4.metric("🟢 Low Risk", f"{low_risk_count:,}")
k5.metric("High-Risk %", f"{flagged_pct:.1f}%")

st.divider()

# ============================================================
# ACCOUNT SELECTION
# ============================================================
st.subheader("🔎 Investigate an Account")

if filtered_risk.empty:
    st.warning("No accounts match the selected filters.")
    st.stop()

# Sort highest risk first
account_options = filtered_risk.sort_values(
    ["risk_score", "account_id"],
    ascending=[False, True]
)["account_id"].tolist()

selected_account = st.selectbox(
    "Select account",
    account_options,
    format_func=lambda x: (
        f"{x}  |  "
        f"Risk {int(filtered_risk.loc[filtered_risk['account_id'] == x, 'risk_score'].iloc[0])}/100"
    )
)

risk_data = risk_scores[
    risk_scores["account_id"] == selected_account
].iloc[0]

account_data = accounts[
    accounts["account_id"] == selected_account
].iloc[0]

incoming = transactions[
    transactions["receiver_account"] == selected_account
].copy()

outgoing = transactions[
    transactions["sender_account"] == selected_account
].copy()

incoming = incoming.sort_values("transaction_time")
outgoing = outgoing.sort_values("transaction_time")

# ============================================================
# SELECTED ACCOUNT KPIs
# ============================================================
risk_score = int(risk_data["risk_score"])
risk_level = str(risk_data["risk_level"])

total_received = incoming["amount"].sum()
total_sent = outgoing["amount"].sum()

unique_senders = incoming["sender_account"].nunique()
unique_receivers = outgoing["receiver_account"].nunique()
unique_devices = pd.concat([
    incoming["device_id"],
    outgoing["device_id"]
]).nunique()

outflow_ratio = (
    total_sent / total_received * 100
    if total_received > 0 else 0
)

a1, a2, a3, a4, a5 = st.columns(5)

a1.metric("Risk Score", f"{risk_score}/100")
a2.metric("Risk Level", risk_level)
a3.metric("Received", f"₹{total_received:,.0f}")
a4.metric("Sent", f"₹{total_sent:,.0f}")
a5.metric("Outflow / Inflow", f"{outflow_ratio:.1f}%")

# ============================================================
# RISK BANNER
# ============================================================
if risk_level == "HIGH":
    st.markdown(
        f'<div class="risk-high">🔴 <b>HIGH RISK</b> — '
        f'{selected_account} requires enhanced investigation based on the configured risk rules.</div>',
        unsafe_allow_html=True
    )
elif risk_level == "MEDIUM":
    st.markdown(
        f'<div class="risk-medium">🟠 <b>MEDIUM RISK</b> — '
        f'{selected_account} shows suspicious indicators requiring review.</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f'<div class="risk-low">🟢 <b>LOW RISK</b> — '
        f'{selected_account} currently shows limited configured risk indicators.</div>',
        unsafe_allow_html=True
    )

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "💸 Transactions",
    "🚨 Risk Analysis",
    "🕸️ Network",
    "📋 Investigation Report"
])

# ============================================================
# TAB 1 — OVERVIEW
# ============================================================
with tab1:

    left, right = st.columns(2)

    with left:
        st.markdown("#### 👤 Account Profile")

        profile = pd.DataFrame({
            "Field": [
                "Account ID",
                "Account Age",
                "KYC Status",
                "City",
                "Unique Senders",
                "Unique Receivers",
                "Associated Devices"
            ],
            "Value": [
                selected_account,
                f"{account_data['account_age_days']} days",
                account_data["kyc_status"],
                account_data["city"],
                unique_senders,
                unique_receivers,
                unique_devices
            ]
        })

        st.dataframe(
            profile,
            hide_index=True,
            use_container_width=True
        )

    with right:
        st.markdown("#### 💰 Money Flow")

        flow_df = pd.DataFrame({
            "Direction": ["Incoming", "Outgoing"],
            "Amount": [total_received, total_sent]
        })

        fig = px.bar(
            flow_df,
            x="Direction",
            y="Amount",
            text_auto=".2s",
            title="Incoming vs Outgoing Funds"
        )

        fig.update_layout(
            height=350,
            xaxis_title="",
            yaxis_title="Amount (₹)"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown("#### 📈 Transaction Activity")

    activity = pd.concat([
        incoming.assign(direction="Incoming"),
        outgoing.assign(direction="Outgoing")
    ])

    if not activity.empty:
        daily = (
            activity.assign(
                date=activity["transaction_time"].dt.date
            )
            .groupby(["date", "direction"])
            .size()
            .reset_index(name="transactions")
        )

        fig = px.line(
            daily,
            x="date",
            y="transactions",
            color="direction",
            markers=True,
            title="Transaction Activity Over Time"
        )

        fig.update_layout(height=350)

        st.plotly_chart(
            fig,
            use_container_width=True
        )
    else:
        st.info("No transaction activity available.")

# ============================================================
# TAB 2 — TRANSACTIONS
# ============================================================
with tab2:

    st.markdown("#### 🔍 Transaction Filters")

    c1, c2, c3 = st.columns(3)

    direction = c1.selectbox(
        "Direction",
        ["All", "Incoming", "Outgoing"]
    )

    transaction_types = sorted(
        transactions["transaction_type"].dropna().unique().tolist()
    )

    selected_types = c2.multiselect(
        "Transaction Type",
        transaction_types,
        default=transaction_types
    )

    search_txn = c3.text_input(
        "Search Transaction ID"
    )

    if direction == "Incoming":
        tx_view = incoming.copy()
    elif direction == "Outgoing":
        tx_view = outgoing.copy()
    else:
        tx_view = pd.concat([
            incoming.assign(direction="Incoming"),
            outgoing.assign(direction="Outgoing")
        ])

    if selected_types:
        tx_view = tx_view[
            tx_view["transaction_type"].isin(selected_types)
        ]

    if search_txn:
        tx_view = tx_view[
            tx_view["transaction_id"]
            .astype(str)
            .str.contains(search_txn, case=False, na=False)
        ]

    st.metric("Matching Transactions", f"{len(tx_view):,}")

    st.dataframe(
        tx_view.sort_values(
            "transaction_time",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

    csv_data = tx_view.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Filtered Transactions",
        csv_data,
        file_name=f"{selected_account}_transactions.csv",
        mime="text/csv"
    )

# ============================================================
# TAB 3 — RISK ANALYSIS
# ============================================================
with tab3:

    r1, r2 = st.columns(2)

    with r1:
        st.markdown("#### 🚨 Risk Indicators")

        indicators = []

        if unique_senders >= 10:
            indicators.append("High number of unique incoming senders")

        if len(incoming) >= 12:
            indicators.append("High incoming transaction volume")

        if len(incoming) >= 15:
            indicators.append("High transaction velocity")

        if unique_devices >= 4:
            indicators.append("Multiple devices associated with account")

        if account_data["account_age_days"] <= 90:
            indicators.append("Recently opened account")

        if len(outgoing) >= 10:
            indicators.append("High outgoing transaction volume")

        if indicators:
            for item in indicators:
                st.warning(f"⚠️ {item}")
        else:
            st.success("No major configured risk indicators identified.")

    with r2:
        st.markdown("#### 📊 Risk Score Distribution")

        distribution = risk_scores.copy()

        fig = px.histogram(
            distribution,
            x="risk_score",
            nbins=20,
            title="All Account Risk Scores"
        )

        fig.add_vline(
            x=risk_score,
            line_dash="dash",
            annotation_text=f"{selected_account}: {risk_score}"
        )

        fig.update_layout(height=350)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown("#### 🧩 Transaction Type Breakdown")

    type_df = pd.concat([
        incoming.assign(direction="Incoming"),
        outgoing.assign(direction="Outgoing")
    ])

    if not type_df.empty:
        type_summary = (
            type_df.groupby(
                ["transaction_type", "direction"]
            )["amount"]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            type_summary,
            x="transaction_type",
            y="amount",
            color="direction",
            barmode="group",
            title="Transaction Value by Type"
        )

        fig.update_layout(height=400)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ============================================================
# TAB 4 — NETWORK
# ============================================================
with tab4:

    st.markdown("#### 🕸️ Network Investigation")

    # Load network-analysis results generated by src/network_analysis.py
    try:
        network_edges = pd.read_csv("data/account_network.csv")
        network_risk = pd.read_csv("data/network_risk_scores.csv")
    except Exception as e:
        st.error(
            "Network analysis files are missing. "
            "Run `python3 src/network_analysis.py` first."
        )
        st.code(str(e))
        st.stop()

    # --------------------------------------------------------
    # NETWORK ACCOUNT SUMMARY
    # --------------------------------------------------------

    selected_network = network_risk[
        network_risk["account_id"] == selected_account
    ]

    if selected_network.empty:
        st.warning(
            f"No network-analysis record found for {selected_account}."
        )
    else:
        network_data = selected_network.iloc[0]

        network_score = int(network_data["network_risk_score"])
        network_level = str(network_data["network_risk_level"])

        n1, n2, n3, n4, n5 = st.columns(5)

        n1.metric(
            "Network Risk",
            f"{network_score}/100"
        )

        n2.metric(
            "Incoming Accounts",
            int(network_data["unique_senders"])
        )

        n3.metric(
            "Outgoing Accounts",
            int(network_data["unique_receivers"])
        )

        n4.metric(
            "Pass-through",
            f"{float(network_data['pass_through_ratio']) * 100:.1f}%"
        )

        n5.metric(
            "Rapid Movements",
            int(network_data["rapid_movements"])
        )

        st.divider()

        # ----------------------------------------------------
        # NETWORK RISK REASONS
        # ----------------------------------------------------

        st.markdown("#### 🚨 Network Risk Indicators")

        reasons = str(
            network_data["network_risk_reasons"]
        ).strip()

        if reasons and reasons.lower() != "nan":
            reason_list = reasons.split(" | ")

            for reason in reason_list:
                st.warning(f"⚠️ {reason}")
        else:
            st.success(
                "No network-specific risk indicators identified."
            )

        st.divider()

        # ----------------------------------------------------
        # BUILD SELECTED ACCOUNT NETWORK
        # ----------------------------------------------------

        incoming_edges = network_edges[
            network_edges["receiver_account"] == selected_account
        ].copy()

        outgoing_edges = network_edges[
            network_edges["sender_account"] == selected_account
        ].copy()

        # Remove self-transfers if present
        incoming_edges = incoming_edges[
            incoming_edges["sender_account"] != selected_account
        ]

        outgoing_edges = outgoing_edges[
            outgoing_edges["receiver_account"] != selected_account
        ]

        # ----------------------------------------------------
        # CONNECTION FILTER
        # ----------------------------------------------------

        st.markdown("#### 🔗 Connected Accounts")

        max_connections = min(
            15,
            max(
                len(incoming_edges) + len(outgoing_edges),
                1
            )
        )

        connection_limit = st.slider(
            "Connections to display",
            min_value=5 if max_connections >= 5 else 1,
            max_value=max_connections,
            value=min(10, max_connections)
        )

        incoming_edges = incoming_edges.sort_values(
            "total_amount",
            ascending=False
        ).head(connection_limit)

        outgoing_edges = outgoing_edges.sort_values(
            "total_amount",
            ascending=False
        ).head(connection_limit)

        # ----------------------------------------------------
        # BUILD GRAPH
        # ----------------------------------------------------

        graph_edges = []

        for _, row in incoming_edges.iterrows():
            graph_edges.append({
                "source": row["sender_account"],
                "target": selected_account,
                "amount": float(row["total_amount"]),
                "count": int(row["transaction_count"]),
                "direction": "Incoming"
            })

        for _, row in outgoing_edges.iterrows():
            graph_edges.append({
                "source": selected_account,
                "target": row["receiver_account"],
                "amount": float(row["total_amount"]),
                "count": int(row["transaction_count"]),
                "direction": "Outgoing"
            })

        if not graph_edges:
            st.info(
                "No connected transactions available for this account."
            )
        else:

            # ------------------------------------------------
            # NODE POSITIONS
            # ------------------------------------------------

            import math

            graph_nodes = {selected_account}

            for edge in graph_edges:
                graph_nodes.add(edge["source"])
                graph_nodes.add(edge["target"])

            incoming_nodes = list(
                dict.fromkeys(
                    edge["source"]
                    for edge in graph_edges
                    if edge["target"] == selected_account
                )
            )

            outgoing_nodes = list(
                dict.fromkeys(
                    edge["target"]
                    for edge in graph_edges
                    if edge["source"] == selected_account
                )
            )

            positions = {}

            # Selected account in the center
            positions[selected_account] = (0, 0)

            # Incoming accounts on the left
            for i, node in enumerate(incoming_nodes):
                angle = (
                    math.pi / 2
                    + math.pi * (i + 1)
                    / (len(incoming_nodes) + 1)
                )

                positions[node] = (
                    -3.5,
                    2.5 * math.cos(angle)
                )

            # Outgoing accounts on the right
            for i, node in enumerate(outgoing_nodes):
                angle = (
                    math.pi / 2
                    + math.pi * (i + 1)
                    / (len(outgoing_nodes) + 1)
                )

                positions[node] = (
                    3.5,
                    2.5 * math.cos(angle)
                )

            # ------------------------------------------------
            # EDGE TRACE
            # ------------------------------------------------

            edge_x = []
            edge_y = []

            for edge in graph_edges:

                x0, y0 = positions[edge["source"]]
                x1, y1 = positions[edge["target"]]

                edge_x.extend([
                    x0,
                    x1,
                    None
                ])

                edge_y.extend([
                    y0,
                    y1,
                    None
                ])

            edge_trace = go.Scatter(
                x=edge_x,
                y=edge_y,
                mode="lines",
                hoverinfo="none",
                line=dict(
                    width=1.5
                )
            )

            # ------------------------------------------------
            # NODE TRACE
            # ------------------------------------------------

            node_x = []
            node_y = []
            node_text = []
            node_sizes = []

            for node in graph_nodes:

                x, y = positions[node]

                node_x.append(x)
                node_y.append(y)

                if node == selected_account:

                    node_text.append(
                        f"<b>{node}</b><br>"
                        f"Selected Account<br>"
                        f"Network Risk: {network_score}/100<br>"
                        f"Level: {network_level}"
                    )

                    node_sizes.append(38)

                elif node in incoming_nodes:

                    node_text.append(
                        f"<b>{node}</b><br>"
                        f"Direction: Incoming<br>"
                        f"To: {selected_account}"
                    )

                    node_sizes.append(20)

                else:

                    node_text.append(
                        f"<b>{node}</b><br>"
                        f"Direction: Outgoing<br>"
                        f"From: {selected_account}"
                    )

                    node_sizes.append(20)

            node_trace = go.Scatter(
                x=node_x,
                y=node_y,
                mode="markers+text",
                text=list(graph_nodes),
                textposition="top center",
                hovertext=node_text,
                hoverinfo="text",
                marker=dict(
                    size=node_sizes,
                    line=dict(width=1)
                )
            )

            # ------------------------------------------------
            # GRAPH FIGURE
            # ------------------------------------------------

            fig = go.Figure(
                data=[
                    edge_trace,
                    node_trace
                ]
            )

            fig.update_layout(
                title=(
                    f"Transaction Network — {selected_account}"
                ),
                height=650,
                showlegend=False,
                hovermode="closest",
                xaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False,
                    range=[-5, 5]
                ),
                yaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False,
                    range=[-4, 4]
                ),
                margin=dict(
                    l=10,
                    r=10,
                    t=50,
                    b=10
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.caption(
                "Left-side nodes are incoming counterparties; "
                "right-side nodes are outgoing counterparties. "
                "The selected account is shown at the center."
            )

        st.divider()

        # ----------------------------------------------------
        # INCOMING CONNECTION TABLE
        # ----------------------------------------------------

        left, right = st.columns(2)

        with left:

            st.markdown("#### 📥 Incoming Connections")

            if not incoming_edges.empty:

                incoming_display = incoming_edges[
                    [
                        "sender_account",
                        "transaction_count",
                        "total_amount",
                        "average_amount"
                    ]
                ].rename(
                    columns={
                        "sender_account": "Sender",
                        "transaction_count": "Transactions",
                        "total_amount": "Total Received",
                        "average_amount": "Average Amount"
                    }
                )

                st.dataframe(
                    incoming_display,
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.info(
                    "No incoming connections."
                )

        # ----------------------------------------------------
        # OUTGOING CONNECTION TABLE
        # ----------------------------------------------------

        with right:

            st.markdown("#### 📤 Outgoing Connections")

            if not outgoing_edges.empty:

                outgoing_display = outgoing_edges[
                    [
                        "receiver_account",
                        "transaction_count",
                        "total_amount",
                        "average_amount"
                    ]
                ].rename(
                    columns={
                        "receiver_account": "Receiver",
                        "transaction_count": "Transactions",
                        "total_amount": "Total Sent",
                        "average_amount": "Average Amount"
                    }
                )

                st.dataframe(
                    outgoing_display,
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.info(
                    "No outgoing connections."
                )

        # ----------------------------------------------------
        # NETWORK EDGE DATA
        # ----------------------------------------------------

        st.markdown("#### 💰 Network Fund Flow")

        if graph_edges:

            fund_flow = pd.DataFrame(graph_edges)

            fund_flow["amount"] = fund_flow["amount"].round(2)

            fund_flow = fund_flow.rename(
                columns={
                    "source": "From",
                    "target": "To",
                    "amount": "Amount",
                    "count": "Transactions",
                    "direction": "Direction"
                }
            )

            st.dataframe(
                fund_flow[
                    [
                        "From",
                        "To",
                        "Amount",
                        "Transactions",
                        "Direction"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇️ Download Network Data",
                fund_flow.to_csv(
                    index=False
                ).encode("utf-8"),
                file_name=(
                    f"{selected_account}_network.csv"
                ),
                mime="text/csv"
            )

# TAB 5 — INVESTIGATION REPORT
# ============================================================
with tab5:

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

    st.markdown("#### 📋 Investigation Summary")

    summary = {
        "Account": selected_account,
        "Risk Score": f"{risk_score}/100",
        "Risk Level": risk_level,
        "Account Age": f"{account_data['account_age_days']} days",
        "KYC Status": str(account_data["kyc_status"]),
        "City": str(account_data["city"]),
        "Incoming Transactions": len(incoming),
        "Unique Senders": unique_senders,
        "Total Received": f"₹{total_received:,.2f}",
        "Outgoing Transactions": len(outgoing),
        "Unique Receivers": unique_receivers,
        "Total Sent": f"₹{total_sent:,.2f}",
        "Associated Devices": unique_devices,
        "Rapid Transfer Events": len(rapid_transfers)
    }

    summary_df = pd.DataFrame(
        list(summary.items()),
        columns=["Investigation Field", "Value"]
    )

    st.dataframe(
        summary_df,
        hide_index=True,
        use_container_width=True
    )

    st.markdown("#### 🧠 Investigation Assessment")

    if risk_level == "HIGH":
        assessment = (
            "The account exhibits multiple high-risk behavioural "
            "indicators consistent with potential mule-account "
            "activity. Further investigation is recommended."
        )
        action = (
            "HIGH-RISK REVIEW / ACCOUNT RESTRICTION "
            "AS PER APPLICABLE POLICY"
        )
    elif risk_level == "MEDIUM":
        assessment = (
            "The account exhibits suspicious behavioural indicators "
            "and requires enhanced review."
        )
        action = "ENHANCED REVIEW"
    else:
        assessment = (
            "The account currently shows limited indicators of "
            "suspicious activity."
        )
        action = "ROUTINE MONITORING"

    st.info(assessment)

    st.markdown("#### ✅ Recommended Action")
    st.warning(action)

    if rapid_transfers:
        st.markdown("#### ⚡ Rapid Fund Movement Events")

        rapid_df = pd.DataFrame(rapid_transfers)

        st.dataframe(
            rapid_df,
            use_container_width=True,
            hide_index=True
        )

    # Download selected-account report
    report_row = pd.DataFrame([{
        "account_id": selected_account,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "account_age_days": account_data["account_age_days"],
        "kyc_status": account_data["kyc_status"],
        "city": account_data["city"],
        "incoming_transactions": len(incoming),
        "unique_senders": unique_senders,
        "total_received": round(total_received, 2),
        "outgoing_transactions": len(outgoing),
        "unique_receivers": unique_receivers,
        "total_sent": round(total_sent, 2),
        "outflow_inflow_ratio": round(outflow_ratio, 2),
        "unique_devices": unique_devices,
        "rapid_transfer_events": len(rapid_transfers),
        "risk_indicators": " | ".join(indicators) if indicators else "None",
        "recommended_action": action
    }])

    st.download_button(
        "⬇️ Download Investigation Report",
        report_row.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_account}_investigation_report.csv",
        mime="text/csv"
    )

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(
    "Mule Account Detection & Investigation System | "
    "Synthetic data for portfolio demonstration"
)
