import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib

# Load dataset
df = pd.read_csv("normal_abnormal.csv")

# Drop unwanted columns and rows with missing values
df.drop(columns=["timestamp", "Unnamed: 11"], inplace=True, errors='ignore')
df.dropna(inplace=True)

# Features and target
features = [
    "total_keys", "avg_hold_time_ms", "avg_delay_ms", "backspace_rate",
    "mouse_move_distance", "left_clicks", "right_clicks", "mouse_idle_time",
    "typing_speed_kpm", "typing_speed_cps"
]
target = "Label"

X = df[features]
y = df[target]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Initialize and train Random Forest model
model = RandomForestClassifier(random_state=42)
model.fit(X_train_scaled, y_train)

# Evaluate
y_pred = model.predict(X_test_scaled)
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred))

# Save model and scaler
joblib.dump(model, "rf_model.joblib")
joblib.dump(scaler, "scaler.joblib")

print("✅ Model and scaler saved.")
