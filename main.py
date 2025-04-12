import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import arabic_reshaper
from bidi.algorithm import get_display

df = pd.read_excel("services 2.xlsx")
st.set_page_config(layout="wide", initial_sidebar_state="expanded", menu_items=None)

####### SideBar
st.sidebar.image("logo.png", width=200)

Department = st.sidebar.multiselect("Department:", options=df["Department"].unique())

Physician = st.sidebar.multiselect("Physician:", options=sorted(df["Physician"].unique()))

st.sidebar.text("Type:")
Consultation = st.sidebar.checkbox("Consultation")
Medicine = st.sidebar.checkbox("Medicine")
Procedure = st.sidebar.checkbox("Procedure")
Supply = st.sidebar.checkbox("Supply")

####### Main Body
st.title("Swan Services Analysis")

type_filter = []
if Consultation:
    type_filter.append("Consultation")
if Medicine:
    type_filter.append("Medicine")
if Procedure:
    type_filter.append("Procedure")
if Supply:
    type_filter.append("Supply")

df_filter = df.copy()
if Department:
    df_filter = df_filter[df_filter["Department"].isin(Department)]

if Physician:
    df_filter = df_filter[df_filter["Physician"].isin(Physician)]

if type_filter:
    df_filter = df_filter[df_filter["Type"].isin(type_filter)]

################################### Metrics

col1, col2, col3, col4 = st.columns(4, gap="large")
col1.metric("Visitors (Insurance)", f"{df_filter['QTY INS'].sum():,}")
col2.metric("Visitors (Cash)", f"{int(df_filter['QTY Cash'].sum()):,}")
col3.metric("Total Services", f"{df_filter["Service"].nunique():,}")

################################### Plot
st.subheader("Top 20 Most Visited Services by Customers")
df_filter['Price'] = df_filter['Price'].replace(['NA', 'N/A', ''], pd.NA)
df_filter['Price'] = df_filter['Price'].fillna('غير محدد')

top_services_total = (
    df_filter.groupby(["Service", "Department", "Price"])[["QTY Cash", "QTY INS"]]
    .sum()
    .assign(QTY_Total=lambda x: x["QTY Cash"] + x["QTY INS"])
    .sort_values("QTY_Total", ascending=False)
    .head(20)
)

# Extract service, department, and price
services = top_services_total.index.get_level_values('Service')
departments = top_services_total.index.get_level_values('Department')
prices = top_services_total.index.get_level_values('Price')

def format_price(price):
    if pd.isna(price) or str(price).strip() in ['', 'NA', 'N/A']:
        return "غير محدد"
    try:
        price = float(price)
        return f"{int(price):,} ريال" if price > 0 else "مجاناً"
    except (ValueError, TypeError):
        price_str = str(price).lower().strip()
        return {
            'free': 'مجاناً',
            'var': 'سعر متغير'
        }.get(price_str, 'غير محدد')

# Reshape Arabic labels and combine service, department, and formatted price
reshaped_labels = []
for service, department, price in zip(services, departments, prices):
    if pd.isna(service) or pd.isna(department):
        continue  # Skip invalid entries
        
    formatted_price = format_price(price)
    label_text = f"{service}\n({department}, السعر: {formatted_price})"
    
    try:
        reshaped_label = get_display(arabic_reshaper.reshape(label_text))
        reshaped_labels.append(reshaped_label)
    except:
        # Fallback for problematic characters
        reshaped_labels.append(label_text)

# Plotting (same as before)
qty_cash = top_services_total["QTY Cash"]
qty_ins = top_services_total["QTY INS"]
totals = qty_cash + qty_ins

fig, ax = plt.subplots(figsize=(14, 12), layout='tight')

bar1 = ax.barh(reshaped_labels, qty_cash, label='Cash')  # Arabic for "Cash"
bar2 = ax.barh(reshaped_labels, qty_ins, left=qty_cash, label='Insurance')  # Arabic for "Insurance"

# Dynamic offset (5% of max total)
max_total = totals.max()
label_offset = max_total * 0.01

for i in range(len(reshaped_labels)):
    cash = qty_cash.iloc[i]
    ins = qty_ins.iloc[i]
    total = totals.iloc[i]

    # Inside cash bar (centered)
    if cash > 0:
        ax.text(cash / 2, i, f"{int(cash):,}", va='center', ha='center', fontsize=9, color='white')
    
    # Inside INS bar (centered)
    if ins > 0:
        ax.text(cash + ins / 2, i, f"{int(ins):,}", va='center', ha='center', fontsize=9, color='white')

    # Total label (dynamic offset)
    ax.text(
        total + label_offset,
        i,
        f"{int(total):,}",
        va='center',
        ha='left',
        fontsize=9,
        fontweight='bold',
        color='black'
    )

# Styling
ax.set_xlabel("Total Quantity", labelpad=10)  # Arabic for "Total Quantity"
ax.invert_yaxis()
ax.legend(loc='lower right')
ax.tick_params(axis='y', labelsize=10, pad=12)

st.pyplot(fig)


print(reshaped_labels)
################################### Data
st.dataframe(df_filter, hide_index=True)
