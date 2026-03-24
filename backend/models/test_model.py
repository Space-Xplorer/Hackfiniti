import pickle
import pandas as pd
import numpy as np


# ==================================================
# SAFE FORMATTERS
# ==================================================
def safe_money(val):
    try:
        return f"₹{float(val):,.0f}"
    except:
        return str(val)


def safe_float(val, decimals=2):
    try:
        return f"{float(val):.{decimals}f}"
    except:
        return str(val)


# ==================================================
# BASE + ADJUSTMENT CALCULATOR
# ==================================================
def compute_base_and_adjustment(model, explanation):

    try:
        base = model.intercept_[0]
    except:
        base = model.intercept_

    effects = np.sum(explanation["scores"])

    return base, effects


# ==================================================
# HUMAN FRIENDLY EXPLANATION ENGINE
# ==================================================
def get_layman_explanation(feature, impact, val, domain):

    # Ignore weak signals
    if domain == "finance" and abs(impact) < 0.05:
        return None

    if domain == "health" and abs(impact) < 100:
        return None


    # Handle interaction terms
    if "&" in feature:
        readable = feature.replace("_", " ").replace("&", " and ")
        return f"• Combined effect of {readable} influenced the outcome."


    # Format value safely
    try:
        display_val = round(float(val), 2)
    except:
        display_val = val


    # ---------------- FINANCE ----------------
    if domain == "finance":

        templates = {
            "cibil_score": f"Your credit score ({display_val}) shows your repayment reliability",
            "income_annum": f"Your yearly income ({safe_money(val)}) affects your repayment capacity",
            "loan_amount": f"The requested loan ({safe_money(val)}) impacts risk evaluation",
            "loan_to_income_ratio": f"Your loan is {safe_float(val)}× your income",
            "asset_to_loan_ratio": f"Your assets cover {safe_float(val)}× of the loan",
            "bank_asset_value": f"Your bank savings ({safe_money(val)}) act as financial security",
            "no_of_dependents": f"You support {display_val} dependents"
        }

        sentiment = "helped your approval" if impact > 0 else "reduced approval chances"


    # ---------------- HEALTH ----------------
    else:

        templates = {
            "age": f"Your age ({display_val} years) affects health risk",
            "bmi": f"Your BMI ({display_val}) reflects fitness level",
            "smoker": f"Smoking status influences medical costs",
            "bloodpressure": f"Blood pressure ({display_val}) impacts risk",
            "diabetes": f"Diabetes history increases coverage risk",
            "weight": f"Body weight ({display_val} kg) affects premiums",
            "sex": f"Gender-related health patterns are considered"
        }

        sentiment = "reduced premium" if impact < 0 else "increased premium"


    base = templates.get(
        feature,
        f"Your {feature.replace('_',' ')} was evaluated"
    )

    return f"• {base}. This {sentiment}."


# ==================================================
# SAFE ENCODING
# ==================================================
def apply_encoders(df, encoders):

    for col, encoder in encoders.items():

        if col in df.columns:

            val = str(df[col].iloc[0])

            if val in encoder.classes_:
                df[col] = encoder.transform([val])[0]
            else:
                df[col] = encoder.transform([encoder.classes_[0]])[0]

    return df


# ==================================================
# MAIN AUDIT SYSTEM
# ==================================================
def run_full_audit():

    print("\nInitializing Explainable AI Engine...\n")


    # ----------------------------------------------
    # Load Models
    # ----------------------------------------------
    try:
        with open("ebm_finance.pkl", "rb") as f:
            fin_model = pickle.load(f)

        with open("ebm_health.pkl", "rb") as f:
            health_model = pickle.load(f)

        with open("fin_encoders.pkl", "rb") as f:
            fin_enc = pickle.load(f)

        with open("health_encoders.pkl", "rb") as f:
            health_enc = pickle.load(f)

    except:
        print("❌ ERROR: Please train models first.")
        return


    # ==================================================
    # SAMPLE USER INPUT (Replace Later With UI)
    # ==================================================

    user_data = {

        "finance": {
            "no_of_dependents": 2,
            "education": "Graduate",
            "self_employed": "No",
            "income_annum": 850000,
            "loan_amount": 250000,
            "cibil_score": 760,
            "residential_assets_value": 1200000,
            "commercial_assets_value": 0,
            "luxury_assets_value": 200000,
            "bank_asset_value": 150000
        },

        "health": {
            "age": 42,
            "sex": "female",
            "weight": 70,
            "bmi": 26.3,
            "hereditary_diseases": "NoDisease",
            "no_of_dependents": 1,
            "smoker": 0,
            "city": "Boston",
            "bloodpressure": 78,
            "diabetes": 0,
            "regular_ex": 1,
            "job_title": "Engineer"
        }
    }


    # ==================================================
    # FINANCE PIPELINE
    # ==================================================

    df_f = pd.DataFrame([user_data["finance"]])


    # Feature engineering
    df_f["loan_to_income_ratio"] = df_f["loan_amount"] / (df_f["income_annum"] + 1)

    df_f["total_assets"] = (
        df_f["residential_assets_value"]
        + df_f["commercial_assets_value"]
        + df_f["luxury_assets_value"]
        + df_f["bank_asset_value"]
    )

    df_f["asset_to_loan_ratio"] = df_f["total_assets"] / (df_f["loan_amount"] + 1)


    df_f = apply_encoders(df_f, fin_enc)


    fin_pred = fin_model.predict(df_f)[0]
    fin_prob = fin_model.predict_proba(df_f)[0][1]

    fin_exp = fin_model.explain_local(df_f).data(0)


    # ==================================================
    # HEALTH PIPELINE
    # ==================================================

    df_h = pd.DataFrame([user_data["health"]])

    df_h = apply_encoders(df_h, health_enc)


    health_pred = health_model.predict(df_h)[0]

    health_exp = health_model.explain_local(df_h).data(0)


    # Base + Adjustment
    health_base, health_adj = compute_base_and_adjustment(
        health_model,
        health_exp
    )


    # ==================================================
    # REPORT
    # ==================================================

    print("=" * 70)
    print("                WHITE-BOX AI AUDIT REPORT")
    print("=" * 70)


    # -------- FINANCE --------
    print(f"\n[FINANCE DECISION]")
    print(f"Status     : {'APPROVED ✅' if fin_pred == 1 else 'REJECTED ❌'}")
    print(f"Confidence : {fin_prob * 100:.2f}%")

    print("\nKey Approval Factors:")

    for name, score in zip(fin_exp["names"], fin_exp["scores"]):

        orig_val = user_data["finance"].get(
            name,
            df_f[name].iloc[0] if name in df_f.columns else "N/A"
        )

        msg = get_layman_explanation(name, score, orig_val, "finance")

        if msg:
            print(msg)


    # -------- HEALTH --------
    print(f"\n[HEALTH INSURANCE ESTIMATE]")

    print(f"Base Premium     : {safe_money(health_base)}")
    print(f"Risk Adjustment  : {safe_money(health_adj)}")
    print(f"Final Premium    : {safe_money(health_pred)}")

    print("\nKey Cost Drivers:")

    for name, score in zip(health_exp["names"], health_exp["scores"]):

        orig_val = user_data["health"].get(
            name,
            df_h[name].iloc[0] if name in df_h.columns else "N/A"
        )

        msg = get_layman_explanation(name, score, orig_val, "health")

        if msg:
            print(msg)


    print("\n" + "=" * 70)
    print("Audit Completed Successfully ✅")


# ==================================================
# RUN
# ==================================================
if __name__ == "__main__":
    run_full_audit()
