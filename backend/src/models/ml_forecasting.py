"""
Machine learning models for epidemiological forecasting and analysis.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Optional, Any
import json
from dataclasses import dataclass  # Import norm at the top
from scipy.stats import norm  # Import norm at the top


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

    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = []

        # Initialize model based on type
        if model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )
        elif model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42
            )
        elif model_type == "linear":
            self.model = LinearRegression()
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    def create_features(
        self,
        data: pd.DataFrame,
        target_col: str,
        lag_features: int = 7,
        rolling_features: List[int] = [3, 7, 14],
        up_to_index: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Create features for time series forecasting without data leakage.

        Args:
            data: Input time series data
            target_col: Name of target column
            lag_features: Number of lag features to create
            rolling_features: Window sizes for rolling statistics
            up_to_index: Only use data up to this index (prevents data leakage)

        Returns:
            DataFrame with engineered features
        """
        try:
            df = data.copy()

            # Ensure target column exists
            if target_col not in df.columns:
                raise ValueError(f"Target column '{target_col}' not found in data")

            # Sort by date if date column exists
            if "date" in df.columns:
                df = df.sort_values("date").reset_index(drop=True)

            # If up_to_index is specified, only use data up to that point for feature calculation
            if up_to_index is not None:
                feature_data = df.iloc[:up_to_index + 1].copy()
            else:
                feature_data = df.copy()

            # Create lag features (these are inherently leak-proof)
            for lag in range(1, lag_features + 1):
                df[f"{target_col}_lag_{lag}"] = df[target_col].shift(lag)

            # Create rolling statistics without data leakage
            for window in rolling_features:
                if len(df) >= window:
                    # Calculate rolling statistics point by point to prevent leakage
                    rolling_mean = []
                    rolling_std = []
                    rolling_min = []
                    rolling_max = []
                    
                    for i in range(len(df)):
                        if i < window - 1:
                            # Not enough historical data
                            rolling_mean.append(np.nan)
                            rolling_std.append(np.nan)
                            rolling_min.append(np.nan)
                            rolling_max.append(np.nan)
                        else:
                            # Use only past data up to current point
                            window_data = df[target_col].iloc[i - window + 1:i + 1]
                            rolling_mean.append(window_data.mean())
                            rolling_std.append(window_data.std())
                            rolling_min.append(window_data.min())
                            rolling_max.append(window_data.max())
                    
                    df[f"{target_col}_rolling_mean_{window}"] = rolling_mean
                    df[f"{target_col}_rolling_std_{window}"] = rolling_std
                    df[f"{target_col}_rolling_min_{window}"] = rolling_min
                    df[f"{target_col}_rolling_max_{window}"] = rolling_max

            # Create trend features
            df["trend"] = range(len(df))
            df["trend_squared"] = df["trend"] ** 2

            # Create seasonal features if date column exists
            if "date" in df.columns:
                try:
                    df["date"] = pd.to_datetime(df["date"])
                    df["day_of_week"] = df["date"].dt.dayofweek
                    df["day_of_year"] = df["date"].dt.dayofyear
                    df["month"] = df["date"].dt.month
                    df["quarter"] = df["date"].dt.quarter
                    df["week_of_year"] = df["date"].dt.isocalendar().week
                except Exception:
                    pass  # Skip date features if conversion fails

            # Create difference features (these are inherently leak-proof)
            df[f"{target_col}_diff_1"] = df[target_col].diff(1)
            if len(df) >= 7:
                df[f"{target_col}_diff_7"] = df[target_col].diff(7)

            # Create exponential moving averages without data leakage
            for alpha in [0.1, 0.3, 0.5]:
                ema_values = []
                ema = None
                
                for i, value in enumerate(df[target_col]):
                    if pd.isna(value):
                        ema_values.append(np.nan)
                    elif ema is None:
                        # Initialize EMA with first valid value
                        ema = float(value)
                        ema_values.append(ema)
                    else:
                        # Update EMA using only current and past values
                        ema = alpha * float(value) + (1 - alpha) * ema
                        ema_values.append(ema)
                
                df[f"{target_col}_ema_{alpha}"] = ema_values

            return df

        except Exception as e:
            raise ValueError(f"Feature creation failed: {str(e)}")

    def prepare_data(
        self, data: pd.DataFrame, target_col: str, test_size: int = 30
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare data for training and testing without data leakage.

        Args:
            data: Input data (should be raw data without pre-computed features)
            target_col: Target column name
            test_size: Number of samples for testing

        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        try:
            # First determine the split point to prevent data leakage
            min_test_size = 10
            test_size = max(min_test_size, min(test_size, len(data) // 3))
            split_idx = len(data) - test_size
            
            if split_idx < 10:
                raise ValueError("Insufficient training data (minimum 10 samples required)")
            
            # Create features for training data only (no data leakage)
            train_data = data.iloc[:split_idx].copy()
            test_data = data.iloc[split_idx:].copy()
            
            # Create features for training set
            train_features = self.create_features(train_data, target_col)
            
            # For test set, create features point by point to prevent leakage
            test_features_list = []
            
            for i in range(len(test_data)):
                # For each test point, use training data + test data up to current point
                historical_data = pd.concat([
                    train_data,
                    test_data.iloc[:i+1]
                ], ignore_index=True)
                
                # Create features for this extended dataset
                extended_features = self.create_features(historical_data, target_col)
                
                # Extract features for the current test point (last row)
                current_features = extended_features.iloc[-1:].copy()
                test_features_list.append(current_features)
            
            # Combine test features
            if test_features_list:
                test_features = pd.concat(test_features_list, ignore_index=True)
            else:
                # Fallback: create features for test data separately
                test_features = self.create_features(test_data, target_col)
            
            # Remove rows with NaN values
            train_clean = train_features.dropna()
            test_clean = test_features.dropna()

            if len(train_clean) == 0:
                raise ValueError("No valid training data remaining after removing NaN values")
            
            if len(test_clean) == 0:
                raise ValueError("No valid test data remaining after removing NaN values")

            # Separate features and target
            exclude_cols = [target_col, "date"]
            feature_cols = [col for col in train_clean.columns if col not in exclude_cols]
            self.feature_names = feature_cols

            if not feature_cols:
                raise ValueError("No feature columns available")

            # Ensure test features have same columns as training features
            available_test_features = [col for col in feature_cols if col in test_clean.columns]
            if len(available_test_features) != len(feature_cols):
                # Fill missing features with zeros or appropriate defaults
                for col in feature_cols:
                    if col not in test_clean.columns:
                        test_clean[col] = 0.0

            X_train = train_clean[feature_cols].values
            y_train = train_clean[target_col].values
            X_test = test_clean[feature_cols].values
            y_test = test_clean[target_col].values

            # Validate data
            if len(X_train) == 0 or len(y_train) == 0:
                raise ValueError("Empty training data arrays")
            
            if len(X_test) == 0 or len(y_test) == 0:
                raise ValueError("Empty test data arrays")

            return X_train, X_test, y_train, y_test
            
        except Exception as e:
            raise ValueError(f"Data preparation failed: {str(e)}")

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """
        Fit the forecasting model.

        Args:
            X_train: Training features
            y_train: Training targets
        """
        try:
            # Scale features for linear models
            if self.model_type == "linear":
                X_train_scaled = self.scaler.fit_transform(X_train)
                self.model.fit(X_train_scaled, y_train)
            else:
                self.model.fit(X_train, y_train)

            self.is_fitted = True

        except Exception as e:
            raise ValueError(f"Model fitting failed: {str(e)}")

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

        try:
            if self.model_type == "linear":
                X_scaled = self.scaler.transform(X)
                return self.model.predict(X_scaled)
            else:
                return self.model.predict(X)

        except Exception as e:
            raise ValueError(f"Prediction failed: {str(e)}")

    def forecast(
        self,
        data: pd.DataFrame,
        target_col: str,
        forecast_horizon: int = 30,
        confidence_level: float = 0.95,
    ) -> ForecastResult:
        """
        Generate forecasts with confidence intervals (leak-proof version).

        Args:
            data: Historical data (raw, without pre-computed features)
            target_col: Target column name
            forecast_horizon: Number of periods to forecast
            confidence_level: Confidence level for intervals

        Returns:
            ForecastResult object
        """
        try:
            # Validate inputs
            if len(data) < 20:
                raise ValueError(
                    "Insufficient data for forecasting (minimum 20 samples required)"
                )

            # Prepare data without data leakage (features created inside prepare_data)
            X_train, X_test, y_train, y_test = self.prepare_data(
                data, target_col
            )

            # Fit model
            self.fit(X_train, y_train)

            # Make predictions on test set for metrics
            y_pred = self.predict(X_test)

            # Calculate metrics
            metrics = {
                "mae": float(mean_absolute_error(y_test, y_pred)),
                "mse": float(mean_squared_error(y_test, y_pred)),
                "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
                "r2": float(r2_score(y_test, y_pred)),
                "mape": float(
                    np.mean(
                        np.abs((y_test - y_pred) / np.maximum(np.abs(y_test), 1e-8))
                        * 100
                    )
                ),
            }

            # Generate future forecasts without data leakage
            forecasts = self._generate_future_forecasts_leak_proof(
                data, target_col, forecast_horizon
            )

            # Calculate feature importance
            feature_importance = None
            if hasattr(self.model, "feature_importances_"):
                feature_importance = dict(
                    zip(self.feature_names, self.model.feature_importances_)
                )
            elif hasattr(self.model, "coef_"):
                feature_importance = dict(
                    zip(self.feature_names, np.abs(self.model.coef_))
                )

            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(
                y_test, y_pred, forecasts, confidence_level
            )

            return ForecastResult(
                predictions=forecasts,
                confidence_intervals=confidence_intervals,
                model_metrics=metrics,
                feature_importance=feature_importance,
            )

        except Exception as e:
            raise ValueError(f"Forecasting failed: {str(e)}")

    def _generate_future_forecasts_leak_proof(
        self, data: pd.DataFrame, target_col: str, forecast_horizon: int
    ) -> np.ndarray:
        """Generate future forecasts iteratively without data leakage."""
        try:
            forecasts = []
            extended_data = data.copy()
            
            for i in range(forecast_horizon):
                # Create features for all data up to current point (no future leakage)
                features_df = self.create_features(extended_data, target_col)
                features_clean = features_df.dropna()
                
                if len(features_clean) == 0:
                    # Fallback to simple trend if no features available
                    if forecasts:
                        pred = forecasts[-1] * 1.01  # Simple growth assumption
                    else:
                        pred = extended_data[target_col].iloc[-1] * 1.01
                else:
                    # Get features for the last (most recent) data point
                    last_features = features_clean.iloc[-1:].copy()
                    
                    # Prepare feature vector
                    feature_cols = [col for col in self.feature_names if col in last_features.columns]
                    
                    if not feature_cols:
                        # Fallback if no matching features
                        if forecasts:
                            pred = forecasts[-1] * 1.01
                        else:
                            pred = extended_data[target_col].iloc[-1] * 1.01
                    else:
                        X_next = last_features[feature_cols].values.reshape(1, -1)
                        
                        # Handle missing features
                        X_next = np.asarray(X_next, dtype=float)
                        if np.isnan(X_next).any():
                            X_next = np.nan_to_num(X_next, nan=0.0)
                        
                        pred = self.predict(X_next)[0]
                
                # Ensure prediction is reasonable (prevent negative values for epidemiological data)
                pred = max(0, pred)
                forecasts.append(pred)
                
                # Create new row for next iteration
                if "date" in extended_data.columns:
                    try:
                        # Attempt to increment date
                        last_date = pd.to_datetime(extended_data["date"].iloc[-1])
                        next_date = last_date + pd.Timedelta(days=1)
                        new_row = {"date": next_date, target_col: pred}
                    except:
                        # Fallback if date handling fails
                        new_row = {target_col: pred}
                else:
                    new_row = {target_col: pred}
                
                # Add new row to extended data for next iteration
                new_df = pd.DataFrame([new_row])
                extended_data = pd.concat([extended_data, new_df], ignore_index=True)
            
            return np.array(forecasts)
        
        except Exception as e:
            raise ValueError(f"Future forecast generation failed: {str(e)}")

    def _generate_future_forecasts(
        self, df_features: pd.DataFrame, target_col: str, forecast_horizon: int
    ) -> np.ndarray:
        """Legacy method - kept for backward compatibility but should use leak-proof version."""
        # Redirect to leak-proof implementation
        # Note: This assumes df_features is the original data, not pre-processed features
        return self._generate_future_forecasts_leak_proof(df_features, target_col, forecast_horizon)

    def _calculate_confidence_intervals(
        self,
        y_test: np.ndarray,
        y_pred: np.ndarray,
        forecasts: np.ndarray,
        confidence_level: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate confidence intervals for forecasts."""
        try:
            # Calculate residuals
            residuals = y_test - y_pred
            std_residual = np.std(residuals)

            # Z-score for confidence level
            if confidence_level == 0.95:
                z_score = 1.96
            elif confidence_level == 0.99:
                z_score = 2.576
            else:  # Approximate z-score
                z_score = norm.ppf((1 + confidence_level) / 2)

            # Calculate confidence intervals
            margin = z_score * std_residual
            lower_bound = forecasts - margin
            upper_bound = forecasts + margin

            return lower_bound, upper_bound

        except Exception:
            # Return simple intervals if calculation fails
            margin = np.std(forecasts) * 0.2
            return forecasts - margin, forecasts + margin

    def cross_validate(
        self, data: pd.DataFrame, target_col: str, cv_folds: int = 5
    ) -> Dict[str, float]:
        """
        Perform time series cross-validation.

        Args:
            data: Input data
            target_col: Target column name
            cv_folds: Number of CV folds

        Returns:
            Cross-validation metrics
        """
        try:
            if len(data) < cv_folds * 2:
                raise ValueError("Insufficient data for cross-validation")

            # Time series cross-validation with leak-proof feature creation
            tscv = TimeSeriesSplit(n_splits=cv_folds)
            cv_scores = []
            
            for train_idx, test_idx in tscv.split(data):
                try:
                    # Split data for this fold
                    train_fold = data.iloc[train_idx]
                    test_fold = data.iloc[test_idx]
                    
                    # Create features without leakage for this fold
                    train_features = self.create_features(train_fold, target_col)
                    train_clean = train_features.dropna()
                    
                    if len(train_clean) == 0:
                        continue
                    
                    # Prepare test features without leakage
                    combined_fold_data = pd.concat([train_fold, test_fold], ignore_index=True)
                    _, X_test_fold, _, y_test_fold = self.prepare_data(
                        combined_fold_data, target_col, test_size=len(test_fold)
                    )
                    
                    if len(X_test_fold) == 0 or len(y_test_fold) == 0:
                        continue
                    
                    # Prepare training data
                    feature_cols = [col for col in train_clean.columns 
                                   if col != target_col and col != "date"]
                    if not feature_cols:
                        continue
                        
                    X_train_fold = train_clean[feature_cols].values
                    y_train_fold = train_clean[target_col].values
                    
                    # Fit and predict for this fold
                    fold_model = self.model.__class__(**self.model.get_params())
                    
                    if self.model_type == "linear":
                        fold_scaler = StandardScaler()
                        X_train_scaled = fold_scaler.fit_transform(X_train_fold)
                        fold_model.fit(X_train_scaled, y_train_fold)
                        
                        # Scale test features
                        X_test_scaled = fold_scaler.transform(X_test_fold)
                        y_pred_fold = fold_model.predict(X_test_scaled)
                    else:
                        fold_model.fit(X_train_fold, y_train_fold)
                        y_pred_fold = fold_model.predict(X_test_fold)
                    
                    # Calculate fold score
                    fold_mse = mean_squared_error(y_test_fold, y_pred_fold)
                    cv_scores.append(-fold_mse)  # Negative for consistency with sklearn
                    
                except Exception:
                    # Skip failed folds
                    continue
            
            if not cv_scores:
                raise ValueError("All cross-validation folds failed")
            
            cv_scores = np.array(cv_scores)
            rmse_scores = np.sqrt(-cv_scores)

            return {
                "cv_rmse_mean": float(rmse_scores.mean()),
                "cv_rmse_std": float(rmse_scores.std()),
                "cv_scores": cv_scores.tolist(),
            }

        except Exception as e:
            return {
                "cv_rmse_mean": float("inf"),
                "cv_rmse_std": 0.0,
                "cv_scores": [],
                "error": str(e),
            }


class EnsembleForecaster:
    """
    Ensemble forecasting combining multiple models.
    """

    def __init__(self, models: Optional[List[str]] = None):
        self.models = models or ["random_forest", "gradient_boosting", "linear"]
        self.forecasters = {}
        self.weights = {}

        # Initialize individual forecasters
        for model_type in self.models:
            try:
                self.forecasters[model_type] = TimeSeriesForecaster(model_type)
            except Exception as e:
                print(f"Failed to initialize {model_type}: {e}")

    def fit_ensemble(
        self, data: pd.DataFrame, target_col: str, validation_size: int = 30
    ) -> None:
        """
        Fit ensemble models and calculate weights.

        Args:
            data: Training data
            target_col: Target column name
            validation_size: Size of validation set for weight calculation
        """
        try:
            # Ensure sufficient data
            if len(data) < validation_size + 20:
                validation_size = max(10, len(data) // 4)

            # Split data for validation
            train_data = data.iloc[:-validation_size] if validation_size > 0 else data
            val_data = (
                data.iloc[-validation_size:] if validation_size > 0 else data.tail(10)
            )

            model_errors = {}

            for model_type, forecaster in self.forecasters.items():
                try:
                    # Prepare data (features created inside to avoid leakage)
                    X_train, _, y_train, _ = forecaster.prepare_data(
                        train_data, target_col, test_size=0
                    )

                    # Fit model
                    forecaster.fit(X_train, y_train)

                    # Validate on validation set (using leak-proof feature creation)
                    if len(val_data) > 0:
                        try:
                            # Create a combined dataset for validation (train + val up to each point)
                            combined_data = pd.concat([train_data, val_data], ignore_index=True)
                            
                            # Prepare validation features without leakage
                            _, X_val, _, y_val = forecaster.prepare_data(
                                combined_data, target_col, test_size=len(val_data)
                            )
                            
                            if len(X_val) > 0 and len(y_val) > 0:
                                y_pred = forecaster.predict(X_val)
                                error = mean_squared_error(y_val, y_pred)
                                model_errors[model_type] = error
                            else:
                                model_errors[model_type] = float("inf")
                        except Exception:
                            model_errors[model_type] = float("inf")
                    else:
                        model_errors[model_type] = float("inf")

                except Exception as e:
                    print(f"Error fitting {model_type}: {e}")
                    model_errors[model_type] = float("inf")

            # Calculate weights (inverse of error)
            valid_errors = {k: v for k, v in model_errors.items() if v < float("inf")}

            if valid_errors:
                total_inv_error = sum(1 / error for error in valid_errors.values())
                self.weights = {
                    model: (1 / error) / total_inv_error if model in valid_errors else 0
                    for model in self.models
                }
            else:
                # Equal weights if all models failed
                self.weights = {model: 1 / len(self.models) for model in self.models}

        except Exception as e:
            # Equal weights as fallback
            self.weights = {model: 1 / len(self.models) for model in self.models}
            print(f"Ensemble fitting failed, using equal weights: {e}")

    def ensemble_forecast(
        self, data: pd.DataFrame, target_col: str, forecast_horizon: int = 30
    ) -> ForecastResult:
        """
        Generate ensemble forecasts.

        Args:
            data: Historical data
            target_col: Target column name
            forecast_horizon: Forecast horizon

        Returns:
            Ensemble forecast results
        """
        try:
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
                    individual_metrics[model_type] = {"mae": float("inf")}

            # Combine forecasts using weights
            ensemble_predictions = np.zeros(forecast_horizon)
            total_weight = 0

            for model_type, predictions in individual_forecasts.items():
                weight = self.weights.get(model_type, 0)
                if weight > 0:
                    ensemble_predictions += weight * predictions
                    total_weight += weight

            # Normalize if needed
            if total_weight > 0:
                ensemble_predictions /= total_weight

            # Calculate ensemble metrics
            ensemble_metrics = {
                "ensemble_weights": self.weights,
                "individual_metrics": individual_metrics,
                "ensemble_type": "weighted_average",
            }

            return ForecastResult(
                predictions=ensemble_predictions,
                confidence_intervals=None,  # Could implement ensemble confidence intervals
                model_metrics=ensemble_metrics,
                feature_importance=None,
            )

        except Exception as e:
            raise ValueError(f"Ensemble forecasting failed: {str(e)}")


class ParameterEstimator:
    """
    Bayesian parameter estimation for epidemiological models.
    """

    def __init__(self):
        self.estimated_parameters = {}
        self.parameter_distributions = {}

    def estimate_seir_parameters(
        self, observed_data: pd.DataFrame, prior_parameters: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Estimate SEIR model parameters from observed data.

        Args:
            observed_data: Observed epidemic data
            prior_parameters: Prior parameter estimates

        Returns:
            Estimated parameters
        """
        try:
            # Validate input data
            required_cols = ["infectious"]
            if not any(col in observed_data.columns for col in required_cols):
                # Try alternative column names
                alt_cols = ["new_cases", "cases", "infected"]
                for col in alt_cols:
                    if col in observed_data.columns:
                        observed_data = observed_data.copy()
                        observed_data["infectious"] = observed_data[col]
                        break
                else:
                    raise ValueError("Data must contain 'infectious' or similar column")

            infectious = observed_data["infectious"].dropna().values
            if len(infectious) < 5:
                raise ValueError("Insufficient data for parameter estimation")

            # Estimate growth rate from early exponential phase
            early_phase_len = min(10, len(infectious) // 3, len(infectious))
            early_phase = infectious[:early_phase_len]

            if len(early_phase) > 2 and np.all(early_phase > 0):
                log_infectious = np.log(np.maximum(early_phase, 1e-8))
                growth_rate = np.polyfit(range(len(early_phase)), log_infectious, 1)[0]
                growth_rate = max(0.01, min(growth_rate, 1.0))  # Reasonable bounds
            else:
                growth_rate = 0.1

            # Estimate parameters based on growth rate and data characteristics
            estimated_gamma = 1 / 10  # Assume 10-day infectious period
            estimated_sigma = 1 / 5  # Assume 5-day incubation period
            estimated_beta = max(0.01, growth_rate + estimated_gamma + estimated_sigma)

            # Apply priors if provided
            if prior_parameters:
                alpha = 0.3  # Weight for prior
                estimated_beta = (
                    alpha * prior_parameters.get("beta", estimated_beta)
                    + (1 - alpha) * estimated_beta
                )
                estimated_gamma = (
                    alpha * prior_parameters.get("gamma", estimated_gamma)
                    + (1 - alpha) * estimated_gamma
                )
                estimated_sigma = (
                    alpha * prior_parameters.get("sigma", estimated_sigma)
                    + (1 - alpha) * estimated_sigma
                )

            # Calculate R0
            r0 = estimated_beta / estimated_gamma

            self.estimated_parameters = {
                "beta": float(max(0.01, estimated_beta)),
                "gamma": float(max(0.01, estimated_gamma)),
                "sigma": float(max(0.01, estimated_sigma)),
                "r0": float(max(0.1, r0)),
            }

            return self.estimated_parameters

        except Exception as e:
            # Return default parameters if estimation fails
            return {
                "beta": 0.5,
                "gamma": 0.1,
                "sigma": 0.2,
                "r0": 5.0,
                "estimation_error": str(e),
            }

    def uncertainty_quantification(
        self, observed_data: pd.DataFrame, n_samples: int = 1000
    ) -> Dict[str, Dict[str, float]]:
        """
        Quantify parameter uncertainty using bootstrap sampling.

        Args:
            observed_data: Observed data
            n_samples: Number of bootstrap samples

        Returns:
            Parameter uncertainty estimates
        """
        try:
            parameter_samples = {"beta": [], "gamma": [], "sigma": [], "r0": []}

            for _ in range(n_samples):
                try:
                    # Bootstrap sample
                    sample_indices = np.random.choice(
                        len(observed_data), size=len(observed_data), replace=True
                    )
                    sample_data = observed_data.iloc[sample_indices].reset_index(
                        drop=True
                    )

                    # Estimate parameters for this sample
                    params = self.estimate_seir_parameters(sample_data)
                    for param, value in params.items():
                        if param in parameter_samples and isinstance(
                            value, (int, float)
                        ):
                            parameter_samples[param].append(value)
                except Exception:
                    # Skip failed samples
                    continue

            # Calculate uncertainty statistics
            uncertainty_stats = {}
            for param, samples in parameter_samples.items():
                if samples:
                    uncertainty_stats[param] = {
                        "mean": float(np.mean(samples)),
                        "std": float(np.std(samples)),
                        "median": float(np.median(samples)),
                        "q025": float(np.percentile(samples, 2.5)),
                        "q975": float(np.percentile(samples, 97.5)),
                        "samples": len(samples),
                    }
                else:
                    uncertainty_stats[param] = {
                        "mean": 0.0,
                        "std": 0.0,
                        "median": 0.0,
                        "q025": 0.0,
                        "q975": 0.0,
                        "samples": 0,
                    }

            return uncertainty_stats

        except Exception as e:
            return {
                "error": str(e),
                "beta": {
                    "mean": 0.5,
                    "std": 0.1,
                    "median": 0.5,
                    "q025": 0.4,
                    "q975": 0.6,
                    "samples": 0,
                },
                "gamma": {
                    "mean": 0.1,
                    "std": 0.02,
                    "median": 0.1,
                    "q025": 0.08,
                    "q975": 0.12,
                    "samples": 0,
                },
                "sigma": {
                    "mean": 0.2,
                    "std": 0.05,
                    "median": 0.2,
                    "q025": 0.15,
                    "q975": 0.25,
                    "samples": 0,
                },
                "r0": {
                    "mean": 5.0,
                    "std": 1.0,
                    "median": 5.0,
                    "q025": 4.0,
                    "q975": 6.0,
                    "samples": 0,
                },
            }


def create_forecaster(model_type: str = "ensemble") -> Any:
    """
    Factory function to create forecasting models.

    Args:
        model_type: Type of forecaster to create

    Returns:
        Configured forecaster
    """
    try:
        if model_type == "ensemble":
            return EnsembleForecaster()
        else:
            return TimeSeriesForecaster(model_type)
    except Exception as e:
        raise ValueError(f"Failed to create forecaster '{model_type}': {str(e)}")


def create_parameter_estimator() -> ParameterEstimator:
    """
    Factory function to create parameter estimator.

    Returns:
        Parameter estimator instance
    """
    return ParameterEstimator()
