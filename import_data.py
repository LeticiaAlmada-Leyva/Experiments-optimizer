import pandas as pd
import re
from database import SessionLocal
import models

# Name of your Excel file
FILE_NAME = "data_carbon_dots.xlsx"

def clean_numeric(value):
    """Helper to safely extract numbers from text strings or handle N/A / NaN / ranges"""
    if pd.isna(value) or str(value).strip().upper() in ["N/A", "", "NONE", "<1"]:
        return None
    try:
        return float(value)
    except ValueError:
        # Extracts the first valid number found in strings like "140 - 220" or "2% - 10%"
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", str(value))
        if numbers:
            return float(numbers[0])
        return None

def import_excel():
    try:
        # Read directly from the Excel file
        df = pd.read_excel(FILE_NAME)
    except Exception as e:
        print(f"Error reading the Excel file: {e}")
        return
    
    # Create a database session
    db = SessionLocal()
    
    try:
        count = 0
        for _, row in df.iterrows():
            # Skip rows where essential fields might be completely missing
            if pd.isna(row.get("doi")) or pd.isna(row.get("microalgae_precursor")):
                continue

            experiment = models.Experiments(
                doi=str(row["doi"]),
                microalgae_precursor=str(row["microalgae_precursor"]),
                temperature_c=clean_numeric(row.get("temperature_c")),
                time_h=clean_numeric(row.get("time_h")),
                weight_vol_ratio=str(row["weight_vol_ratio"]) if pd.notnull(row["weight_vol_ratio"]) else "N/A",
                solvent=str(row["solvent"]) if pd.notnull(row["solvent"]) else "water",
                pretreatment=str(row["pretreatment"]) if pd.notnull(row["pretreatment"]) else None,
                yield_pct=clean_numeric(row.get("yield_pct")),
                size_nm=clean_numeric(row.get("size_nm")),
                qy_pct=clean_numeric(row.get("qy_pct")),
                lambda_exc_nm=clean_numeric(row.get("lambda_exc_nm")),
                lambda_em_nm=clean_numeric(row.get("lambda_em_nm"))
            )
            db.add(experiment)
            count += 1
        
        db.commit()
        print(f"Success! {count} records have been imported into the database.")
    
    except Exception as e:
        db.rollback()
        print(f"An error occurred during database import: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    import_excel()