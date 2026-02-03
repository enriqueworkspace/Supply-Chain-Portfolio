import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

# ------------------------------
# Simulation parameters
# ------------------------------
n_records = 750               # total procurement orders
start_date = datetime(2024, 1, 1)
end_date   = datetime(2025, 12, 31)
today      = datetime(2025, 10, 15)   # "current" date for expiry risk simulation

vendors = [
    "GlobalSteel Ltd", "AsiaChem Inc", "EuroPack Solutions", "US Logistics Co",
    "ChinaPrecision", "DutchAgri Supplies", "BrazilNut Co", "IndiaTextiles",
    "VendorLateAlways", "FastTrack GmbH", "ReliableParts NV", "ProblemVendor12"
]
vendor_ids = [f"V{i:03d}" for i in range(1, len(vendors)+1)]

skus = [f"SKU-{i:04d}" for i in range(1001, 1251)]  # 250 different SKUs

# Late vendors (for bottlenecks)
late_vendors = ["VendorLateAlways", "ProblemVendor12", "AsiaChem Inc"]
late_prob = 0.75   # high chance of being late
late_days_mean = 12

# ------------------------------
# 1. Procurement Table
# ------------------------------
po_dates = [start_date + timedelta(days=random.randint(0, (end_date - start_date).days)) 
            for _ in range(n_records)]

data_proc = {
    "PO_Number": [f"PO-{i:07d}" for i in range(1000001, 1000001 + n_records)],
    "Order_Date": po_dates,
    "Vendor_ID": np.random.choice(vendor_ids, n_records),
    "Vendor_Name": [vendors[int(v[1:])-1] for v in np.random.choice(vendor_ids, n_records)],
    "Contract_ID": [f"CTR-{random.randint(100, 399):03d}" for _ in range(n_records)],
    "Total_Spend_USD": np.round(np.random.lognormal(mean=9.5, sigma=1.1, size=n_records), 2),
    "Agreed_Delivery_Date": [d + timedelta(days=random.randint(7, 90)) for d in po_dates]
}

df_proc = pd.DataFrame(data_proc)

# ------------------------------
# 2. Logistics / Receipt Table (one row per PO, some missing = not yet delivered)
# ------------------------------
delivered_mask = np.random.choice([True, False], n_records, p=[0.92, 0.08])  # ~8% still open

receipt_dates = []
condition_notes = []

for i in range(n_records):
    vendor = df_proc.iloc[i]["Vendor_Name"]
    agreed = df_proc.iloc[i]["Agreed_Delivery_Date"]
    
    if not delivered_mask[i]:
        receipt_dates.append(None)
        condition_notes.append(None)
        continue
    
    if vendor in late_vendors and random.random() < late_prob:
        delay = max(1, int(np.random.normal(late_days_mean, 5)))
        actual = agreed + timedelta(days=delay)
    else:
        # mostly on time or early
        offset = int(np.random.normal(0, 4))
        actual = agreed + timedelta(days=offset)
    
    receipt_dates.append(actual)
    
    # condition notes (some defects)
    if random.random() < 0.06:
        condition_notes.append(random.choice(["Damaged packaging", "Partial damage", "5% units defective", "Wet / moisture damage"]))
    else:
        condition_notes.append("Good condition")

data_log = {
    "PO_Number": df_proc["PO_Number"],
    "Receipt_Date": receipt_dates,
    "Quantity_Received": np.random.randint(50, 1200, n_records),
    "Condition_Notes": condition_notes
}
df_log = pd.DataFrame(data_log)

# ------------------------------
# 3. Legal / Contracts Table (unique contracts)
# ------------------------------
unique_contracts = df_proc["Contract_ID"].unique()
n_contracts = len(unique_contracts)

contract_starts = [today - timedelta(days=random.randint(180, 1460)) for _ in range(n_contracts)]
contract_ends   = [s + timedelta(days=random.randint(365, 1095)) for s in contract_starts]

# Force some high-risk expiries soon
high_risk_idx = random.sample(range(n_contracts), 12)
for idx in high_risk_idx:
    contract_ends[idx] = today + timedelta(days=random.randint(18, 95))

data_contr = {
    "Contract_ID": unique_contracts,
    "Contract_Start_Date": contract_starts,
    "Contract_End_Date": contract_ends,
    "One_Time_Extension": np.random.choice([True, False], n_contracts, p=[0.18, 0.82]),
    "Extension_Justification": [""] * n_contracts,
    "Penalty_Clause_Active": np.random.choice([True, False], n_contracts, p=[0.35, 0.65])
}

df_contr = pd.DataFrame(data_contr)

# Add some justifications where extended
for i in df_contr.index[df_contr["One_Time_Extension"]]:
    df_contr.at[i, "Extension_Justification"] = random.choice([
        "Supply shortage due to geopolitical event",
        "Force majeure – port strike",
        "Vendor production delay accepted",
        "Mutual agreement for continuity",
        "Price renegotiation pending"
    ])

# ------------------------------
# Save to CSV
# ------------------------------
output_dir = "../data"   # relative from scripts/ folder
os.makedirs(output_dir, exist_ok=True)

df_proc.to_csv(os.path.join(output_dir, "procurement.csv"), index=False)
df_log.to_csv(os.path.join(output_dir, "logistics.csv"), index=False)
df_contr.to_csv(os.path.join(output_dir, "contracts.csv"), index=False)

print("Generated files:")
print(f" - procurement.csv ({len(df_proc)} rows)")
print(f" - logistics.csv   ({len(df_log)} rows)")
print(f" - contracts.csv   ({len(df_contr)} rows)")
print("Files saved to: ../data/")