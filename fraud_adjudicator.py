import numpy as np
import pandas as pd
import streamlit as st


def createLayout():
    # Layout
    container1 = st.container()
    # logo, province = container1.columns([4, 1])
    container2 = st.container()

    col0, col1, col2, col3, col4 = container2.columns([2, 2, 1, 1, 2])
    container3 = st.container()

    return (container1, container2, col0, col1, col2, col3, col4, container3)


def format(x):
    return "${:,.2f}".format(x)


@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")


PAGE_CONFIG = {
    "page_title": "Fraud Alert Adjudicator",
    "layout": "wide",
    "page_icon": ":dollar:",
}

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """

st.set_page_config(
    **PAGE_CONFIG,
)
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


st.title(PAGE_CONFIG["page_title"])
container1, container2, col0, col1, col2, col3, col4, container3 = createLayout()


with container1:
    st.write(
        """
    <h3>Description</h3>
    This application is designed to assist in the adjudication of money laundering alerts.
    <br> 
    Users can toggle criticality thresholds between SMARTS and the DataRobot computed probability of fraud.
    <br><br>
    """,
        unsafe_allow_html=True,
    )

data = pd.read_csv("aml_alert_scored.csv",).assign(
    kycRiskScore=lambda x: 5 - x.kycRiskScore,
    SAR_1_PREDICTION=lambda x: 100 * x.SAR_1_PREDICTION,
)

with col0:
    alert_threshold = st.slider("Alert Threshold", 0, 100, 10, 1, format="%d%%")
    toggle_filter = st.checkbox("Filter by Adjudication Status")

with col1:
    kyc_score = st.slider("Maximum Allowable SMARTS Criticality", 0, 6, 3, 1)
    # download_button = st.download_button(
    #         "Download Connections",
    #         csv,
    #         file_name="connections_export.csv",
    #         key="download_button",
    #     )
# with col2:
#     go_button = st.button("Run Alerts", key="go_button")


data["Adjudicate"] = np.where(
    (data["SAR_1_PREDICTION"] > alert_threshold) | (data["kycRiskScore"] > kyc_score),
    "Yes",
    "No",
)


display_data = (
    data[
        [
            "association_id",
            "Adjudicate",
            "SAR_1_PREDICTION",
            "kycRiskScore",
            "overpaymentAmt90d",
            # "nbrCustReqRefunds90d",
            "totalMerchCred90d",
            "csrNotes",
            "EXPLANATION_1_FEATURE_NAME",
            "EXPLANATION_1_QUALITATIVE_STRENGTH",
            "EXPLANATION_2_FEATURE_NAME",
            "EXPLANATION_2_QUALITATIVE_STRENGTH",
        ]
    ]
    .assign(
        keep_column=lambda x: np.where(
            (x["Adjudicate"] == "Yes") | (toggle_filter == False), "Yes", "No"
        )
    )
    .loc[lambda x: x.keep_column == "Yes"]
    .assign(
        SAR_1_PREDICTION=lambda x: x["SAR_1_PREDICTION"].map(
            lambda x: str(round(x, 2)) + "%"
        ),
        association_id=lambda x: "ALX-"
        + x["association_id"].astype(str).str.pad(6, side="left", fillchar="0"),
        overpaymentAmt90d=lambda x: x["overpaymentAmt90d"].map(format),
        totalMerchCred90d=lambda x: x["totalMerchCred90d"].map(format),
        primary_explanation=lambda x: x["EXPLANATION_1_FEATURE_NAME"]
        + ": "
        + x["EXPLANATION_1_QUALITATIVE_STRENGTH"],
        secondary_explanation=lambda x: x["EXPLANATION_2_FEATURE_NAME"]
        + ": "
        + x["EXPLANATION_2_QUALITATIVE_STRENGTH"],
        kycRiskScore=lambda x: x["kycRiskScore"].map(lambda x: str(x)),
    )
    .rename(
        columns={
            "kycRiskScore": "SMARTS Criticality Score",
            "csrNotes": "Representative Notes",
            "SAR_1_PREDICTION": "Probability of Fraud",
            "association_id": "Transaction ID",
            "overpaymentAmt90d": "Overpayment Amount 90 Days",
            "nbrCustReqRefunds90d": "Refund Requests 90 Days",
            "totalMerchCred90d": "Total Merchant Credit 90 Days",
            "primary_explanation": "Primary Explanation",
            "secondary_explanation": "Secondary Explanation",
        }
    )
    .drop(
        columns=[
            "keep_column",
            "EXPLANATION_1_FEATURE_NAME",
            "EXPLANATION_1_QUALITATIVE_STRENGTH",
            "EXPLANATION_2_FEATURE_NAME",
            "EXPLANATION_2_QUALITATIVE_STRENGTH",
        ]
    )
)


with col3:
    st.metric("Total Alerts", display_data.shape[0])

with container3:
    st.write(display_data)
    download_button = st.download_button(
        "Download Alerts",
        convert_df(display_data),
        file_name="fraud_alerts.csv",
        key="download_button",
    )
