"""
FinancialProof - ARIMA Zeitreihenanalyse
Prognosen basierend auf AutoRegressive Integrated Moving Average
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import warnings

# Unterdrücke statsmodels Warnungen
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

from analysis.base import (
    BaseAnalyzer, AnalysisResult, AnalysisParameters,
    AnalysisCategory, AnalysisTimeframe
)
from analysis.registry import AnalysisRegistry


@AnalysisRegistry.register
class ARIMAAnalyzer(BaseAnalyzer):
    """
    ARIMA-basierte Zeitreihenanalyse für Kursprognosen.

    Verwendet automatische Parameteroptimierung (auto_arima ähnlich)
    um die besten ARIMA-Parameter zu finden.
    """

    name = "arima"
    display_name = "Zeitreihenanalyse (ARIMA)"
    category = AnalysisCategory.STATISTICAL
    description = "Prognostiziert zukünftige Kurse basierend auf historischen Mustern"
    estimated_duration = 30
    min_data_points = 60

    supported_timeframes = [
        AnalysisTimeframe.SHORT,
        AnalysisTimeframe.MEDIUM,
        AnalysisTimeframe.LONG
    ]

    # Forecast-Horizonte in Tagen
    FORECAST_DAYS = {
        AnalysisTimeframe.SHORT: 7,
        AnalysisTimeframe.MEDIUM: 30,
        AnalysisTimeframe.LONG: 90
    }

    @classmethod
    def get_parameter_schema(cls) -> Dict[str, Any]:
        """Return JSON schema for analysis parameters.

        Returns:
            Dict containing a JSON Schema object describing all configurable
            parameters with their types, defaults, and constraints.
        """
        return {
            "type": "object",
            "properties": {
                "timeframe": {
                    "type": "string",
                    "enum": ["short", "medium", "long"],
                    "default": "medium",
                    "description": "Prognosehorizont"
                },
                "confidence_interval": {
                    "type": "number",
                    "default": 0.95,
                    "minimum": 0.8,
                    "maximum": 0.99,
                    "description": "Konfidenzintervall (0.8-0.99)"
                }
            }
        }

    async def analyze(self, params: AnalysisParameters) -> AnalysisResult:
        """Führt die ARIMA-Analyse durch"""
        symbol = params.symbol
        data = params.data
        timeframe = params.timeframe

        # Validierung
        errors = self.validate_data(data)
        if errors:
            return self.create_empty_result(self.name, symbol, errors[0])

        self.set_progress(10)

        try:
            # Daten vorbereiten
            close = data['Close'].dropna()

            # ARIMA-Modell erstellen und fitten
            self.set_progress(30)
            model_result = self._fit_arima(close)

            if model_result is None:
                return self.create_empty_result(
                    self.name, symbol,
                    "ARIMA-Modell konnte nicht erstellt werden"
                )

            self.set_progress(60)

            # Prognose erstellen
            forecast_days = self.FORECAST_DAYS.get(timeframe, 30)
            confidence = params.custom_params.get('confidence_interval', 0.95)

            forecast, conf_int = self._forecast(
                model_result, forecast_days, confidence
            )

            self.set_progress(80)

            # Ergebnisse aufbereiten
            result = self._build_result(
                symbol, close, forecast, conf_int,
                model_result, timeframe
            )

            self.set_progress(100)
            return result

        except Exception as e:
            return self.create_empty_result(self.name, symbol, str(e))

    def _fit_arima(self, data: pd.Series) -> Any:
        """
        Fittet ein ARIMA-Modell mit automatischer Parametersuche.
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
            from statsmodels.tsa.stattools import adfuller

            # Stationaritätstest
            adf_result = adfuller(data.values)
            is_stationary = adf_result[1] < 0.05

            # Differenzierungsordnung bestimmen
            d = 0 if is_stationary else 1

            # Grid Search für p, q (vereinfacht)
            best_aic = np.inf
            best_model = None
            best_order = (1, d, 1)

            for p in range(0, 4):
                for q in range(0, 4):
                    if p == 0 and q == 0:
                        continue
                    try:
                        model = ARIMA(data, order=(p, d, q))
                        fitted = model.fit()
                        if fitted.aic < best_aic:
                            best_aic = fitted.aic
                            best_model = fitted
                            best_order = (p, d, q)
                    except Exception:
                        continue

            if best_model is None:
                # Fallback auf Standard-ARIMA
                model = ARIMA(data, order=(1, d, 1))
                best_model = model.fit()

            # Speichere Order für später
            best_model._best_order = best_order

            return best_model

        except ImportError:
            # Fallback ohne statsmodels
            return self._simple_forecast_model(data)
        except Exception as e:
            print(f"ARIMA Fit Error: {e}")
            return None

    def _simple_forecast_model(self, data: pd.Series):
        """
        Einfaches Fallback-Modell wenn statsmodels nicht verfügbar.
        Verwendet exponentielles Glätten.
        """
        class SimpleForecast:
            """Fallback forecast model using exponential smoothing."""

            def __init__(self, data):
                self.data = data
                self.alpha = 0.3  # Glättungsfaktor
                self._best_order = (0, 0, 0)

            def forecast(self, steps):
                """Generate point forecasts using exponential trend smoothing.

                Args:
                    steps: Number of future time steps to forecast.

                Returns:
                    numpy array of forecasted values.
                """
                # Exponentielles Glätten
                forecast = []
                last = self.data.iloc[-1]
                trend = self.data.diff().iloc[-10:].mean()

                for i in range(steps):
                    next_val = last + trend
                    forecast.append(next_val)
                    last = next_val

                return np.array(forecast)

            def get_forecast(self, steps, alpha=0.05):
                """Generate forecasts with confidence intervals.

                Args:
                    steps: Number of future time steps to forecast.
                    alpha: Significance level (default 0.05 = 95% CI).

                Returns:
                    ForecastResult with predicted_mean and conf_int attributes.
                """
                pred = self.forecast(steps)
                # Konfidenzintervall basierend auf historischer Volatilität
                std = self.data.pct_change().std() * self.data.iloc[-1]
                z = 1.96  # 95% Konfidenz

                conf_int = np.array([
                    [p - z * std * np.sqrt(i+1), p + z * std * np.sqrt(i+1)]
                    for i, p in enumerate(pred)
                ])

                class ForecastResult:
                    """Minimal forecast result container compatible with statsmodels API."""

                    def __init__(self, pred, conf):
                        self.predicted_mean = pred
                        self.conf_int = lambda: conf

                return ForecastResult(pred, conf_int)

        return SimpleForecast(data)

    def _forecast(
        self,
        model,
        steps: int,
        confidence: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Erstellt Prognose mit Konfidenzintervall"""
        try:
            alpha = 1 - confidence
            forecast_result = model.get_forecast(steps=steps, alpha=alpha)

            forecast = forecast_result.predicted_mean
            conf_int = forecast_result.conf_int()

            return np.array(forecast), np.array(conf_int)

        except Exception as e:
            print(f"Forecast error: {e}")
            # Fallback: Lineare Extrapolation
            last_price = model.data.iloc[-1] if hasattr(model, 'data') else 100
            trend = 0.001  # Minimaler Aufwärtstrend
            forecast = np.array([last_price * (1 + trend * i) for i in range(1, steps + 1)])
            std = last_price * 0.02
            conf_int = np.array([[f - 2*std, f + 2*std] for f in forecast])
            return forecast, conf_int

    def _build_result(
        self,
        symbol: str,
        historical: pd.Series,
        forecast: np.ndarray,
        conf_int: np.ndarray,
        model,
        timeframe: AnalysisTimeframe
    ) -> AnalysisResult:
        """Baut das Analyse-Ergebnis zusammen"""
        current_price = historical.iloc[-1]
        forecast_end = forecast[-1]
        change_pct = ((forecast_end - current_price) / current_price) * 100

        # Trend bestimmen
        if change_pct > 5:
            trend = "bullish"
            recommendation = "buy"
        elif change_pct < -5:
            trend = "bearish"
            recommendation = "sell"
        else:
            trend = "neutral"
            recommendation = "hold"

        # Konfidenz basierend auf Modellgüte
        spread = (conf_int[-1, 1] - conf_int[-1, 0]) / current_price
        confidence = max(0.3, min(0.9, 1 - spread))

        # ARIMA Order
        order = getattr(model, '_best_order', (1, 0, 1))

        summary = (
            f"ARIMA{order} Prognose: {trend.capitalize()} Trend erwartet. "
            f"Kursziel: {forecast_end:.2f} ({change_pct:+.1f}%) "
            f"in {len(forecast)} Tagen."
        )

        # Forecast-Daten für Visualisierung
        last_date = historical.index[-1]
        forecast_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=len(forecast),
            freq='B'  # Business days
        )

        chart_data = pd.DataFrame({
            'date': forecast_dates,
            'forecast': forecast,
            'lower': conf_int[:, 0],
            'upper': conf_int[:, 1]
        })

        return AnalysisResult(
            analysis_type=self.name,
            symbol=symbol,
            timestamp=datetime.now(),
            summary=summary,
            confidence=confidence,
            data={
                'current_price': current_price,
                'forecast_end': forecast_end,
                'change_percent': change_pct,
                'arima_order': order,
                'forecast_days': len(forecast),
                'timeframe': timeframe.value
            },
            predictions={
                'forecast': forecast.tolist(),
                'lower_bound': conf_int[:, 0].tolist(),
                'upper_bound': conf_int[:, 1].tolist(),
                'dates': [d.isoformat() for d in forecast_dates]
            },
            signals=[{
                'type': recommendation,
                'indicator': 'ARIMA',
                'description': f'Prognose: {trend} Trend',
                'price_target': forecast_end,
                'confidence': confidence
            }],
            recommendation=recommendation,
            chart_data=chart_data
        )
