"""
ShelterLink - Step 2: Train your first AI model (intent classifier)

Goal: read what a child says and decide what they need:
    FOOD, HEALTH, EDUCATION, EMERGENCY or OTHER

What this script teaches you:
  - Turning text into numbers (TF-IDF with character n-grams)
  - Training a model (logistic regression)
  - Measuring it honestly (cross-validation, precision, recall)
  - Why EMERGENCY recall matters most, and how a safety threshold helps
  - Saving the model so the chatbot can use it later

Run it from the ShelterLink folder:
    python notebooks/02_train_intent_classifier.py
"""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

sys.stdout.reconfigure(encoding="utf-8")  # so Bangla prints correctly on Windows

PROJECT = Path(__file__).resolve().parent.parent
MODELS = PROJECT / "models"
MODELS.mkdir(exist_ok=True)

# If the model thinks there is at least this chance of an emergency,
# we treat it as an emergency. Missing a real emergency is far worse
# than a false alarm, so this is set low on purpose.
EMERGENCY_THRESHOLD = 0.30

# ---------------------------------------------------------------
# 1. Load the sentences
# ---------------------------------------------------------------
data = pd.read_csv(PROJECT / "data" / "intent_examples.csv")
texts = data["text"].str.lower()
labels = data["intent"]
print(f"Sentences: {len(data)}")
print(labels.value_counts().to_string(), "\n")

# ---------------------------------------------------------------
# 2. Build the model
#    TF-IDF turns each sentence into numbers.
#    "char_wb" looks at small pieces of words (2 to 4 letters), so
#    "khida", "khide" and "khidha" still look similar. That helps with
#    Banglish, where everyone spells differently, and works for Bangla script too.
#    Logistic regression then learns which pieces point to which intent.
# ---------------------------------------------------------------
def build_model():
    return make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4)),
        LogisticRegression(max_iter=1000, class_weight="balanced"),
    )


def apply_safety_rule(model_classes, probabilities, predictions):
    """If EMERGENCY is likely enough, switch the answer to EMERGENCY."""
    emergency_col = list(model_classes).index("EMERGENCY")
    safe = predictions.copy()
    safe[probabilities[:, emergency_col] >= EMERGENCY_THRESHOLD] = "EMERGENCY"
    return safe


# ---------------------------------------------------------------
# 3. Test it honestly with 5-fold cross-validation
#    The data is split into 5 parts. The model trains on 4 and is tested
#    on the 1 it has never seen, 5 times over. Every sentence gets
#    tested exactly once, by a model that never saw it.
# ---------------------------------------------------------------
folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
probs = cross_val_predict(build_model(), texts, labels, cv=folds, method="predict_proba")
classes = np.array(sorted(labels.unique()))  # same order scikit-learn uses
plain_pred = classes[probs.argmax(axis=1)]
safe_pred = apply_safety_rule(classes, probs, plain_pred)

print("=== RESULTS (on sentences the model never saw) ===\n")
print("Without safety rule:")
print(classification_report(labels, plain_pred, digits=2, zero_division=0))
print(f"With safety rule (EMERGENCY if chance >= {EMERGENCY_THRESHOLD:.0%}):")
print(classification_report(labels, safe_pred, digits=2, zero_division=0))

print("Confusion matrix (rows = true intent, columns = predicted), with safety rule:")
matrix = pd.DataFrame(
    confusion_matrix(labels, safe_pred, labels=classes), index=classes, columns=classes
)
print(matrix.to_string(), "\n")

# The most important number: of all real emergencies, how many did we catch?
is_emergency = labels == "EMERGENCY"
caught = (safe_pred[is_emergency] == "EMERGENCY").sum()
print(f"EMERGENCY caught: {caught} of {is_emergency.sum()} ({caught / is_emergency.sum():.0%})")

missed = data[is_emergency & (safe_pred != "EMERGENCY")]
if len(missed):
    print("Missed emergencies (add more sentences like these!):")
    for text in missed["text"]:
        print(f"  - {text}")
print()

# ---------------------------------------------------------------
# 4. Train on ALL sentences and save the final model
# ---------------------------------------------------------------
model = build_model().fit(texts, labels)
joblib.dump(model, MODELS / "intent_model.joblib")
print(f"Model saved to: {MODELS / 'intent_model.joblib'}\n")

# ---------------------------------------------------------------
# 5. Try it on brand-new sentences
# ---------------------------------------------------------------
new_sentences = [
    "khub khida lagse bhai",
    "আমার জ্বর আর মাথা ব্যথা",
    "kal ki class hobe",
    "ekta lok amake marche",
    "tumi ki robot",
]
print("=== TRY IT ===")
new_probs = model.predict_proba([s.lower() for s in new_sentences])
new_pred = apply_safety_rule(model.classes_, new_probs, model.classes_[new_probs.argmax(axis=1)])
for sentence, intent, p in zip(new_sentences, new_pred, new_probs):
    print(f"  {sentence:30} -> {intent:10} (confidence {p.max():.0%})")
