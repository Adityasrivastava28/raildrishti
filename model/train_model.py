import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

print("Loading training data...")
df = pd.read_csv("data/train_history.csv")

# Encode categorical columns into numbers
# ML models only understand numbers — not strings like "Delhi" or "Monsoon"
le_zone    = LabelEncoder()
le_type    = LabelEncoder()
le_season  = LabelEncoder()
le_label   = LabelEncoder()

df["zone_enc"]   = le_zone.fit_transform(df["zone"])
df["type_enc"]   = le_type.fit_transform(df["train_type"])
df["season_enc"] = le_season.fit_transform(df["season"])
df["label_enc"]  = le_label.fit_transform(df["label"])

# Features (X) — what the model uses to predict
# Target (y) — what the model predicts
X = df[["zone_enc", "type_enc", "hour", "day_of_week", "season_enc"]]
y = df["label_enc"]

# Split: 80% training, 20% testing
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training on {len(X_train)} records...")
print(f"Testing on  {len(X_test)} records...")

# Train the Random Forest
model = RandomForestClassifier(
    n_estimators=100,    # 100 decision trees
    max_depth=10,        # max depth of each tree
    random_state=42
)
model.fit(X_train, y_train)

# Evaluate
y_pred   = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\nModel accuracy: {accuracy*100:.1f}%")
print(f"\nDetailed report:")
print(classification_report(y_test, y_pred, target_names=le_label.classes_))

# Save everything — gateway will load these on startup
os.makedirs("model", exist_ok=True)
joblib.dump(model,    "model/delay_model.pkl")
joblib.dump(le_zone,  "model/le_zone.pkl")
joblib.dump(le_type,  "model/le_type.pkl")
joblib.dump(le_season,"model/le_season.pkl")
joblib.dump(le_label, "model/le_label.pkl")

print("\nModel saved to model/delay_model.pkl")
print("Label encoders saved to model/")
print("\nFeature importance:")
for feat, imp in zip(["zone","train_type","hour","day_of_week","season"],
                     model.feature_importances_):
    print(f"  {feat:<15} {imp*100:.1f}%")