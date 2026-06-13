"""
Train a gesture classifier from collected landmark data.

Usage:
    poetry run python -m hand_mouse.train

Outputs a model file at data/gesture_model.pkl
"""

import os
import pickle

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

DATA_PATH = os.path.join(os.path.dirname(__file__), "../../../data/landmarks.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../../data/gesture_model.pkl")


def main():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} samples")
    print(df["label"].value_counts())

    X = df.drop("label", axis=1).values
    le = LabelEncoder()
    y = le.fit_transform(df["label"].values)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"model": clf, "label_encoder": le}, f)

    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
