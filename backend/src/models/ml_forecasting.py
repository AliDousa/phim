"""
Machine learning models for epidemiological forecasting and analysis.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from typing import Dict, List, Tuple, Optional, Any
import json
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')


@dataclass
class ForecastResult:
    """Results from forecasting model."""
    predictions: np.ndarray
    confidence_intervals: Optional[Tuple[np.ndarray, np.ndarray]]
    model_metrics: Dict[str, float]
    feature_importance: Optional[Dict[str, float]]


class TimeSeriesForecaster:
    """
    Time series forecasting for epidemiological data using machine learning.
    """
    
    def __init__(self, model_type: str = 'random_forest'):
        self.model_type = model_type
        self.model = None
        self.is_fitted = False
        self.feature_names = []
        
        # Initialize model based on type
        if model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                random_state=42
            )
        elif model_type == 'linear':
            self.model = LinearRegression()
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    def create_features(self, 
                       data: pd.DataFrame, 
                       target_col: str,
                       lag_features: int = 7,
                       rolling_features: List[int] = [3, 7, 14]) -> pd.DataFrame:
        """
        Create features for time series forecasting.
        
        Args:
            data: Input time series data
            target_col: Name of target column
            lag_features: Number of lag features to create
            rolling_features: Window sizes for rolling statistics
            
        Returns:
            DataFrame with engineered features
        """
        df = data.copy()
        
        # Create lag features
        for lag in range(1, lag_features + 1):
            df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
        
        # Create rolling statistics
        for window in rolling_features:
            df[f'{target_col}_rolling_mean_{window}'] = df[target_col].rolling(window).mean()
            df[f'{target_col}_rolling_std_{window}'] = df[target_col].rolling(window).std()
            df[f'{target_col}_rolling_min_{window}'] = df[target_col].rolling(window).min()
            df[f'{target_col}_rolling_max_{window}'] = df[target_col].rolling(window).max()
        
        # Create trend features
        df['trend'] = range(len(df))
        df['trend_squared'] = df['trend'] ** 2
        
        # Create seasonal features if date column exists
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['day_of_week'] = df['date'].dt.dayofweek
            df['day_of_year'] = df['date'].dt.dayofyear
            df['month'] = df['date'].dt.month
            df['quarter'] = df['date'].dt.quarter
        
        # Create difference features
        df[f'{target_col}_diff_1'] = df[target_col].diff(1)
        df[f'{target_col}_diff_7'] = df[target_col].diff(7)
        
        return df
    
    def prepare_data(self, 
                    data: pd.DataFrame, 
                    target_col: str,
                    test_size: int = 30) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare data for training and testing.
        
        Args:
            data: Input data with features
            target_col: Target column name
            test_size: Number of samples for testing
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        # Remove rows with NaN values
        df_clean = data.dropna()
        
        # Separate features and target
        feature_cols = [col for col in df_clean.columns if col != target_col and col != 'date']
        self.feature_names = feature_cols
        
        X = df_clean[feature_cols].values
        y = df_clean[target_col].values
        
        # Split data (time series split)
        split_idx = len(X) - test_size
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        return X_train, X_test, y_train, y_test
    
    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """
        Fit the forecasting model.
        
        Args:
            X_train: Training features
            y_train: Training targets
        """
        self.model.fit(X_train, y_train)
        self.is_fitted = True
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions.
        
        Args:
            X: Input features
            
        Returns:
            Predictions
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        return self.model.predict(X)
    
    def forecast(self, 
                data: pd.DataFrame,
                target_col: str,
                forecast_horizon: int = 30,
                confidence_level: float = 0.95) -> ForecastResult:
        """
        Generate forecasts with confidence intervals.
        
        Args:
            data: Historical data
            target_col: Target column name
            forecast_horizon: Number of periods to forecast
            confidence_level: Confidence level for intervals
            
        Returns:
            ForecastResult object
        """
        # Create features
        df_features = self.create_features(data, target_col)
        
        # Prepare data
        X_train, X_test, y_train, y_test = self.prepare_data(df_features, target_col)
        
        # Fit model
        self.fit(X_train, y_train)
        
        # Make predictions on test set
        y_pred = self.predict(X_test)
        
        # Calculate metrics
        metrics = {
            'mae': mean_absolute_error(y_test, y_pred),
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred)
        }
        
        # Generate future forecasts
        last_row = df_features.iloc[-1:].copy()
        forecasts = []
        
        for i in range(forecast_horizon):
            # Prepare features for next prediction
            X_next = last_row[self.feature_names].values
            
            # Make prediction
            pred = self.predict(X_next)[0]
            forecasts.append(pred)
            
            # Update features for next iteration
            # This is a simplified approach - in practice, you'd update all lag features
            last_row[target_col] = pred
            last_row = self.create_features(last_row, target_col).iloc[-1:]
        
        forecasts = np.array(forecasts)
        
        # Calculate feature importance
        feature_importance = None
        if hasattr(self.model, 'feature_importances_'):
            feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
        
        # Simple confidence intervals (would use more sophisticated methods in practice)
        residuals = y_test - y_pred
        std_residual = np.std(residuals)
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
        
        lower_bound = forecasts - z_score * std_residual
        upper_bound = forecasts + z_score * std_residual
        
        return ForecastResult(
            predictions=forecasts,
            confidence_intervals=(lower_bound, upper_bound),
            model_metrics=metrics,
            feature_importance=feature_importance
        )
    
    def cross_validate(self, 
                      data: pd.DataFrame,
                      target_col: str,
                      cv_folds: int = 5) -> Dict[str, float]:
        """
        Perform time series cross-validation.
        
        Args:
            data: Input data
            target_col: Target column name
            cv_folds: Number of CV folds
            
        Returns:
            Cross-validation metrics
        """
        # Create features
        df_features = self.create_features(data, target_col)
        df_clean = df_features.dropna()
        
        # Prepare data
        feature_cols = [col for col in df_clean.columns if col != target_col and col != 'date']
        X = df_clean[feature_cols].values
        y = df_clean[target_col].values
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=cv_folds)
        
        # Calculate cross-validation scores
        cv_scores = cross_val_score(self.model, X, y, cv=tscv, scoring='neg_mean_squared_error')
        
        return {
            'cv_rmse_mean': np.sqrt(-cv_scores.mean()),
            'cv_rmse_std': np.sqrt(cv_scores.std()),
            'cv_scores': cv_scores.tolist()
        }


class EnsembleForecaster:
    """
    Ensemble forecasting combining multiple models.
    """
    
    def __init__(self, models: Optional[List[str]] = None):
        self.models = models or ['random_forest', 'gradient_boosting', 'linear']
        self.forecasters = {}
        self.weights = {}
        
        # Initialize individual forecasters
        for model_type in self.models:
            self.forecasters[model_type] = TimeSeriesForecaster(model_type)
    
    def fit_ensemble(self, 
                    data: pd.DataFrame,
                    target_col: str,
                    validation_size: int = 30) -> None:
        """
        Fit ensemble models and calculate weights.
        
        Args:
            data: Training data
            target_col: Target column name
            validation_size: Size of validation set for weight calculation
        """
        # Split data for validation
        train_data = data.iloc[:-validation_size]
        val_data = data.iloc[-validation_size:]
        
        model_errors = {}
        
        for model_type, forecaster in self.forecasters.items():
            try:
                # Create features and prepare data
                df_features = forecaster.create_features(train_data, target_col)
                X_train, _, y_train, _ = forecaster.prepare_data(df_features, target_col, test_size=0)
                
                # Fit model
                forecaster.fit(X_train, y_train)
                
                # Validate on validation set
                val_features = forecaster.create_features(val_data, target_col)
                val_clean = val_features.dropna()
                
                if len(val_clean) > 0:
                    X_val = val_clean[forecaster.feature_names].values
                    y_val = val_clean[target_col].values
                    
                    y_pred = forecaster.predict(X_val)
                    error = mean_squared_error(y_val, y_pred)
                    model_errors[model_type] = error
                else:
                    model_errors[model_type] = float('inf')
                    
            except Exception as e:
                print(f"Error fitting {model_type}: {e}")
                model_errors[model_type] = float('inf')
        
        # Calculate weights (inverse of error)
        total_inv_error = sum(1/error if error > 0 else 0 for error in model_errors.values())
        
        if total_inv_error > 0:
            self.weights = {
                model: (1/error) / total_inv_error if error > 0 else 0
                for model, error in model_errors.items()
            }
        else:
            # Equal weights if all models failed
            self.weights = {model: 1/len(self.models) for model in self.models}
    
    def ensemble_forecast(self, 
                         data: pd.DataFrame,
                         target_col: str,
                         forecast_horizon: int = 30) -> ForecastResult:
        """
        Generate ensemble forecasts.
        
        Args:
            data: Historical data
            target_col: Target column name
            forecast_horizon: Forecast horizon
            
        Returns:
            Ensemble forecast results
        """
        individual_forecasts = {}
        individual_metrics = {}
        
        # Get forecasts from each model
        for model_type, forecaster in self.forecasters.items():
            try:
                result = forecaster.forecast(data, target_col, forecast_horizon)
                individual_forecasts[model_type] = result.predictions
                individual_metrics[model_type] = result.model_metrics
            except Exception as e:
                print(f"Error forecasting with {model_type}: {e}")
                individual_forecasts[model_type] = np.zeros(forecast_horizon)
                individual_metrics[model_type] = {'mae': float('inf')}
        
        # Combine forecasts using weights
        ensemble_predictions = np.zeros(forecast_horizon)
        for model_type, predictions in individual_forecasts.items():
            weight = self.weights.get(model_type, 0)
            ensemble_predictions += weight * predictions
        
        # Calculate ensemble metrics (simplified)
        ensemble_metrics = {
            'ensemble_weights': self.weights,
            'individual_metrics': individual_metrics
        }
        
        return ForecastResult(
            predictions=ensemble_predictions,
            confidence_intervals=None,  # Would implement ensemble confidence intervals
            model_metrics=ensemble_metrics,
            feature_importance=None
        )


class ParameterEstimator:
    """
    Bayesian parameter estimation for epidemiological models.
    """
    
    def __init__(self):
        self.estimated_parameters = {}
        self.parameter_distributions = {}
    
    def estimate_seir_parameters(self, 
                                observed_data: pd.DataFrame,
                                prior_parameters: Optional[Dict] = None) -> Dict[str, float]:
        """
        Estimate SEIR model parameters from observed data.
        
        Args:
            observed_data: Observed epidemic data
            prior_parameters: Prior parameter estimates
            
        Returns:
            Estimated parameters
        """
        # Simplified parameter estimation using least squares
        # In practice, would use MCMC or other Bayesian methods
        
        if 'infectious' not in observed_data.columns:
            raise ValueError("Data must contain 'infectious' column")
        
        infectious = observed_data['infectious'].values
        time = np.arange(len(infectious))
        
        # Estimate growth rate from early exponential phase
        early_phase = infectious[:min(10, len(infectious)//3)]
        if len(early_phase) > 2 and np.all(early_phase > 0):
            log_infectious = np.log(early_phase)
            growth_rate = np.polyfit(range(len(early_phase)), log_infectious, 1)[0]
        else:
            growth_rate = 0.1
        
        # Estimate parameters based on growth rate and data characteristics
        estimated_gamma = 1/10  # Assume 10-day infectious period
        estimated_sigma = 1/5   # Assume 5-day incubation period
        estimated_beta = growth_rate + estimated_gamma + estimated_sigma
        
        # Apply priors if provided
        if prior_parameters:
            alpha = 0.3  # Weight for prior
            estimated_beta = alpha * prior_parameters.get('beta', estimated_beta) + (1-alpha) * estimated_beta
            estimated_gamma = alpha * prior_parameters.get('gamma', estimated_gamma) + (1-alpha) * estimated_gamma
            estimated_sigma = alpha * prior_parameters.get('sigma', estimated_sigma) + (1-alpha) * estimated_sigma
        
        self.estimated_parameters = {
            'beta': max(0.01, estimated_beta),
            'gamma': max(0.01, estimated_gamma),
            'sigma': max(0.01, estimated_sigma),
            'r0': max(0.01, estimated_beta) / max(0.01, estimated_gamma)
        }
        
        return self.estimated_parameters
    
    def uncertainty_quantification(self, 
                                  observed_data: pd.DataFrame,
                                  n_samples: int = 1000) -> Dict[str, Dict[str, float]]:
        """
        Quantify parameter uncertainty using bootstrap sampling.
        
        Args:
            observed_data: Observed data
            n_samples: Number of bootstrap samples
            
        Returns:
            Parameter uncertainty estimates
        """
        parameter_samples = {'beta': [], 'gamma': [], 'sigma': [], 'r0': []}
        
        for _ in range(n_samples):
            # Bootstrap sample
            sample_indices = np.random.choice(len(observed_data), size=len(observed_data), replace=True)
            sample_data = observed_data.iloc[sample_indices].reset_index(drop=True)
            
            try:
                # Estimate parameters for this sample
                params = self.estimate_seir_parameters(sample_data)
                for param, value in params.items():
                    parameter_samples[param].append(value)
            except:
                # Skip failed samples
                continue
        
        # Calculate uncertainty statistics
        uncertainty_stats = {}
        for param, samples in parameter_samples.items():
            if samples:
                uncertainty_stats[param] = {
                    'mean': np.mean(samples),
                    'std': np.std(samples),
                    'median': np.median(samples),
                    'q025': np.percentile(samples, 2.5),
                    'q975': np.percentile(samples, 97.5)
                }
            else:
                uncertainty_stats[param] = {
                    'mean': 0, 'std': 0, 'median': 0, 'q025': 0, 'q975': 0
                }
        
        return uncertainty_stats


def create_forecaster(model_type: str = 'ensemble') -> Any:
    """
    Factory function to create forecasting models.
    
    Args:
        model_type: Type of forecaster to create
        
    Returns:
        Configured forecaster
    """
    if model_type == 'ensemble':
        return EnsembleForecaster()
    else:
        return TimeSeriesForecaster(model_type)


def create_parameter_estimator() -> ParameterEstimator:
    """
    Factory function to create parameter estimator.
    
    Returns:
        Parameter estimator instance
    """
    return ParameterEstimator()

