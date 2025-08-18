import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import RandomOverSampler
import numpy as np
import pickle

file_path = "Final_Updated_Dataset_Cleaned_Shuffled.csv"
df = pd.read_csv(file_path)

if 'ID' in df.columns:
    df.drop(columns=['ID'], inplace=True)

target_col = 'Disease'
label_encoder = LabelEncoder()
df[target_col] = label_encoder.fit_transform(df[target_col])

X = df.drop(columns=[target_col])
y = df[target_col]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

ros = RandomOverSampler(random_state=42)
X_train_resampled, y_train_resampled = ros.fit_resample(X_train, y_train)

missing_classes = set(np.unique(y)) - set(np.unique(y_train_resampled))
if missing_classes:
    print(f"Adding missing classes: {missing_classes}")
    for cls in missing_classes:
        sample = df[df[target_col] == cls].drop(columns=[target_col]).sample(n=1, random_state=42)
        X_train_resampled = np.vstack([X_train_resampled, sample])
        y_train_resampled = np.append(y_train_resampled, cls)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train_resampled)
X_test = scaler.transform(X_test)

rf_params = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 15, 20],
    'min_samples_split': [2, 5, 10]
}
rf_model = RandomForestClassifier(random_state=42)
grid_search = GridSearchCV(rf_model, rf_params, cv=3, scoring='accuracy', n_jobs=-1)
grid_search.fit(X_train, y_train_resampled)
best_rf_model = grid_search.best_estimator_

y_pred_rf = best_rf_model.predict(X_test)

all_classes = np.unique(y)  
all_class_names = [label_encoder.classes_[i] for i in all_classes]

accuracy_rf = accuracy_score(y_test, y_pred_rf)
report_rf = classification_report(y_test, y_pred_rf, labels=all_classes, target_names=all_class_names, zero_division=0)

print(f"Best Random Forest Accuracy: {accuracy_rf:.2f}")
print("Random Forest Classification Report:\n", report_rf)
print("Random Forest is the final chosen model for predictions.")

with open("random_forest_model.pkl", "wb") as model_file:
    pickle.dump(best_rf_model, model_file)

with open("label_encoder.pkl", "wb") as encoder_file:
    pickle.dump(label_encoder, encoder_file)

with open("scaler.pkl", "wb") as scaler_file:
    pickle.dump(scaler, scaler_file)

print("Model, Label Encoder, and Scaler saved successfully.")
