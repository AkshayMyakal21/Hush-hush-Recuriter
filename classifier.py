import numpy as np
from database import connect_db
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

def load_training_data():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.followers, c.public_repos, c.total_stars, c.total_forks, c.commit_count, s.is_selected
        from candidates c
        JOIN scores s ON c.id = s.candidate_id
        WHERE s.id IN (
                   SELECT MAX(id) FROM scores GROUP BY candidate_id
                   )
     """)
    
    rows = cursor.fetchall()
    conn.close()
    X = np.array([row[:5] for row in rows])
    y = np.array([row[5] for row in rows])

    return X, y

def train_model():
    X, y = load_training_data()
    model = RandomForestClassifier(n_estimators = 100, random_state = 42)
    model.fit(X, y)
    joblib.dump(model, "model.joblib")
    print("Model trained and saved")
    print(classification_report(y, model.predict(X)))
    return model

def predict_candidate(followers, public_repos, total_stars, total_forks, commit_count):
    model = joblib.load("model.joblib")
    return int (model.predict([[followers, public_repos, total_stars, total_forks, commit_count]])[0])

def predict_confidence(followers, public_repos, total_stars, total_forks, commit_count):
    model = joblib.load("model.joblib")
    return float( model.predict_proba([[followers, public_repos, total_stars, total_forks, commit_count]])[0][1] * 100)

if __name__ == "__main__":
    X, y = load_training_data()
    print(X.shape)
    print(y)
    train_model()
    result = predict_candidate(10792, 31, 29820, 87742)
    print(result)

