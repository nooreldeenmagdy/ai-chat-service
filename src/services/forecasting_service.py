import numpy as np
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error

logger = logging.getLogger(__name__)

class ForecastingService:
    """Time series forecasting service using ARIMA model"""
    
    def __init__(self):
        self.model = None
        self.fitted = False
    
    def prepare_data(self, data: List[float], dates: List[str] = None) -> pd.Series:
        """Prepare data for forecasting"""
        if dates:
            try:
                date_index = pd.to_datetime(dates)
            except Exception:
                # If date parsing fails, create a simple index
                date_index = pd.date_range(
                    start=datetime.now() - timedelta(days=len(data)-1),
                    periods=len(data),
                    freq='D'
                )
        else:
            date_index = pd.date_range(
                start=datetime.now() - timedelta(days=len(data)-1),
                periods=len(data),
                freq='D'
            )
        
        return pd.Series(data, index=date_index)
    
    def find_best_arima_order(self, data: pd.Series) -> tuple:
        """Find the best ARIMA order using AIC"""
        best_aic = float('inf')
        best_order = (1, 1, 1)
        
        # Try different ARIMA orders
        for p in range(0, 3):
            for d in range(0, 2):
                for q in range(0, 3):
                    try:
                        model = ARIMA(data, order=(p, d, q))
                        fitted_model = model.fit()
                        aic = fitted_model.aic
                        
                        if aic < best_aic:
                            best_aic = aic
                            best_order = (p, d, q)
                    except Exception:
                        continue
        
        return best_order
    
    def forecast(
        self, 
        data: List[float], 
        dates: List[str] = None,
        steps: int = 5,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Generate forecasts using ARIMA model
        
        Args:
            data: List of numerical values for time series
            dates: Optional list of date strings
            steps: Number of forecast steps
            confidence_level: Confidence level for prediction intervals
        
        Returns:
            Dictionary containing forecasts and metadata
        """
        start_time = datetime.now()
        
        try:
            # Validate input
            if len(data) < 10:
                raise ValueError("Need at least 10 data points for reliable forecasting")
            
            if not all(isinstance(x, (int, float)) for x in data):
                raise ValueError("All data points must be numeric")
            
            # Prepare data
            ts_data = self.prepare_data(data, dates)
            
            # Find best ARIMA order
            best_order = self.find_best_arima_order(ts_data)
            
            # Fit ARIMA model
            model = ARIMA(ts_data, order=best_order)
            fitted_model = model.fit()
            
            # Generate forecasts
            forecast_result = fitted_model.forecast(
                steps=steps,
                alpha=1-confidence_level
            )
            
            forecast_values = forecast_result.tolist()
            
            # Generate forecast dates
            last_date = ts_data.index[-1]
            forecast_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=steps,
                freq='D'
            )
            
            # Calculate model performance on historical data
            fitted_values = fitted_model.fittedvalues
            residuals = ts_data - fitted_values
            mae = mean_absolute_error(ts_data[1:], fitted_values[1:])  # Skip first fitted value
            rmse = np.sqrt(mean_squared_error(ts_data[1:], fitted_values[1:]))
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "forecasts": [
                    {
                        "date": date.isoformat()[:10],
                        "value": float(value),
                        "index": i + 1
                    }
                    for i, (date, value) in enumerate(zip(forecast_dates, forecast_values))
                ],
                "model_info": {
                    "model_type": "ARIMA",
                    "order": best_order,
                    "aic": float(fitted_model.aic),
                    "data_points_used": len(data)
                },
                "performance_metrics": {
                    "mae": float(mae),
                    "rmse": float(rmse),
                    "mean_residual": float(np.mean(residuals)),
                    "residual_std": float(np.std(residuals))
                },
                "metadata": {
                    "processing_time_ms": processing_time,
                    "confidence_level": confidence_level,
                    "forecast_horizon": steps,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info(f"Forecast generated successfully - Model: ARIMA{best_order}, Steps: {steps}, Processing time: {processing_time:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Forecasting error: {str(e)}")
            raise ValueError(f"Forecasting failed: {str(e)}")
    
    def validate_time_series(self, data: List[float]) -> Dict[str, Any]:
        """Validate and analyze time series data"""
        try:
            ts_data = self.prepare_data(data)
            
            return {
                "is_valid": True,
                "length": len(data),
                "statistics": {
                    "mean": float(np.mean(data)),
                    "std": float(np.std(data)),
                    "min": float(np.min(data)),
                    "max": float(np.max(data)),
                    "trend": "increasing" if data[-1] > data[0] else "decreasing"
                },
                "missing_values": sum(1 for x in data if x is None or np.isnan(x)),
                "recommendations": self._get_recommendations(data)
            }
        except Exception as e:
            return {
                "is_valid": False,
                "error": str(e),
                "recommendations": ["Fix data quality issues before forecasting"]
            }
    
    def _get_recommendations(self, data: List[float]) -> List[str]:
        """Get recommendations for time series forecasting"""
        recommendations = []
        
        if len(data) < 20:
            recommendations.append("Consider collecting more data points for better accuracy")
        
        if np.std(data) == 0:
            recommendations.append("Data shows no variation - forecasting may not be meaningful")
        
        if len(data) < 50:
            recommendations.append("For seasonal patterns, consider collecting at least 2-3 cycles of data")
        
        return recommendations

# Global forecasting service instance
forecasting_service = ForecastingService()
