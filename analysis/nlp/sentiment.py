"""
FinancialProof - Sentiment Analyse
NLP-basierte Stimmungsanalyse von News und Social Media
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
import re

from analysis.base import (
    BaseAnalyzer, AnalysisResult, AnalysisParameters,
    AnalysisCategory, AnalysisTimeframe
)
from analysis.registry import AnalysisRegistry


@AnalysisRegistry.register
class SentimentAnalyzer(BaseAnalyzer):
    """
    Sentiment-Analyse für Aktien/Assets.

    Analysiert News-Überschriften und Social Media Beiträge
    um die Marktstimmung zu messen.
    """

    name = "sentiment"
    display_name = "Sentiment & News Analyse"
    category = AnalysisCategory.NLP
    description = "Analysiert Nachrichten und Social Media für Marktstimmung"
    estimated_duration = 15
    min_data_points = 1  # Braucht keine historischen Kursdaten

    supported_timeframes = [
        AnalysisTimeframe.SHORT
    ]

    # Finanz-spezifisches Sentiment-Lexikon
    POSITIVE_WORDS = {
        'buy', 'bullish', 'upgrade', 'growth', 'profit', 'gain', 'surge',
        'rally', 'breakthrough', 'beat', 'exceed', 'record', 'strong',
        'positive', 'optimistic', 'outperform', 'winner', 'success',
        'momentum', 'breakout', 'opportunity', 'kaufen', 'stark', 'wachstum',
        'gewinn', 'durchbruch', 'erfolg', 'positiv', 'chancen'
    }

    NEGATIVE_WORDS = {
        'sell', 'bearish', 'downgrade', 'loss', 'decline', 'drop', 'crash',
        'fall', 'miss', 'weak', 'negative', 'warning', 'risk', 'concern',
        'underperform', 'loser', 'failure', 'bankruptcy', 'fraud', 'lawsuit',
        'verkaufen', 'schwach', 'verlust', 'risiko', 'warnung', 'absturz',
        'krise', 'pleite', 'negativ'
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
                "include_news": {
                    "type": "boolean",
                    "default": True,
                    "description": "yfinance News analysieren"
                },
                "max_articles": {
                    "type": "integer",
                    "default": 20,
                    "minimum": 5,
                    "maximum": 50,
                    "description": "Maximale Anzahl Artikel"
                }
            }
        }

    async def analyze(self, params: AnalysisParameters) -> AnalysisResult:
        """Führt die Sentiment-Analyse durch"""
        symbol = params.symbol

        self.set_progress(10)

        try:
            # News laden
            include_news = params.custom_params.get('include_news', True)
            max_articles = params.custom_params.get('max_articles', 20)

            self.set_progress(20)

            articles = []
            if include_news:
                articles = self._fetch_news(symbol, max_articles)

            self.set_progress(40)

            if not articles:
                return AnalysisResult(
                    analysis_type=self.name,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    summary="Keine Nachrichten gefunden für Sentiment-Analyse.",
                    confidence=0.3,
                    data={'articles_analyzed': 0},
                    warnings=["Keine News verfügbar"]
                )

            # Sentiment berechnen
            self.set_progress(60)
            analyzed_articles = self._analyze_articles(articles)

            # Aggregierte Metriken
            self.set_progress(80)
            metrics = self._aggregate_sentiment(analyzed_articles)

            # Ergebnis aufbereiten
            result = self._build_result(symbol, analyzed_articles, metrics)

            self.set_progress(100)
            return result

        except Exception as e:
            return self.create_empty_result(self.name, symbol, str(e))

    def _fetch_news(self, symbol: str, limit: int) -> List[Dict]:
        """Lädt News von yfinance"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            news = ticker.news

            if not news:
                return []

            articles = []
            for item in news[:limit]:
                articles.append({
                    'title': item.get('title', ''),
                    'publisher': item.get('publisher', 'Unknown'),
                    'link': item.get('link', ''),
                    'published': item.get('providerPublishTime', 0),
                    'type': item.get('type', 'news')
                })

            return articles

        except Exception as e:
            print(f"News fetch error: {e}")
            return []

    def _analyze_articles(self, articles: List[Dict]) -> List[Dict]:
        """Analysiert einzelne Artikel"""
        analyzed = []

        # Versuche transformers zu verwenden
        use_transformers = False
        sentiment_pipeline = None

        try:
            from transformers import pipeline
            sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            use_transformers = True
        except ImportError:
            pass
        except Exception:
            pass

        for article in articles:
            title = article['title']

            if use_transformers and sentiment_pipeline:
                # Transformers Sentiment
                try:
                    result = sentiment_pipeline(title[:512])[0]
                    sentiment_score = result['score']
                    if result['label'] == 'NEGATIVE':
                        sentiment_score = -sentiment_score
                except Exception:
                    sentiment_score = self._simple_sentiment(title)
            else:
                # Fallback: Wort-basierte Analyse
                sentiment_score = self._simple_sentiment(title)

            analyzed.append({
                **article,
                'sentiment_score': sentiment_score,
                'sentiment_label': self._score_to_label(sentiment_score)
            })

        return analyzed

    def _simple_sentiment(self, text: str) -> float:
        """
        Einfache wort-basierte Sentiment-Analyse.
        Fallback wenn transformers nicht verfügbar.
        """
        text_lower = text.lower()
        words = re.findall(r'\w+', text_lower)

        positive_count = sum(1 for w in words if w in self.POSITIVE_WORDS)
        negative_count = sum(1 for w in words if w in self.NEGATIVE_WORDS)

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        # Score zwischen -1 und 1
        score = (positive_count - negative_count) / total
        return score

    def _score_to_label(self, score: float) -> str:
        """Konvertiert Score zu Label"""
        if score > 0.3:
            return "positiv"
        elif score < -0.3:
            return "negativ"
        return "neutral"

    def _aggregate_sentiment(self, articles: List[Dict]) -> Dict:
        """Aggregiert Sentiment über alle Artikel"""
        if not articles:
            return {'average': 0, 'positive_pct': 0, 'negative_pct': 0}

        scores = [a['sentiment_score'] for a in articles]

        positive = sum(1 for s in scores if s > 0.3)
        negative = sum(1 for s in scores if s < -0.3)
        neutral = len(scores) - positive - negative

        return {
            'average': np.mean(scores),
            'median': np.median(scores),
            'std': np.std(scores),
            'positive_count': positive,
            'negative_count': negative,
            'neutral_count': neutral,
            'positive_pct': positive / len(scores) * 100,
            'negative_pct': negative / len(scores) * 100,
            'neutral_pct': neutral / len(scores) * 100,
            'total_articles': len(scores)
        }

    def _build_result(
        self,
        symbol: str,
        articles: List[Dict],
        metrics: Dict
    ) -> AnalysisResult:
        """Baut das Analyse-Ergebnis zusammen"""
        avg_sentiment = metrics['average']

        # Gesamtbewertung
        if avg_sentiment > 0.3:
            overall = "bullish"
            recommendation = "buy"
            emoji = "🐂"
        elif avg_sentiment < -0.3:
            overall = "bearish"
            recommendation = "sell"
            emoji = "🐻"
        else:
            overall = "neutral"
            recommendation = "hold"
            emoji = "😐"

        # Konfidenz basierend auf Konsistenz der Artikel
        if metrics['std'] < 0.3:
            confidence = 0.7 + abs(avg_sentiment) * 0.2
        else:
            confidence = 0.5 + abs(avg_sentiment) * 0.1

        confidence = min(0.85, confidence)

        summary = (
            f"Marktstimmung {emoji}: {overall.upper()} "
            f"(Score: {avg_sentiment:.2f}). "
            f"Analysiert: {metrics['total_articles']} Artikel. "
            f"Positiv: {metrics['positive_pct']:.0f}%, "
            f"Negativ: {metrics['negative_pct']:.0f}%."
        )

        # Top Headlines nach Sentiment
        sorted_articles = sorted(
            articles,
            key=lambda x: abs(x['sentiment_score']),
            reverse=True
        )

        top_positive = [a for a in sorted_articles if a['sentiment_score'] > 0][:3]
        top_negative = [a for a in sorted_articles if a['sentiment_score'] < 0][:3]

        warnings = []
        if metrics['std'] > 0.5:
            warnings.append(
                "Hohe Varianz im Sentiment - gemischte Signale"
            )
        if metrics['total_articles'] < 5:
            warnings.append(
                "Wenige Artikel analysiert - Ergebnis unsicher"
            )

        return AnalysisResult(
            analysis_type=self.name,
            symbol=symbol,
            timestamp=datetime.now(),
            summary=summary,
            confidence=confidence,
            data={
                'overall_sentiment': overall,
                'average_score': avg_sentiment,
                'median_score': metrics['median'],
                'std_deviation': metrics['std'],
                'positive_count': metrics['positive_count'],
                'negative_count': metrics['negative_count'],
                'neutral_count': metrics['neutral_count'],
                'positive_percent': metrics['positive_pct'],
                'negative_percent': metrics['negative_pct'],
                'total_articles': metrics['total_articles'],
                'top_positive_headlines': [
                    {'title': a['title'], 'score': a['sentiment_score']}
                    for a in top_positive
                ],
                'top_negative_headlines': [
                    {'title': a['title'], 'score': a['sentiment_score']}
                    for a in top_negative
                ],
                'all_articles': [
                    {
                        'title': a['title'],
                        'publisher': a['publisher'],
                        'sentiment': a['sentiment_label'],
                        'score': a['sentiment_score']
                    }
                    for a in articles
                ]
            },
            signals=[{
                'type': recommendation,
                'indicator': 'Sentiment',
                'description': f'Marktstimmung: {overall} ({avg_sentiment:.2f})',
                'confidence': confidence
            }],
            recommendation=recommendation,
            warnings=warnings
        )
