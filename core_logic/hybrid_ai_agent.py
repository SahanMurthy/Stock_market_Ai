# core_logic/hybrid_ai_agent.py - PRODUCTION READY

import os
import json
import logging
import pickle
import re
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

# Safe imports
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    RandomForestRegressor = None
    StandardScaler = None

import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class HybridAIAgent:
    """
    Hybrid AI system combining:
    - Gemini AI (primary)
    - Local ML model (fallback + continuous training)
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.use_gemini = False
        self.gemini_model = None

        # Initialize Gemini if available
        if GENAI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                self.use_gemini = True
                logger.info("✅ Gemini AI initialized")
            except Exception as e:
                logger.warning(f"⚠️  Gemini init failed: {e}. Using local ML model.")
                self.use_gemini = False
        else:
            logger.warning("⚠️  Gemini API not available. Using local ML model only.")

        # Initialize local ML model
        self.ml_model = None
        self.scaler = None
        self.model_path = 'models/stock_predictor.pkl'
        self.scaler_path = 'models/scaler.pkl'

        if SKLEARN_AVAILABLE:
            self.scaler = StandardScaler()
            self._load_or_create_model()
        else:
            logger.warning("⚠️  scikit-learn not available. ML features disabled.")

        # Training data buffer
        self.training_data = []
        self.max_training_samples = 1000

    def _load_or_create_model(self):
        """Load existing model or create new one"""
        if not SKLEARN_AVAILABLE:
            return

        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                with open(self.model_path, 'rb') as f:
                    self.ml_model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info("✅ Local ML model loaded")
            else:
                self.ml_model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
                logger.info("✅ New ML model created")
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            self.ml_model = RandomForestRegressor(n_estimators=50, random_state=42)

    def analyze_stock(
            self,
            symbol: str,
            current_price: float,
            investment_amount: float,
            stock_type: str,
            technical_data: Dict,
            historical_data: pd.DataFrame = None
    ) -> Dict:
        """
        Analyze stock using Gemini (if available) or local ML model
        """

        # Try Gemini first
        if self.use_gemini:
            try:
                return self._analyze_with_gemini(
                    symbol, current_price, investment_amount,
                    stock_type, technical_data
                )
            except Exception as e:
                logger.warning(f"Gemini failed for {symbol}: {e}. Using ML model.")

        # Fallback to local ML model
        return self._analyze_with_ml(
            symbol, current_price, investment_amount,
            stock_type, technical_data, historical_data
        )

    def _analyze_with_gemini(
            self,
            symbol: str,
            current_price: float,
            investment_amount: float,
            stock_type: str,
            technical_data: Dict
    ) -> Dict:
        """Use Gemini AI for analysis"""

        prompt = f"""You are an expert stock market analyst. Analyze {symbol} and provide recommendations.

**Current Data:**
- Price: ₹{current_price:.2f}
- Investment: ₹{investment_amount:,.0f}
- Category: {stock_type}
- RSI: {technical_data.get('rsi', 'N/A')}
- SMA(20): ₹{technical_data.get('sma_20', 'N/A')}
- Volatility: {technical_data.get('volatility', 'N/A')}%
- Volume Trend: {technical_data.get('volume_trend', 'N/A')}

**Provide analysis in VALID JSON format ONLY (no markdown, no extra text):**
{{
  "action": "BUY or SELL or HOLD",
  "confidence": 75,
  "target_price": 1200.0,
  "stop_loss": 1000.0,
  "expected_return": 12.5,
  "risk_level": "LOW or MEDIUM or HIGH",
  "time_horizon": "3-6 months",
  "reasoning": "Brief analysis in 1-2 sentences",
  "key_signals": ["signal1", "signal2", "signal3"]
}}
"""

        response = self.gemini_model.generate_content(prompt)
        analysis = self._parse_response(response.text)
        analysis['source'] = 'Gemini AI'

        # Store for training
        self._store_prediction(symbol, current_price, technical_data, analysis)

        return analysis

    def _analyze_with_ml(
            self,
            symbol: str,
            current_price: float,
            investment_amount: float,
            stock_type: str,
            technical_data: Dict,
            historical_data: pd.DataFrame = None
    ) -> Dict:
        """Use local ML model for analysis"""

        # Extract features
        features = self._extract_features(current_price, technical_data)

        # Predict if model is trained and sklearn available
        if SKLEARN_AVAILABLE and self.ml_model and hasattr(self.ml_model, 'feature_importances_'):
            try:
                features_scaled = self.scaler.transform([features])
                predicted_change = self.ml_model.predict(features_scaled)[0]
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}")
                predicted_change = 0.08
        else:
            # Model not trained yet - use heuristics
            predicted_change = 0.08
            rsi = technical_data.get('rsi', 50)
            if rsi < 30:
                predicted_change = 0.12  # Oversold - higher potential
            elif rsi > 70:
                predicted_change = 0.04  # Overbought - lower potential

        target_price = current_price * (1 + predicted_change)
        stop_loss = current_price * 0.92

        # Determine action
        if predicted_change > 0.10:
            action = 'BUY'
            confidence = min(85, 60 + int(predicted_change * 100))
        elif predicted_change < -0.05:
            action = 'SELL'
            confidence = 70
        else:
            action = 'HOLD'
            confidence = 65

        analysis = {
            'action': action,
            'confidence': int(confidence),
            'target_price': round(target_price, 2),
            'stop_loss': round(stop_loss, 2),
            'expected_return': round(predicted_change * 100, 2),
            'risk_level': self._calculate_risk(technical_data.get('volatility', 0)),
            'time_horizon': '3-6 months',
            'reasoning': f'Technical analysis based on RSI: {technical_data.get("rsi", "N/A")}, Volatility: {technical_data.get("volatility", "N/A")}%. {"ML model trained with " + str(len(self.training_data)) + " patterns." if self.ml_model else "Rule-based analysis."}',
            'key_signals': self._generate_signals(technical_data),
            'source': 'Local ML Model' if SKLEARN_AVAILABLE else 'Rule-based Analysis'
        }

        return analysis

    def _extract_features(self, price: float, technical_data: Dict) -> List[float]:
        """Extract numerical features for ML model"""
        return [
            technical_data.get('rsi', 50) / 100,
            technical_data.get('volatility', 0) / 100,
            technical_data.get('sma_20', price) / price,
            technical_data.get('sma_50', price) / price,
            1 if technical_data.get('volume_trend') == 'Increasing' else 0,
            technical_data.get('support', price) / price,
            technical_data.get('resistance', price) / price
        ]

    def _calculate_risk(self, volatility: float) -> str:
        """Calculate risk level from volatility"""
        if volatility < 15:
            return 'LOW'
        elif volatility < 30:
            return 'MEDIUM'
        else:
            return 'HIGH'

    def _generate_signals(self, technical_data: Dict) -> List[str]:
        """Generate key trading signals"""
        signals = []

        rsi = technical_data.get('rsi', 50)
        if rsi < 30:
            signals.append("Oversold - potential buy")
        elif rsi > 70:
            signals.append("Overbought - consider profit booking")
        else:
            signals.append("Neutral RSI")

        if technical_data.get('volume_trend') == 'Increasing':
            signals.append("Strong volume momentum")
        else:
            signals.append("Weak volume")

        volatility = technical_data.get('volatility', 0)
        if volatility > 25:
            signals.append("High volatility - use tight stop-loss")
        else:
            signals.append("Low volatility")

        return signals[:5]

    def _store_prediction(self, symbol: str, price: float,
                          technical_data: Dict, analysis: Dict):
        """Store prediction for later training"""
        if not SKLEARN_AVAILABLE:
            return

        self.training_data.append({
            'symbol': symbol,
            'price': price,
            'features': self._extract_features(price, technical_data),
            'prediction': analysis.get('expected_return', 0) / 100,
            'timestamp': datetime.now()
        })

        # Keep only recent samples
        if len(self.training_data) > self.max_training_samples:
            self.training_data = self.training_data[-self.max_training_samples:]

    def train_model(self):
        """Train/retrain ML model with collected data"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, skipping training")
            return False

        if len(self.training_data) < 50:
            logger.info(f"Not enough data to train. Have {len(self.training_data)}/50 samples")
            return False

        try:
            X = np.array([d['features'] for d in self.training_data])
            y = np.array([d['prediction'] for d in self.training_data])

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.ml_model.fit(X_scaled, y)

            # Save model
            os.makedirs('models', exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.ml_model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)

            logger.info(f"✅ Model trained with {len(self.training_data)} samples")
            return True

        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False

    def _parse_response(self, text: str) -> Dict:
        """Parse AI response - extract JSON"""
        try:
            # Remove markdown code blocks
            text = text.replace('``````', '').strip()

            # Try direct JSON parse
            try:
                return json.loads(text)
            except:
                pass

            # Find JSON pattern
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, text, re.DOTALL)

            for match in matches:
                try:
                    data = json.loads(match)
                    if 'action' in data and 'confidence' in data:
                        return data
                except:
                    continue

            # Find first { to last }
            start = text.find('{')
            end = text.rfind('}')

            if start != -1 and end > start:
                json_str = text[start:end + 1]
                return json.loads(json_str)

        except Exception as e:
            logger.error(f"Parsing failed: {e}")

        # Fallback
        return {
            'action': 'HOLD',
            'confidence': 50,
            'target_price': 0,
            'stop_loss': 0,
            'expected_return': 5.0,
            'risk_level': 'MEDIUM',
            'time_horizon': '3-6 months',
            'reasoning': 'Analysis unavailable - using conservative defaults',
            'key_signals': ['Awaiting response']
        }
