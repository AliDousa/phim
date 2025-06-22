# Public Health Intelligence Platform - Backend

A robust Flask-based API for epidemiological modeling and forecasting.

## Features

- **Authentication & Authorization**: JWT-based auth with role-based access control
- **Dataset Management**: Upload and manage epidemiological datasets with flexible column mapping
- **Simulation Engine**: Multiple epidemiological models (SEIR, Agent-based, Network, ML forecasting)
- **Machine Learning**: Advanced forecasting with ensemble methods
- **Audit Logging**: Comprehensive tracking of user actions
- **Cross-platform**: Optimized for Windows, macOS, and Linux

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:5000`

### Alternative Running Methods

```bash
# Method 1: Using the startup script (recommended)
python run.py

# Method 2: Direct module execution
python -m src.main

# Method 3: Flask development server
export FLASK_APP=src.main
flask run
```

## API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user |
| POST | `/login` | User login |
| POST | `/logout` | User logout |
| POST | `/refresh` | Refresh JWT token |
| POST | `/verify` | Verify JWT token |
| POST | `/change-password` | Change password |
| GET | `/profile` | Get user profile |
| PUT | `/profile` | Update user profile |

### Datasets (`/api/datasets`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List user's datasets |
| POST | `/` | Upload new dataset |
| POST | `/get-headers` | Get file column headers |
| GET | `/{id}` | Get specific dataset |
| DELETE | `/{id}` | Delete dataset |
| GET | `/{id}/data` | Get dataset data points |

### Simulations (`/api/simulations`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List user's simulations |
| POST | `/` | Create new simulation |
| GET | `/{id}` | Get specific simulation |
| DELETE | `/{id}` | Delete simulation |
| GET | `/{id}/forecasts` | Get simulation forecasts |
| POST | `/compare` | Compare multiple simulations |
| GET | `/types` | Get available simulation types |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System health check |
| GET | `/` | API information |

## Model Types

### 1. SEIR Model
Compartmental model with Susceptible, Exposed, Infectious, Recovered populations.

**Parameters:**
- `beta`: Transmission rate
- `sigma`: Incubation rate
- `gamma`: Recovery rate
- `population`: Total population
- `time_horizon`: Simulation duration (days)

### 2. Agent-Based Model
Individual agent simulation with contact networks.

**Parameters:**
- `population_size`: Number of agents
- `transmission_probability`: Transmission probability per contact
- `recovery_time`: Recovery time (days)
- `incubation_time`: Incubation time (days)

### 3. Network Model
Disease spread on social networks.

**Parameters:**
- `population_size`: Network size
- `transmission_rate`: Transmission rate
- `recovery_rate`: Recovery rate
- `network_type`: Network topology

### 4. ML Forecasting
Machine learning-based forecasting (requires dataset).

**Parameters:**
- `ml_model_type`: Model type (ensemble, random_forest, gradient_boosting)
- `target_column`: Column to forecast
- `forecast_horizon`: Forecast period (days)

## Dataset Format

### Supported Formats
- CSV files
- JSON files (array of objects)

### Required Columns
When uploading datasets, map these required fields:
- **Timestamp**: Date/time information
- **Location**: Geographic identifier
- **New Cases**: Daily new cases
- **New Deaths**: Daily new deaths

### Optional Columns
- Population
- Existing infections
- Recovered cases
- Any custom metrics

### Example CSV
```csv
date,region,daily_cases,daily_deaths,population
2024-01-01,Region A,120,5,1000000
2024-01-02,Region A,135,3,1000000
```

### Column Mapping
When uploading, provide a mapping object:
```json
{
  "timestamp_col": "date",
  "location_col": "region", 
  "new_cases_col": "daily_cases",
  "new_deaths_col": "daily_deaths",
  "population_col": "population"
}
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication.

### Getting a Token
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```

### Using the Token
Include the token in the Authorization header:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/datasets
```

## User Roles

- **analyst**: Can create and manage own datasets/simulations
- **researcher**: Enhanced permissions (future feature)
- **admin**: Full system access

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | Auto-generated (dev) |
| `DATABASE_URL` | Database connection string | SQLite file |
| `FLASK_ENV` | Environment (development/production) | development |

### Database

Default: SQLite database stored in `backend/data/phip.db`

For production, set `DATABASE_URL` to your database connection string.

## Development

### Project Structure
```
backend/
├── src/
│   ├── models/           # Database models
│   ├── routes/           # API endpoints
│   ├── auth.py          # Authentication utilities
│   ├── config.py        # Configuration
│   └── main.py          # Application entry point
├── data/                # Database and uploads
├── requirements.txt     # Dependencies
├── run.py              # Startup script
└── README.md
```

### Adding New Models

1. Create model class in `src/models/epidemiological.py`
2. Add factory function
3. Register in simulation routes
4. Update documentation

### Database Migrations

The application automatically creates tables on startup. For production:

1. Use Flask-Migrate for schema changes
2. Backup database before updates
3. Test migrations in staging environment

## Security Considerations

### Development vs Production

**Development (default):**
- Debug mode enabled
- Relaxed CORS settings
- SQLite database
- Basic error messages

**Production:**
- Set `FLASK_ENV=production`
- Use strong `SECRET_KEY`
- Configure secure database
- Enable HTTPS
- Implement rate limiting

### Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for configuration
3. **Enable HTTPS** in production
4. **Regular security updates** of dependencies
5. **Monitor and log** security events

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Ensure you're in the backend directory
cd backend

# Use the startup script
python run.py
```

**Database Issues:**
```bash
# Delete and recreate database
rm data/phip.db
python run.py
```

**Permission Errors:**
```bash
# Check file permissions
ls -la data/

# Ensure data directory exists
mkdir -p data
```

**Port Already in Use:**
```bash
# Kill process using port 5000
lsof -ti:5000 | xargs kill -9

# Or use different port
export FLASK_RUN_PORT=5001
```

### Logging

Application logs are printed to console. For production:

1. Configure file-based logging
2. Use log aggregation services
3. Set appropriate log levels
4. Monitor error rates

## Testing

### Manual Testing

Health check:
```bash
curl http://localhost:5000/api/health
```

Create user:
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "Test123!"}'
```

### Automated Testing

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest tests/
```

## Performance

### Optimization Tips

1. **Database indexing** for large datasets
2. **Pagination** for API responses
3. **Caching** for frequently accessed data
4. **Background processing** for long simulations
5. **Connection pooling** for database

### Monitoring

Key metrics to monitor:
- Response times
- Error rates
- Database query performance
- Memory usage
- Simulation completion rates

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Follow PEP 8 style guidelines
5. Submit pull request

## License

[Your chosen license]

## Support

For issues and questions:
1. Check this README
2. Review error logs
3. Search existing issues
4. Create new issue with details

---

**Version:** 1.0.0  
**Last Updated:** December 2024