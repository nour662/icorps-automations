import pandas as pd
import re
from rapidfuzz import fuzz
from datetime import datetime
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score, roc_curve
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

import logging
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import numpy as np

logging.basicConfig(filename="log.txt", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def clean_masterlist(df):
    logging.info("Cleaning masterlist...")

    try:
        df = df.replace({np.nan: None})
        df["Full Name"] = df["First Name"] + " " + df["Last Name"]
        df.drop(columns=["First Name", "Last Name"], inplace=True)
        df["Incorporation Year"] = df["Incorporation Year"].apply(lambda x: None if pd.isna(x) else str(int(x)))

        grouped = df.groupby("Company")[[
            "Full Name", "Shipping Street", "Shipping City",
            "Shipping State/Province", "Shipping Country",
            "Shipping Zip/Postal Code", "Website", "Incorporation Year"
        ]].agg(list).reset_index()

        grouped = grouped.rename(columns={'Company': 'sf_company_name',
                                         "Shipping Zip/Postal Code": "Zipcode",
                                         "Shipping State/Province": "State",
                                         "Shipping Country": "Country",
                                         "Shipping Street": "Street",
                                         "Shipping City": "City"})

        for col in ["Full Name", "Street", "City", "State",
                    "Country", "Zipcode", "Website", "Incorporation Year"]:
            # Clean the column by applying the correct lambda functions
            grouped[f"sf_{col.lower().replace(' ', '_')}"] = grouped[col].apply(
                lambda x: x[0]
            )
        grouped["sf_full_name"] = grouped["Full Name"]

        grouped.to_csv("one.csv", index=False)

        cols = ['Full Name', 'Street', 'City', 'State', 'Country',
                'Zipcode', 'Website', 'Incorporation Year']

        grouped.drop(columns=cols, inplace=True)
        return grouped

    except Exception as e:
        logging.error(f"Error in cleaning masterlist: {e}")
        raise


def clean_training(df, master_df):
    logging.info("Cleaning training dataset...")

    df = df.rename(columns={'legal_name': 'sam_company_name', "entity_url": "sam_website"})

    def split_address(address):
        if pd.isna(address):
            return [None] * 4
        pattern = r"^(\d+ [A-Za-z0-9\s]+(?: [A-Za-z0-9]+)?),([A-Za-z\s]+),\s([A-Za-z\s]+),(\d{5})(?:-\d{4})?,\s(.*)$"
        match = re.match(pattern, address.strip())
        return [
            match.group(1) if match else None,  # Street
            match.group(2) if match else None,  # City
            match.group(3) if match else None,  # State
            match.group(4) if match else None   # Zipcode
        ]

    for col in ["physical_address", "mailing_address"]:
        components = ["street", "city", "state", "zipcode"]
        df[[f"sam_{col}_{comp}" for comp in components]] = df[col].apply(
            lambda x: pd.Series(split_address(x))
        )

    def extract_year(date_str):
        try:
            return str(datetime.strptime(date_str, "%b %d, %Y").year) if pd.notna(date_str) else None
        except ValueError:
            return None

    df["sam_incorp_year"] = df["start_date"].apply(extract_year)

    def extract_name(name):
        if pd.isna(name):
            return None

        pattern = r"^([A-Za-z]+)\s?([A-Za-z]?.)?\s([A-Za-z]+)"
        match = re.match(pattern, name.strip())
        if match:
            first_name = match.group(1)
            last_name = match.group(3)
            return f"{first_name} {last_name}" if first_name and last_name else None
        return None

    df["sam_contacts"] = df.apply(
        lambda row: [extract_name(row.get("contact1")), extract_name(row.get("contact2"))],
        axis=1
    )
    merged = pd.merge(
        df, master_df, left_on="keyword", right_on="sf_company_name", how="inner"
    )

    drop_columns = ["mailing_address", "cage", "num_uei",
                    "physical_address", "state_country_incorporation",
                    "contact1", "contact2", "start_date",
                    "congressional_district"]
    merged.drop(columns=drop_columns, inplace=True)
    
    
    merged.to_csv("one.csv")
    return merged


def calculate_fuzzy_scores(merged):

    logging.info("Calculating fuzzy scores...")

    def fuzzy_match(var_one, var_two):
        if not var_one or not var_two:
            return 0 
        return fuzz.ratio(str(var_one).lower().strip(), str(var_two).lower().strip())

    correlated_columns = ["company_name", "website", "incorp_year"]
    for col in correlated_columns:
        merged[f"ms_{col}_fuzzy_score"] = merged.apply(
            lambda row: fuzzy_match(row.get(f"sam_{col}"), row.get(f"sf_{col}")),
            axis=1
        )

    address_components = ["street", "city", "state", "zipcode"]
    for component in address_components:
        # Calculate fuzzy score for physical address
        merged[f"ms_{component}_fuzzy_score_physical"] = merged.apply(
            lambda row: fuzzy_match(
                row.get(f"sam_physical_address_{component}"),
                row.get(f"sf_{component}")
            ),
            axis=1
        )
        merged[f"ms_{component}_fuzzy_score_mailing"] = merged.apply(
            lambda row: fuzzy_match(
                row.get(f"sam_mailing_address_{component}"),
                row.get(f"sf_{component}")
            ),
            axis=1
        )

    highest_fuzzy_scores = []
    for i, row_1 in merged.iterrows():
        max_score = 0
        for j, row_2 in merged.iterrows():
            if i != j:  
                score = 0
                for col in correlated_columns:
                    score = max(score, fuzzy_match(row_1.get(f"sam_{col}"), row_2.get(f"sf_{col}")))
                
                for component in address_components:
                    score = max(score, fuzzy_match(row_1.get(f"sam_physical_address_{component}"), row_2.get(f"sf_{component}")))
                    score = max(score, fuzzy_match(row_1.get(f"sam_mailing_address_{component}"), row_2.get(f"sf_{component}")))

                max_score = max(max_score, score)
        
        highest_fuzzy_scores.append(max_score)
    
    merged['highest_fuzzy_score'] = highest_fuzzy_scores

    merged.to_csv("temp.csv", index=False)

    return merged

def train_model(df):
    logging.info("Starting model training...")

    X = df[[col for col in df.columns if col.startswith("ms_")]]
    
    zip_code_columns = [col for col in X.columns if "zipcode" in col]
    X = X.drop(columns=zip_code_columns)
    
    y = df["match"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled_df = pd.DataFrame(X_scaled, columns=X.columns)  

    X_train, X_test, y_train, y_test = train_test_split(X_scaled_df, y, test_size=0.2, random_state=42)

    rf_model = RandomForestClassifier(
        n_estimators=200,               # Number of trees in the forest
        max_depth=None,                 # No max depth (tree depth grows until leaves are pure or they contain less than min_samples_split samples)
        min_samples_split=15,           # Minimum samples required to split an internal node
        min_samples_leaf=6,             # Minimum samples required to be at a leaf node
        bootstrap=True,                 # Whether bootstrap samples are used when building trees
        max_features='sqrt',            # Number of features to consider when looking for the best split
        criterion='gini',               # The function to measure the quality of a split
        random_state=42                 # For reproducibility
    )
    
    rf_model.fit(X_train, y_train)

    y_pred = rf_model.predict(X_test)
    y_probs = rf_model.predict_proba(X_test)  

    logging.info("Model Performance:")
    logging.info(f"Accuracy: {accuracy_score(y_test, y_pred)}")
    logging.info(f"Classification Report:\n{classification_report(y_test, y_pred)}")
    logging.info(f"ROC AUC Score: {roc_auc_score(y_test, y_probs[:, 1])}")

    cm = confusion_matrix(y_test, y_pred)
    logging.info(f"Confusion Matrix:\n{cm}")

    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=rf_model.classes_)
    disp.plot(cmap=plt.cm.Blues)
    plt.show()

    low_conf_threshold = 0.6  
    confidence_scores = y_probs[:, 1]  
    low_conf_mask = (confidence_scores > (1 - low_conf_threshold)) & (confidence_scores < low_conf_threshold)

    results_df = pd.DataFrame({
        "True_Label": y_test.reset_index(drop=True),
        "Predicted_Label": y_pred,
        "Confidence_Score": confidence_scores,
        "Low_Confidence": low_conf_mask
    })

    logging.info("Low-Confidence Predictions:\n")
    logging.info(results_df[results_df["Low_Confidence"]])

    cv_scores = cross_val_score(rf_model, X_train, y_train, cv=5, scoring="roc_auc")
    logging.info(f"Average Cross-Validation ROC AUC: {cv_scores.mean()}")

    y_pred_final = rf_model.predict(X_test)
    logging.info("Final Model Performance:")
    logging.info(f"Accuracy: {accuracy_score(y_test, y_pred_final)}")
    logging.info(f"Classification Report:\n{classification_report(y_test, y_pred_final)}")

    return rf_model

def main():
    df_master = pd.read_csv("../inputs/icorps_masterlist.csv")
    df_training = pd.read_csv("training.csv")

    master_df = clean_masterlist(df_master)
    merged_df = clean_training(df_training, master_df)

    merged_with_scores = calculate_fuzzy_scores(merged_df)

    best_model = train_model(merged_with_scores)
    

if __name__ == "__main__":
    main()
