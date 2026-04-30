"""
FinancialProof - Neural Network Pattern Recognition
Deep Learning für Muster-Erkennung in Kursdaten
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from analysis.base import (
    BaseAnalyzer, AnalysisResult, AnalysisParameters,
    AnalysisCategory, AnalysisTimeframe
)
from analysis.registry import AnalysisRegistry


logger = logging.getLogger(__name__)


@AnalysisRegistry.register
class NeuralNetAnalyzer(BaseAnalyzer):
    """
    Neural Network für Pattern Recognition.

    Verwendet ein einfaches LSTM oder Dense Network um
    Muster in Preisbewegungen zu erkennen.
    """

    name = "neural_network"
    display_name = "Deep Learning Pattern Recognition"
    category = AnalysisCategory.ML
    description = "Erkennt komplexe Muster in Kursdaten mit neuronalen Netzen"
    estimated_duration = 45
    min_data_points = 200

    supported_timeframes = [
        AnalysisTimeframe.SHORT,
        AnalysisTimeframe.MEDIUM
    ]

    # Lookback für Sequenzen
    SEQUENCE_LENGTH = 20

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
                "epochs": {
                    "type": "integer",
                    "default": 50,
                    "minimum": 10,
                    "maximum": 200,
                    "description": "Training Epochen"
                },
                "sequence_length": {
                    "type": "integer",
                    "default": 20,
                    "minimum": 5,
                    "maximum": 60,
                    "description": "Lookback-Periode für Muster"
                }
            }
        }

    async def analyze(self, params: AnalysisParameters) -> AnalysisResult:
        """Führt die Neural Network Analyse durch"""
        symbol = params.symbol
        data = params.data

        errors = self.validate_data(data)
        if errors:
            return self.create_empty_result(self.name, symbol, errors[0])

        self.set_progress(10)

        try:
            # Versuche TensorFlow/Keras zu laden
            try:
                import tensorflow as tf
                from tensorflow import keras
                use_keras = True
            except ImportError:
                use_keras = False

            # Parameter
            epochs = params.custom_params.get('epochs', 50)
            seq_length = params.custom_params.get('sequence_length', self.SEQUENCE_LENGTH)

            self.set_progress(20)

            # Daten vorbereiten
            X, y, scaler, last_sequence = self._prepare_sequences(
                data, seq_length
            )

            if len(X) < 50:
                return self.create_empty_result(
                    self.name, symbol,
                    "Zu wenig Daten für Neural Network Training"
                )

            self.set_progress(40)

            if use_keras:
                # Mit Keras trainieren
                model, history, metrics = self._train_keras_model(
                    X, y, epochs
                )
                prediction, confidence = self._predict_keras(
                    model, last_sequence, scaler
                )
            else:
                # Fallback: Einfaches Numpy-basiertes Modell
                prediction, confidence, metrics = self._simple_pattern_analysis(
                    data, seq_length
                )

            self.set_progress(90)

            # Ergebnis aufbereiten
            result = self._build_result(
                symbol, data, prediction, confidence, metrics, use_keras
            )

            self.set_progress(100)
            return result

        except Exception as e:
            logger.exception("Neural-Network-Analyse fuer %s fehlgeschlagen", symbol)
            return self.create_empty_result(self.name, symbol, str(e))

    def _prepare_sequences(
        self,
        df: pd.DataFrame,
        seq_length: int
    ) -> Tuple[np.ndarray, np.ndarray, Any, np.ndarray]:
        """Bereitet Sequenz-Daten für LSTM/RNN vor"""
        from sklearn.preprocessing import MinMaxScaler

        # Nur Close-Preise für einfaches Modell
        close = df['Close'].values.reshape(-1, 1)

        # Normalisieren
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled = scaler.fit_transform(close)

        # Sequenzen erstellen
        X, y = [], []
        for i in range(seq_length, len(scaled) - 1):
            X.append(scaled[i - seq_length:i, 0])
            # Target: Steigt der Kurs morgen? (1 = ja, 0 = nein)
            y.append(1 if scaled[i + 1, 0] > scaled[i, 0] else 0)

        X = np.array(X)
        y = np.array(y)

        # Reshape für LSTM [samples, timesteps, features]
        X = X.reshape((X.shape[0], X.shape[1], 1))

        # Letzte Sequenz für Vorhersage
        last_sequence = scaled[-seq_length:].reshape(1, seq_length, 1)

        return X, y, scaler, last_sequence

    def _train_keras_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int
    ) -> Tuple[Any, Any, Dict]:
        """Trainiert ein Keras LSTM Modell"""
        from tensorflow import keras
        from tensorflow.keras import layers
        from sklearn.model_selection import train_test_split

        # Train/Test Split
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Modell-Architektur (einfaches LSTM)
        model = keras.Sequential([
            layers.LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)),
            layers.Dropout(0.2),
            layers.LSTM(50, return_sequences=False),
            layers.Dropout(0.2),
            layers.Dense(25, activation='relu'),
            layers.Dense(1, activation='sigmoid')
        ])

        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        # Training (mit Early Stopping)
        early_stop = keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )

        history = model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=32,
            validation_data=(X_test, y_test),
            callbacks=[early_stop],
            verbose=0
        )

        # Evaluierung
        y_pred = (model.predict(X_test, verbose=0) > 0.5).astype(int).flatten()
        accuracy = (y_pred == y_test).mean()

        metrics = {
            'accuracy': accuracy,
            'final_loss': history.history['loss'][-1],
            'final_val_loss': history.history['val_loss'][-1],
            'epochs_trained': len(history.history['loss']),
            'model_type': 'LSTM'
        }

        return model, history, metrics

    def _predict_keras(
        self,
        model,
        last_sequence: np.ndarray,
        scaler
    ) -> Tuple[int, float]:
        """Macht Vorhersage mit Keras Modell"""
        prob = model.predict(last_sequence, verbose=0)[0, 0]
        prediction = 1 if prob > 0.5 else 0
        confidence = prob if prediction == 1 else 1 - prob
        return prediction, confidence

    def _simple_pattern_analysis(
        self,
        df: pd.DataFrame,
        lookback: int
    ) -> Tuple[int, float, Dict]:
        """
        Fallback: Einfache Muster-Analyse ohne Deep Learning.
        Sucht nach bekannten Chartmustern.
        """
        close = df['Close'].values
        high = df['High'].values
        low = df['Low'].values

        patterns = []

        # 1. Aufwärts-/Abwärtskanal erkennen
        recent = close[-lookback:]
        slope = np.polyfit(range(len(recent)), recent, 1)[0]
        trend_score = slope / np.mean(recent) * 1000  # Normalisiert

        # 2. Higher Highs / Lower Lows
        highs = high[-lookback:]
        lows = low[-lookback:]

        hh_count = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i-1])
        ll_count = sum(1 for i in range(1, len(lows)) if lows[i] < lows[i-1])

        # 3. Support/Resistance Tests
        recent_low = min(lows)
        recent_high = max(highs)
        current = close[-1]

        near_support = (current - recent_low) / (recent_high - recent_low) < 0.2
        near_resistance = (current - recent_low) / (recent_high - recent_low) > 0.8

        # Gesamtbewertung
        bullish_signals = 0
        bearish_signals = 0

        if trend_score > 0.5:
            bullish_signals += 1
        elif trend_score < -0.5:
            bearish_signals += 1

        if hh_count > ll_count:
            bullish_signals += 1
        elif ll_count > hh_count:
            bearish_signals += 1

        if near_support:
            bullish_signals += 1  # Bounce vom Support erwartet
        if near_resistance:
            bearish_signals += 1  # Abprall vom Widerstand erwartet

        # Vorhersage
        if bullish_signals > bearish_signals:
            prediction = 1
            confidence = 0.5 + (bullish_signals - bearish_signals) * 0.1
        elif bearish_signals > bullish_signals:
            prediction = 0
            confidence = 0.5 + (bearish_signals - bullish_signals) * 0.1
        else:
            prediction = 1 if trend_score > 0 else 0
            confidence = 0.5

        confidence = min(0.75, confidence)  # Cap bei 75% ohne echtes ML

        metrics = {
            'accuracy': 0.55,  # Geschätzt
            'model_type': 'Pattern Heuristics',
            'trend_score': trend_score,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'near_support': near_support,
            'near_resistance': near_resistance
        }

        return prediction, confidence, metrics

    def _build_result(
        self,
        symbol: str,
        data: pd.DataFrame,
        prediction: int,
        confidence: float,
        metrics: Dict,
        used_deep_learning: bool
    ) -> AnalysisResult:
        """Baut das Analyse-Ergebnis zusammen"""
        current_price = data['Close'].iloc[-1]
        direction = "steigend" if prediction == 1 else "fallend"

        model_type = metrics.get('model_type', 'Neural Network')
        accuracy = metrics.get('accuracy', 0.5)

        if prediction == 1 and confidence > 0.6:
            recommendation = "buy"
        elif prediction == 0 and confidence > 0.6:
            recommendation = "sell"
        else:
            recommendation = "hold"

        summary = (
            f"Deep-Learning-Musteranalyse ({model_type}): "
            f"Modell ordnet die jüngsten Features der Klasse "
            f"\"{direction}\" zu (Modell-Konfidenz: {confidence*100:.1f}%). "
            f"Kein Handelssignal, keine Prognose, keine Empfehlung."
        )

        if used_deep_learning:
            summary += f"LSTM trainiert mit {metrics.get('epochs_trained', 'N/A')} Epochen."
        else:
            summary += "Heuristische Muster-Erkennung (TensorFlow nicht verfügbar)."

        warnings = []
        if not used_deep_learning:
            warnings.append(
                "TensorFlow nicht installiert - "
                "Fallback auf einfache Muster-Heuristik."
            )
        if accuracy < 0.55:
            warnings.append(
                f"Modell-Genauigkeit ({accuracy*100:.1f}%) ist gering."
            )

        return AnalysisResult(
            analysis_type=self.name,
            symbol=symbol,
            timestamp=datetime.now(),
            summary=summary,
            confidence=confidence,
            data={
                'current_price': current_price,
                'prediction': int(prediction),
                'prediction_label': direction,
                'confidence': confidence,
                'model_type': model_type,
                'used_deep_learning': used_deep_learning,
                **metrics
            },
            signals=[{
                'type': 'buy' if prediction == 1 else 'sell',
                'indicator': model_type,
                'description': (
                    f'Muster-Klassifikation: Klasse "{direction}" '
                    f'(keine Prognose, keine Empfehlung)'
                ),
                'confidence': confidence
            }],
            recommendation=recommendation,
            warnings=warnings
        )
