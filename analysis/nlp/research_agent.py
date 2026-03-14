"""
FinancialProof - Web Research Agent
Sammelt Informationen aus verschiedenen Web-Quellen
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
class ResearchAgent(BaseAnalyzer):
    """
    Web Research Agent für umfassende Asset-Recherche.

    Sammelt Informationen aus:
    - yfinance (Fundamentaldaten, Analysten-Empfehlungen)
    - News-Quellen
    - (Optional) Twitter/X, YouTube mit API-Keys
    """

    name = "research_agent"
    display_name = "Web-Recherche Agent"
    category = AnalysisCategory.RESEARCH
    description = "Sammelt umfassende Informationen aus Web-Quellen"
    estimated_duration = 30
    min_data_points = 1

    supported_timeframes = [
        AnalysisTimeframe.SHORT,
        AnalysisTimeframe.MEDIUM
    ]

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
                "include_fundamentals": {
                    "type": "boolean",
                    "default": True,
                    "description": "Fundamentaldaten einbeziehen"
                },
                "include_recommendations": {
                    "type": "boolean",
                    "default": True,
                    "description": "Analysten-Empfehlungen einbeziehen"
                },
                "include_news": {
                    "type": "boolean",
                    "default": True,
                    "description": "News einbeziehen"
                },
                "research_topic": {
                    "type": "string",
                    "default": "",
                    "description": "Optionales Recherche-Thema"
                }
            }
        }

    async def analyze(self, params: AnalysisParameters) -> AnalysisResult:
        """Führt die Web-Recherche durch"""
        symbol = params.symbol

        self.set_progress(5)

        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)

            research_data = {}
            sections = []

            # Fundamentaldaten
            if params.custom_params.get('include_fundamentals', True):
                self.set_progress(20)
                fundamentals = self._get_fundamentals(ticker)
                research_data['fundamentals'] = fundamentals
                sections.append(('fundamentals', fundamentals))

            # Analysten-Empfehlungen
            if params.custom_params.get('include_recommendations', True):
                self.set_progress(40)
                recommendations = self._get_recommendations(ticker)
                research_data['recommendations'] = recommendations
                sections.append(('recommendations', recommendations))

            # News-Übersicht
            if params.custom_params.get('include_news', True):
                self.set_progress(60)
                news = self._get_news_summary(ticker)
                research_data['news'] = news
                sections.append(('news', news))

            # Dividenden & Splits
            self.set_progress(75)
            dividends = self._get_dividend_info(ticker)
            research_data['dividends'] = dividends

            # Gesamt-Bewertung erstellen
            self.set_progress(90)
            result = self._build_result(symbol, research_data, sections)

            self.set_progress(100)
            return result

        except Exception as e:
            return self.create_empty_result(self.name, symbol, str(e))

    def _get_fundamentals(self, ticker) -> Dict:
        """Sammelt Fundamentaldaten"""
        try:
            info = ticker.info

            return {
                'company_name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'country': info.get('country', 'N/A'),
                'employees': info.get('fullTimeEmployees', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'market_cap_formatted': self._format_large_number(
                    info.get('marketCap', 0)
                ),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'forward_pe': info.get('forwardPE', 'N/A'),
                'peg_ratio': info.get('pegRatio', 'N/A'),
                'price_to_book': info.get('priceToBook', 'N/A'),
                'debt_to_equity': info.get('debtToEquity', 'N/A'),
                'profit_margins': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 'N/A',
                'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 'N/A',
                'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 'N/A',
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 'N/A')),
                'target_price': info.get('targetMeanPrice', 'N/A'),
                'target_high': info.get('targetHighPrice', 'N/A'),
                'target_low': info.get('targetLowPrice', 'N/A'),
                '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
                'beta': info.get('beta', 'N/A'),
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'description': info.get('longBusinessSummary', '')[:500] if info.get('longBusinessSummary') else 'N/A'
            }
        except Exception as e:
            return {'error': str(e)}

    def _get_recommendations(self, ticker) -> Dict:
        """Sammelt Analysten-Empfehlungen"""
        try:
            rec = ticker.recommendations
            if rec is None or rec.empty:
                return {'available': False}

            # Letzte Empfehlungen
            recent = rec.tail(10)

            # Aggregation
            grades = recent['To Grade'].value_counts().to_dict() if 'To Grade' in recent.columns else {}

            # Gesamtbewertung
            buy_grades = ['Buy', 'Strong Buy', 'Overweight', 'Outperform']
            sell_grades = ['Sell', 'Strong Sell', 'Underweight', 'Underperform']
            hold_grades = ['Hold', 'Neutral', 'Market Perform', 'Equal-Weight']

            buy_count = sum(grades.get(g, 0) for g in buy_grades)
            sell_count = sum(grades.get(g, 0) for g in sell_grades)
            hold_count = sum(grades.get(g, 0) for g in hold_grades)

            total = buy_count + sell_count + hold_count
            if total > 0:
                consensus = 'buy' if buy_count > sell_count + hold_count else \
                           'sell' if sell_count > buy_count + hold_count else 'hold'
            else:
                consensus = 'unknown'

            return {
                'available': True,
                'total_recommendations': total,
                'buy_count': buy_count,
                'hold_count': hold_count,
                'sell_count': sell_count,
                'consensus': consensus,
                'grade_distribution': grades,
                'recent': recent.to_dict('records')[-5:] if len(recent) > 0 else []
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def _get_news_summary(self, ticker) -> Dict:
        """Sammelt News-Übersicht"""
        try:
            news = ticker.news
            if not news:
                return {'available': False}

            articles = []
            for item in news[:10]:
                articles.append({
                    'title': item.get('title', ''),
                    'publisher': item.get('publisher', ''),
                    'link': item.get('link', ''),
                    'published': datetime.fromtimestamp(
                        item.get('providerPublishTime', 0)
                    ).strftime('%Y-%m-%d %H:%M') if item.get('providerPublishTime') else 'N/A'
                })

            return {
                'available': True,
                'total_articles': len(news),
                'recent_articles': articles
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def _get_dividend_info(self, ticker) -> Dict:
        """Sammelt Dividenden-Informationen"""
        try:
            info = ticker.info
            dividends = ticker.dividends

            return {
                'pays_dividend': info.get('dividendYield', 0) > 0,
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'dividend_rate': info.get('dividendRate', 'N/A'),
                'ex_dividend_date': info.get('exDividendDate', 'N/A'),
                'payout_ratio': info.get('payoutRatio', 'N/A'),
                'recent_dividends': dividends.tail(4).to_dict() if dividends is not None and len(dividends) > 0 else {}
            }
        except Exception as e:
            return {'error': str(e)}

    def _format_large_number(self, num) -> str:
        """Formatiert große Zahlen lesbar"""
        if not num or num == 'N/A':
            return 'N/A'
        try:
            num = float(num)
            if num >= 1e12:
                return f"{num/1e12:.2f}T"
            elif num >= 1e9:
                return f"{num/1e9:.2f}B"
            elif num >= 1e6:
                return f"{num/1e6:.2f}M"
            elif num >= 1e3:
                return f"{num/1e3:.2f}K"
            return f"{num:.2f}"
        except Exception:
            return str(num)

    def _build_result(
        self,
        symbol: str,
        research_data: Dict,
        sections: List
    ) -> AnalysisResult:
        """Baut das Recherche-Ergebnis zusammen"""
        # Gesamt-Bewertung aus verschiedenen Quellen
        signals = []
        recommendations = []

        # Fundamental-basierte Bewertung
        fundamentals = research_data.get('fundamentals', {})
        if fundamentals.get('pe_ratio') and fundamentals.get('pe_ratio') != 'N/A':
            pe = fundamentals['pe_ratio']
            if pe < 15:
                signals.append(('fundamental', 'buy', 'Niedriges KGV'))
            elif pe > 30:
                signals.append(('fundamental', 'sell', 'Hohes KGV'))

        # Target Price Bewertung
        current = fundamentals.get('current_price', 0)
        target = fundamentals.get('target_price', 0)
        if current and target and current != 'N/A' and target != 'N/A':
            upside = ((target - current) / current) * 100
            if upside > 15:
                signals.append(('analyst', 'buy', f'Kursziel +{upside:.1f}%'))
            elif upside < -10:
                signals.append(('analyst', 'sell', f'Kursziel {upside:.1f}%'))

        # Analysten-Empfehlungen
        rec_data = research_data.get('recommendations', {})
        if rec_data.get('available') and rec_data.get('consensus'):
            consensus = rec_data['consensus']
            signals.append(('consensus', consensus, f'Analysten-Konsens: {consensus}'))

        # Gesamtempfehlung
        buy_signals = sum(1 for s in signals if s[1] == 'buy')
        sell_signals = sum(1 for s in signals if s[1] == 'sell')

        if buy_signals > sell_signals:
            overall_recommendation = 'buy'
            confidence = 0.5 + (buy_signals - sell_signals) * 0.1
        elif sell_signals > buy_signals:
            overall_recommendation = 'sell'
            confidence = 0.5 + (sell_signals - buy_signals) * 0.1
        else:
            overall_recommendation = 'hold'
            confidence = 0.5

        confidence = min(0.8, confidence)

        # Summary erstellen
        company = fundamentals.get('company_name', symbol)
        sector = fundamentals.get('sector', 'Unbekannt')
        market_cap = fundamentals.get('market_cap_formatted', 'N/A')

        summary = (
            f"Recherche-Bericht für {company} ({symbol}). "
            f"Sektor: {sector}. Marktkapitalisierung: {market_cap}. "
            f"Gesamteinschätzung: {overall_recommendation.upper()}. "
            f"Basierend auf {len(signals)} Signalen."
        )

        return AnalysisResult(
            analysis_type=self.name,
            symbol=symbol,
            timestamp=datetime.now(),
            summary=summary,
            confidence=confidence,
            data={
                'company_name': fundamentals.get('company_name', symbol),
                'fundamentals': fundamentals,
                'recommendations': rec_data,
                'news': research_data.get('news', {}),
                'dividends': research_data.get('dividends', {}),
                'signals_found': [
                    {'source': s[0], 'signal': s[1], 'reason': s[2]}
                    for s in signals
                ]
            },
            signals=[{
                'type': overall_recommendation,
                'indicator': 'Research Agent',
                'description': f'Kombinierte Analyse: {len(signals)} Signale',
                'confidence': confidence
            }],
            recommendation=overall_recommendation
        )
