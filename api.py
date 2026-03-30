import os
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_URL = (
    f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(
    DB_URL,
    pool_size=5,
    max_overflow=2,
    pool_timeout=10,
    pool_recycle=1800,
    connect_args={"connect_timeout": 5}
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load("churn_model.pkl")


@app.post("/predict")
def predict(data: dict):
    features = np.array([[
        data["total_spent"],
        data["days_since_last_purchase"],
        data["purchase_count"],
        data["avg_order_value"]
    ]])

    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0][1]

    return {
        "churn": bool(prediction),
        "risk_score": float(probability)
    }


@app.get("/bulk_predict")
def bulk_predict():
    try:
        # FORCE the connection to use web_project
        with engine.connect() as connection:
            connection.execute("USE web_project") # This is the magic line
            
            query = """
                SELECT
                    COALESCE(c.total_spent, 0) as total_spent,
                    COALESCE(DATEDIFF(CURDATE(), c.last_purchase_date), 365) as days_since_last_purchase,
                    COUNT(s.id) as purchase_count,
                    COALESCE(AVG(s.total_amount), 0) as avg_order_value
                FROM clients c
                LEFT JOIN sales s ON c.id = s.client_id
                GROUP BY c.id
            """
            df = pd.read_sql(query, connection) # Use 'connection' here instead of 'engine'

        if df.empty:
            return {"success": True, "at_risk_count": 0}

        feature_cols = ['total_spent', 'days_since_last_purchase', 'purchase_count', 'avg_order_value']
        features = df[feature_cols].fillna(0)

        predictions = model.predict(features)
        at_risk_count = int(sum(predictions))

        return {"success": True, "at_risk_count": at_risk_count}

    except Exception as e:
        print(f"SQL Error: {e}")
        return {"success": False, "error": str(e)}
@app.get("/debug")
def debug():
    return {
        "DB_USER": os.getenv("DB_USER"),
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_NAME": os.getenv("DB_NAME"),
    }
@app.get("/")
def read_root():
    return {"status": "online", "message": "CRM AI is running"}