ROLE_QUERIES = {
      "software_engineer": ['python', 'java', 'cplusplus', 'system design', 'algorithms'],
      "data_scientist": ['pandas', 'numpy', 'scikit-learn', 'data visualization', 'statistics', 'jupyter'],
      "ml engineer": ['model deployment', 'training pipeline', 'data preprocessing', 'feature engineering', 'model evaluation'],
      "backend engineer": ['nodejs', 'express', 'mongodb', 'mysql', 'postgresql'],
      "cloud engineer": ['aws', 'gcp', 'azure', 'docker', 'kubernetes', 'terraform'],
      }
def build_queries(role):
      queries = ROLE_QUERIES.get(role, [])
      return [f"{q} type:user" for q in queries]