# Testing Guide for Public Health Intelligence Platform

This guide shows how to test the platform using the generated test datasets.

## Quick Start

### 1. Generate Test Data
```bash
python generate_test_data.py
```
This creates realistic epidemiological datasets in `test_datasets/` directory.

### 2. Manual Server Testing
Start the backend server:
```bash
python run.py
```

Start the frontend (in separate terminal):
```bash
cd ../frontend
npm run dev
```

### 3. Automated Testing
Run comprehensive tests:
```bash
python test_app_with_data.py
```

Or start server and test automatically:
```bash
python start_server_and_test.py
```

## Test Datasets Generated

### 1. `small_test_dataset.csv` (30 records)
- **Purpose**: Quick testing and development
- **Content**: 30 days of COVID-19 data with SEIR compartments
- **Use for**: Basic functionality testing, ML model validation

### 2. `covid_outbreak_seir.csv` (180 records)
- **Purpose**: Comprehensive SEIR model testing
- **Content**: 6 months of COVID data with interventions and seasonal effects
- **Features**: 
  - Realistic epidemic curve
  - Policy interventions (lockdowns, reopening)
  - Seasonal transmission variations
  - Vaccination rollout
- **Use for**: SEIR parameter estimation, long-term forecasting

### 3. `multi_location_outbreak.csv` (600 records)
- **Purpose**: Spatial analysis and multi-location modeling
- **Content**: 5 major US cities, 120 days each
- **Features**:
  - Different outbreak intensities by location
  - Geographic coordinates
  - Population-adjusted metrics
- **Use for**: Comparative analysis, spatial modeling, ensemble forecasting

### 4. `seasonal_flu_2022_2023.csv` (243 records)
- **Purpose**: Seasonal pattern detection
- **Content**: Full flu season with age stratification
- **Features**:
  - Realistic seasonal patterns
  - Age-group breakdowns
  - Lower mortality than COVID
- **Use for**: Seasonal forecasting, demographic analysis

### 5. `outbreak_data.json` (90 records)
- **Purpose**: JSON format testing and API validation
- **Content**: Structured outbreak data with rich metadata
- **Features**:
  - Nested JSON structure
  - Data quality indicators
  - Confidence intervals
- **Use for**: API testing, data quality assessment

## Manual Testing Scenarios

### Scenario 1: Basic Data Upload and Forecasting
1. Login to web interface (http://localhost:5173)
2. Upload `small_test_dataset.csv`
3. Wait for processing to complete
4. Create ML forecasting simulation:
   - Model: Random Forest
   - Forecast horizon: 14 days
   - Target: new_cases
5. View results and confidence intervals

### Scenario 2: SEIR Model Fitting
1. Upload `covid_outbreak_seir.csv`
2. Create SEIR simulation:
   - Population: 100,000
   - Initial conditions: S=99950, E=40, I=10, R=0
   - Let system estimate parameters
3. Compare model fit to actual data
4. Generate future projections

### Scenario 3: Multi-Location Analysis
1. Upload `multi_location_outbreak.csv`
2. View spatial distribution on map
3. Compare outbreak patterns across cities
4. Create ensemble forecasts
5. Analyze geographic spread

### Scenario 4: Data Quality Testing
1. Upload `outbreak_data.json`
2. Review data quality scores
3. Identify interpolated data points
4. Check confidence intervals
5. Validate data processing pipeline

## API Testing with curl

### Authentication
```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "Alio", "password": "XmP6_6afz:NqTzT"}'

# Extract token from response and use in subsequent requests
TOKEN="your_token_here"
```

### Dataset Operations
```bash
# List datasets
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/datasets

# Upload dataset (programmatically)
curl -X POST http://localhost:5000/api/datasets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Dataset",
    "description": "API uploaded dataset",
    "data_type": "time_series",
    "source": "curl test"
  }'
```

### Simulation Operations
```bash
# List simulations
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/simulations

# Create ML forecasting simulation
curl -X POST http://localhost:5000/api/simulations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API ML Forecast",
    "description": "ML forecast via API",
    "model_type": "ml_forecast",
    "dataset_id": 1,
    "parameters": {
      "forecast_horizon": 14,
      "target_column": "new_cases",
      "model_types": ["random_forest"],
      "confidence_level": 0.95
    }
  }'
```

## Expected Results

### ML Forecasting
- **Processing time**: 10-30 seconds for small datasets
- **Metrics**: MAE, RMSE, R² scores
- **Output**: 14-day forecast with confidence intervals
- **Validation**: Out-of-sample performance metrics

### SEIR Modeling
- **Parameter estimation**: Automatic fitting to data
- **Model outputs**: Projected compartment sizes
- **R₀ calculation**: Basic reproduction number
- **Sensitivity analysis**: Parameter uncertainty

### Data Processing
- **Validation**: Automatic data quality checks
- **Statistics**: Record counts, date ranges, completeness
- **Visualization**: Time series plots, geographic maps
- **Export**: Results downloadable as CSV/JSON

## Troubleshooting

### Common Issues

1. **Server not starting**
   - Check port 5000 is available
   - Verify Python dependencies installed
   - Check database connection

2. **Authentication fails**
   - Verify test user exists (Alio/XmP6_6afz:NqTzT)
   - Check JWT configuration
   - Review server logs

3. **Data upload fails**
   - Verify file format (CSV/JSON)
   - Check file size limits
   - Validate data structure

4. **Simulations fail**
   - Check dataset has required columns
   - Verify sufficient data points (minimum 20)
   - Review parameter constraints

### Debug Commands
```bash
# Check server logs
tail -f logs/app.log

# Test database connection
python -c "from src.models.database import db; print('DB OK')"

# Verify data structure
python -c "import pandas as pd; print(pd.read_csv('test_datasets/small_test_dataset.csv').info())"
```

## Performance Expectations

### Small Dataset (30 records)
- Upload: < 1 second
- Processing: < 5 seconds
- ML Forecast: 5-15 seconds
- SEIR Model: 2-10 seconds

### Medium Dataset (180 records)
- Upload: < 2 seconds
- Processing: < 10 seconds  
- ML Forecast: 15-45 seconds
- SEIR Model: 5-20 seconds

### Large Dataset (600 records)
- Upload: < 5 seconds
- Processing: < 30 seconds
- ML Forecast: 30-90 seconds
- SEIR Model: 10-45 seconds

## Success Criteria

A successful test should demonstrate:
1. ✅ User authentication and authorization
2. ✅ Dataset upload and validation
3. ✅ Data processing and quality checks
4. ✅ ML forecasting with reasonable accuracy
5. ✅ SEIR model fitting and parameter estimation
6. ✅ Results visualization and export
7. ✅ Error handling and validation
8. ✅ API endpoints functionality

## Next Steps

After successful testing:
1. Try with real epidemiological data
2. Experiment with different model parameters
3. Test with larger datasets
4. Explore ensemble forecasting
5. Validate against known outbreak patterns
6. Test production deployment scenarios