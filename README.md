# Public Health Intelligence Platform

A comprehensive platform for epidemiological modeling, disease surveillance, and public health analytics with machine learning capabilities.

## Features

- **Advanced Epidemiological Models**: SEIR, Agent-based, Network-based modeling
- **Machine Learning Forecasting**: Ensemble methods with uncertainty quantification
- **Real-time Data Processing**: Time-series analysis and parameter estimation
- **Interactive Dashboard**: Modern React-based user interface
- **RESTful API**: Comprehensive backend with authentication
- **Cross-platform**: Works on Windows, macOS, and Linux

## Quick Start

### Windows Users
1. Download or clone this repository
2. Double-click `setup-windows.bat` to install dependencies
3. Double-click `start-platform.bat` to run the application
4. Open http://localhost:5173 in your browser

### Other Platforms
See detailed setup instructions in the documentation.

## System Requirements

- **Python 3.11+**
- **Node.js 18+**
- **4GB RAM minimum** (8GB recommended for large simulations)
- **2GB disk space**

## Architecture

```
public-health-intelligence-platform/
├── backend/                 # Flask API server
│   ├── src/
│   │   ├── main.py         # Application entry point
│   │   ├── auth.py         # Authentication system
│   │   ├── models/         # Data models and ML algorithms
│   │   └── routes/         # API endpoints
│   └── requirements.txt    # Python dependencies
├── frontend/               # React application
│   ├── src/
│   │   ├── App.jsx        # Main application component
│   │   └── components/    # UI components
│   └── package.json       # Node.js dependencies
├── setup-windows.bat      # Windows setup script
├── start-platform.bat     # Windows startup script
└── WINDOWS_SETUP.md       # Detailed Windows instructions
```

## Core Models

### Epidemiological Models
- **SEIR Model**: Susceptible-Exposed-Infectious-Recovered compartmental model
- **Agent-Based Model**: Individual agent interactions and disease transmission
- **Network Model**: Social network-based transmission modeling
- **System Dynamics**: Complex system behavior modeling

### Machine Learning
- **Random Forest**: Ensemble decision tree forecasting
- **Gradient Boosting**: Advanced boosting algorithms
- **Linear Models**: Statistical regression analysis
- **Ensemble Methods**: Combined model predictions
- **Bayesian Estimation**: Parameter uncertainty quantification

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/verify` - Token verification

### Datasets
- `GET /api/datasets` - List all datasets
- `POST /api/datasets` - Upload new dataset
- `GET /api/datasets/{id}` - Get dataset details
- `PUT /api/datasets/{id}` - Update dataset
- `DELETE /api/datasets/{id}` - Delete dataset

### Simulations
- `GET /api/simulations` - List all simulations
- `POST /api/simulations` - Create new simulation
- `GET /api/simulations/{id}` - Get simulation results
- `PUT /api/simulations/{id}` - Update simulation
- `DELETE /api/simulations/{id}` - Delete simulation

## Usage Examples

### Running a SEIR Simulation
```python
from models.epidemiological import create_seir_model

# Create model with parameters
model = create_seir_model({
    'beta': 0.5,      # Transmission rate
    'sigma': 1/5.1,   # Incubation rate
    'gamma': 1/10,    # Recovery rate
    'population': 100000
})

# Run simulation
results = model.simulate(
    initial_conditions={'S': 99999, 'E': 0, 'I': 1, 'R': 0},
    time_points=np.linspace(0, 365, 365)
)
```

### Machine Learning Forecasting
```python
from models.ml_forecasting import create_forecaster

# Create ensemble forecaster
forecaster = create_forecaster('ensemble')

# Generate forecast
result = forecaster.forecast(
    data=time_series_data,
    target_column='infectious',
    forecast_horizon=14
)
```

## Configuration

### Database Configuration
The platform supports both SQLite (default) and MySQL:

**SQLite (No setup required)**
```python
DATABASE_URL = 'sqlite:///phip.db'
```

**MySQL**
```python
DATABASE_URL = 'mysql://username:password@localhost/mydb'
```

### Environment Variables
Create a `.env` file in the backend directory:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///phip.db
DEBUG=True
```

## Testing

### Backend Tests
```bash
cd backend
python ../test_models.py
```

### Model Validation
The platform includes comprehensive model testing:
- SEIR model validation with known parameters
- Agent-based model population dynamics
- Network model transmission patterns
- ML model cross-validation and metrics

## Performance

### Optimization Features
- **Vectorized Computations**: NumPy and SciPy optimization
- **Parallel Processing**: Multi-core simulation support
- **Memory Management**: Efficient data structures
- **Caching**: Result caching for repeated simulations

### Benchmarks
- SEIR simulation (100k population, 365 days): ~0.1 seconds
- Agent-based model (1k agents, 50 steps): ~0.5 seconds
- ML forecasting (100 data points): ~2 seconds
- Network model (500 nodes): ~1 second

## Security

### Authentication
- JWT token-based authentication
- Role-based access control (Admin, Researcher, Analyst)
- Password hashing with secure algorithms
- Session management

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- CORS configuration
- Secure file upload handling

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Standards
- Python: PEP 8 style guide
- JavaScript: ESLint configuration
- Documentation: Comprehensive docstrings
- Testing: Unit tests for all models

## Troubleshooting

### Common Issues

**Windows Path Issues**
- Use forward slashes in configuration files
- Ensure Python and Node.js are in PATH

**Memory Issues**
- Reduce simulation population size
- Use smaller time steps
- Enable result caching

**Performance Issues**
- Close unnecessary applications
- Use SSD storage
- Increase available RAM

### Support
- Check the WINDOWS_SETUP.md for Windows-specific issues
- Review error logs in the console
- Ensure all dependencies are properly installed

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- SciPy and NumPy communities for scientific computing libraries
- React and Flask communities for web framework support
- Epidemiological modeling research community
- Open source contributors

## Version History

- **v1.0.0**: Initial release with core functionality
  - SEIR, Agent-based, and Network models
  - Machine learning forecasting
  - React dashboard
  - RESTful API
  - Windows compatibility

