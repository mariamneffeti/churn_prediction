import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="web_project"
)

query = """
SELECT 
    c.id,
    c.total_spent,
    DATEDIFF(CURDATE(), c.last_purchase_date) as days_since_last_purchase,
    COUNT(s.id) as purchase_count,
    AVG(s.total_amount) as avg_order_value
FROM clients c
LEFT JOIN sales s ON c.id = s.client_id
GROUP BY c.id
"""

df = pd.read_sql(query, conn)

df['churn'] = df['days_since_last_purchase'] > 60

X = df[['total_spent', 'days_since_last_purchase', 'purchase_count', 'avg_order_value']]
y = df['churn']

model = RandomForestClassifier()
model.fit(X, y)

joblib.dump(model, 'churn_model.pkl')

print("Model trained ")