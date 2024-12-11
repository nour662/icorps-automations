def train_model(df):
    """
    Trains and evaluates a Random Forest model with hyperparameter optimization.
    Includes feature scaling, cross-validation, and performance visualization.
    """
    logging.info("Starting model training...")

    # Extract features and target
    X = df[[col for col in df.columns if col.startswith("ms_")]]
    y = df["match"]

    # Feature scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print(X.columns)

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # Baseline Random Forest model
    rf_model = RandomForestClassifier(random_state=42)
    rf_model.fit(X_train, y_train)

    # Evaluate baseline model
    y_pred = rf_model.predict(X_test)
    logging.info("Baseline Model Performance:")
    logging.info(f"Accuracy: {accuracy_score(y_test, y_pred)}")
    logging.info(f"Classification Report:\n{classification_report(y_test, y_pred)}")
    logging.info(f"ROC AUC Score: {roc_auc_score(y_test, rf_model.predict_proba(X_test)[:, 1])}")

    # Hyperparameter tuning with GridSearchCV
    param_grid = {
        "n_estimators": [50, 100, 200],
        "max_depth": [None, 10, 20, 30],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
    }
    grid_search = GridSearchCV(
        RandomForestClassifier(random_state=42),
        param_grid,
        scoring="roc_auc",
        cv=5,
        n_jobs=-1,
        verbose=2
    )
    grid_search.fit(X_train, y_train)
    best_model = grid_search.best_estimator_
    logging.info(f"Best Model Parameters: {grid_search.best_params_}")

    # Cross-validation
    cv_scores = cross_val_score(best_model, X_train, y_train, cv=5, scoring="roc_auc")
    logging.info(f"Average Cross-Validation ROC AUC: {cv_scores.mean()}")

    # Final Model Evaluation
    y_pred_final = best_model.predict(X_test)
    logging.info("Final Model Performance:")
    logging.info(f"Accuracy: {accuracy_score(y_test, y_pred_final)}")
    logging.info(f"Classification Report:\n{classification_report(y_test, y_pred_final)}")

    feature_importances = best_model.feature_importances_
    indices = np.argsort(feature_importances)[::-1]  # Sort by importance

    # If X_train is a NumPy array, you can create a range of feature indices
    n_features = X_train.shape[1]  # number of features in X_train
    plt.figure(figsize=(10, 6))
    plt.title("Feature Importance")
    plt.barh(range(n_features), feature_importances[indices], align="center")
    plt.yticks(range(n_features), [f'Feature {i+1}' for i in indices])  # You can label features as 'Feature 1', 'Feature 2', etc.
    plt.xlabel("Relative Importance")
    plt.show()
