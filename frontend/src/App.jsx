import { useEffect, useMemo, useState } from "react";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Scatter,
  ScatterChart,
  ReferenceLine,
} from "recharts";

import "./App.css";

const STOCK_LOGOS = {
  ADANIENT: "https://www.google.com/s2/favicons?sz=128&domain=adanienterprises.com",
  AXISBANK: "https://www.google.com/s2/favicons?sz=128&domain=axisbank.com",
  HCLTECH: "https://www.google.com/s2/favicons?sz=128&domain=hcltech.com",
  HDFCBANK: "https://www.google.com/s2/favicons?sz=128&domain=hdfcbank.com",
  HINDUNILVR: "https://www.google.com/s2/favicons?sz=128&domain=hul.co.in",
  ICICIBANK: "https://www.google.com/s2/favicons?sz=128&domain=icicibank.com",
  INFY: "https://www.google.com/s2/favicons?sz=128&domain=infosys.com",
  IOC: "https://www.google.com/s2/favicons?sz=128&domain=iocl.com",
  ITC: "https://www.google.com/s2/favicons?sz=128&domain=itcportal.com",
  LT: "https://www.google.com/s2/favicons?sz=128&domain= Larsen.com",
  MARUTI: "https://www.google.com/s2/favicons?sz=128&domain=marutisuzuki.com",
  RELIANCE: "https://www.google.com/s2/favicons?sz=128&domain=ril.com",
  SBIN: "https://www.google.com/s2/favicons?sz=128&domain=sbi.co.in",
  SUNPHARMA: "https://www.google.com/s2/favicons?sz=128&domain=sunpharma.com",
  TCS: "https://www.google.com/s2/favicons?sz=128&domain=tcs.com",
  TATAPOWER: "https://www.google.com/s2/favicons?sz=128&domain=tatapower.com",
  TATASTEEL: "https://www.google.com/s2/favicons?sz=128&domain=tatasteel.com",
  WIPRO: "https://www.google.com/s2/favicons?sz=128&domain=wipro.com",
};

const API = "http://127.0.0.1:8000";

function App() {
  const [stocks, setStocks] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [history, setHistory] = useState([]);
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState("overview");
  const [loadingStocks, setLoadingStocks] = useState(true);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [error, setError] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // ==========================================================
  // LOAD STOCKS
  // ==========================================================

  useEffect(() => {
    loadStocks();
  }, []);

  // ==========================================================
// AUTOMATIC MARKET DATA REFRESH
// ==========================================================

useEffect(() => {

  if (!selectedStock) {
    return;
  }

  const refreshInterval =
    setInterval(async () => {

      try {

        setIsRefreshing(true);

        const response =
          await fetch(
            `${API}/stocks/${selectedStock}`
          );

        if (!response.ok) {
          return;
        }

        const data =
          await response.json();

        setAnalysis((previousAnalysis) => {

          if (!previousAnalysis) {
            return previousAnalysis;
          }

          return {
            ...previousAnalysis,
            ...data,
          };

        });

        setLastUpdated(
          new Date()
        );

      }

      catch (err) {

        console.error(
          "Automatic refresh error:",
          err
        );

      }

      finally {

        setIsRefreshing(false);

      }

    }, 15000);

  return () => {

    clearInterval(
      refreshInterval
    );

  };

}, [selectedStock]);

  async function loadStocks() {
    try {
      setLoadingStocks(true);
      setError("");

      const response = await fetch(`${API}/stocks`);

      if (!response.ok) {
        throw new Error("Unable to load stocks");
      }

      const data = await response.json();

      if (!Array.isArray(data)) {
        throw new Error("Invalid stock list received from API");
      }

      const formattedStocks = data.map((item) => {
        if (Array.isArray(item)) {
          return {
            ticker: String(item[0] ?? "").toUpperCase(),
            company_name: item[1] ?? item[0] ?? "",
            sector: item[2] ?? "Unknown",
          };
        }

        const ticker =
          item?.ticker ??
          item?.Ticker ??
          item?.stock ??
          item?.Stock ??
          item?.symbol ??
          item?.Symbol ??
          "";

        const company =
          item?.company_name ??
          item?.Company_Name ??
          item?.company ??
          item?.Company ??
          item?.companyName ??
          item?.CompanyName ??
          item?.name ??
          item?.Name ??
          item?.longName ??
          item?.shortName ??
          ticker;

        const sector =
          item?.sector ??
          item?.Sector ??
          item?.industry ??
          item?.Industry ??
          "Unknown";

        return {
          ticker: String(ticker).toUpperCase(),
          company_name: company,
          sector: sector,
        };
      });

      setStocks(formattedStocks);
    } catch (err) {
      console.error("Stock loading error:", err);

      setError(
        "Unable to load stocks. Make sure FastAPI is running."
      );
    } finally {
      setLoadingStocks(false);
    }
  }

 // ==========================================================
// SELECT STOCK
// ==========================================================

async function selectStock(ticker) {

  const normalizedTicker =
    String(ticker)
      .trim()
      .toUpperCase();

  if (!normalizedTicker) {
    return;
  }

  console.log(
    "Selecting stock:",
    normalizedTicker
  );

  setSelectedStock(normalizedTicker);
  setLoadingAnalysis(true);
  setError("");
  setActiveTab("overview");
  setAnalysis(null);
  setHistory([]);

  try {

    // ------------------------------------------------------
    // FETCH COMPLETE STOCK DATA
    // ------------------------------------------------------

    const response = await fetch(
      `${API}/stocks/${normalizedTicker}`
    );

    console.log(
      "Stock API response:",
      response.status
    );

    if (!response.ok) {

      let message =
        `Unable to load ${normalizedTicker}.`;

      try {

        const errorData =
          await response.json();

        message =
          errorData?.detail ||
          message;

      } catch {
        // Ignore JSON parsing error
      }

      throw new Error(message);
    }

    const data =
      await response.json();

    console.log(
      "Complete stock response:",
      data
    );

    // ------------------------------------------------------
    // NORMALIZE STOCK DATA
    // ------------------------------------------------------

    const row =
      Array.isArray(data)
        ? data[0]
        : data;

    if (!row) {
      throw new Error(
        `No data returned for ${normalizedTicker}.`
      );
    }

    const formattedAnalysis = {

      ticker:
        row?.ticker ??
        normalizedTicker,

      company_name:
        row?.company_name ??
        row?.Company_Name ??
        normalizedTicker,

      sector:
        row?.sector ??
        row?.Sector ??
        "Unknown",

      industry:
        row?.industry ??
        row?.Industry ??
        "Unknown",

      market_cap:
        row?.market_cap ??
        row?.Market_Cap,

      pe_ratio:
        row?.pe_ratio ??
        row?.PE_Ratio,

      dividend_yield:
        row?.dividend_yield ??
        row?.Dividend_Yield,

      annual_dividend:
        row?.annual_dividend ??
        row?.Annual_Dividend,

      latest_dividend:
        row?.latest_dividend ??
        row?.Latest_Dividend,

      quarterly_dividend:
        row?.quarterly_dividend ??
        row?.Quarterly_Dividend,

      fifty_two_week_high:
        row?.fifty_two_week_high ??
        row?.Fifty_Two_Week_High,

      fifty_two_week_low:
        row?.fifty_two_week_low ??
        row?.Fifty_Two_Week_Low,

      latest_price:
        row?.latest_price ??
        row?.Latest_Price,

      highest_price:
        row?.highest_price ??
        row?.Highest_Price,

      lowest_price:
        row?.lowest_price ??
        row?.Lowest_Price,

      daily_volatility:
        row?.daily_volatility ??
        row?.Daily_Volatility,

      annualized_volatility:
        row?.annualized_volatility ??
        row?.Annualized_Volatility,

      annualized_return:
        row?.annualized_return ??
        row?.Annualized_Return,

      maximum_drawdown:
        row?.maximum_drawdown ??
        row?.Maximum_Drawdown,

      sharpe_ratio:
        row?.sharpe_ratio ??
        row?.Sharpe_Ratio,

      average_volume:
        row?.average_volume ??
        row?.Average_Volume,

      latest_trade_date:
        row?.latest_trade_date ??
        row?.Latest_Trade_Date,

      data_source:
        row?.data_source ??
        "Yahoo Finance",

      data_refreshed_at:
        row?.data_refreshed_at,

    };

    // ------------------------------------------------------
    // FORMAT HISTORY
    // ------------------------------------------------------

  let rawHistory = [];

try {

  const historyResponse =
    await fetch(
      `${API}/stocks/${normalizedTicker}/history`
    );

  if (!historyResponse.ok) {

    throw new Error(
      `History request failed: ${historyResponse.status}`
    );

  }

  const historyData =
    await historyResponse.json();

  console.log(
    "Complete OHLCV history response:",
    historyData
  );

  if (
    historyData &&
    Array.isArray(historyData.history)
  ) {

    rawHistory =
      historyData.history;

  }
  else if (
    Array.isArray(historyData)
  ) {

    rawHistory =
      historyData;

  }

}
catch (historyError) {

  console.error(
    "History loading error:",
    historyError
  );

  rawHistory = [];

}
    

    const formattedHistory =
      rawHistory
        .map((item) => {

          if (
            item &&
            typeof item === "object" &&
            !Array.isArray(item)
          ) {

            const date =
              item.trade_date ??
              item.date ??
              item.Date;

            const close =
              item.close_price ??
              item.close ??
              item.Close;

            return {

              date,

              open:
                Number(
                  item.open_price ??
                  item.open
                ),

              high:
                Number(
                  item.high_price ??
                  item.high
                ),

              low:
                Number(
                  item.low_price ??
                  item.low
                ),

              close:
                Number(close),

              volume:
                Number(
                  item.volume ?? 0
                ),

            };
          }

          if (Array.isArray(item)) {

            return {

              date:
                item[0],

              close:
                Number(item[1]),

            };
          }

          return null;

        })
        .filter(
          (item) =>
            item &&
            item.date &&
            Number.isFinite(
              item.close
            )
        );

    console.log(
      "Formatted history:",
      formattedHistory.length,
      "rows"
    );

    // ------------------------------------------------------
    // SET DATA
    // ------------------------------------------------------

    setAnalysis(
      formattedAnalysis
    );

    setHistory(
      formattedHistory
    );

    // ------------------------------------------------------
    // ADD STOCK TO CARDS IF DYNAMICALLY SEARCHED
    // ------------------------------------------------------

    setStocks((previousStocks) => {

      const exists =
        previousStocks.some(
          (stock) =>
            String(stock.ticker)
              .toUpperCase() ===
            normalizedTicker
        );

      if (exists) {
        return previousStocks;
      }

      return [
        ...previousStocks,

        {
          ticker:
            normalizedTicker,

          company_name:
            formattedAnalysis.company_name ||
            normalizedTicker,

          sector:
            formattedAnalysis.sector ||
            "Unknown",

        },

      ].sort(
        (a, b) =>
          String(a.ticker).localeCompare(
            String(b.ticker)
          )
      );

    });

    // ------------------------------------------------------
    // SCROLL TO ANALYSIS
    // ------------------------------------------------------

    setTimeout(() => {

      const section =
        document.getElementById(
          "analysis"
        );

      if (section) {

        section.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });

      }

    }, 100);

  }

  catch (err) {

    console.error(
      "Analysis error:",
      err
    );

    setError(
      err?.message ||
      `Unable to load ${normalizedTicker}.`
    );

    setAnalysis(null);
    setHistory([]);

  }

  finally {

    // VERY IMPORTANT:
    // Always stop the loading screen.

    setLoadingAnalysis(false);

  }

}
 async function handleSearch(e) {
  e.preventDefault();

  const query = search.trim();

  if (!query) {
    return;
  }

  setSearchFocused(false);
  setLoadingAnalysis(true);
  setError("");

  try {

    // Search dynamically by ticker OR company name
    const response = await fetch(
      `${API}/search/${encodeURIComponent(query)}`
    );

    if (!response.ok) {
      throw new Error(
        "Unable to search for the stock."
      );
    }

    const data = await response.json();

    console.log(
      "Dynamic search response:",
      data
    );

    if (
      !data.found ||
      !Array.isArray(data.results) ||
      data.results.length === 0
    ) {
      throw new Error(
        `No Indian stock found for "${query}".`
      );
    }

    // Backend resolves company name → NSE ticker
    const matchedStock =
      data.results[0];

    const resolvedTicker =
      matchedStock.ticker;

    console.log(
      "Resolved ticker:",
      resolvedTicker
    );

    // Fetch complete analytics using the resolved ticker
    await selectStock(
      resolvedTicker
    );

  } catch (err) {

    console.error(
      "Dynamic search error:",
      err
    );

    setError(
      err?.message ||
      "Unable to find the stock."
    );

    setLoadingAnalysis(false);
  }
}
  // ==========================================================
  // SEARCH SUGGESTIONS
  // ==========================================================

  const filteredStocks = useMemo(() => {
    const query = search
      .trim()
      .toLowerCase();

    if (!query) {
      return stocks.slice(0, 6);
    }

    return stocks
      .filter((stock) => {
        return (
          String(stock.ticker)
            .toLowerCase()
            .includes(query) ||
          String(stock.company_name)
            .toLowerCase()
            .includes(query) ||
          String(stock.sector)
            .toLowerCase()
            .includes(query)
        );
      })
      .slice(0, 6);
  }, [search, stocks]);

  // ==========================================================
  // FORMAT FUNCTIONS
  // ==========================================================

  function isValidNumber(value) {
    return (
      value !== null &&
      value !== undefined &&
      value !== "" &&
      Number.isFinite(Number(value))
    );
  }

  function formatPrice(value) {
    if (!isValidNumber(value)) {
      return "N/A";
    }

    return `₹${Number(value).toLocaleString(
      "en-IN",
      {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }
    )}`;
  }

  function formatPercent(value) {
    if (!isValidNumber(value)) {
      return "N/A";
    }

    return `${(
      Number(value) * 100
    ).toFixed(2)}%`;
  }

  function formatDividendYield(value) {
    if (!isValidNumber(value)) {
      return "N/A";
    }

    return `${Number(value).toFixed(2)}%`;
  }

  function formatRatio(value) {
    if (!isValidNumber(value)) {
      return "N/A";
    }

    return Number(value).toFixed(2);
  }

  function formatVolume(value) {
    if (!isValidNumber(value)) {
      return "N/A";
    }

    return Math.round(
      Number(value)
    ).toLocaleString("en-IN");
  }

  // ==========================================================
  // CORRECT MARKET CAP CONVERSION
  // ==========================================================

  function formatMarketCap(value) {
    if (!isValidNumber(value)) {
      return "N/A";
    }

    const number = Number(value);

    // ₹1 Lakh Crore = ₹1,000,000,000,000
    //
    // Example:
    // ₹1,943,082,487,689
    // / ₹1,000,000,000,000
    // = ₹1.943 L Cr
    //
    // Therefore IOC displays:
    // ₹1.94 L Cr

    if (number >= 1_000_000_000_000) {
      return `₹${(
        number / 1_000_000_000_000
      ).toFixed(2)} L Cr`;
    }

    // ₹1 Crore = ₹10,000,000

    if (number >= 10_000_000) {
      return `₹${(
        number / 10_000_000
      ).toFixed(2)} Cr`;
    }

    return `₹${number.toLocaleString(
      "en-IN"
    )}`;
  }

  function formatDividend(value) {
    if (!isValidNumber(value)) {
      return "N/A";
    }

    return `₹${Number(value).toFixed(2)}`;
  }

  function formatDate(value) {
    if (!value) {
      return "N/A";
    }

    return value;
  }

  // ==========================================================
  // RISK PROFILE
  // ==========================================================

  function getRiskProfile() {
    if (!analysis) {
      return {
        label: "Not Available",
        description:
          "Select a stock to calculate its risk profile.",
      };
    }

    const volatility = Number(
      analysis.annualized_volatility
    );

    const sharpe = Number(
      analysis.sharpe_ratio
    );

    if (
      volatility < 0.2 &&
      sharpe > 0.5
    ) {
      return {
        label: "Low Risk / Strong",
        description:
          "Lower volatility with relatively strong risk-adjusted performance.",
      };
    }

    if (
      volatility > 0.3 ||
      sharpe < -0.75
    ) {
      return {
        label: "High Risk",
        description:
          "The stock shows relatively high volatility or weak risk-adjusted performance.",
      };
    }

    return {
      label: "Moderate",
      description:
        "The stock has a balanced but meaningful level of market risk.",
    };
  }

  // ==========================================================
  // PERFORMANCE DATA
  // ==========================================================

  const performanceData = useMemo(() => {
    if (!history.length) {
      return [];
    }

    const firstPrice = Number(
      history[0]?.close
    );

    if (
      !Number.isFinite(firstPrice) ||
      firstPrice === 0
    ) {
      return [];
    }

    return history.map((item) => ({
      date: item.date,
      close: item.close,
      performance:
        ((item.close - firstPrice) /
          firstPrice) *
        100,
    }));
  }, [history]);

  // ==========================================================
  // RISK / RETURN DATA
  // ==========================================================

  const riskReturnData = useMemo(() => {
    if (!analysis) {
      return [];
    }

    return [
      {
        name: analysis.ticker,
        return:
          Number(
            analysis.annualized_return
          ) * 100,
        volatility:
          Number(
            analysis.annualized_volatility
          ) * 100,
      },
    ];
 }, [analysis]);


// ==========================================================
// ADDITIONAL CHART DATA
// ==========================================================

// ----------------------------------------------------------
// MOVING AVERAGES
// ----------------------------------------------------------

const movingAverageData = useMemo(() => {

  if (!history.length) {
    return [];
  }

  const prices = history.map((item) =>
    Number(item.close)
  );

  const calculateMA = (index, period) => {

    if (index + 1 < period) {
      return null;
    }

    const values = prices.slice(
      index + 1 - period,
      index + 1
    );

    return (
      values.reduce(
        (sum, value) => sum + value,
        0
      ) / period
    );
  };

  return history.map((item, index) => ({
    date: item.date,

    close:
      Number(item.close),

    ma20:
      calculateMA(index, 20),

    ma50:
      calculateMA(index, 50),

    ma200:
      calculateMA(index, 200),
  }));

}, [history]);


// ----------------------------------------------------------
// DRAWDOWN
// ----------------------------------------------------------

const drawdownData = useMemo(() => {

  if (!history.length) {
    return [];
  }

  let runningMaximum =
    Number(history[0]?.close);

  return history.map((item) => {

    const price =
      Number(item.close);

    runningMaximum =
      Math.max(
        runningMaximum,
        price
      );

    const drawdown =
      (
        (
          price -
          runningMaximum
        ) /
        runningMaximum
      ) * 100;

    return {
      date: item.date,
      drawdown,
    };

  });

}, [history]);


// ----------------------------------------------------------
// 20-DAY ROLLING VOLATILITY
// ----------------------------------------------------------

const volatilityData = useMemo(() => {

  if (history.length < 2) {
    return [];
  }

  const returns = history.map(
    (item, index) => {

      if (index === 0) {
        return null;
      }

      const current =
        Number(item.close);

      const previous =
        Number(
          history[index - 1]?.close
        );

      if (
        !Number.isFinite(current) ||
        !Number.isFinite(previous) ||
        previous === 0
      ) {
        return null;
      }

      return (
        current / previous
      ) - 1;
    }
  );

  return history.map(
    (item, index) => {

      const start =
        Math.max(1, index - 19);

      const window =
        returns
          .slice(start, index + 1)
          .filter(
            (value) =>
              value !== null
          );

      let volatility = null;

      if (window.length > 1) {

        const mean =
          window.reduce(
            (sum, value) =>
              sum + value,
            0
          ) / window.length;

        const variance =
          window.reduce(
            (sum, value) =>
              sum +
              Math.pow(
                value - mean,
                2
              ),
            0
          ) /
          (window.length - 1);

        volatility =
          Math.sqrt(variance) *
          Math.sqrt(252) *
          100;
      }

      return {
        date: item.date,
        volatility,
      };

    }
  );

}, [history]);


// ----------------------------------------------------------
// DAILY RETURNS
// ----------------------------------------------------------

const dailyReturnData = useMemo(() => {

  if (history.length < 2) {
    return [];
  }

  return history
    .map((item, index) => {

      if (index === 0) {
        return null;
      }

      const current =
        Number(item.close);

      const previous =
        Number(
          history[index - 1]?.close
        );

      if (
        !Number.isFinite(current) ||
        !Number.isFinite(previous) ||
        previous === 0
      ) {
        return null;
      }

      return {
        date: item.date,

        return:
          (
            current / previous - 1
          ) * 100,
      };

    })
    .filter(Boolean);

}, [history]);




  const riskProfile = getRiskProfile();

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div className="app">

      {/* ====================================================
          NAVBAR
      ==================================================== */}

      <header className="navbar">

        <div className="logo">
          <span className="logo-icon">
            📈
          </span>

          <span>
            Stock Market Analytics
          </span>
        </div>

        <nav>
          <a href="#home">Home</a>
          <a href="#stocks">Stocks</a>
          <a href="#analysis">Analytics</a>
        </nav>

      </header>

      {/* ====================================================
          HERO
      ==================================================== */}

      <section
        className="hero"
        id="home"
      >

        <div className="hero-content">

          <div className="eyebrow">
            FINANCIAL ANALYTICS PLATFORM
          </div>

          <h1>
            Analyze the Indian Stock Market
          </h1>

          <p>
            Search any Indian stock and explore
            price performance, fundamentals,
            risk and return analytics.
          </p>

          <form
            className="search-box"
            onSubmit={handleSearch}
          >

            <div className="search-input-wrapper">

              <span className="search-icon">
                🔎
              </span>

              <input
                type="text"
                placeholder="Search stock e.g. TCS, WIPRO, SBIN, RELIANCE"
                value={search}
                onChange={(e) =>
                  setSearch(e.target.value)
                }
                onFocus={() =>
                  setSearchFocused(true)
                }
                onBlur={() =>
                  setTimeout(
                    () =>
                      setSearchFocused(false),
                    150
                  )
                }
              />

              {search && (
                <button
                  type="button"
                  className="clear-search"
                  onClick={() =>
                    setSearch("")
                  }
                >
                  ×
                </button>
              )}

              {searchFocused &&
                filteredStocks.length > 0 && (
                  <div className="search-suggestions">

                    {filteredStocks.map(
                      (stock) => (
                        <button
                          type="button"
                          className="suggestion-item"
                          key={stock.ticker}
                          onMouseDown={() => {
                            setSearch(
                              stock.ticker
                            );

                            setSearchFocused(
                              false
                            );

                            selectStock(
                              stock.ticker
                            );
                          }}
                        >

                          <div>
                            <strong>
                              {stock.ticker}
                            </strong>

                            <span>
                              {stock.company_name}
                            </span>
                          </div>

                          <small>
                            {stock.sector}
                          </small>

                        </button>
                      )
                    )}

                  </div>
                )}

            </div>

            <button
              type="submit"
              className="search-button"
              disabled={loadingAnalysis}
            >
              {loadingAnalysis
                ? "Loading..."
                : "Analyze"}
            </button>

          </form>

          {error && (
            <div className="error-message">
              <span>⚠️</span>
              {error}
            </div>
          )}

        </div>

      </section>

      {/* ====================================================
          MARKET OVERVIEW
      ==================================================== */}

      <section
        className="market-section"
        id="stocks"
      >

        <div className="section-header">

          <div className="eyebrow">
            MARKET
          </div>

          <h2>
            Explore Stocks
          </h2>

          <p>
            Click any stock to instantly
            open its analytics dashboard.
          </p>

        </div>

        {loadingStocks ? (
          <div className="loading-message">
            <div className="spinner"></div>
            Loading stocks...
          </div>
        ) : (
          <>
            <div className="market-toolbar">
              <span>
                {stocks.length} stocks available
              </span>

              <span>
                Click a card to analyze →
              </span>
            </div>

            <div className="stock-grid">

              {stocks.map((stock) => (
                <button
                  type="button"
                  className={`stock-card ${
                    selectedStock ===
                    stock.ticker
                      ? "selected"
                      : ""
                  }`}
                  key={stock.ticker}
                  onClick={() =>
                    selectStock(
                      stock.ticker
                    )
                  }
                >

                  <div className="stock-card-top">

                    <div className="stock-ticker">
                      {stock.ticker}
                    </div>

                    {selectedStock ===
                      stock.ticker && (
                      <span className="selected-badge">
                        Active
                      </span>
                    )}

                  </div>

                  <div className="stock-company">
                    {stock.company_name ||
                      stock.ticker}
                  </div>

                  <div className="stock-sector">
                    {stock.sector ||
                      "Unknown"}
                  </div>

                  <div className="stock-card-action">
                    View analysis
                    <span>→</span>
                  </div>

                </button>
              ))}

            </div>
          </>
        )}

      </section>

      {/* ====================================================
          ANALYSIS
      ==================================================== */}

      <section
        className="analysis-section"
        id="analysis"
      >

        {!selectedStock && (
          <div className="empty-analysis">

            <div className="empty-icon">
              📊
            </div>

            <div className="eyebrow">
              STOCK ANALYSIS
            </div>

            <h2>
              Select a stock to begin
            </h2>

            <p>
              Choose a stock card above or
              search for any Indian stock.
            </p>

          </div>
        )}

        {loadingAnalysis && (
          <div className="loading-analysis">

            <div className="spinner large"></div>

            <h3>
              Fetching stock analytics...
            </h3>

            <p>
              FastAPI is retrieving the latest
              data and preparing the analysis.
            </p>

          </div>
        )}

        {selectedStock &&
          !loadingAnalysis &&
          analysis && (

          <div className="analysis-container">

            {/* ==================================================
                STOCK HEADER
            ================================================== */}

            <div className="analysis-header">

              <div>

                <div className="eyebrow">
                  STOCK ANALYSIS
                </div>

                <div className="stock-title-row">

                  <h2>
                    {analysis.ticker}
                  </h2>

                  <span className="sector-badge">
                    {analysis.sector ||
                      "Unknown"}
                  </span>

                </div>

                <p className="company-name">
                  {analysis.company_name ||
                    analysis.ticker}
                </p>

                <p className="data-meta">

                  {analysis.industry &&
                    `${analysis.industry} • `}

                  Latest trading date:{" "}
                  {formatDate(
                    analysis.latest_trade_date
                  )}

                </p>

              </div>

              <div className="current-price">

                <span>
                  Current Price
                </span>

                <strong>
                  {formatPrice(
                    analysis.latest_price
                  )}
                </strong>

              </div>

            </div>

            {/* ==================================================
                TABS
            ================================================== */}

            <div className="analysis-tabs">

              <button
                className={
                  activeTab === "overview"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setActiveTab("overview")
                }
              >
                Overview
              </button>

              <button
                className={
                  activeTab === "charts"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setActiveTab("charts")
                }
              >
                Charts
              </button>

              <button
                className={
                  activeTab === "fundamentals"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setActiveTab(
                    "fundamentals"
                  )
                }
              >
                Fundamentals
              </button>

            </div>

            {/* ==================================================
                OVERVIEW
            ================================================== */}

            {activeTab === "overview" && (
              <div className="tab-content">

                <div className="section-title">

                  <div className="eyebrow">
                    MARKET DATA
                  </div>

                  <h3>
                    Price & Company Size
                  </h3>

                </div>

                <div className="metrics-grid four-column">

                  <MetricCard
                    title="Latest Price"
                    value={formatPrice(
                      analysis.latest_price
                    )}
                  />

                  <MetricCard
                    title="Market Cap"
                    value={formatMarketCap(
                      analysis.market_cap
                    )}
                  />

                  <MetricCard
                    title="52W High"
                    value={formatPrice(
                      analysis.fifty_two_week_high ??
                        analysis.highest_price
                    )}
                  />

                  <MetricCard
                    title="52W Low"
                    value={formatPrice(
                      analysis.fifty_two_week_low ??
                        analysis.lowest_price
                    )}
                  />

                </div>

                <div className="section-title">

                  <div className="eyebrow">
                    RISK & PERFORMANCE
                  </div>

                  <h3>
                    Financial Profile
                  </h3>

                </div>

                <div className="metrics-grid four-column">

                  <MetricCard
                    title="Annual Return"
                    value={formatPercent(
                      analysis.annualized_return
                    )}
                  />

                  <MetricCard
                    title="Annual Volatility"
                    value={formatPercent(
                      analysis.annualized_volatility
                    )}
                  />

                  <MetricCard
                    title="Maximum Drawdown"
                    value={formatPercent(
                      analysis.maximum_drawdown
                    )}
                  />

                  <MetricCard
                    title="Sharpe Ratio"
                    value={formatRatio(
                      analysis.sharpe_ratio
                    )}
                  />

                </div>

                <div className="risk-profile">

                  <div>

                    <div className="eyebrow">
                      RISK-ADJUSTED VIEW
                    </div>

                    <h3>
                      {analysis.ticker}
                      {" "}
                      Performance Profile
                    </h3>

                    <p>
                      {riskProfile.description}
                    </p>

                  </div>

                  <div className="risk-result">

                    <strong>
                      {riskProfile.label}
                    </strong>

                    <span>
                      Sharpe{" "}
                      {formatRatio(
                        analysis.sharpe_ratio
                      )}
                    </span>

                  </div>

                </div>

                <div className="insight-card">

                  <div className="insight-icon">
                    💡
                  </div>

                  <div>

                    <div className="eyebrow">
                      QUICK INSIGHT
                    </div>

                    <h3>
                      {analysis.ticker}
                      {" "}
                      Risk & Return Profile
                    </h3>

                    <p>

                      Annualized return is{" "}

                      <strong>
                        {formatPercent(
                          analysis.annualized_return
                        )}
                      </strong>

                      {" "}with annualized volatility
                      of{" "}

                      <strong>
                        {formatPercent(
                          analysis.annualized_volatility
                        )}
                      </strong>

                      {" "}and a Sharpe ratio of{" "}

                      <strong>
                        {formatRatio(
                          analysis.sharpe_ratio
                        )}
                      </strong>.

                    </p>

                  </div>

                </div>

              </div>
            )}

                        {/* ==================================================
                CHARTS
            ================================================== */}

            {activeTab === "charts" && (
              <div className="tab-content">

                {history.length > 0 ? (
                  <>

                    {/* ==================================================
                        1. CLOSING PRICE
                    ================================================== */}

                    <div className="chart-card">

                      <div className="chart-header">

                        <div>

                          <div className="eyebrow">
                            PRICE HISTORY
                          </div>

                          <h3>
                            {analysis.ticker} Closing Price
                          </h3>

                        </div>

                        <span className="chart-period">
                          1 Year
                        </span>

                      </div>

                      <div className="chart-container">

                        <ResponsiveContainer
                          width="100%"
                          height={360}
                        >

                          <LineChart
                            data={history}
                            margin={{
                              top: 10,
                              right: 20,
                              left: 0,
                              bottom: 10,
                            }}
                          >

                            <CartesianGrid
                              strokeDasharray="3 3"
                            />

                            <XAxis
                              dataKey="date"
                              tick={{
                                fontSize: 10,
                              }}
                              minTickGap={35}
                            />

                            <YAxis
                              tick={{
                                fontSize: 11,
                              }}
                            />

                            <Tooltip
                              formatter={(value) => [
                                formatPrice(value),
                                "Closing Price",
                              ]}
                            />

                            <Line
                              type="monotone"
                              dataKey="close"
                              stroke="#5267e8"
                              strokeWidth={2.5}
                              dot={false}
                              activeDot={{
                                r: 5,
                              }}
                            />

                          </LineChart>

                        </ResponsiveContainer>

                      </div>

                    </div>


                    {/* ==================================================
                        2. MOVING AVERAGES
                    ================================================== */}

                    {movingAverageData.length > 0 && (
                      <div className="chart-card">

                        <div className="chart-header">

                          <div>

                            <div className="eyebrow">
                              TECHNICAL ANALYSIS
                            </div>

                            <h3>
                              Price with Moving Averages
                            </h3>

                          </div>

                          <span className="chart-period">
                            MA20 • MA50 • MA200
                          </span>

                        </div>

                        <div className="chart-container">

                          <ResponsiveContainer
                            width="100%"
                            height={360}
                          >

                            <LineChart
                              data={movingAverageData}
                              margin={{
                                top: 10,
                                right: 20,
                                left: 0,
                                bottom: 10,
                              }}
                            >

                              <CartesianGrid
                                strokeDasharray="3 3"
                              />

                              <XAxis
                                dataKey="date"
                                tick={{
                                  fontSize: 10,
                                }}
                                minTickGap={35}
                              />

                              <YAxis
                                tick={{
                                  fontSize: 11,
                                }}
                              />

                              <Tooltip
                                formatter={(
                                  value,
                                  name
                                ) => {

                                  if (
                                    value === null ||
                                    value === undefined
                                  ) {
                                    return [
                                      "N/A",
                                      name,
                                    ];
                                  }

                                  return [
                                    formatPrice(value),
                                    name === "close"
                                      ? "Closing Price"
                                      : name === "ma20"
                                      ? "20-Day MA"
                                      : name === "ma50"
                                      ? "50-Day MA"
                                      : "200-Day MA",
                                  ];

                                }}
                              />

                              <Line
                                type="monotone"
                                dataKey="close"
                                name="close"
                                stroke="#5267e8"
                                strokeWidth={2.5}
                                dot={false}
                              />

                              <Line
                                type="monotone"
                                dataKey="ma20"
                                name="ma20"
                                stroke="#e09f3e"
                                strokeWidth={2}
                                dot={false}
                                connectNulls
                              />

                              <Line
                                type="monotone"
                                dataKey="ma50"
                                name="ma50"
                                stroke="#3a9d5d"
                                strokeWidth={2}
                                dot={false}
                                connectNulls
                              />

                              <Line
                                type="monotone"
                                dataKey="ma200"
                                name="ma200"
                                stroke="#c94c4c"
                                strokeWidth={2}
                                dot={false}
                                connectNulls
                              />

                            </LineChart>

                          </ResponsiveContainer>

                        </div>

                      </div>
                    )}


                    {/* ==================================================
                        3. DRAWDOWN
                    ================================================== */}

                    {drawdownData.length > 0 && (
                      <div className="chart-card">

                        <div className="chart-header">

                          <div>

                            <div className="eyebrow">
                              RISK ANALYTICS
                            </div>

                            <h3>
                              Drawdown
                            </h3>

                          </div>

                          <span className="chart-period">
                            From Previous Peak
                          </span>

                        </div>

                        <div className="chart-container">

                          <ResponsiveContainer
                            width="100%"
                            height={320}
                          >

                            <AreaChart
                              data={drawdownData}
                            >

                              <CartesianGrid
                                strokeDasharray="3 3"
                              />

                              <XAxis
                                dataKey="date"
                                tick={{
                                  fontSize: 10,
                                }}
                                minTickGap={35}
                              />

                              <YAxis
                                tick={{
                                  fontSize: 11,
                                }}
                                tickFormatter={(value) =>
                                  `${value.toFixed(0)}%`
                                }
                              />

                              <Tooltip
                                formatter={(value) => [
                                  `${Number(
                                    value
                                  ).toFixed(2)}%`,
                                  "Drawdown",
                                ]}
                              />

                              <Area
                                type="monotone"
                                dataKey="drawdown"
                                stroke="#c94c4c"
                                fill="#c94c4c"
                                fillOpacity={0.14}
                              />

                            </AreaChart>

                          </ResponsiveContainer>

                        </div>

                      </div>
                    )}


                    {/* ==================================================
                        4. ROLLING VOLATILITY
                    ================================================== */}

                    {volatilityData.length > 0 && (
                      <div className="chart-card">

                        <div className="chart-header">

                          <div>

                            <div className="eyebrow">
                              RISK ANALYTICS
                            </div>

                            <h3>
                              20-Day Rolling Volatility
                            </h3>

                          </div>

                          <span className="chart-period">
                            Annualized
                          </span>

                        </div>

                        <div className="chart-container">

                          
                          
                            <ResponsiveContainer
                              width="100%"
                              height={320}
                            >

                              <LineChart
                                data={volatilityData}
                              >

                                <CartesianGrid
                                  strokeDasharray="3 3"
                                />

                                <XAxis
                                  dataKey="date"
                                  tick={{
                                    fontSize: 10,
                                  }}
                                  minTickGap={35}
                                />

                                <YAxis
                                  tick={{
                                    fontSize: 11,
                                  }}
                                  tickFormatter={(value) =>
                                    `${Number(value).toFixed(0)}%`
                                  }
                                />

                                <Tooltip
                                  formatter={(value) => [
                                    `${Number(value).toFixed(2)}%`,
                                    "Rolling Volatility",
                                  ]}
                                    
                                  
                                />

                                <Line
                                  type="monotone"
                                  dataKey="volatility"
                                  name="volatility"
                                  stroke="#e09f3e"
                                  strokeWidth={2.5}
                                  dot={false}
                                  connectNulls
                                  isAnimationActive={false}
                                />

                              </LineChart>

                            </ResponsiveContainer>

                          

                        </div>

                      </div>
                    )}


                    {/* ==================================================
                        5. DAILY RETURNS
                    ================================================== */}

                    {dailyReturnData.length > 0 && (
                      <div className="chart-card">

                        <div className="chart-header">

                          <div>

                            <div className="eyebrow">
                              DAILY PERFORMANCE
                            </div>

                            <h3>
                              Daily Returns
                            </h3>

                          </div>

                          <span className="chart-period">
                            Daily %
                          </span>

                        </div>

                        <div className="chart-container">

                          <ResponsiveContainer
                            width="100%"
                            height={320}
                          >

                            <BarChart
                              data={dailyReturnData}
                            >

                              <CartesianGrid
                                strokeDasharray="3 3"
                              />

                              <XAxis
                                dataKey="date"
                                tick={{
                                  fontSize: 10,
                                }}
                                minTickGap={35}
                              />

                              <YAxis
                                tick={{
                                  fontSize: 11,
                                }}
                                tickFormatter={(value) =>
                                  `${value}%`
                                }
                              />

                              <Tooltip
                                formatter={(value) => [
                                  `${Number(
                                    value
                                  ).toFixed(2)}%`,
                                  "Daily Return",
                                ]}
                              />

                              <ReferenceLine
                                y={0}
                              />

                              <Bar
                                dataKey="return"
                                fill="#5267e8"
                              />

                            </BarChart>

                          </ResponsiveContainer>

                        </div>

                      </div>
                    )}


                    {/* ==================================================
                        6. TRADING VOLUME
                    ================================================== */}

                    {history.some(
                      (item) =>
                        Number.isFinite(
                          Number(item.volume)
                        ) &&
                        Number(item.volume) > 0
                    ) && (
                      <div className="chart-card">

                        <div className="chart-header">

                          <div>

                            <div className="eyebrow">
                              MARKET ACTIVITY
                            </div>

                            <h3>
                              Trading Volume
                            </h3>

                          </div>

                          <span className="chart-period">
                            Daily Volume
                          </span>

                        </div>

                        <div className="chart-container">

                          <ResponsiveContainer
                            width="100%"
                            height={320}
                          >

                            <BarChart
                              data={history}
                            >

                              <CartesianGrid
                                strokeDasharray="3 3"
                              />

                              <XAxis
                                dataKey="date"
                                tick={{
                                  fontSize: 10,
                                }}
                                minTickGap={35}
                              />

                              <YAxis
                                tick={{
                                  fontSize: 11,
                                }}
                                tickFormatter={(value) =>
                                  Number(value).toLocaleString(
                                    "en-IN"
                                  )
                                }
                              />

                              <Tooltip
                                formatter={(value) => [
                                  formatVolume(value),
                                  "Volume",
                                ]}
                              />

                              <Bar
                                dataKey="volume"
                                fill="#5267e8"
                              />

                            </BarChart>

                          </ResponsiveContainer>

                        </div>

                      </div>
                    )}


                    {/* ==================================================
                        7. PRICE MOVEMENT
                    ================================================== */}

                    {performanceData.length > 0 && (
                      <div className="chart-card">

                        <div className="chart-header">

                          <div>

                            <div className="eyebrow">
                              PERFORMANCE
                            </div>

                            <h3>
                              Price Movement
                            </h3>

                          </div>

                          <span className="chart-period">
                            Base = 0%
                          </span>

                        </div>

                        <div className="chart-container">

                          <ResponsiveContainer
                            width="100%"
                            height={320}
                          >

                            <AreaChart
                              data={performanceData}
                            >

                              <CartesianGrid
                                strokeDasharray="3 3"
                              />

                              <XAxis
                                dataKey="date"
                                tick={{
                                  fontSize: 10,
                                }}
                                minTickGap={35}
                              />

                              <YAxis
                                tick={{
                                  fontSize: 11,
                                }}
                                tickFormatter={(value) =>
                                  `${value}%`
                                }
                              />

                              <Tooltip
                                formatter={(value) => [
                                  `${Number(
                                    value
                                  ).toFixed(2)}%`,
                                  "Return",
                                ]}
                              />

                              <Area
                                type="monotone"
                                dataKey="performance"
                                stroke="#5267e8"
                                fill="#5267e8"
                                fillOpacity={0.16}
                              />

                            </AreaChart>

                          </ResponsiveContainer>

                        </div>

                      </div>
                    )}

                    {/* =================================================
    TRADING VOLUME
================================================= */}

<div className="chart-card">

  <div className="chart-header">

    <div>

      <div className="eyebrow">
        MARKET ACTIVITY
      </div>

      <h3>
        {analysis.ticker}
        {" "}
        Trading Volume
      </h3>

    </div>

    <span className="chart-period">
      1 Year
    </span>

  </div>


  <div className="chart-container">

    <ResponsiveContainer
      width="100%"
      height={320}
    >

      <BarChart
        data={history}
        margin={{
          top: 10,
          right: 20,
          left: 0,
          bottom: 10,
        }}
      >

        <CartesianGrid
          strokeDasharray="3 3"
        />


        <XAxis
          dataKey="date"
          tick={{
            fontSize: 10,
          }}
          minTickGap={35}
        />


        <YAxis
          tick={{
            fontSize: 11,
          }}
          tickFormatter={(value) =>
            Number(value).toLocaleString(
              "en-IN",
              {
                notation: "compact",
                maximumFractionDigits: 1,
              }
            )
          }
        />


        <Tooltip
          formatter={(value) => [
            formatVolume(value),
            "Trading Volume",
          ]}
        />


        <Bar
          dataKey="volume"
          name="Trading Volume"
          fill="#5267e8"
          radius={[
            3,
            3,
            0,
            0,
          ]}
        />

      </BarChart>

    </ResponsiveContainer>

  </div>

</div>





                    {/* ==================================================
                        8. RISK VS RETURN
                    ================================================== */}

                    <div className="chart-card">

                      <div className="chart-header">

                        <div>

                          <div className="eyebrow">
                            RISK ANALYTICS
                          </div>

                          <h3>
                            Risk vs Return
                          </h3>

                        </div>

                      </div>

                      <div className="chart-container">

                        <ResponsiveContainer
                          width="100%"
                          height={320}
                        >

                          <BarChart
                            data={riskReturnData}
                          >

                            <CartesianGrid
                              strokeDasharray="3 3"
                            />

                            <XAxis
                              dataKey="name"
                            />

                            <YAxis
                              tickFormatter={(value) =>
                                `${value}%`
                              }
                            />

                            <Tooltip
                              formatter={(
                                value,
                                name
                              ) => [
                                `${Number(
                                  value
                                ).toFixed(2)}%`,
                                name === "return"
                                  ? "Annual Return"
                                  : "Annual Volatility",
                              ]}
                            />

                            <Bar
                              dataKey="return"
                              name="return"
                              fill="#5267e8"
                              radius={[
                                6,
                                6,
                                0,
                                0,
                              ]}
                            />

                            <Bar
                              dataKey="volatility"
                              name="volatility"
                              fill="#9aa4d8"
                              radius={[
                                6,
                                6,
                                0,
                                0,
                              ]}
                            />

                          </BarChart>

                        </ResponsiveContainer>

                      </div>

                    </div>

                  </>
                ) : (
                  <div className="empty-analysis">

                    <div className="empty-icon">
                      📈
                    </div>

                    <h3>
                      Historical chart unavailable
                    </h3>

                    <p>
                      No historical price data was
                      returned for this stock.
                    </p>

                  </div>
                )}

              </div>
            )}

            {/* ==================================================
                FUNDAMENTALS
            ================================================== */}

            {activeTab === "fundamentals" && (
              <div className="tab-content">

                <div className="section-title">

                  <div className="eyebrow">
                    FUNDAMENTALS
                  </div>

                  <h3>
                    Valuation & Dividend
                  </h3>

                </div>

                <div className="metrics-grid four-column">

                  <MetricCard
                    title="Market Cap"
                    value={formatMarketCap(
                      analysis.market_cap
                    )}
                  />

                  <MetricCard
                    title="P/E Ratio"
                    value={formatRatio(
                      analysis.pe_ratio
                    )}
                  />

                  <MetricCard
                    title="Dividend Yield"
                    value={formatDividendYield(
                      analysis.dividend_yield
                    )}
                  />

                  <MetricCard
                    title="Annual Dividend"
                    value={formatDividend(
                      analysis.annual_dividend
                    )}
                  />

                  <MetricCard
                    title="Latest Dividend"
                    value={formatDividend(
                      analysis.latest_dividend
                    )}
                  />

                  <MetricCard
                    title="Quarterly Dividend (Normalized)"
                    value={formatDividend(
                      analysis.quarterly_dividend
                    )}
                  />

                  <MetricCard
                    title="52-Week High"
                    value={formatPrice(
                      analysis.fifty_two_week_high ??
                        analysis.highest_price
                    )}
                  />

                  <MetricCard
                    title="52-Week Low"
                    value={formatPrice(
                      analysis.fifty_two_week_low ??
                        analysis.lowest_price
                    )}
                  />

                </div>

                <div className="fundamentals-grid">

                  <div className="fundamental-info-card">
                    <span>Company</span>
                    <strong>
                      {analysis.company_name ||
                        "N/A"}
                    </strong>
                  </div>

                  <div className="fundamental-info-card">
                    <span>Sector</span>
                    <strong>
                      {analysis.sector ||
                        "Unknown"}
                    </strong>
                  </div>

                  <div className="fundamental-info-card">
                    <span>Industry</span>
                    <strong>
                      {analysis.industry ||
                        "Unknown"}
                    </strong>
                  </div>

                  <div className="fundamental-info-card">
                    <span>Average Volume</span>
                    <strong>
                      {formatVolume(
                        analysis.average_volume
                      )}
                    </strong>
                  </div>

                  <div className="fundamental-info-card">
                    <span>Daily Volatility</span>
                    <strong>
                      {formatPercent(
                        analysis.daily_volatility
                      )}
                    </strong>
                  </div>

                  <div className="fundamental-info-card">
                    <span>
                      Latest Trading Date
                    </span>
                    <strong>
                      {formatDate(
                        analysis.latest_trade_date
                      )}
                    </strong>
                  </div>

                </div>

                <div className="fundamental-note">

                  <span>
                    ℹ️
                  </span>

                  <p>
                    Market and fundamental information
                    is retrieved dynamically through the
                    FastAPI backend. Dividend yield is
                    calculated from trailing 12-month
                    dividend payments and current price.
                    Quarterly dividend is a normalized
                    annual dividend divided by four.
                  </p>

                </div>

              </div>
            )}

          </div>
        )}

      </section>

      {/* ====================================================
          FOOTER
      ==================================================== */}

      <footer className="footer">

        <h3>
          Stock Market Analytics
        </h3>

        <p>
          Python • FastAPI • React • MySQL •
          Power BI • Tableau • Excel
        </p>

        <span>
          Data-driven financial analysis platform
        </span>

      </footer>

    </div>
  );
}


// ============================================================
// METRIC CARD
// ============================================================

function MetricCard({
  title,
  value,
}) {
  return (
    <div className="metric-card">

      <div className="metric-title">
        {title}
      </div>

      <div className="metric-value">
        {value}
      </div>

    </div>
  );
}

export default App;