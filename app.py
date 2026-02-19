# app.py
import streamlit as st
import pandas as pd
from logic import run_pricing_logic

st.set_page_config(
    page_title="Brokerage Pricing Assistant",
    page_icon="🚚",
    layout="wide",
)

# Optional: small CSS to tighten the look
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #222 0, #000 45%, #111 100%);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        border-radius: 999px;
        padding: 0.6rem 1.8rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.title("🚛 Pricing Tool")
    st.markdown(
        "Upload your standard **Pricing Tool Template V9.xlsx**, "
        "then click **Run Logic** to generate scoped lanes and notes."
    )
    st.caption("Division V · MIDWEST/WEST · LOI & DoNotPrice logic baked in.")

st.title("Brokerage Pricing Assistant")
st.markdown(
    "Smart lane scoping and **LOI / DoNotPrice** tagging for your contract bids."
)

uploaded_file = st.file_uploader(
    "Upload Pricing Tool Template (V9 or later)", type=["xlsx"]
)

run_clicked = st.button("Run Logic 🚀", type="primary", use_container_width=False)

if run_clicked:
    if uploaded_file is None:
        st.error("Please upload an Excel file first.")
    else:
        with st.spinner("Crunching lanes and applying LOI / DoNotPrice logic..."):
            df = run_pricing_logic(uploaded_file.read())

        st.success(
            f"Done. Scoped lanes: {len(df)} · "
            f"Lanes with notes: {(df['My_Pricing_Notes'] != '').sum()} · "
            f"Without notes: {(df['My_Pricing_Notes'] == '').sum()}"
        )

        # Show table
        st.subheader("Scoped lanes with pricing notes")
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        # Download button
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv_bytes,
            file_name="pricing_logic_output.csv",
            mime="text/csv",
        )
