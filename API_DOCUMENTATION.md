# Public Health Intelligence Platform - API Documentation

**Version:** 1.0.0  
**Author:** Manus AI  
**Date:** June 8, 2025  

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Examples](#examples)
8. [SDK and Libraries](#sdk-and-libraries)

## Introduction

The Public Health Intelligence Platform provides a comprehensive RESTful API for epidemiological modeling, disease surveillance, and public health analytics. This API enables researchers, public health officials, and data scientists to access advanced machine learning models, manage datasets, and perform sophisticated epidemiological simulations.

The API is built using Flask and follows REST principles, providing JSON responses for all endpoints. All endpoints support CORS for cross-origin requests, making it suitable for web applications and mobile clients.

### Base URL

```
http://localhost:5000/api
```

### Content Type

All requests and responses use JSON format:

```
Content-Type: application/json
```

### API Versioning

The current API version is v1. Future versions will be accessible via version-specific endpoints:

```
http://localhost:5000/api/v1/
```

## Authentication

The API uses JWT (JSON Web Token) based authentication. Users must register and login to obtain access tokens for protected endpoints.

### Authentication Flow

1. **Register** a new user account
2. **Login** with credentials to receive JWT token
3. **Include token** in Authorization header for protected requests
4. **Refresh token** when it expires

### Token Format

Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Token Expiration

JWT tokens expire after 24 hours. Clients should handle token refresh or re-authentication when tokens expire.



## API Endpoints

### Authentication Endpoints

#### POST /api/auth/register

Register a new user account.

**Request Body:**
```json
{
  "username": "string (required, 3-50 characters)",
  "email": "string (required, valid email format)",
  "password": "string (required, minimum 8 characters)",
  "full_name": "string (optional)",
  "organization": "string (optional)",
  "role": "string (optional, default: 'analyst')"
}
```

**Response (201 Created):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "organization": "Health Department",
    "role": "analyst",
    "created_at": "2025-06-08T10:30:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `409 Conflict`: Username or email already exists

#### POST /api/auth/login

Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "analyst"
  },
  "expires_at": "2025-06-09T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Missing credentials
- `401 Unauthorized`: Invalid credentials

#### POST /api/auth/verify

Verify JWT token validity.

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Response (200 OK):**
```json
{
  "valid": true,
  "user": {
    "id": 1,
    "username": "john_doe",
    "role": "analyst"
  },
  "expires_at": "2025-06-09T10:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token

### Dataset Management Endpoints

#### GET /api/datasets

Retrieve all datasets for the authenticated user.

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Query Parameters:**
- `page` (integer, optional): Page number for pagination (default: 1)
- `per_page` (integer, optional): Items per page (default: 20, max: 100)
- `data_type` (string, optional): Filter by data type (time_series, cross_sectional, spatial)
- `validated` (boolean, optional): Filter by validation status

**Response (200 OK):**
```json
{
  "datasets": [
    {
      "id": 1,
      "name": "COVID-19 Regional Data",
      "description": "Daily case counts by region",
      "data_type": "time_series",
      "source": "Health Department",
      "upload_date": "2025-06-08T10:30:00Z",
      "is_validated": true,
      "record_count": 1500,
      "metadata": {
        "columns": ["date", "region", "cases", "deaths"],
        "date_range": ["2020-01-01", "2025-06-08"],
        "regions": ["North", "South", "East", "West"]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "pages": 1
  }
}
```

#### POST /api/datasets

Upload a new dataset.

**Headers:**
```
Authorization: Bearer <jwt-token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file` (file, required): CSV or JSON data file
- `name` (string, required): Dataset name
- `description` (string, optional): Dataset description
- `data_type` (string, required): Data type (time_series, cross_sectional, spatial)
- `source` (string, optional): Data source information

**Response (201 Created):**
```json
{
  "message": "Dataset uploaded successfully",
  "dataset": {
    "id": 2,
    "name": "New Dataset",
    "description": "Description of the dataset",
    "data_type": "time_series",
    "upload_date": "2025-06-08T11:00:00Z",
    "is_validated": false,
    "file_path": "/uploads/dataset_2.csv"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file format or missing required fields
- `413 Payload Too Large`: File size exceeds limit (100MB)

#### GET /api/datasets/{id}

Retrieve a specific dataset by ID.

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Path Parameters:**
- `id` (integer, required): Dataset ID

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "COVID-19 Regional Data",
  "description": "Daily case counts by region",
  "data_type": "time_series",
  "source": "Health Department",
  "upload_date": "2025-06-08T10:30:00Z",
  "is_validated": true,
  "validation_errors": null,
  "record_count": 1500,
  "metadata": {
    "columns": ["date", "region", "cases", "deaths"],
    "date_range": ["2020-01-01", "2025-06-08"],
    "regions": ["North", "South", "East", "West"],
    "statistics": {
      "total_cases": 125000,
      "total_deaths": 3200,
      "peak_date": "2021-01-15"
    }
  },
  "sample_data": [
    {
      "date": "2025-06-08",
      "region": "North",
      "cases": 45,
      "deaths": 1
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: Dataset not found or access denied

#### PUT /api/datasets/{id}

Update dataset metadata.

**Headers:**
```
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

**Path Parameters:**
- `id` (integer, required): Dataset ID

**Request Body:**
```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "source": "string (optional)"
}
```

**Response (200 OK):**
```json
{
  "message": "Dataset updated successfully",
  "dataset": {
    "id": 1,
    "name": "Updated Dataset Name",
    "description": "Updated description",
    "source": "Updated source"
  }
}
```

#### DELETE /api/datasets/{id}

Delete a dataset and all associated data.

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Path Parameters:**
- `id` (integer, required): Dataset ID

**Response (200 OK):**
```json
{
  "message": "Dataset deleted successfully"
}
```

**Error Responses:**
- `404 Not Found`: Dataset not found
- `409 Conflict`: Dataset is being used by active simulations

### Simulation Management Endpoints

#### GET /api/simulations

Retrieve all simulations for the authenticated user.

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Query Parameters:**
- `page` (integer, optional): Page number for pagination
- `per_page` (integer, optional): Items per page
- `model_type` (string, optional): Filter by model type (seir, agent_based, network, ml_forecast)
- `status` (string, optional): Filter by status (pending, running, completed, failed)

**Response (200 OK):**
```json
{
  "simulations": [
    {
      "id": 1,
      "name": "COVID-19 SEIR Model",
      "model_type": "seir",
      "status": "completed",
      "created_at": "2025-06-08T10:00:00Z",
      "completed_at": "2025-06-08T10:05:00Z",
      "dataset_id": 1,
      "parameters": {
        "beta": 0.5,
        "sigma": 0.2,
        "gamma": 0.1,
        "population": 100000
      },
      "results_summary": {
        "peak_infections": 15000,
        "peak_date": "2025-08-15",
        "total_infected": 75000,
        "r0": 2.5
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "pages": 1
  }
}
```

#### POST /api/simulations

Create a new simulation.

**Headers:**
```
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (required)",
  "model_type": "string (required, one of: seir, agent_based, network, ml_forecast)",
  "dataset_id": "integer (required)",
  "parameters": {
    "beta": 0.5,
    "sigma": 0.2,
    "gamma": 0.1,
    "population": 100000,
    "time_horizon": 365
  },
  "description": "string (optional)"
}
```

**Response (201 Created):**
```json
{
  "message": "Simulation created successfully",
  "simulation": {
    "id": 2,
    "name": "New SEIR Simulation",
    "model_type": "seir",
    "status": "pending",
    "created_at": "2025-06-08T11:30:00Z",
    "dataset_id": 1,
    "parameters": {
      "beta": 0.5,
      "sigma": 0.2,
      "gamma": 0.1,
      "population": 100000
    }
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid parameters or model type
- `404 Not Found`: Dataset not found

#### GET /api/simulations/{id}

Retrieve detailed simulation results.

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Path Parameters:**
- `id` (integer, required): Simulation ID

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "COVID-19 SEIR Model",
  "model_type": "seir",
  "status": "completed",
  "created_at": "2025-06-08T10:00:00Z",
  "completed_at": "2025-06-08T10:05:00Z",
  "dataset_id": 1,
  "parameters": {
    "beta": 0.5,
    "sigma": 0.2,
    "gamma": 0.1,
    "population": 100000,
    "time_horizon": 365
  },
  "results": {
    "time_series": [
      {
        "day": 0,
        "susceptible": 99999,
        "exposed": 0,
        "infectious": 1,
        "recovered": 0
      },
      {
        "day": 1,
        "susceptible": 99998,
        "exposed": 1,
        "infectious": 1,
        "recovered": 0
      }
    ],
    "summary": {
      "peak_infections": 15000,
      "peak_date": "2025-08-15",
      "total_infected": 75000,
      "attack_rate": 0.75,
      "r0": 2.5,
      "final_size": 75000
    },
    "metrics": {
      "duration_days": 365,
      "computation_time": 5.2,
      "model_accuracy": 0.95
    }
  }
}
```

#### PUT /api/simulations/{id}

Update simulation metadata or re-run with new parameters.

**Headers:**
```
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "parameters": "object (optional, triggers re-run if provided)"
}
```

#### DELETE /api/simulations/{id}

Delete a simulation and its results.

**Headers:**
```
Authorization: Bearer <jwt-token>
```

**Response (200 OK):**
```json
{
  "message": "Simulation deleted successfully"
}
```


## Data Models

### User Model

```json
{
  "id": "integer (primary key)",
  "username": "string (unique, 3-50 characters)",
  "email": "string (unique, valid email)",
  "password_hash": "string (hashed)",
  "full_name": "string (optional)",
  "organization": "string (optional)",
  "role": "string (analyst, researcher, admin)",
  "created_at": "datetime (ISO 8601)",
  "last_login": "datetime (ISO 8601, optional)",
  "is_active": "boolean (default: true)"
}
```

### Dataset Model

```json
{
  "id": "integer (primary key)",
  "name": "string (required, max 200 characters)",
  "description": "text (optional)",
  "data_type": "string (time_series, cross_sectional, spatial)",
  "source": "string (optional, max 200 characters)",
  "upload_date": "datetime (ISO 8601)",
  "file_path": "string (server file path)",
  "dataset_metadata": "json (column info, statistics, etc.)",
  "is_validated": "boolean (default: false)",
  "validation_errors": "text (optional)",
  "user_id": "integer (foreign key to users.id)",
  "record_count": "integer (number of data records)"
}
```

### Simulation Model

```json
{
  "id": "integer (primary key)",
  "name": "string (required, max 200 characters)",
  "description": "text (optional)",
  "model_type": "string (seir, agent_based, network, ml_forecast)",
  "status": "string (pending, running, completed, failed)",
  "created_at": "datetime (ISO 8601)",
  "started_at": "datetime (ISO 8601, optional)",
  "completed_at": "datetime (ISO 8601, optional)",
  "parameters": "json (model-specific parameters)",
  "results": "json (simulation output data)",
  "error_message": "text (optional, for failed simulations)",
  "dataset_id": "integer (foreign key to datasets.id)",
  "user_id": "integer (foreign key to users.id)",
  "computation_time": "float (seconds)"
}
```

### DataPoint Model

```json
{
  "id": "integer (primary key)",
  "dataset_id": "integer (foreign key to datasets.id)",
  "timestamp": "datetime (ISO 8601)",
  "location": "string (optional, geographic identifier)",
  "values": "json (key-value pairs of measurements)",
  "metadata": "json (optional, additional context)"
}
```

### Forecast Model

```json
{
  "id": "integer (primary key)",
  "simulation_id": "integer (foreign key to simulations.id)",
  "forecast_date": "datetime (ISO 8601)",
  "target_date": "datetime (ISO 8601)",
  "predicted_value": "float",
  "confidence_lower": "float (optional)",
  "confidence_upper": "float (optional)",
  "model_version": "string",
  "created_at": "datetime (ISO 8601)"
}
```

## Error Handling

The API uses standard HTTP status codes and provides detailed error messages in JSON format.

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": "Additional technical details (optional)",
    "timestamp": "2025-06-08T10:30:00Z"
  }
}
```

### Common HTTP Status Codes

| Status Code | Description | Common Causes |
|-------------|-------------|---------------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input data, missing required fields |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions for the operation |
| 404 | Not Found | Resource not found or access denied |
| 409 | Conflict | Resource already exists or constraint violation |
| 413 | Payload Too Large | File upload exceeds size limit |
| 422 | Unprocessable Entity | Valid JSON but invalid data values |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

### Error Codes

| Error Code | Description |
|------------|-------------|
| `INVALID_CREDENTIALS` | Username or password is incorrect |
| `TOKEN_EXPIRED` | JWT token has expired |
| `TOKEN_INVALID` | JWT token is malformed or invalid |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| `RESOURCE_NOT_FOUND` | Requested resource does not exist |
| `DUPLICATE_RESOURCE` | Resource with same identifier already exists |
| `VALIDATION_ERROR` | Input data failed validation |
| `FILE_TOO_LARGE` | Uploaded file exceeds size limit |
| `UNSUPPORTED_FORMAT` | File format is not supported |
| `SIMULATION_ERROR` | Error occurred during simulation execution |
| `RATE_LIMIT_EXCEEDED` | Too many requests in time window |

## Rate Limiting

The API implements rate limiting to ensure fair usage and system stability.

### Rate Limits

| Endpoint Category | Limit | Window |
|------------------|-------|---------|
| Authentication | 10 requests | 1 minute |
| Dataset Upload | 5 requests | 1 hour |
| Simulation Creation | 20 requests | 1 hour |
| General API | 1000 requests | 1 hour |

### Rate Limit Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1625097600
```

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again later.",
    "retry_after": 3600
  }
}
```

## Examples

### Complete Workflow Example

This example demonstrates a complete workflow from user registration to running a simulation.

#### 1. Register a New User

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "epidemiologist",
    "email": "epi@health.gov",
    "password": "SecurePass123",
    "full_name": "Dr. Jane Smith",
    "organization": "Public Health Department",
    "role": "researcher"
  }'
```

#### 2. Login and Get Token

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "epidemiologist",
    "password": "SecurePass123"
  }'
```

Response:
```json
{
  "message": "Login successful",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "epidemiologist",
    "role": "researcher"
  }
}
```

#### 3. Upload Dataset

```bash
curl -X POST http://localhost:5000/api/datasets \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -F "file=@covid_data.csv" \
  -F "name=COVID-19 Regional Data" \
  -F "description=Daily case counts by region" \
  -F "data_type=time_series" \
  -F "source=Health Department"
```

#### 4. Create SEIR Simulation

```bash
curl -X POST http://localhost:5000/api/simulations \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "COVID-19 SEIR Model",
    "model_type": "seir",
    "dataset_id": 1,
    "parameters": {
      "beta": 0.5,
      "sigma": 0.2,
      "gamma": 0.1,
      "population": 100000,
      "time_horizon": 365
    },
    "description": "SEIR model for COVID-19 spread analysis"
  }'
```

#### 5. Check Simulation Status

```bash
curl -X GET http://localhost:5000/api/simulations/1 \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Python SDK Example

```python
import requests
import json

class PHIPClient:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.token = None
    
    def login(self, username, password):
        """Login and store JWT token."""
        response = requests.post(f"{self.base_url}/auth/login", json={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            return True
        return False
    
    def _headers(self):
        """Get headers with authorization token."""
        return {"Authorization": f"Bearer {self.token}"}
    
    def upload_dataset(self, file_path, name, data_type, description=None):
        """Upload a dataset file."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'name': name,
                'data_type': data_type,
                'description': description or ''
            }
            response = requests.post(
                f"{self.base_url}/datasets",
                headers=self._headers(),
                files=files,
                data=data
            )
        return response.json()
    
    def create_simulation(self, name, model_type, dataset_id, parameters):
        """Create a new simulation."""
        response = requests.post(
            f"{self.base_url}/simulations",
            headers={**self._headers(), "Content-Type": "application/json"},
            json={
                "name": name,
                "model_type": model_type,
                "dataset_id": dataset_id,
                "parameters": parameters
            }
        )
        return response.json()
    
    def get_simulation_results(self, simulation_id):
        """Get simulation results."""
        response = requests.get(
            f"{self.base_url}/simulations/{simulation_id}",
            headers=self._headers()
        )
        return response.json()

# Usage example
client = PHIPClient()
client.login("epidemiologist", "SecurePass123")

# Upload dataset
dataset = client.upload_dataset(
    "covid_data.csv",
    "COVID-19 Regional Data",
    "time_series",
    "Daily case counts by region"
)

# Create SEIR simulation
simulation = client.create_simulation(
    "COVID-19 SEIR Model",
    "seir",
    dataset["dataset"]["id"],
    {
        "beta": 0.5,
        "sigma": 0.2,
        "gamma": 0.1,
        "population": 100000,
        "time_horizon": 365
    }
)

# Get results
results = client.get_simulation_results(simulation["simulation"]["id"])
print(f"Peak infections: {results['results']['summary']['peak_infections']}")
```

## SDK and Libraries

### Official Python SDK

A Python SDK is available for easy integration with the API:

```bash
pip install phip-sdk
```

```python
from phip_sdk import PHIPClient

client = PHIPClient("http://localhost:5000/api")
client.login("username", "password")

# Upload and analyze data
dataset = client.upload_csv("data.csv", "My Dataset", "time_series")
simulation = client.run_seir_model(dataset.id, beta=0.5, gamma=0.1)
results = simulation.get_results()
```

### JavaScript/Node.js SDK

```bash
npm install phip-js-sdk
```

```javascript
const { PHIPClient } = require('phip-js-sdk');

const client = new PHIPClient('http://localhost:5000/api');
await client.login('username', 'password');

const dataset = await client.uploadDataset('data.csv', {
  name: 'My Dataset',
  dataType: 'time_series'
});

const simulation = await client.createSimulation({
  name: 'SEIR Model',
  modelType: 'seir',
  datasetId: dataset.id,
  parameters: { beta: 0.5, gamma: 0.1 }
});
```

### R Package

```r
# Install from CRAN
install.packages("phipr")

library(phipr)

# Connect to API
client <- phip_connect("http://localhost:5000/api")
phip_login(client, "username", "password")

# Upload data and run simulation
dataset <- phip_upload_data(client, "data.csv", name = "My Dataset")
simulation <- phip_seir_model(client, dataset$id, beta = 0.5, gamma = 0.1)
results <- phip_get_results(client, simulation$id)
```

---

**Note:** This documentation covers API version 1.0.0. For the latest updates and additional features, please refer to the online documentation at the project repository.

**Support:** For technical support and questions, please contact the development team or create an issue in the project repository.

**License:** This API is provided under the MIT License. See the LICENSE file for full terms and conditions.

