# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
from datetime import datetime
import pandas 
import plotly
# import pyodbc  # Uncomment for MSSQL

# Database Configuration
DB_CONFIG = {
    'sqlite': {
        'driver': 'sqlite3',
        'database': 'finance_tracker.db'
    },
    # 'mssql': {  # Uncomment for MSSQL
    #     'driver': 'ODBC Driver 17 for SQL Server',
    #     'server': 'localhost',
    #     'database': 'FinanceTracker',
    #     'trusted_connection': 'yes'
    # }
}

# Initialize Database
def init_db():
    if DB_CONFIG['sqlite']['driver'] == 'sqlite3':
        conn = sqlite3.connect(DB_CONFIG['sqlite']['database'])
        
    # Uncomment for MSSQL
    # else:
    #     conn_str = f"DRIVER={DB_CONFIG['mssql']['driver']};SERVER={DB_CONFIG['mssql']['server']};DATABASE={DB_CONFIG['mssql']['database']};Trusted_Connection={DB_CONFIG['mssql']['trusted_connection']};"
    #     conn = pyodbc.connect(conn_str)
    
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS financial_plans1
                 (id INTEGER PRIMARY KEY,
                  timestamp DATETIME,
                  pay_per_hour REAL,
                  hours_per_day REAL,
                  days_worked INTEGER,
                  target_savings REAL,
                  timeline_days INTEGER,
                  expenses TEXT,
                  savings_mode TEXT,
                  money_left REAL TEXT,
                  days_needed REAL,
                  max_category TEXT,
                  max_category_value REAL)''')
    conn.commit()
    conn.close()

# Save to Database
def save_to_db(data):
    conn = sqlite3.connect(DB_CONFIG['sqlite']['database'])
    # Uncomment for MSSQL connection
    # conn_str = ... (as above)
    # conn = pyodbc.connect(conn_str)
    
    c = conn.cursor()
    c.execute('''INSERT INTO financial_plans1 
                 (timestamp, pay_per_hour, hours_per_day, days_worked, target_savings, 
                  timeline_days, expenses, savings_mode, money_left, days_needed,
                  max_category, max_category_value)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', data)
    conn.commit()
    conn.close()
    
    
def check_savings_adjustment(current_mode, problem_type, I, Z, T, p, h, Ti, savings_rates):
    modes = ["high", "medium", "low", "none"]
    current_index = modes.index(current_mode)
    adjustment_modes = modes[current_index + 1:]
    
    adjustment_log = []
    for mode in adjustment_modes:
        S_new = I * savings_rates[mode]
        if problem_type == "M<0":
            M_new = I - (Z + S_new)
            adjustment_log.append(f"  - {mode.title()} Mode: Savings = ${S_new:.2f}, New Account Money = ${M_new:.2f}")

            if M_new >= 0:
                return mode.title(), adjustment_log

        else:  # For timeline adjustment (Ti < fr)
            B_new = T - (I - Z - S_new)
            fr_new = B_new / (p * h) if (p * h) != 0 else float('inf')
            adjustment_log.append(
                f"  - {mode.title()} Mode: Savings = ${S_new:.2f}, Days Needed = {fr_new:.1f}"
            )
            if fr_new <= Ti:
                return mode.title(), adjustment_log
    return None, adjustment_log


    

def finance_tracker():
    st.title("💰 Smart Finance Tracker")
    st.subheader("Your Personal Financial Planning Assistant")
    
    with st.form("finance_form"):
        st.header("💸 Income Details")
        col1, col2, col3 = st.columns(3)
        p = col1.number_input("Pay per hour ($)", min_value=7.25, value=15.0, step=1.0)
        h = col2.number_input("Hours worked per day", min_value=1.0, value=8.0, step=0.5)
        D = col3.number_input("Days worked this month", min_value=0, value=20, step=1)
        
        st.header("🎯 Savings Target")
        col1, col2 = st.columns(2)
        T = col1.number_input("Target savings ($)", min_value=0.0, value=5000.0)
        Ti = col2.number_input("Approximate timeline (days)", min_value=1, value=90)
        
        
        st.header("📉 Expense Details")
        expenses = {
            "Grocery": st.number_input("Grocery ($)", min_value=0.0, value=300.0),
            "Rent": st.number_input("Rent ($)", min_value=0.0, value=1200.0),
            "Mobile Bill": st.number_input("Mobile Bill ($)", min_value=0.0, value=80.0),
            "Social Spending": st.number_input("Social Spending ($)", min_value=0.0, value=200.0),
            "Travel": st.number_input("Travel ($)", min_value=0.0, value=150.0),
            "Additional Spend": st.number_input("Additional Spend ($)", min_value=0.0, value=100.0)
        }
        Z = sum(expenses.values())
        
        st.header("💾 Savings Mode")
        savings_mode = st.selectbox("Select savings mode", 
                                   ["High (35%)", "Medium (15%)", "Low (5%)", "None (0%)"])
        savings_rates = {"high": 0.35, "medium": 0.15, "low": 0.05, "none": 0.0}
        savings_mode_key = savings_mode.split()[0].lower()
        
        submitted = st.form_submit_button("🚀 Calculate Financial Plan")
        
        if submitted:
            max_possible_income = (p * h * D) + (p * h * Ti)
            if max_possible_income < T:
                st.error(f"""🚨 **TARGET IMPOSSIBLE ALERT** 🚨
            
                        Even if you worked {Ti} days with:
             
                         Zero Expenses
                         Zero Saving deductions
             
                        You'd only earn: ${max_possible_income:,.2f}
            
                        Your target requires: ${T:,.2f}""")
            
                if (T - max_possible_income) > 1000:
                    st.info("💡 Consider adjusting timeline or increasing income")
                return
        
            # Core Calculations
            I = p * h * D
            S = I * savings_rates[savings_mode_key]
            M = I - (Z + S)
            B = max(T - M, 0)
            fr = B / (p * h) if (p * h) != 0 else 0
            
            max_category = max(expenses, key=expenses.get)
            max_category_value = expenses[max_category]
            
            # Save to database
            save_data = (
                datetime.now(),
                p, h, D, T, Ti,
                str(expenses),
                savings_mode,
                M,
                fr,
                max_category,
                max_category_value
            )
            save_to_db(save_data)
            
            # Display results
            
            st.markdown(
    """
    <style>
    /* Label text (e.g. "Total Income") */
    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
    }
    /* Main metric value (e.g. "$2,400.00") */
    [data-testid="stMetricValue"] {
        font-size: 14px !important;
    }
    /* Delta text (if any) */
    [data-testid="stMetricDelta"] {
        font-size: 14px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
            
            st.balloons()
            st.subheader("📊 Financial Results")
            
            col1, col2, col3, col4, col5  = st.columns(5)
            col1.metric("Total Income", f"${I:,.2f}")
            col2.metric("Total Expenses", f"${Z:,.2f}")
            col3.metric("Savings Amount", f"${S:,.2f}")
            col4.metric("Account Money ", f"${M:,.2f}" )
            col5.metric(f"Days to {T} ",f"{fr:,.1f}")
            
            st.divider()
            
            # Timeline Message
            timeline_message = ""
            alert_message = ""
            if fr == 0:
                timeline_message = "🎉 Target already achieved! "
                if M > T:
                    timeline_message += f"Extra ${M-T:.2f} available for investments!"

            else:
                if Ti >= fr:
                    if M >= 0:
                        timeline_message = ("You are on Track! 👏 Maintain the Balance 🚴♀️" )
                        if M * (Ti - fr) > 0:
                            st.info(f"Potential extra savings: ${M * (Ti - fr):,.2f}")
                else:
                    deficit = fr - Ti
                    timeline_message = f"Buckle Up! 🐱👤 You need {deficit:.1f} extra days from your set timeframe."
                    suggested_mode, adjustment_log = check_savings_adjustment(savings_mode_key, "Ti<fr", I, Z, T, p, h, Ti, savings_rates)
                    if suggested_mode:
                        timeline_message += "\n" + "\n".join(adjustment_log)
                        timeline_message += f"\n\n✅ **Solution:** Switch to {suggested_mode} Savings Mode."
                    else:
                        timeline_message += "\n\n🚨 **Even the Lowest Saving Mode is not enough. Radical Changes Needed**\n" + "\n".join(adjustment_log)
                        timeline_message += f"\n- ⚠️ Drastically reduce {max_category} (${expenses[max_category]:.2f})."

                    
            # Negative Balance Alert
            if M < 0:
                st.error("🚨 Negative Balance Alert!")
                
                suggested_mode, adjustment_log = check_savings_adjustment(savings_mode_key, "M<0", I, Z, T, p, h, Ti, savings_rates)
                if suggested_mode:
                    alert_message = f"🛑 **Cash Deficit Solution:** Switch to {suggested_mode} Savings Mode.\n\n"
                    alert_message += "\n" + "\n".join(adjustment_log)
                else:
                    alert_message = "🚨 **No Saving Mode is enough. Critical Cash Deficit:**\n\n"
                    alert_message += "\n" + "\n".join(adjustment_log)
                    alert_message += f"\n- ⚠️ Stop ALL savings and reduce {max_category} (${expenses[max_category]:.2f})."
            
            st.markdown(timeline_message.replace("\n", "  \n"))
            if alert_message:
                 st.error(alert_message.replace("\n", "  \n"))
                 
            # Display messages with proper formatting
            #if timeline_message:
            #    st.markdown(f"**Timeline Analysis:**\n{timeline_message.replace('NewAccountMoney', 'New Account Money')}")
        
            #if alert_message:
            #    st.error(f"**Financial Alert:**\n{alert_message.replace('NewAccountMoney', 'New Account Money')}")
            
            st.write(f"**Most expensive category:** {max_category} (${max_category_value:,.2f})")

# Initialize database
init_db()

if __name__ == "__main__":
    finance_tracker()