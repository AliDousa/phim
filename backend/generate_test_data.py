#!/usr/bin/env python3
"""
Generate realistic epidemiological test data for the Public Health Intelligence Platform.
Creates multiple datasets in different formats (CSV, JSON) with various scenarios.
"""

import pandas as pd
import numpy as np
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Set random seed for reproducible data
np.random.seed(42)
random.seed(42)

def generate_covid_outbreak_data():
    """Generate realistic COVID-19 outbreak data with SEIR dynamics."""
    
    # Parameters for realistic epidemic curve
    start_date = datetime(2023, 1, 1)
    n_days = 180  # 6 months of data
    population = 100000
    
    # SEIR model parameters
    beta = 0.4    # Transmission rate
    sigma = 0.2   # Incubation rate (1/5 days)
    gamma = 0.1   # Recovery rate (1/10 days)
    
    # Initial conditions
    I0 = 10  # Initial infectious
    E0 = 50  # Initial exposed
    S0 = population - I0 - E0
    R0 = 0
    
    # Storage arrays
    dates = []
    susceptible = []
    exposed = []
    infectious = []
    recovered = []
    deaths = []
    new_cases = []
    new_deaths = []
    new_recoveries = []
    
    # Current state
    S, E, I, R, D = S0, E0, I0, R0, 0
    
    for day in range(n_days):
        current_date = start_date + timedelta(days=day)
        dates.append(current_date.strftime('%Y-%m-%d'))
        
        # SEIR dynamics with stochasticity
        # Add some policy interventions and seasonal effects
        if 30 <= day <= 90:  # Lockdown period
            beta_eff = beta * 0.3
        elif 90 < day <= 120:  # Gradual reopening
            beta_eff = beta * 0.6
        else:  # Normal transmission
            beta_eff = beta
        
        # Seasonal adjustment (winter = higher transmission)
        seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * day / 365 + np.pi)
        beta_eff *= seasonal_factor
        
        # Calculate new transitions
        new_infections = beta_eff * S * I / population
        new_symptoms = sigma * E
        new_recoveries_day = gamma * I * 0.98  # 98% recover
        new_deaths_day = gamma * I * 0.02      # 2% death rate
        
        # Add noise
        new_infections += np.random.normal(0, np.sqrt(max(1, new_infections)))
        new_symptoms += np.random.normal(0, np.sqrt(max(1, new_symptoms)))
        new_recoveries_day += np.random.normal(0, np.sqrt(max(1, new_recoveries_day)))
        new_deaths_day += np.random.normal(0, np.sqrt(max(1, new_deaths_day)))
        
        # Ensure non-negative values
        new_infections = max(0, new_infections)
        new_symptoms = max(0, new_symptoms)
        new_recoveries_day = max(0, new_recoveries_day)
        new_deaths_day = max(0, new_deaths_day)
        
        # Update compartments
        S = max(0, S - new_infections)
        E = max(0, E + new_infections - new_symptoms)
        I = max(0, I + new_symptoms - new_recoveries_day - new_deaths_day)
        R = R + new_recoveries_day
        D = D + new_deaths_day
        
        # Store values
        susceptible.append(int(S))
        exposed.append(int(E))
        infectious.append(int(I))
        recovered.append(int(R))
        deaths.append(int(D))
        new_cases.append(int(new_symptoms))
        new_deaths.append(int(new_deaths_day))
        new_recoveries.append(int(new_recoveries_day))
    
    # Create DataFrame
    data = pd.DataFrame({
        'date': dates,
        'location': ['TestCity'] * n_days,
        'location_code': ['TC001'] * n_days,
        'population': [population] * n_days,
        'susceptible': susceptible,
        'exposed': exposed,
        'infectious': infectious,
        'recovered': recovered,
        'deaths': deaths,
        'new_cases': new_cases,
        'new_deaths': new_deaths,
        'new_recoveries': new_recoveries,
        'test_positivity_rate': np.random.beta(2, 8, n_days),  # Realistic positivity rates
        'hospitalization_rate': np.random.beta(1.5, 10, n_days),
        'icu_occupancy': np.random.beta(1, 20, n_days),
        'vaccination_rate': np.minimum(1.0, np.cumsum(np.random.beta(2, 50, n_days))),  # Cumulative vaccination
    })
    
    return data

def generate_multi_location_data():
    """Generate data for multiple locations to test spatial analysis."""
    
    locations = [
        {'name': 'New York City', 'code': 'NYC', 'population': 8400000, 'lat': 40.7128, 'lon': -74.0060},
        {'name': 'Los Angeles', 'code': 'LAX', 'population': 3900000, 'lat': 34.0522, 'lon': -118.2437},
        {'name': 'Chicago', 'code': 'CHI', 'population': 2700000, 'lat': 41.8781, 'lon': -87.6298},
        {'name': 'Houston', 'code': 'HOU', 'population': 2300000, 'lat': 29.7604, 'lon': -95.3698},
        {'name': 'Phoenix', 'code': 'PHX', 'population': 1600000, 'lat': 33.4484, 'lon': -112.0740}
    ]
    
    all_data = []
    start_date = datetime(2023, 3, 1)
    n_days = 120
    
    for loc in locations:
        # Base outbreak intensity varies by location
        base_intensity = np.random.uniform(0.1, 1.0)
        
        for day in range(n_days):
            current_date = start_date + timedelta(days=day)
            
            # Simulate epidemic curve with different phases
            if day < 20:
                # Early exponential growth
                cases = int(base_intensity * 5 * np.exp(0.15 * day) + np.random.poisson(5))
            elif day < 60:
                # Peak and decline
                peak_day = 30
                cases = int(base_intensity * 100 * np.exp(-0.08 * abs(day - peak_day)) + np.random.poisson(10))
            else:
                # Steady state with occasional flare-ups
                base_cases = base_intensity * 20
                if day % 14 == 0:  # Bi-weekly flare-ups
                    cases = int(base_cases * 2 + np.random.poisson(15))
                else:
                    cases = int(base_cases + np.random.poisson(8))
            
            deaths = max(0, int(cases * 0.02 + np.random.poisson(1)))
            recoveries = max(0, int(cases * 0.95 + np.random.poisson(cases // 10)))
            
            all_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'location': loc['name'],
                'location_code': loc['code'],
                'latitude': loc['lat'],
                'longitude': loc['lon'],
                'population': loc['population'],
                'new_cases': cases,
                'new_deaths': deaths,
                'new_recoveries': recoveries,
                'cumulative_cases': None,  # Will be calculated
                'cumulative_deaths': None,
                'test_positivity_rate': max(0.01, min(0.3, np.random.beta(2, 8))),
                'hospitalization_rate': max(0.001, min(0.15, np.random.beta(1.5, 10))),
                'icu_occupancy': max(0.001, min(0.05, np.random.beta(1, 20))),
            })
    
    df = pd.DataFrame(all_data)
    
    # Calculate cumulative values by location
    for loc_code in df['location_code'].unique():
        mask = df['location_code'] == loc_code
        df.loc[mask, 'cumulative_cases'] = df.loc[mask, 'new_cases'].cumsum()
        df.loc[mask, 'cumulative_deaths'] = df.loc[mask, 'new_deaths'].cumsum()
    
    return df

def generate_seasonal_flu_data():
    """Generate seasonal influenza data with realistic patterns."""
    
    start_date = datetime(2022, 10, 1)  # Start of flu season
    end_date = datetime(2023, 5, 31)    # End of flu season
    n_days = (end_date - start_date).days + 1
    
    data = []
    
    for day in range(n_days):
        current_date = start_date + timedelta(days=day)
        day_of_year = current_date.timetuple().tm_yday
        
        # Seasonal flu pattern (peaks in winter)
        seasonal_intensity = np.exp(-0.5 * ((day_of_year - 15) / 30) ** 2)  # Peak around Jan 15
        
        # Add weekly pattern (higher on weekdays)
        weekly_pattern = 1 + 0.3 * np.sin(2 * np.pi * day / 7)
        
        base_cases = seasonal_intensity * weekly_pattern * 150
        cases = max(0, int(base_cases + np.random.normal(0, base_cases * 0.3)))
        
        # Flu has lower death rate than COVID
        deaths = max(0, int(cases * 0.001 + np.random.poisson(0.5)))
        recoveries = max(0, int(cases * 0.99 + np.random.poisson(cases // 20)))
        
        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'location': 'National',
            'location_code': 'US',
            'disease': 'Influenza A/B',
            'new_cases': cases,
            'new_deaths': deaths,
            'new_recoveries': recoveries,
            'hospitalizations': max(0, int(cases * 0.05 + np.random.poisson(2))),
            'icu_admissions': max(0, int(cases * 0.01 + np.random.poisson(1))),
            'age_0_17': int(cases * 0.25 + np.random.poisson(cases * 0.05)),
            'age_18_49': int(cases * 0.35 + np.random.poisson(cases * 0.07)),
            'age_50_64': int(cases * 0.25 + np.random.poisson(cases * 0.05)),
            'age_65_plus': int(cases * 0.15 + np.random.poisson(cases * 0.03)),
        })
    
    return pd.DataFrame(data)

def generate_outbreak_json_data():
    """Generate JSON format data for testing API endpoints."""
    
    outbreak_data = {
        "metadata": {
            "dataset_name": "Test Outbreak Dataset",
            "description": "Synthetic outbreak data for testing ML forecasting models",
            "data_type": "time_series",
            "source": "Synthetic Data Generator v1.0",
            "created_at": datetime.now().isoformat(),
            "location_type": "city",
            "disease": "COVID-19",
            "population": 50000,
            "coordinates": {"latitude": 37.7749, "longitude": -122.4194}
        },
        "data_points": []
    }
    
    start_date = datetime(2023, 6, 1)
    
    for day in range(90):  # 3 months of data
        current_date = start_date + timedelta(days=day)
        
        # Generate realistic outbreak curve
        if day < 10:
            cases = max(0, int(2 * np.exp(0.2 * day) + np.random.poisson(3)))
        elif day < 45:
            peak_day = 25
            cases = max(0, int(50 * np.exp(-0.1 * abs(day - peak_day)) + np.random.poisson(8)))
        else:
            cases = max(0, int(10 + 5 * np.sin(day / 7) + np.random.poisson(5)))
        
        data_point = {
            "timestamp": current_date.isoformat(),
            "location": "San Francisco",
            "location_code": "SF",
            "new_cases": cases,
            "new_deaths": max(0, int(cases * 0.015 + np.random.poisson(0.5))),
            "new_recoveries": max(0, int(cases * 0.95 + np.random.poisson(2))),
            "active_cases": None,  # Will be calculated
            "test_positivity_rate": max(0.01, min(0.25, np.random.beta(2, 10))),
            "tests_performed": max(cases * 10, int(np.random.normal(cases * 15, cases * 3))),
            "hospitalizations": max(0, int(cases * 0.08 + np.random.poisson(1))),
            "icu_admissions": max(0, int(cases * 0.02 + np.random.poisson(0.3))),
            "data_quality_score": min(1.0, max(0.7, np.random.normal(0.9, 0.1))),
            "is_interpolated": random.choice([True, False]) if day % 7 == 0 else False,
            "confidence_interval": max(0.1, min(0.9, np.random.normal(0.8, 0.1)))
        }
        
        outbreak_data["data_points"].append(data_point)
    
    return outbreak_data

def create_test_datasets():
    """Create all test datasets and save them."""
    
    output_dir = Path("test_datasets")
    output_dir.mkdir(exist_ok=True)
    
    print("Generating test datasets...")
    
    # 1. COVID-19 SEIR model data (CSV)
    print("1. Creating COVID-19 SEIR model data...")
    covid_data = generate_covid_outbreak_data()
    covid_file = output_dir / "covid_outbreak_seir.csv"
    covid_data.to_csv(covid_file, index=False)
    print(f"   Saved: {covid_file} ({len(covid_data)} records)")
    
    # 2. Multi-location data (CSV)
    print("2. Creating multi-location outbreak data...")
    multi_loc_data = generate_multi_location_data()
    multi_loc_file = output_dir / "multi_location_outbreak.csv"
    multi_loc_data.to_csv(multi_loc_file, index=False)
    print(f"   Saved: {multi_loc_file} ({len(multi_loc_data)} records)")
    
    # 3. Seasonal flu data (CSV)
    print("3. Creating seasonal flu data...")
    flu_data = generate_seasonal_flu_data()
    flu_file = output_dir / "seasonal_flu_2022_2023.csv"
    flu_data.to_csv(flu_file, index=False)
    print(f"   Saved: {flu_file} ({len(flu_data)} records)")
    
    # 4. JSON format data
    print("4. Creating JSON format outbreak data...")
    json_data = generate_outbreak_json_data()
    json_file = output_dir / "outbreak_data.json"
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"   Saved: {json_file} ({len(json_data['data_points'])} records)")
    
    # 5. Create a small test file for quick testing
    print("5. Creating small test file...")
    small_data = covid_data.head(30).copy()  # First 30 days
    small_file = output_dir / "small_test_dataset.csv"
    small_data.to_csv(small_file, index=False)
    print(f"   Saved: {small_file} ({len(small_data)} records)")
    
    # Create a README for the test datasets
    readme_content = """# Test Datasets for Public Health Intelligence Platform

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
"""
    
    readme_file = output_dir / "README.md"
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    print(f"   Created: {readme_file}")
    
    print(f"\n[SUCCESS] All test datasets created successfully in '{output_dir}' directory!")
    return output_dir

if __name__ == "__main__":
    create_test_datasets()