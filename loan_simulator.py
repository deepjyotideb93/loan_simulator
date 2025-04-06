import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

class Loan:
    def __init__(self, principal, annual_roi, tenure_years):
        self.principal = principal
        self.annual_roi = annual_roi
        self.tenure_years = tenure_years

    def calculate_emi(self, principal=None, tenure_months=None):
        principal = principal if principal is not None else self.principal
        tenure_months = tenure_months if tenure_months is not None else self.tenure_years * 12
        monthly_roi = self.annual_roi / 12 / 100
        emi = principal * monthly_roi * ((1 + monthly_roi) ** tenure_months) / (((1 + monthly_roi) ** tenure_months) - 1)
        return round(emi, 2)

    def simulate_with_prepayment(self, prepayment=None, mode="reduce_tenure"):
        data = []
        principal = self.principal
        tenure_months = self.tenure_years * 12
        monthly_roi = self.annual_roi / 12 / 100
        emi = self.calculate_emi(principal, tenure_months)
        month = 0
        year = 0

        while principal > 0:
            interest = principal * monthly_roi
            principal_component = min(emi - interest, principal)
            principal -= principal_component
            lumpsum = 0

            if month == 11 and prepayment and year + 1 in prepayment:
                lumpsum = min(prepayment[year + 1], principal)
                principal -= lumpsum
                if mode == "reduce_emi":
                    remaining_months = tenure_months - (year * 12 + month + 1)
                    emi = self.calculate_emi(principal, remaining_months)

            data.append({
                "principal": round(self.principal, 2),
                "roi": round(self.annual_roi, 2),
                "year": year,
                "month": month,
                "emi": round(emi, 2),
                "lumpsump": round(lumpsum, 2),
                "outstanding_principal": round(principal, 2)
            })

            if principal <= 0:
                break

            month += 1
            if month == 12:
                month = 0
                year += 1

        return data

    def generate_prepayment_schedule(self, start_year, base, total_years, step_up_pct=0.0, frequency=1):
        schedule = {}
        for i in range(total_years):
            year = start_year + i * frequency
            amount = base * ((1 + step_up_pct / 100) ** i)
            schedule[year] = round(amount, 2)
        return schedule

    def compare_with_prepayment(self, vanilla, prepay):
        df_vanilla = pd.DataFrame(vanilla)
        df_prepay = pd.DataFrame(prepay)

        total_paid_vanilla = df_vanilla["emi"].sum() + df_vanilla["lumpsump"].sum()
        total_paid_prepay = df_prepay["emi"].sum() + df_prepay["lumpsump"].sum()

        interest_vanilla = total_paid_vanilla - self.principal
        interest_prepay = total_paid_prepay - self.principal

        months_vanilla = len(df_vanilla)
        months_prepay = len(df_prepay)

        st.subheader("\U0001F4CA Savings Summary")
        st.markdown(f"**Original Interest Paid**: ₹{interest_vanilla:,.2f}")
        st.markdown(f"**Prepaid Interest Paid**: ₹{interest_prepay:,.2f}")
        st.markdown(f"**\U0001F4B8 Interest Saved**: ₹{(interest_vanilla - interest_prepay):,.2f}")
        st.markdown(f"**Original Tenure**: {months_vanilla} months")
        st.markdown(f"**Prepaid Tenure**: {months_prepay} months")
        st.markdown(f"**\u23F1\uFE0F Time Saved**: {months_vanilla - months_prepay} months")

        fig, ax = plt.subplots()
        ax.plot(df_vanilla["year"] + df_vanilla["month"] / 12, df_vanilla["outstanding_principal"], label="Without Prepayment", color='tab:red')
        ax.plot(df_prepay["year"] + df_prepay["month"] / 12, df_prepay["outstanding_principal"], label="With Prepayment", color='tab:green')
        ax.set_xlabel("Loan Duration (Years)")
        ax.set_ylabel("Outstanding Principal")
        ax.set_title("Loan Repayment Comparison")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        return df_vanilla, df_prepay

# Streamlit UI
st.title("📘 Loan EMI & Prepayment Simulator")

with st.sidebar:
    principal = st.number_input("Loan Principal", value=500000.0)
    annual_roi = st.number_input("Annual ROI (%)", value=8.5)
    tenure_years = st.number_input("Loan Tenure (Years)", value=20)
    use_prepay = st.checkbox("Enable Prepayment")

    if use_prepay:
        mode = st.radio("Prepayment Mode", ["1 - Reduce Tenure", "2 - Reduce EMI"])
        mode = "reduce_tenure" if mode.startswith("1") else "reduce_emi"

        prepay_type = st.selectbox("Prepayment Option", ["None", "Fixed Yearly", "List of Amounts", "Custom Dict", "Step-Up Schedule"])

        if prepay_type == "Fixed Yearly":
            amount = st.number_input("Fixed Prepayment Amount", value=50000.0)
            start_year = st.number_input("Start Year (1 = after 1st year)", min_value=1, value=1)
            years = st.number_input("Number of Years to Prepay", value=5)
            prepay_dict = {start_year + i: amount for i in range(int(years))}

        elif prepay_type == "List of Amounts":
            raw = st.text_input("Comma-separated prepayment amounts", "50000,60000,70000")
            start_year = st.number_input("Start Year (1 = after 1st year)", min_value=1, value=1)
            amounts = [float(x.strip()) for x in raw.split(',') if x.strip()]
            prepay_dict = {start_year + i: amt for i, amt in enumerate(amounts)}

        elif prepay_type == "Custom Dict":
            raw = st.text_input("Enter dict like {2: 50000, 5: 80000}", "{2: 50000, 5: 80000}")
            try:
                prepay_dict = eval(raw)
            except:
                st.error("Invalid dictionary format")
                prepay_dict = {}

        elif prepay_type == "Step-Up Schedule":
            base = st.number_input("Base Prepayment Amount", value=40000.0)
            start_year = st.number_input("Start Year (1 = after 1st year)", min_value=1, value=1)
            total_years = st.number_input("Total Years for Prepayment", value=5)
            step = st.number_input("Step-up Percentage per Year", value=10.0)
            frequency = st.number_input("Prepay every X years", value=1)
            loan = Loan(principal, annual_roi, tenure_years)
            prepay_dict = loan.generate_prepayment_schedule(start_year, base, int(total_years), step, frequency)

        else:
            prepay_dict = None
    else:
        mode = "reduce_tenure"
        prepay_dict = None

if st.button("Simulate Loan"):
    loan = Loan(principal, annual_roi, tenure_years)
    vanilla = loan.simulate_with_prepayment(prepayment=None)
    prepay = loan.simulate_with_prepayment(prepayment=prepay_dict, mode=mode)
    df_vanilla, df_prepay = loan.compare_with_prepayment(vanilla, prepay)

    with st.expander("Vanilla Schedule"):
        st.dataframe(df_vanilla)

    with st.expander("Prepayment Schedule"):
        st.dataframe(df_prepay)

    st.download_button("Download Vanilla CSV", df_vanilla.to_csv(index=False), file_name="vanilla_schedule.csv")
    st.download_button("Download Prepay CSV", df_prepay.to_csv(index=False), file_name="prepayment_schedule.csv")
