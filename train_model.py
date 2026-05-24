import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

def train():
    # Load synthetic data
    df = pd.read_csv('synthetic_tree_data.csv')
    
    # Features and Target
    X = df[['latitude', 'longitude', 'elevation', 'ndvi', 'slope', 'aspect']]
    y = df['species']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Random Forest Model
    # We use a classifier because we have discrete species classes. 
    # The probabilities will give us the "Survival Probability".
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("Model Performance:")
    print(classification_report(y_test, y_pred))
    
    # Save Model
    joblib.dump(model, 'tree_model.joblib')
    print("Model saved as tree_model.joblib")

if __name__ == "__main__":
    train()
