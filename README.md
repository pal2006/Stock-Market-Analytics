# 📊 Stock Market Analytics

A full-stack stock market analytics project that combines **Python, SQL, Excel, Power BI, React, and FastAPI** to collect, process, analyze, visualize, and explore stock market data.

The project provides both **business intelligence dashboards** and an interactive web application where users can search for stocks and analyze their historical performance, risk, returns, fundamentals, price movements, and trading volume.

---

## 🚀 Project Overview

The objective of this project is to build an end-to-end stock market analytics system that transforms raw market data into meaningful financial insights.

The project follows this pipeline:

Raw Market Data  
↓  
Python Data Collection  
↓  
Data Cleaning & Validation  
↓  
Financial Analysis  
↓  
MySQL Database  
↓  
Power BI / Excel Analytics  
↓  
FastAPI Backend  
↓  
React Frontend  
↓  
Interactive Stock Analytics Dashboard

---

## 🎯 Key Objectives

- Collect historical stock market data
- Clean and validate financial datasets
- Store structured data in MySQL
- Calculate financial performance and risk metrics
- Perform sector-level analysis
- Build interactive Power BI dashboards
- Perform financial analysis using Excel
- Develop a full-stack stock analytics web application
- Allow users to dynamically search for stocks
- Display historical prices, moving averages, returns, volatility, drawdown and trading volume
- Retrieve the latest available market information

---

# 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| **Python** | Data collection, cleaning and financial analysis |
| **Pandas** | Data manipulation and processing |
| **NumPy** | Numerical calculations |
| **yfinance** | Market data retrieval |
| **MySQL** | Database storage |
| **SQL** | Data querying and analysis |
| **Excel** | Financial analysis and dashboards |
| **Power BI** | Interactive business intelligence dashboards |
| **React.js** | Frontend web application |
| **FastAPI** | Backend REST API |
| **JavaScript / JSX** | Frontend development |
| **CSS** | User interface styling |
| **Git & GitHub** | Version control |

---

# 📁 Project Structure

```text
Stock-Market-Analytics/
│
├── Data/
│   ├── Raw/
│   ├── Processed/
│   └── Charts/
│
├── Excel/
│   ├── Stock_Market_Analytics.xlsx
│   └── Stock_Market_Analytics_Backup/
│
├── Power BI/
│   └── Stock_Market_Analytics_Dashboard.pbix
│
├── Python/
│   ├── data_collection.py
│   ├── data_ingestion.py
│   ├── data_inspection.py
│   ├── data_cleaning.py
│   ├── financial_analysis.py
│   ├── sector_analysis.py
│   ├── summary_analysis.py
│   └── visualization.py
│
├── SQL/
│
├── backend/
│   ├── main.py
│   └── database.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── Tableau/
│
├── .gitignore
└── README.md
