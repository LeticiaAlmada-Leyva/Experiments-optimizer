import streamlit as st
import pandas as pd
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
from database import DATABASE_URL

# Setup database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Page configuration (Only called once)
st.set_page_config(
    page_title="Carbon Dots Synthesis Dashboard",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 Carbon Dots Synthesis Dashboard")
st.markdown("Manage, visualize, and optimize microalgae-derived carbon quantum dots experiments.")

# Load data function
def load_data():
    db = SessionLocal()
    experiments = db.query(models.Experiments).all()
    db.close()
    
    data = [{
        "id": exp.id,
        "doi": exp.doi,
        "microalgae_precursor": exp.microalgae_precursor,
        "temperature_c": exp.temperature_c,
        "time_h": exp.time_h,
        "weight_vol_ratio": exp.weight_vol_ratio,
        "solvent": exp.solvent,
        "pretreatment": exp.pretreatment,
        "yield_pct": exp.yield_pct,
        "size_nm": exp.size_nm,
        "qy_pct": exp.qy_pct,
        "lambda_exc_nm": exp.lambda_exc_nm,
        "lambda_em_nm": exp.lambda_em_nm
    } for exp in experiments]
    
    return pd.DataFrame(data)

df = load_data()

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(["📊 View Experiments", "➕ Register New Experiment", "🎯 Intelligent Optimizer"])

with tab1:
    st.subheader("Experimental Database Records")
    
    if df.empty:
        st.warning("No experiments found in the database yet.")
    else:
        precursors = ["All"] + list(df["microalgae_precursor"].unique())
        selected_precursor = st.selectbox("Filter by Microalgae Precursor", precursors, key="filter_prec")
        
        if selected_precursor != "All":
            filtered_df = df[df["microalgae_precursor"] == selected_precursor]
        else:
            filtered_df = df
            
        st.dataframe(filtered_df, use_container_width=True)
        
        st.markdown("### Quick Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Experiments", len(df))
        with col2:
            avg_yield = filtered_df["yield_pct"].mean() if not filtered_df.empty else 0
            st.metric("Average Yield (%)", f"{avg_yield:.2f}")
        with col3:
            avg_size = filtered_df["size_nm"].mean() if not filtered_df.empty else 0
            st.metric("Average Size (nm)", f"{avg_size:.2f}")

with tab2:
    st.subheader("Register a New Synthesis Experiment")
    
    with st.form("experiment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            doi = st.text_input("DOI", placeholder="10.1016/j...")
            microalgae_precursor = st.text_input("Microalgae Precursor", placeholder="e.g., Chlorella vulgaris")
            temperature_c = st.number_input("Temperature (°C)", value=180.0)
            time_h = st.number_input("Time (h)", value=4.0)
            weight_vol_ratio = st.text_input("Weight/Volume Ratio", value="N/A")
            solvent = st.text_input("Solvent", value="water")
            
        with col2:
            pretreatment = st.text_input("Pretreatment", placeholder="e.g., hydrothermal")
            yield_pct = st.number_input("Yield (%)", value=0.0)
            size_nm = st.number_input("Size (nm)", value=0.0)
            qy_pct = st.number_input("Quantum Yield QY (%)", value=0.0)
            lambda_exc_nm = st.number_input("Lambda Excitation (nm)", value=0.0)
            lambda_em_nm = st.number_input("Lambda Emission (nm)", value=0.0)
            
        submit_button = st.form_submit_button(label="Save Experiment")
        
        if submit_button:
            db = SessionLocal()
            try:
                new_exp = models.Experiments(
                    doi=doi,
                    microalgae_precursor=microalgae_precursor,
                    temperature_c=temperature_c,
                    time_h=time_h,
                    weight_vol_ratio=weight_vol_ratio,
                    solvent=solvent,
                    pretreatment=pretreatment,
                    yield_pct=yield_pct,
                    size_nm=size_nm,
                    qy_pct=qy_pct,
                    lambda_exc_nm=lambda_exc_nm,
                    lambda_em_nm=lambda_em_nm
                )
                db.add(new_exp)
                db.commit()
                st.success("Experiment registered successfully and saved to database!")
            except Exception as e:
                db.rollback()
                st.error(f"An error occurred: {e}")
            finally:
                db.close()

with tab3:
    st.subheader("Intelligent Synthesis Optimizer (Optuna + ML)")
    st.markdown("Configure your target properties below to find the optimal synthesis conditions via FastAPI backend.")

    opt_col1, opt_col2 = st.columns(2)
    with opt_col1:
        target_emission = st.number_input("Target Emission (nm)", value=450.0, step=5.0)
    with opt_col2:
        target_size = st.number_input("Target Size (nm)", value=4.0, step=0.5)

    if st.button("Run Optimization"):
        with st.spinner("Calculating optimal conditions via FastAPI..."):
            try:
                api_url = f"http://127.0.0.1:8000/api/optimize?target_emission={target_emission}&target_size={target_size}"
                response = requests.post(api_url)
                
                if response.status_code == 200:
                    results = response.json()
                    st.success("Optimization completed!")
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Optimal Temperature", f"{results.get('temperature_c', 0):.2f} °C")
                    m2.metric("Optimal Time", f"{results.get('time_h', 0):.2f} h")
                    m3.metric("Predicted Yield", f"{results.get('predicted_yield', 0):.2f} %")
                    m4.metric("Predicted Size", f"{results.get('predicted_size', 0):.2f} nm")
                    
                    st.divider()
                    st.subheader("Synthesis Details")
                    res_col1, res_col2 = st.columns(2)
                    res_col1.write(f"**Precursor:** {results.get('microalgae_precursor', 'N/A')}")
                    res_col1.write(f"**Weight/Vol Ratio:** {results.get('weight_vol_ratio', 'N/A')}")
                    res_col2.write(f"**Excitation:** {results.get('predicted_excitation', 0):.2f} nm")
                    res_col2.write(f"**Emission:** {results.get('predicted_emission', 0):.2f} nm")
                    
                else:
                    error_data = response.json()
                    st.error(f"Error: {error_data.get('detail', 'Could not process optimization')}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to FastAPI. Make sure your server is running at http://127.0.0.1:8000")