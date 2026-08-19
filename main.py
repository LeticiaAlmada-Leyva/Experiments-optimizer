from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import optuna

import models
import schemas
from database import get_db, engine

# Ensure tables are created
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Carbon Dots Synthesis",
    description="Database and optimization backend for microalgae-derived CQD",
    version="1.0.0"
)

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Carbon Dots Synthesis API is running successfully!", "docs": "/docs"}

# Endpoint to register an experiment
@app.post("/experiments/", response_model=schemas.ExperimentResponse)
def crear_experimento(experimento: schemas.ExperimentCreate, db: Session = Depends(get_db)):
    db_experimento = models.Experiments(**experimento.model_dump())
    db.add(db_experimento)
    db.commit()
    db.refresh(db_experimento)
    return db_experimento

# Endpoint to list all experiments
@app.get("/experiments/", response_model=List[schemas.ExperimentResponse])
def listar_experimentos(db: Session = Depends(get_db)):
    return db.query(models.Experiments).all()

# Endpoint to run Optuna optimization
@app.post("/api/optimize")
def run_optimization_api(target_emission: float = 450.0, target_size: float = 4.0):
    db_path = "carbon_dots.db"  # Cambia por tu archivo de base de datos si es diferente
    try:
        conn = sqlite3.connect(db_path)
        query = """
            SELECT microalgae_precursor, temperature_c, time_h, weight_vol_ratio, 
                   size_nm, lambda_exc_nm, lambda_em_nm, yield_pct 
            FROM Experiments
        """
        df = pd.read_sql(query, conn)
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    if df.empty:
        raise HTTPException(status_code=404, detail="The database does not contain records.")

    target_cols = ['size_nm', 'lambda_exc_nm', 'lambda_em_nm', 'yield_pct']
    df = df.dropna(subset=target_cols)

    if len(df) < 5:
        raise HTTPException(status_code=400, detail="Not enough complete records to train the model (at least 5 required).")

    df_processed = pd.get_dummies(df, columns=['microalgae_precursor', 'weight_vol_ratio'], drop_first=False)

    y = df_processed[['size_nm', 'lambda_exc_nm', 'lambda_em_nm', 'yield_pct']]
    X = df_processed.drop(columns=['size_nm', 'lambda_exc_nm', 'lambda_em_nm', 'yield_pct'])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {}
    for col in y.columns:
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train[col])
        models[col] = model

    def objective(trial):
        temp = trial.suggest_float('temperature_c', 150.0, 250.0)
        time = trial.suggest_float('time_h', 1.0, 24.0)
        
        candidate_dict = {'temperature_c': temp, 'time_h': time}
        for col in X.columns:
            if col.startswith('microalgae_precursor_') or col.startswith('weight_vol_ratio_'):
                candidate_dict[col] = trial.suggest_categorical(col, [0, 1])
                
        candidate = pd.DataFrame([candidate_dict], columns=X.columns)
        
        pred_size = models['size_nm'].predict(candidate)[0]
        pred_em = models['lambda_em_nm'].predict(candidate)[0]
        pred_yield = models['yield_pct'].predict(candidate)[0]
        
        emission_penalty = abs(pred_em - target_emission)
        size_penalty = abs(pred_size - target_size)
        
        global_score = pred_yield - (0.5 * emission_penalty) - (2.0 * size_penalty)
        return global_score

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=50)

    best_params = study.best_params
    
    best_candidate_dict = {'temperature_c': best_params['temperature_c'], 'time_h': best_params['time_h']}
    for col in X.columns:
        if col.startswith('microalgae_precursor_') or col.startswith('weight_vol_ratio_'):
            best_candidate_dict[col] = best_params.get(col, 0)
            
    best_candidate_df = pd.DataFrame([best_candidate_dict], columns=X.columns)
    
    results = {
        "temperature_c": best_params['temperature_c'],
        "time_h": best_params['time_h'],
        "predicted_yield": float(models['yield_pct'].predict(best_candidate_df)[0]),
        "predicted_size": float(models['size_nm'].predict(best_candidate_df)[0]),
        "predicted_emission": float(models['lambda_em_nm'].predict(best_candidate_df)[0]),
        "predicted_excitation": float(models['lambda_exc_nm'].predict(best_candidate_df)[0]),
        "microalgae_precursor": "N/A",
        "weight_vol_ratio": "N/A"
    }
    
    for key, val in best_params.items():
        if key.startswith('microalgae_precursor_') and val == 1:
            results['microalgae_precursor'] = key.replace('microalgae_precursor_', '')
        if key.startswith('weight_vol_ratio_') and val == 1:
            results['weight_vol_ratio'] = key.replace('weight_vol_ratio_', '')

    return results