# Third-Party Licenses & Level 1 SBOM Inventory

**Project:** `FinancialProof` (Local-First Financial Market Analysis & Statistical Pattern Detection)  
**License:** [MIT License](LICENSE)  
**Audit Date:** 2026-09-22  
**Repository:** [assistassets-ai/FinancialProof](https://github.com/assistassets-ai/FinancialProof)  
**Organization:** [assistassets-ai](https://github.com/assistassets-ai)  
**Umbrella Ecosystem:** [open-bricks](https://github.com/open-bricks)  

---

## Runtime Architecture & Zero-Cloud Core

`FinancialProof` is a local-first financial market data analysis dashboard built with Python 3.11+ and Streamlit. The application runs entirely on the user's workstation, stores persistent state (watchlists, strategy presets, job queue history, and analysis results) in a local SQLite database (`data/financial_proof.db`), and exposes an offline PWA companion (`web_companion/`) that operates with zero network egress.

---

## Direct Runtime Dependencies

All direct runtime dependencies are distributed under permissive open-source licenses (MIT, Apache-2.0, BSD-3-Clause, PSFL). No viral copyleft (GPL, AGPL) components are bundled into the distribution:

| Component / Package | Version Constraint | License | Project URL | Purpose |
|---|---|---|---|---|
| **`streamlit`** | `>=1.57.0,<2.0.0` | Apache-2.0 | [streamlit/streamlit](https://github.com/streamlit/streamlit) | Reactive web UI framework for the local analytical dashboard. |
| **`yfinance`** | `>=1.4.0,<2.0.0` | Apache-2.0 | [ranaroussi/yfinance](https://github.com/ranaroussi/yfinance) | Public market data extraction interface with token-bucket rate limiting. |
| **`pandas`** | `>=2.0.0,<4.0.0` | BSD-3-Clause | [pandas-dev/pandas](https://github.com/pandas-dev/pandas) | High-performance data manipulation, OHLCV time series structures. |
| **`numpy`** | `>=1.24.0,<3.0.0` | BSD-3-Clause | [numpy/numpy](https://github.com/numpy/numpy) | Array math, statistical computations, Monte Carlo random walks. |
| **`plotly`** | `>=6.7.0,<7.0.0` | MIT | [plotly/plotly.py](https://github.com/plotly/plotly.py) | Interactive financial charts (candlesticks, indicator subplots). |
| **`statsmodels`** | `>=0.14.6,<1.0.0` | BSD-3-Clause | [statsmodels/statsmodels](https://github.com/statsmodels/statsmodels) | Econometric time series modeling, ARIMA estimation, autocorrelation. |
| **`scipy`** | `>=1.11.0,<2.0.0` | BSD-3-Clause | [scipy/scipy](https://github.com/scipy/scipy) | Scientific computing, optimization, statistical distributions. |
| **`arch`** | `>=6.2.0,<9.0.0` | NCSA / BSD | [bashtage/arch](https://github.com/bashtage/arch) | Volatility estimation, ARCH/GARCH modeling for historical risk. |
| **`scikit-learn`** | `>=1.4.0,<1.10.0` | BSD-3-Clause | [scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn) | Random Forest classifiers, preprocessing, pipeline transformers. |
| **`tensorflow`** | `>=2.21.0,<3.0.0` | Apache-2.0 | [tensorflow/tensorflow](https://github.com/tensorflow/tensorflow) | Optional deep learning pattern recognition network. |
| **`transformers`** | `>=5.9.0,<6.0.0` | Apache-2.0 | [huggingface/transformers](https://github.com/huggingface/transformers) | Optional NLP pipeline for sentiment extraction from financial news. |
| **`torch`** | `>=2.0.0,<3.0.0` | BSD-3-Clause | [pytorch/pytorch](https://github.com/pytorch/pytorch) | Tensor backend supporting machine learning and embedding workflows. |
| **`requests`** | `>=2.31.0,<3.0.0` | Apache-2.0 | [psf/requests](https://github.com/psf/requests) | HTTP client for market news and web research agent routines. |
| **`beautifulsoup4`**| `>=4.14.3,<5.0.0` | MIT | [wention/BeautifulSoup4](https://git.launchpad.net/beautifulsoup) | HTML parsing for web research headlines and article extracts. |
| **`tweepy`** | `>=4.14.0,<5.0.0` | MIT | [tweepy/tweepy](https://github.com/tweepy/tweepy) | Optional social sentiment ingestion client (inactive by default). |
| **`google-api-python-client`** | `>=2.100.0,<3.0.0` | Apache-2.0 | [googleapis/google-api-python-client](https://github.com/googleapis/google-api-python-client) | Optional Google search integration for research enrichment. |
| **`cryptography`** | `>=48.0.0,<50.0.0` | Apache-2.0 / BSD | [pyca/cryptography](https://github.com/pyca/cryptography) | Fernet symmetric authenticated encryption for local secret storage. |
| **`python-dotenv`** | `>=1.2.2,<2.0.0` | BSD-3-Clause | [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv) | Local `.env` file parsing without environment pollution. |

---

## Development, Testing & Verification Dependencies

The following tools are used strictly during development, static analysis, and automated CI pipelines:

| Tool / Framework | Version / Scope | License | Project URL | Purpose |
|---|---|---|---|---|
| **pytest** | `>=8.0.0` | MIT | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) | Automated unit, regression, and metadata test execution. |
| **ruff** | `>=0.5.0` | MIT / Apache-2.0 | [astral-sh/ruff](https://github.com/astral-sh/ruff) | High-performance Python linter and code formatting enforcement. |
| **Node.js test runner** | `>=20.0.0` (built-in) | MIT | [nodejs.org](https://nodejs.org) | Zero-dependency test runner for the offline PWA companion (`web_companion`). |

---

## Zero-Copyleft Guarantee & Unprivileged Execution

- **Zero-Copyleft Guarantee:** All analytical code, UI components, job queue dispatchers, indicators, and launcher scripts in this repository are governed strictly by the permissive [MIT License](LICENSE). No GPL, AGPL, or viral copyleft code is bundled into the distribution.
- **Unprivileged User Mode (`RunAsInvoker`):** `FinancialProof` operates strictly within the unprivileged user context. No administrative elevation, Windows service installation, root access, or registry manipulation is required.
- **Data Isolation:** All user data, watchlists, API keys, and analysis caches are isolated inside the local working directory (`data/`) and excluded from Git versioning via `.gitignore`.

---

## Governance & Runtime Invariants

`FinancialProof` implements and adheres to ten foundational governance and runtime invariants:

| Invariant | Category | Description | Verification Method |
|---|---|---|---|
| `INV-LOCAL-01` | Local-First & Zero Egress | All state, databases, and analysis run locally; zero analytics or telemetry egress. | `tests/test_database.py` & `SECURITY.md` |
| `INV-NOADV-02` | No Financial Advice Gate | § 32 KWG / § 2 Abs. 9 WpHG 4-checkbox acknowledgement mandatory before runtime analysis. | `ui/disclaimer_widget.py` & `tests/test_ui_interactions.py` |
| `INV-RUNAS-03` | Unprivileged User Mode | Runs strictly in user space (`RunAsInvoker`) without administrative elevation. | `build_exe.bat` & `SECURITY.md` |
| `INV-RATE-04` | Token-Bucket Rate Limiting | Configurable throttling, capacity governance, and telemetry on external API calls. | `core/rate_limiter.py` & `tests/test_rate_limiter.py` |
| `INV-SQLITE-05` | SQLite Local Persistence | Watchlists, presets, job queue, and run logs stored locally with transactional ACID integrity. | `core/database.py` & `tests/test_database.py` |
| `INV-EXPORT-06` | Redacted Portable Export | `financialproof-workspace-v1.json` workspace export automatically strips secrets and API keys. | `tests/test_workspace_export.py` & `EXPORTFORMAT.md` |
| `INV-PWA-07` | Offline PWA Companion | Standalone browser companion operates 100% offline with zero external network requests. | `web_companion/tests/` (151 tests) |
| `INV-SEC-08` | Secret Quarantine & Encryption | Fernet symmetric authenticated encryption for optional API keys; `.env` quarantined. | `config.py` & `tests/test_config.py` |
| `INV-DOCS-09` | Bilingual Documentation Parity | Complete 18-point structural and anchor parity between English (`README.md`) and German (`README_de.md`). | `tests/test_metadata.py` |
| `INV-SLA-10` | 48-Hour Security Response SLA & § 521 BGB | Initial triage for vulnerabilities within 48h; statutory gift liability limited to intent and gross negligence. | `SECURITY.md` & `README.md` |
