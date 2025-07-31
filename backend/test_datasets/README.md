# Test Datasets for Public Health Intelligence Platform

This directory contains synthetic epidemiological datasets for testing the platform's features.

## Files:

1. **covid_outbreak_seir.csv** - COVID-19 outbreak data generated using SEIR model
   - 180 days of data for a single location
   - Includes SEIR compartments, interventions, and realistic parameters
   - Tests: ML forecasting, time series analysis, SEIR model fitting

2. **multi_location_outbreak.csv** - Multi-location outbreak data
   - 5 major US cities, 120 days of data each
   - Tests: Spatial analysis, comparative epidemiology, ensemble forecasting

3. **seasonal_flu_2022_2023.csv** - Seasonal influenza data
   - Full flu season (Oct 2022 - May 2023)
   - Tests: Seasonal pattern detection, age-stratified analysis

4. **outbreak_data.json** - JSON format outbreak data
   - 90 days of detailed outbreak data with metadata
   - Tests: JSON data import, API endpoints, data quality assessment

5. **small_test_dataset.csv** - Small dataset for quick testing
   - 30 days of COVID data
   - Tests: Basic functionality, development testing

## Data Quality Features:
- Realistic epidemic curves with multiple phases
- Stochastic variation and noise
- Missing data patterns
- Data quality indicators
- Spatial and temporal correlations
- Policy intervention effects

## Usage:
Upload these files through the platform's web interface or API to test various features:
- Data validation and processing
- ML forecasting models
- SEIR parameter estimation
- Visualization and dashboards
- Alert systems and monitoring
