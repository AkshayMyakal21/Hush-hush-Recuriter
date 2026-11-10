import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans

def cluster_candidates(candidates):

    features = np.array([[candidate.total_stars, candidate.total_forks, candidate.followers, candidate.public_repos, candidate.commit_count]
                        for candidate in candidates])
    
    scaler = MinMaxScaler()
    # features_normalized = scaler.fit_transform(features)
    features_normalized = scaler.fit_transform(np.log1p(features))

    kmeans = KMeans(n_clusters = 2, random_state = 42, n_init = 10)
    cluster_labels = kmeans.fit_predict(features_normalized)

    return cluster_labels

def identify_strong_cluster(candidates, cluster_labels):

    cluster_0_scores = [candidate.github_score for candidate, label in zip(candidates, cluster_labels) if label == 0]
    cluster_1_scores = [candidate.github_score for candidate, label in zip(candidates, cluster_labels) if label == 1]

    avg_0 = sum(cluster_0_scores) / len(cluster_0_scores)
    avg_1 = sum(cluster_1_scores) / len(cluster_1_scores)

    return 1 if avg_1 > avg_0 else 0

def label_candidate(candidates, cluster_labels, strong_cluster):

    for candidate, label in zip(candidates, cluster_labels):
        candidate.is_selected = bool(label == strong_cluster)

    return candidates

