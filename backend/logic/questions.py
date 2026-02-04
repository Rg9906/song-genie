def generate_questions(feature_values):
    questions = []

    for feature, values in feature_values.items():
        for value in values:
            questions.append({
                "feature": feature,
                "value": value,
                "text": f"Is the {feature.replace('_', ' ')} {value.replace('_', ' ')}?"
            })

    return questions
