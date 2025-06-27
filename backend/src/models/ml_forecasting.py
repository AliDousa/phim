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
    ) -> pd.DataFrame:
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
        try:
            df = data.copy()

            # Ensure target column exists
            if target_col not in df.columns:
                raise ValueError(f"Target column '{target_col}' not found in data")

            # Sort by date if date column exists
            if "date" in df.columns:
                df = df.sort_values("date").reset_index(drop=True)

            # Create lag features
            for lag in range(1, lag_features + 1):
                df[f"{target_col}_lag_{lag}"] = df[target_col].shift(lag)

            # Create rolling statistics
            for window in rolling_features:
                if len(df) >= window:
                    df[f"{target_col}_rolling_mean_{window}"] = (
                        df[target_col].rolling(window).mean()
                    )
                    df[f"{target_col}_rolling_std_{window}"] = (
                        df[target_col].rolling(window).std()
                    )
                    df[f"{target_col}_rolling_min_{window}"] = (
                        df[target_col].rolling(window).min()
                    )
                    df[f"{target_col}_rolling_max_{window}"] = (
                        df[target_col].rolling(window).max()
                    )

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

            # Create difference features
            df[f"{target_col}_diff_1"] = df[target_col].diff(1)
            if len(df) >= 7:
                df[f"{target_col}_diff_7"] = df[target_col].diff(7)

            # Create exponential moving averages
            for alpha in [0.1, 0.3, 0.5]:
                df[f"{target_col}_ema_{alpha}"] = df[target_col].ewm(alpha=alpha).mean()

            return df

        except Exception as e:
            raise ValueError(f"Feature creation failed: {str(e)}")

    def prepare_data(
        self, data: pd.DataFrame, target_col: str, test_size: int = 30
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare data for training and testing.

        Args:
            data: Input data with features
            target_col: Target column name
            test_size: Number of samples for testing

        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        try:
            # Remove rows with NaN values
            df_clean = data.dropna()

            if len(df_clean) == 0:
                raise ValueError("No valid data remaining after removing NaN values")

            # Separate features and target
            exclude_cols = [target_col, "date"]
            feature_cols = [col for col in df_clean.columns if col not in exclude_cols]
            self.feature_names = feature_cols

            if not feature_cols:
                raise ValueError("No feature columns available")

            X = df_clean[feature_cols].values
            y = df_clean[target_col].values

            # Validate data
            if len(X) == 0 or len(y) == 0:
                raise ValueError("Empty data arrays")

            # Split data (time series split)
            min_test_size = 10  # Ensure at least 10 samples for testing
            test_size = max(
                min_test_size, min(test_size, len(X) // 3)
            )  # Ensure reasonable split
            split_idx = len(X) - test_size
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]

            # Check for minimum training data
            if len(X_train) < 10:
                raise ValueError(
                    "Insufficient training data (minimum 10 samples required)"
                )

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
        Generate forecasts with confidence intervals.

        Args:
            data: Historical data
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

            # Create features
            df_features = self.create_features(data, target_col)

            # Prepare data
            X_train, X_test, y_train, y_test = self.prepare_data(
                df_features, target_col
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

            # Generate future forecasts
            forecasts = self._generate_future_forecasts(
                df_features, target_col, forecast_horizon
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

    def _generate_future_forecasts(
        self, df_features: pd.DataFrame, target_col: str, forecast_horizon: int
    ) -> np.ndarray:
        """Generate future forecasts iteratively."""
        try:
            # Get the last valid row for starting predictions
            last_row = df_features.dropna().iloc[-1:].copy()
            forecasts = []

            for i in range(forecast_horizon):
                # Prepare features for next prediction
                feature_cols = [
                    col for col in self.feature_names if col in last_row.columns
                ]

                if not feature_cols:
                    # If no features available, use simple trend
                    if forecasts:
                        pred = forecasts[-1]
                    else:
                        pred = last_row[target_col].iloc[0]
                else:
                    X_next = last_row[feature_cols].values.reshape(1, -1)

                    # Handle missing features by filling with last known values
                    if np.isnan(X_next).any():
                        X_next = np.nan_to_num(X_next, nan=0.0)

                    pred = self.predict(X_next)[0]

                forecasts.append(pred)

                # Update last_row for next iteration (simplified approach)
                last_row[target_col] = pred

                # Update trend features
                if "trend" in last_row.columns:
                    last_row["trend"] = last_row["trend"].iloc[0] + 1
                if "trend_squared" in last_row.columns:
                    last_row["trend_squared"] = last_row["trend"].iloc[0] ** 2

            return np.array(forecasts)

        except Exception as e:
            raise ValueError(f"Future forecast generation failed: {str(e)}")

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
            # Create features
            df_features = self.create_features(data, target_col)
            df_clean = df_features.dropna()

            if len(df_clean) < cv_folds * 2:
                raise ValueError("Insufficient data for cross-validation")

            # Prepare data
            feature_cols = [
                col for col in df_clean.columns if col != target_col and col != "date"
            ]
            X = df_clean[feature_cols].values
            y = df_clean[target_col].values

            # Time series cross-validation
            tscv = TimeSeriesSplit(n_splits=cv_folds)

            # Calculate cross-validation scores
            cv_scores = cross_val_score(
                self.model, X, y, cv=tscv, scoring="neg_mean_squared_error"
            )

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
                    # Create features and prepare data
                    df_features = forecaster.create_features(train_data, target_col)
                    X_train, _, y_train, _ = forecaster.prepare_data(
                        df_features, target_col, test_size=0
                    )

                    # Fit model
                    forecaster.fit(X_train, y_train)

                    # Validate on validation set
                    val_features = forecaster.create_features(val_data, target_col)
                    val_clean = val_features.dropna()

                    if len(val_clean) > 0:
                        available_features = [
                            f
                            for f in forecaster.feature_names
                            if f in val_clean.columns
                        ]
                        if available_features:
                            X_val = val_clean[available_features].values
                            y_val = val_clean[target_col].values

                            y_pred = forecaster.predict(X_val)
                            error = mean_squared_error(y_val, y_pred)
                            model_errors[model_type] = error
                        else:
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
