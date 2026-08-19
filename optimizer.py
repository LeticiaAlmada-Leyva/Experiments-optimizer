import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import optuna

def run_optimization():
    # 1. Connection and data extraction
    # Make sure to replace with your actual database filename
    db_path = "carbon_dots.db"  
    conn = sqlite3.connect(db_path)
    
    query = """
        SELECT microalgae_precursor, temperature_c, time_h, weight_vol_ratio, 
               size_nm, lambda_exc_nm, lambda_em_nm, yield_pct 
        FROM Experiments
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        print("The database does not contain records to train the model.")
        return

    # Drop rows where target variables contain NaN (missing experimental results)
    target_cols = ['size_nm', 'lambda_exc_nm', 'lambda_em_nm', 'yield_pct']
    df = df.dropna(subset=target_cols)

    if df.empty:
        print("There are no records with complete target data for training.")
        return


       # 2. Categorical variable processing (Microalgae and Weight/Vol ratio since it's a string)
    df_processed = pd.get_dummies(df, columns=['microalgae_precursor', 'weight_vol_ratio'], drop_first=False)

    # Define target variables (y) and predictor variables (X)
    y = df_processed[['size_nm', 'lambda_exc_nm', 'lambda_em_nm', 'yield_pct']]
    X = df_processed.drop(columns=['size_nm', 'lambda_exc_nm', 'lambda_em_nm', 'yield_pct'])

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Train an independent model for each output property
    models = {}
    for col in y.columns:
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train[col])
        models[col] = model

    # 4. Configure Optuna optimization
    def objective(trial):
        # Numerical search ranges based on your experimental parameters
        temp = trial.suggest_float('temperature_c', 150.0, 250.0)
        time = trial.suggest_float('time_h', 1.0, 24.0)
        
        # Create the base row with numerical variables
        candidate_dict = {
            'temperature_c': temp,
            'time_h': time
        }
        
        # Add encoded categorical columns (microalgae and weight_vol_ratio)
        for col in X.columns:
            if col.startswith('microalgae_precursor_') or col.startswith('weight_vol_ratio_'):
                candidate_dict[col] = trial.suggest_categorical(col, [0, 1])
                
        candidate = pd.DataFrame([candidate_dict], columns=X.columns)
        
        # Predict properties
        pred_size = models['size_nm'].predict(candidate)[0]
        pred_exc = models['lambda_exc_nm'].predict(candidate)[0]
        pred_em = models['lambda_em_nm'].predict(candidate)[0]
        pred_yield = models['yield_pct'].predict(candidate)[0]
        
        # --- OBJECTIVE FUNCTION / GOALS ---
        # Example: Maximize yield, target a desired emission (e.g., 450 nm), 
        # and keep particle size controlled (e.g., around 4 nm).
        target_emission = 450.0
        target_size = 4.0
        
        emission_penalty = abs(pred_em - target_emission)
        size_penalty = abs(pred_size - target_size)
        
        # Global score to maximize
        global_score = pred_yield - (0.5 * emission_penalty) - (2.0 * size_penalty)
        
        return global_score

    # Run the optimization study
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=100)

    print("\n--- BEST CONDITIONS FOUND ---")
    print(study.best_params)

if __name__ == "__main__":
    run_optimization()