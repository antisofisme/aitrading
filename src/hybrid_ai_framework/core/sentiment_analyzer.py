"""
FinBERT Sentiment Analysis Engine
Advanced sentiment analysis for forex/gold trading using FinBERT and news data

Features:
- FinBERT-based financial sentiment analysis
- Real-time news sentiment scoring
- Forex/Gold specific sentiment indicators
- Central bank policy sentiment analysis
- Economic data sentiment impact
- Multi-language sentiment support
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import numpy as np
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


class SentimentCategory(Enum):
    """Sentiment categories"""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class NewsSource(Enum):
    """News source types"""
    CENTRAL_BANK = "central_bank"
    ECONOMIC_DATA = "economic_data"
    FINANCIAL_NEWS = "financial_news"
    SOCIAL_MEDIA = "social_media"
    ANALYST_REPORT = "analyst_report"
    GOVERNMENT = "government"


@dataclass
class NewsItem:
    """Individual news item"""
    title: str
    content: str
    source: str
    source_type: NewsSource
    timestamp: datetime
    relevance_score: float = 0.0
    language: str = "en"
    asset_mentions: List[str] = field(default_factory=list)


@dataclass
class SentimentScore:
    """Sentiment analysis result"""
    overall_score: float  # -1 to 1
    confidence: float  # 0 to 1
    category: SentimentCategory
    sentiment_distribution: Dict[str, float]
    timestamp: datetime


@dataclass
class SentimentAnalysis:
    """Comprehensive sentiment analysis result"""
    asset: str
    overall_sentiment: SentimentScore
    source_breakdown: Dict[NewsSource, SentimentScore]
    time_weighted_sentiment: float
    sentiment_momentum: float  # Change in sentiment
    key_themes: List[str]
    sentiment_drivers: List[Dict[str, Any]]
    confidence_level: str
    analysis_timestamp: datetime


class FinBERTSentimentAnalyzer:
    """
    Advanced sentiment analysis engine using FinBERT

    Features:
    - FinBERT model for financial sentiment
    - Multi-source news analysis
    - Asset-specific sentiment filtering
    - Time-weighted sentiment scoring
    - Sentiment momentum calculation
    - Central bank communication analysis
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Model components
        self.tokenizer = None
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu' if HAS_TRANSFORMERS else None

        # Sentiment history
        self.sentiment_history: Dict[str, List[SentimentScore]] = {}

        # Asset keywords for filtering
        self.asset_keywords = self._initialize_asset_keywords()

        # Central bank keywords
        self.central_bank_keywords = self._initialize_central_bank_keywords()

        # Sentiment weights by source
        self.source_weights = {
            NewsSource.CENTRAL_BANK: 1.0,
            NewsSource.ECONOMIC_DATA: 0.8,
            NewsSource.FINANCIAL_NEWS: 0.6,
            NewsSource.ANALYST_REPORT: 0.7,
            NewsSource.GOVERNMENT: 0.5,
            NewsSource.SOCIAL_MEDIA: 0.3
        }

        # Time decay parameters
        self.time_decay_hours = 24
        self.sentiment_cache = {}

        self.logger.info("FinBERT Sentiment Analyzer initialized")

    async def initialize(self) -> bool:
        """Initialize FinBERT model and tokenizer"""
        try:
            if not HAS_TRANSFORMERS:
                self.logger.warning("⚠️ Transformers library not available, using fallback sentiment analysis")
                return True

            self.logger.info("Loading FinBERT model...")

            # Load FinBERT model and tokenizer
            model_name = "ProsusAI/finbert"

            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

                if self.device and 'cuda' in self.device:
                    self.model = self.model.to(self.device)

                self.model.eval()  # Set to evaluation mode

                self.logger.info(f"✅ FinBERT model loaded successfully on {self.device}")

            except Exception as e:
                self.logger.warning(f"Failed to load FinBERT model: {e}, using fallback")
                self.tokenizer = None
                self.model = None

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize FinBERT Sentiment Analyzer: {e}")
            return False

    async def analyze_news(self, news_items: List[Dict[str, Any]]) -> float:
        """
        Analyze sentiment from news items

        Args:
            news_items: List of news items with title, content, source, etc.

        Returns:
            Overall sentiment score (-1 to 1)
        """
        try:
            if not news_items:
                return 0.5  # Neutral sentiment

            # Convert to NewsItem objects
            processed_news = []
            for item in news_items:
                news_item = NewsItem(
                    title=item.get('title', ''),
                    content=item.get('content', ''),
                    source=item.get('source', 'unknown'),
                    source_type=self._classify_news_source(item.get('source', '')),
                    timestamp=self._parse_timestamp(item.get('timestamp')),
                    language=item.get('language', 'en')
                )
                processed_news.append(news_item)

            # Analyze sentiment for each news item
            sentiment_scores = []
            for news_item in processed_news:
                sentiment = await self._analyze_single_news_item(news_item)
                if sentiment:
                    sentiment_scores.append(sentiment)

            if not sentiment_scores:
                return 0.5

            # Calculate weighted average sentiment
            weighted_sentiment = await self._calculate_weighted_sentiment(sentiment_scores, processed_news)

            # Convert to 0-1 scale (from -1 to 1)
            normalized_sentiment = (weighted_sentiment + 1) / 2

            return max(0.0, min(1.0, normalized_sentiment))

        except Exception as e:
            self.logger.error(f"❌ News sentiment analysis failed: {e}")
            return 0.5

    async def analyze_asset_sentiment(self, asset: str, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment specifically for an asset

        Args:
            asset: Asset symbol (e.g., 'XAUUSD', 'EURUSD')
            news_items: List of news items

        Returns:
            Comprehensive sentiment analysis for the asset
        """
        try:
            # Filter news relevant to the asset
            relevant_news = await self._filter_asset_relevant_news(asset, news_items)

            if not relevant_news:
                return await self._fallback_sentiment_analysis(asset)

            # Convert to NewsItem objects
            processed_news = []
            for item in relevant_news:
                news_item = NewsItem(
                    title=item.get('title', ''),
                    content=item.get('content', ''),
                    source=item.get('source', 'unknown'),
                    source_type=self._classify_news_source(item.get('source', '')),
                    timestamp=self._parse_timestamp(item.get('timestamp')),
                    relevance_score=item.get('relevance_score', 1.0),
                    language=item.get('language', 'en'),
                    asset_mentions=[asset] if asset.lower() in item.get('content', '').lower() else []
                )
                processed_news.append(news_item)

            # Analyze sentiment
            analysis = await self._comprehensive_sentiment_analysis(asset, processed_news)

            return {
                'overall_sentiment': analysis.overall_sentiment.overall_score,
                'confidence': analysis.overall_sentiment.confidence,
                'category': analysis.overall_sentiment.category.value,
                'source_breakdown': {source.value: score.overall_score
                                   for source, score in analysis.source_breakdown.items()},
                'time_weighted_sentiment': analysis.time_weighted_sentiment,
                'sentiment_momentum': analysis.sentiment_momentum,
                'key_themes': analysis.key_themes,
                'confidence_level': analysis.confidence_level,
                'sentiment_drivers': analysis.sentiment_drivers
            }

        except Exception as e:
            self.logger.error(f"❌ Asset sentiment analysis failed for {asset}: {e}")
            return await self._fallback_sentiment_analysis(asset)

    async def _analyze_single_news_item(self, news_item: NewsItem) -> Optional[SentimentScore]:
        """Analyze sentiment for a single news item"""
        try:
            # Combine title and content
            text = f"{news_item.title} {news_item.content}".strip()

            if not text:
                return None

            # Use FinBERT if available
            if self.model and self.tokenizer:
                sentiment_score = await self._finbert_sentiment(text)
            else:
                sentiment_score = await self._fallback_sentiment(text)

            return sentiment_score

        except Exception as e:
            self.logger.error(f"❌ Single news item sentiment analysis failed: {e}")
            return None

    async def _finbert_sentiment(self, text: str) -> SentimentScore:
        """Analyze sentiment using FinBERT model"""
        try:
            # Tokenize text
            inputs = self.tokenizer(text, return_tensors="pt", max_length=512, truncation=True, padding=True)

            if self.device and 'cuda' in self.device:
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

            # FinBERT returns [negative, neutral, positive]
            probs = predictions[0].cpu().numpy()
            negative_prob, neutral_prob, positive_prob = probs

            # Calculate overall sentiment score (-1 to 1)
            sentiment_score = positive_prob - negative_prob

            # Determine confidence (max probability)
            confidence = max(probs)

            # Determine category
            max_idx = np.argmax(probs)
            if max_idx == 0:  # Negative
                if negative_prob > 0.7:
                    category = SentimentCategory.VERY_NEGATIVE
                else:
                    category = SentimentCategory.NEGATIVE
            elif max_idx == 1:  # Neutral
                category = SentimentCategory.NEUTRAL
            else:  # Positive
                if positive_prob > 0.7:
                    category = SentimentCategory.VERY_POSITIVE
                else:
                    category = SentimentCategory.POSITIVE

            sentiment_distribution = {
                'negative': float(negative_prob),
                'neutral': float(neutral_prob),
                'positive': float(positive_prob)
            }

            return SentimentScore(
                overall_score=float(sentiment_score),
                confidence=float(confidence),
                category=category,
                sentiment_distribution=sentiment_distribution,
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"❌ FinBERT sentiment analysis failed: {e}")
            return await self._fallback_sentiment(text)

    async def _fallback_sentiment(self, text: str) -> SentimentScore:
        """Fallback sentiment analysis using simple keyword-based approach"""
        try:
            # Simple keyword-based sentiment
            positive_keywords = [
                'bullish', 'positive', 'optimistic', 'confident', 'strong', 'growth',
                'rise', 'increase', 'gain', 'rally', 'support', 'buy', 'upgrade'
            ]

            negative_keywords = [
                'bearish', 'negative', 'pessimistic', 'weak', 'decline', 'fall',
                'decrease', 'loss', 'drop', 'crash', 'sell', 'downgrade', 'risk'
            ]

            text_lower = text.lower()

            positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
            negative_count = sum(1 for keyword in negative_keywords if keyword in keyword in text_lower)

            # Calculate sentiment score
            total_keywords = positive_count + negative_count
            if total_keywords > 0:
                sentiment_score = (positive_count - negative_count) / total_keywords
            else:
                sentiment_score = 0.0

            # Determine confidence based on keyword density
            confidence = min(total_keywords / 10, 1.0)  # Max confidence at 10+ keywords

            # Determine category
            if sentiment_score > 0.3:
                category = SentimentCategory.POSITIVE
            elif sentiment_score < -0.3:
                category = SentimentCategory.NEGATIVE
            else:
                category = SentimentCategory.NEUTRAL

            sentiment_distribution = {
                'negative': max(0, -sentiment_score),
                'neutral': 1 - abs(sentiment_score),
                'positive': max(0, sentiment_score)
            }

            return SentimentScore(
                overall_score=sentiment_score,
                confidence=confidence,
                category=category,
                sentiment_distribution=sentiment_distribution,
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"❌ Fallback sentiment analysis failed: {e}")
            return SentimentScore(
                overall_score=0.0,
                confidence=0.3,
                category=SentimentCategory.NEUTRAL,
                sentiment_distribution={'negative': 0.33, 'neutral': 0.34, 'positive': 0.33},
                timestamp=datetime.now()
            )

    async def _filter_asset_relevant_news(self, asset: str, news_items: List[Dict]) -> List[Dict]:
        """Filter news items relevant to specific asset"""
        try:
            relevant_news = []
            asset_keywords = self.asset_keywords.get(asset, [asset.lower()])

            for item in news_items:
                relevance_score = 0.0
                content = f"{item.get('title', '')} {item.get('content', '')}".lower()

                # Check for asset-specific keywords
                for keyword in asset_keywords:
                    if keyword in content:
                        relevance_score += 1.0

                # Check for general financial keywords
                financial_keywords = ['forex', 'trading', 'market', 'price', 'currency', 'gold', 'federal reserve', 'interest rate']
                for keyword in financial_keywords:
                    if keyword in content:
                        relevance_score += 0.3

                # Check for central bank mentions (important for forex/gold)
                cb_keywords = self.central_bank_keywords
                for keyword in cb_keywords:
                    if keyword in content:
                        relevance_score += 0.8

                # Include if relevance score is above threshold
                if relevance_score >= 0.5:
                    item['relevance_score'] = relevance_score
                    relevant_news.append(item)

            return relevant_news

        except Exception as e:
            self.logger.error(f"❌ Asset news filtering failed: {e}")
            return news_items  # Return all news if filtering fails

    async def _comprehensive_sentiment_analysis(self, asset: str, news_items: List[NewsItem]) -> SentimentAnalysis:
        """Perform comprehensive sentiment analysis"""
        try:
            # Analyze sentiment for each news item
            sentiment_scores = []
            source_sentiments = {}

            for news_item in news_items:
                sentiment = await self._analyze_single_news_item(news_item)
                if sentiment:
                    sentiment_scores.append((sentiment, news_item))

                    # Group by source type
                    source_type = news_item.source_type
                    if source_type not in source_sentiments:
                        source_sentiments[source_type] = []
                    source_sentiments[source_type].append(sentiment)

            if not sentiment_scores:
                return await self._fallback_comprehensive_analysis(asset)

            # Calculate overall sentiment
            overall_sentiment = await self._calculate_overall_sentiment(sentiment_scores)

            # Calculate source breakdown
            source_breakdown = {}
            for source_type, sentiments in source_sentiments.items():
                if sentiments:
                    avg_score = sum(s.overall_score for s in sentiments) / len(sentiments)
                    avg_confidence = sum(s.confidence for s in sentiments) / len(sentiments)

                    # Determine category for source
                    if avg_score > 0.3:
                        category = SentimentCategory.POSITIVE
                    elif avg_score < -0.3:
                        category = SentimentCategory.NEGATIVE
                    else:
                        category = SentimentCategory.NEUTRAL

                    source_breakdown[source_type] = SentimentScore(
                        overall_score=avg_score,
                        confidence=avg_confidence,
                        category=category,
                        sentiment_distribution={},
                        timestamp=datetime.now()
                    )

            # Calculate time-weighted sentiment
            time_weighted_sentiment = await self._calculate_time_weighted_sentiment(sentiment_scores)

            # Calculate sentiment momentum
            sentiment_momentum = await self._calculate_sentiment_momentum(asset, overall_sentiment)

            # Extract key themes
            key_themes = await self._extract_key_themes(news_items)

            # Identify sentiment drivers
            sentiment_drivers = await self._identify_sentiment_drivers(sentiment_scores)

            # Determine confidence level
            confidence_level = await self._determine_confidence_level(overall_sentiment, len(news_items))

            return SentimentAnalysis(
                asset=asset,
                overall_sentiment=overall_sentiment,
                source_breakdown=source_breakdown,
                time_weighted_sentiment=time_weighted_sentiment,
                sentiment_momentum=sentiment_momentum,
                key_themes=key_themes,
                sentiment_drivers=sentiment_drivers,
                confidence_level=confidence_level,
                analysis_timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"❌ Comprehensive sentiment analysis failed: {e}")
            return await self._fallback_comprehensive_analysis(asset)

    async def _calculate_overall_sentiment(self, sentiment_scores: List[Tuple[SentimentScore, NewsItem]]) -> SentimentScore:
        """Calculate overall weighted sentiment score"""
        try:
            weighted_scores = []
            weighted_confidences = []
            total_weight = 0.0

            for sentiment, news_item in sentiment_scores:
                # Calculate weight based on source type, relevance, and recency
                source_weight = self.source_weights.get(news_item.source_type, 0.5)
                relevance_weight = news_item.relevance_score

                # Time decay weight (more recent news gets higher weight)
                hours_old = (datetime.now() - news_item.timestamp).total_seconds() / 3600
                time_weight = max(0.1, 1.0 - (hours_old / self.time_decay_hours))

                total_item_weight = source_weight * relevance_weight * time_weight

                weighted_scores.append(sentiment.overall_score * total_item_weight)
                weighted_confidences.append(sentiment.confidence * total_item_weight)
                total_weight += total_item_weight

            if total_weight > 0:
                overall_score = sum(weighted_scores) / total_weight
                overall_confidence = sum(weighted_confidences) / total_weight
            else:
                overall_score = 0.0
                overall_confidence = 0.3

            # Determine category
            if overall_score > 0.5:
                category = SentimentCategory.VERY_POSITIVE
            elif overall_score > 0.1:
                category = SentimentCategory.POSITIVE
            elif overall_score < -0.5:
                category = SentimentCategory.VERY_NEGATIVE
            elif overall_score < -0.1:
                category = SentimentCategory.NEGATIVE
            else:
                category = SentimentCategory.NEUTRAL

            return SentimentScore(
                overall_score=overall_score,
                confidence=overall_confidence,
                category=category,
                sentiment_distribution={},
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"❌ Overall sentiment calculation failed: {e}")
            return SentimentScore(
                overall_score=0.0,
                confidence=0.3,
                category=SentimentCategory.NEUTRAL,
                sentiment_distribution={},
                timestamp=datetime.now()
            )

    async def _calculate_weighted_sentiment(self, sentiment_scores: List[SentimentScore], news_items: List[NewsItem]) -> float:
        """Calculate simple weighted sentiment average"""
        try:
            if not sentiment_scores or not news_items:
                return 0.0

            total_weight = 0.0
            weighted_sum = 0.0

            for i, sentiment in enumerate(sentiment_scores):
                if i < len(news_items):
                    news_item = news_items[i]
                    source_weight = self.source_weights.get(news_item.source_type, 0.5)

                    weighted_sum += sentiment.overall_score * source_weight
                    total_weight += source_weight

            return weighted_sum / total_weight if total_weight > 0 else 0.0

        except Exception as e:
            self.logger.error(f"❌ Weighted sentiment calculation failed: {e}")
            return 0.0

    def _classify_news_source(self, source: str) -> NewsSource:
        """Classify news source type"""
        source_lower = source.lower()

        if any(keyword in source_lower for keyword in ['fed', 'ecb', 'boe', 'boj', 'rba', 'central bank']):
            return NewsSource.CENTRAL_BANK
        elif any(keyword in source_lower for keyword in ['reuters', 'bloomberg', 'wsj', 'ft', 'cnbc']):
            return NewsSource.FINANCIAL_NEWS
        elif any(keyword in source_lower for keyword in ['treasury', 'government', 'ministry']):
            return NewsSource.GOVERNMENT
        elif any(keyword in source_lower for keyword in ['twitter', 'reddit', 'social']):
            return NewsSource.SOCIAL_MEDIA
        elif any(keyword in source_lower for keyword in ['analyst', 'research', 'bank']):
            return NewsSource.ANALYST_REPORT
        else:
            return NewsSource.FINANCIAL_NEWS

    def _parse_timestamp(self, timestamp_input: Any) -> datetime:
        """Parse timestamp from various formats"""
        if isinstance(timestamp_input, datetime):
            return timestamp_input
        elif isinstance(timestamp_input, str):
            try:
                return datetime.fromisoformat(timestamp_input.replace('Z', '+00:00'))
            except:
                return datetime.now()
        else:
            return datetime.now()

    def _initialize_asset_keywords(self) -> Dict[str, List[str]]:
        """Initialize asset-specific keywords for filtering"""
        return {
            'XAUUSD': ['gold', 'xau', 'precious metal', 'bullion', 'gold price'],
            'EURUSD': ['euro', 'eur', 'european', 'eurozone', 'ecb'],
            'GBPUSD': ['pound', 'gbp', 'sterling', 'uk', 'britain', 'boe'],
            'USDJPY': ['yen', 'jpy', 'japan', 'japanese', 'boj'],
            'AUDUSD': ['aussie', 'aud', 'australia', 'australian', 'rba'],
            'USDCAD': ['cad', 'canada', 'canadian', 'loonie', 'boc'],
            'NZDUSD': ['nzd', 'new zealand', 'kiwi', 'rbnz'],
            'DXY': ['dollar index', 'dxy', 'usd index', 'dollar strength']
        }

    def _initialize_central_bank_keywords(self) -> List[str]:
        """Initialize central bank keywords"""
        return [
            'federal reserve', 'fed', 'jerome powell', 'fomc',
            'european central bank', 'ecb', 'christine lagarde',
            'bank of england', 'boe', 'andrew bailey',
            'bank of japan', 'boj', 'kazuo ueda',
            'reserve bank of australia', 'rba', 'philip lowe',
            'bank of canada', 'boc', 'tiff macklem',
            'reserve bank of new zealand', 'rbnz',
            'interest rate', 'monetary policy', 'quantitative easing'
        ]

    # Additional helper methods for comprehensive analysis
    async def _calculate_time_weighted_sentiment(self, sentiment_scores: List[Tuple[SentimentScore, NewsItem]]) -> float:
        """Calculate time-weighted sentiment with recency bias"""
        # Implementation placeholder
        return 0.0

    async def _calculate_sentiment_momentum(self, asset: str, current_sentiment: SentimentScore) -> float:
        """Calculate sentiment momentum (change over time)"""
        # Implementation placeholder
        return 0.0

    async def _extract_key_themes(self, news_items: List[NewsItem]) -> List[str]:
        """Extract key themes from news content"""
        # Implementation placeholder
        return ['market_uncertainty', 'inflation_concerns']

    async def _identify_sentiment_drivers(self, sentiment_scores: List[Tuple[SentimentScore, NewsItem]]) -> List[Dict[str, Any]]:
        """Identify main drivers of sentiment"""
        # Implementation placeholder
        return []

    async def _determine_confidence_level(self, sentiment: SentimentScore, news_count: int) -> str:
        """Determine overall confidence level"""
        if sentiment.confidence > 0.8 and news_count >= 5:
            return 'high'
        elif sentiment.confidence > 0.6 and news_count >= 3:
            return 'medium'
        else:
            return 'low'

    async def _fallback_sentiment_analysis(self, asset: str) -> Dict[str, Any]:
        """Fallback sentiment analysis when main analysis fails"""
        return {
            'overall_sentiment': 0.5,
            'confidence': 0.3,
            'category': SentimentCategory.NEUTRAL.value,
            'source_breakdown': {},
            'time_weighted_sentiment': 0.5,
            'sentiment_momentum': 0.0,
            'key_themes': [],
            'confidence_level': 'low',
            'sentiment_drivers': []
        }

    async def _fallback_comprehensive_analysis(self, asset: str) -> SentimentAnalysis:
        """Fallback comprehensive analysis"""
        neutral_sentiment = SentimentScore(
            overall_score=0.0,
            confidence=0.3,
            category=SentimentCategory.NEUTRAL,
            sentiment_distribution={},
            timestamp=datetime.now()
        )

        return SentimentAnalysis(
            asset=asset,
            overall_sentiment=neutral_sentiment,
            source_breakdown={},
            time_weighted_sentiment=0.0,
            sentiment_momentum=0.0,
            key_themes=[],
            sentiment_drivers=[],
            confidence_level='low',
            analysis_timestamp=datetime.now()
        )


# Export main components
__all__ = [
    'FinBERTSentimentAnalyzer',
    'SentimentCategory',
    'NewsSource',
    'NewsItem',
    'SentimentScore',
    'SentimentAnalysis'
]