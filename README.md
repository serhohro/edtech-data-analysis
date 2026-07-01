# EdTech Data Analysis: CRM Analytics for an Online Programming School

An automated data cleaning pipeline, comprehensive business analysis, and interactive performance dashboard of an EdTech platform covering a 12-month period (July 2023 – June 2024)[cite: 1, 2, 7].

---

## 📌 Project Overview

This project delivers an end-to-end data pipeline designed to process raw CRM data dumps from an online school, execute Exploratory Data Analysis (EDA), and deliver actionable insights for C-level management[cite: 1, 3, 7].

**Core Project Insight:** The company is *conversion-limited*[cite: 1]. While traffic and lead generation channels are sufficient, the primary lever for revenue growth lies in internal process optimization and strict SLA control[cite: 1]. Statistical analysis proves that reducing manager response time to $\le60$ minutes increases the conversion rate by **+19.4%**, generating an additional **+€98K** without increasing the marketing budget[cite: 1].

---

## 🛠 Tech Stack

* **Programming Language:** Python[cite: 1]
* **Data Processing Libraries:** Pandas, NumPy[cite: 3]
* **Data Visualization:** Matplotlib, Seaborn[cite: 3]
* **Statistical Analysis:** SciPy (Hypothesis Testing, Chi-Square Test)[cite: 1]
* **Deployment & Presentation:** HTML / GitHub Pages[cite: 1]

---

## ⚙️ Core Pipeline Stages

### 1. Automated Data Cleaning
Custom-built scripts automate the preprocessing pipeline for four major datasets (Calls, Contacts, Deals, Spend), handling over 136,000 data rows in total[cite: 1, 2, 7]:
* **Hidden Duplicates Removal:** Identified and eliminated 15,756 partial duplicates in the Deals table (records sharing identical attributes but assigned unique `Id` values)[cite: 1, 6].
* **Time-Anomaly Filtering:** Excluded logical data entries, such as deals marked with a `Closing Date` prior to their `Created Time`[cite: 6].
* **Outlier Handling:** Detected and trimmed extreme call duration anomalies using the 99th percentile threshold[cite: 3].
* **Data Formatting & Imputation:** Standardized date formats to ISO, handled missing categorical variables, and normalized city names[cite: 2, 4, 5, 6].

### 2. Business Modeling & KPI Calculations
* Built a comprehensive **Metric Tree** for revenue decomposition[cite: 1].
* Evaluated key performance indicators (KPIs): Total Revenue (**€3.80M**), end-to-end conversion rate (**C1: 32.23%**), **ROMI (2440%)**, average order value (AOV), and product unit economics[cite: 1].
* Conducted sales team performance analysis, uncovering systemic anomalies in lead distribution workflows[cite: 1, 3].
* Performed cohort analysis, product breakdown, and geographical evaluation (with Berlin leading the market)[cite: 1].

### 3. Hypothesis Testing & Visualization
* Generated **11 analytical charts**, including conversion funnels, deal velocity trends, and channel-specific ROMI distributions[cite: 3].
* Formulated and quantified 3 budget-free optimization hypotheses, revealing a total revenue growth potential of **+€810K**[cite: 1].

---

## 📂 Repository Structure

* `run_all_cleaning.py` — Main execution script for the data cleaning pipeline[cite: 7].
* `Calls.py`, `Contacts.py`, `Deals.py`, `Spend.py` — Modular scripts cleaning individual CRM entities[cite: 2, 4, 5, 6, 7].
* `calculations.py` — Pipeline for business metrics computing, statistical testing, and visualization[cite: 3].
* `index.html` — Interactive project presentation (17 slides)[cite: 1].
* `cleaning_report.csv` — Automatically generated data quality report[cite: 7].

---

## 📊 Business Performance Dashboard

| Business Metric | Target Metric | Metric Value | Unit |
| :--- | :---: | :---: | :---: |
| Total Actual Revenue | Revenue | 3.80M | € |
| Overall Return on Marketing Investment | Overall ROMI | 2440.00 | % |
| End-to-End Conversion Rate | CR (C1) | 32.23 | % |
| Global Customer Acquisition Cost | Global CAC | 57.00 | € |
| Unit Economics Efficiency Ratio | LTV/CAC | 21.0 | × |

> 🔗 **[View Interactive Project Presentation Website](https://serhohro.github.io/edtech-data-analysis/)**
