"""
Tests fuer DataProvider-Modul (yfinance gemockt)
"""
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime


@pytest.fixture
def sample_df():
    """Erstellt einen minimalen OHLCV-DataFrame fuer Tests."""
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame({
        "Open":   [100.0, 101.0, 102.0, 103.0, 104.0],
        "High":   [105.0, 106.0, 107.0, 108.0, 109.0],
        "Low":    [ 99.0, 100.0, 101.0, 102.0, 103.0],
        "Close":  [102.0, 103.0, 104.0, 105.0, 106.0],
        "Volume": [1000,  2000,  3000,  4000,  5000],
    }, index=dates)


class TestGetMarketData:
    def test_returns_dataframe_on_success(self, sample_df):
        """get_market_data gibt einen DataFrame zurueck wenn yfinance Daten liefert."""
        with patch("yfinance.download", return_value=sample_df):
            from core.data_provider import DataProvider
            DataProvider.get_market_data.cache_clear()
            result = DataProvider.get_market_data("AAPL", period="1y")
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_returns_none_on_empty_df(self):
        """get_market_data gibt None zurueck wenn yfinance einen leeren DataFrame liefert."""
        empty_df = pd.DataFrame()
        with patch("yfinance.download", return_value=empty_df):
            from core.data_provider import DataProvider
            DataProvider.get_market_data.cache_clear()
            result = DataProvider.get_market_data("INVALID_TICKER_XYZ")
        assert result is None

    def test_returns_none_on_exception(self, caplog):
        """get_market_data gibt None zurueck bei einer Exception von yfinance."""
        with patch("yfinance.download", side_effect=Exception("Network error")):
            from core.data_provider import DataProvider
            DataProvider.get_market_data.cache_clear()
            with caplog.at_level("WARNING"):
                result = DataProvider.get_market_data("AAPL")
        assert result is None
        assert "Fehler beim Laden der Daten fuer AAPL" in caplog.text

    def test_required_columns_present(self, sample_df):
        """get_market_data gibt DataFrame mit allen OHLCV-Spalten zurueck."""
        with patch("yfinance.download", return_value=sample_df):
            from core.data_provider import DataProvider
            DataProvider.get_market_data.cache_clear()
            result = DataProvider.get_market_data("AAPL")
        assert result is not None
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            assert col in result.columns

    def test_missing_required_column_returns_none(self):
        """get_market_data gibt None zurueck wenn Pflicht-Spalte fehlt."""
        incomplete_df = pd.DataFrame({
            "Open": [100.0], "High": [105.0], "Low": [99.0], "Close": [102.0]
            # Volume fehlt
        }, index=pd.date_range("2024-01-01", periods=1))
        with patch("yfinance.download", return_value=incomplete_df):
            from core.data_provider import DataProvider
            DataProvider.get_market_data.cache_clear()
            result = DataProvider.get_market_data("AAPL")
        assert result is None


class TestGetTickerInfo:
    def test_returns_dict_on_success(self):
        """get_ticker_info gibt ein Dict mit Ticker-Metadaten zurueck."""
        mock_info = {"shortName": "Apple Inc.", "sector": "Technology", "marketCap": 3e12}
        mock_ticker = MagicMock()
        mock_ticker.info = mock_info
        with patch("yfinance.Ticker", return_value=mock_ticker):
            from core.data_provider import DataProvider
            DataProvider.get_ticker_info.cache_clear()
            result = DataProvider.get_ticker_info("AAPL")
        assert isinstance(result, dict)
        assert result.get("shortName") == "Apple Inc."

    def test_returns_empty_dict_on_exception(self, caplog):
        """get_ticker_info gibt leeres Dict zurueck bei Exception."""
        with patch("yfinance.Ticker", side_effect=Exception("Timeout")):
            from core.data_provider import DataProvider
            DataProvider.get_ticker_info.cache_clear()
            with caplog.at_level(logging.WARNING, logger="core.data_provider"):
                result = DataProvider.get_ticker_info("AAPL")
        assert result == {}
        assert "Ticker-Info fuer AAPL konnte nicht geladen werden" in caplog.text

    def test_returns_empty_dict_when_info_is_none(self):
        """get_ticker_info gibt leeres Dict zurueck wenn info None ist."""
        mock_ticker = MagicMock()
        mock_ticker.info = None
        with patch("yfinance.Ticker", return_value=mock_ticker):
            from core.data_provider import DataProvider
            DataProvider.get_ticker_info.cache_clear()
            result = DataProvider.get_ticker_info("UNKNOWN")
        assert result == {}


class TestGetNews:
    def test_returns_news_list(self):
        """get_news gibt eine Liste von News-Dicts zurueck."""
        mock_news = [
            {"title": "Apple hits record", "link": "https://example.com/1"},
            {"title": "New iPhone launch", "link": "https://example.com/2"},
        ]
        mock_ticker = MagicMock()
        mock_ticker.news = mock_news
        with patch("yfinance.Ticker", return_value=mock_ticker):
            from core.data_provider import DataProvider
            DataProvider.get_news.cache_clear()
            result = DataProvider.get_news("AAPL", limit=5)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["title"] == "Apple hits record"

    def test_respects_limit(self):
        """get_news liefert maximal limit Eintraege zurueck."""
        mock_news = [{"title": f"News {i}"} for i in range(10)]
        mock_ticker = MagicMock()
        mock_ticker.news = mock_news
        with patch("yfinance.Ticker", return_value=mock_ticker):
            from core.data_provider import DataProvider
            DataProvider.get_news.cache_clear()
            result = DataProvider.get_news("AAPL", limit=3)
        assert len(result) == 3

    def test_returns_empty_list_on_exception(self, caplog):
        """get_news gibt leere Liste zurueck bei Exception."""
        with patch("yfinance.Ticker", side_effect=Exception("Timeout")):
            from core.data_provider import DataProvider
            DataProvider.get_news.cache_clear()
            with caplog.at_level(logging.WARNING, logger="core.data_provider"):
                result = DataProvider.get_news("AAPL")
        assert result == []
        assert "News fuer AAPL konnten nicht geladen werden" in caplog.text


class TestGetCurrentPrice:
    def test_get_current_price_with_2d_history(self):
        """get_current_price berechnet Preis und Aenderung aus 2-Tages-History."""
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        hist_df = pd.DataFrame({"Close": [100.0, 105.0]}, index=dates)
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = hist_df
        with patch("yfinance.Ticker", return_value=mock_ticker):
            from core.data_provider import DataProvider
            result = DataProvider.get_current_price("AAPL")
        assert result is not None
        price, change, change_pct = result
        assert price == pytest.approx(105.0)
        assert change == pytest.approx(5.0)
        assert change_pct == pytest.approx(5.0)

    def test_get_current_price_returns_none_on_empty_history(self):
        """get_current_price gibt None zurueck wenn keine History-Daten vorhanden."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        with patch("yfinance.Ticker", return_value=mock_ticker):
            from core.data_provider import DataProvider
            result = DataProvider.get_current_price("UNKNOWN")
        assert result is None

    def test_get_current_price_logs_exception(self, caplog):
        """get_current_price protokolliert den Fallback bei unerwarteten Fehlern."""
        with patch("yfinance.Ticker", side_effect=Exception("Timeout")):
            from core.data_provider import DataProvider
            with caplog.at_level(logging.WARNING, logger="core.data_provider"):
                result = DataProvider.get_current_price("AAPL")
        assert result is None
        assert "Aktueller Preis fuer AAPL konnte nicht geladen werden" in caplog.text


class TestGetMultipleTickers:
    def test_get_multiple_tickers_with_multiindex(self):
        """get_multiple_tickers parst MultiIndex-DataFrame und gibt {ticker: df} zurueck."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        columns = pd.MultiIndex.from_product(
            [["AAPL", "MSFT"], ["Open", "High", "Low", "Close", "Volume"]]
        )
        data = {
            ("AAPL", "Open"): [100.0] * 5, ("AAPL", "High"): [105.0] * 5,
            ("AAPL", "Low"): [99.0] * 5,  ("AAPL", "Close"): [102.0] * 5,
            ("AAPL", "Volume"): [1000] * 5,
            ("MSFT", "Open"): [200.0] * 5, ("MSFT", "High"): [205.0] * 5,
            ("MSFT", "Low"): [199.0] * 5,  ("MSFT", "Close"): [202.0] * 5,
            ("MSFT", "Volume"): [2000] * 5,
        }
        multi_df = pd.DataFrame(data, index=dates)
        with patch("yfinance.download", return_value=multi_df):
            from core.data_provider import DataProvider
            DataProvider.get_multiple_tickers.cache_clear()
            result = DataProvider.get_multiple_tickers(("AAPL", "MSFT"))
        assert isinstance(result, dict)
        assert "AAPL" in result
        assert "MSFT" in result
        assert isinstance(result["AAPL"], pd.DataFrame)


class TestAdditionalFallbackLogging:
    def test_validate_ticker_logs_exception(self, caplog):
        """validate_ticker gibt False zurueck und protokolliert API-Fehler."""
        with patch("yfinance.download", side_effect=Exception("Network error")):
            from core.data_provider import DataProvider
            with caplog.at_level(logging.WARNING, logger="core.data_provider"):
                result = DataProvider.validate_ticker("AAPL")
        assert result is False
        assert "Ticker-Validierung fuer AAPL fehlgeschlagen" in caplog.text

    def test_get_financials_logs_exception(self, caplog):
        """get_financials gibt ein leeres Dict zurueck und protokolliert Fehler."""
        with patch("yfinance.Ticker", side_effect=Exception("Timeout")):
            from core.data_provider import DataProvider
            with caplog.at_level(logging.WARNING, logger="core.data_provider"):
                result = DataProvider.get_financials("AAPL")
        assert result == {}
        assert "Finanzberichte fuer AAPL konnten nicht geladen werden" in caplog.text


class TestDropnaEdgeCases:
    def test_dropna_all_nan_returns_none_or_empty(self):
        """get_market_data gibt None oder leeren DataFrame zurueck wenn alle Werte NaN."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        nan_df = pd.DataFrame({
            "Open":   [np.nan] * 3, "High":   [np.nan] * 3,
            "Low":    [np.nan] * 3, "Close":  [np.nan] * 3,
            "Volume": [np.nan] * 3,
        }, index=dates)
        with patch("yfinance.download", return_value=nan_df):
            from core.data_provider import DataProvider
            DataProvider.get_market_data.cache_clear()
            result = DataProvider.get_market_data("NAN_TICKER_TEST")
        # Nach dropna() ist der DataFrame leer - entweder None oder empty df
        assert result is None or (isinstance(result, pd.DataFrame) and result.empty)


class TestCacheBehavior:
    def test_cache_prevents_duplicate_api_calls(self):
        """Gleicher Ticker + gleiche Parameter -> yfinance.download nur einmal aufgerufen."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        sample_df = pd.DataFrame({
            "Open":   [100.0] * 5, "High":   [105.0] * 5,
            "Low":    [99.0] * 5,  "Close":  [102.0] * 5,
            "Volume": [1000] * 5,
        }, index=dates)
        call_count = {"n": 0}

        def counting_download(*args, **kwargs):
            call_count["n"] += 1
            return sample_df

        with patch("yfinance.download", side_effect=counting_download):
            from core.data_provider import DataProvider
            DataProvider.get_market_data.cache_clear()
            DataProvider.get_market_data("CACHE_TEST", period="1y")
            DataProvider.get_market_data("CACHE_TEST", period="1y")
        assert call_count["n"] == 1, "Cache sollte zweiten API-Call verhindern"
