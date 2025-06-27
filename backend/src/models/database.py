"""
Production-ready database models for the public health intelligence platform.
Includes proper indexes, constraints, and optimizations.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import json
import uuid
from sqlalchemy import Index, CheckConstraint, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.hybrid import hybrid_property

db = SQLAlchemy()


class TimestampMixin:
    """Mixin for adding timestamp fields to models."""

    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class User(db.Model, TimestampMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="analyst", nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)

    # Profile information
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    organization = db.Column(db.String(200))
    department = db.Column(db.String(100))

    # Security fields
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    password_changed_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Preferences
    timezone = db.Column(db.String(50), default="UTC")
    language = db.Column(db.String(10), default="en")
    preferences = db.Column(db.Text)  # JSON string for user preferences

    # Relationships
    datasets = db.relationship(
        "Dataset", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    simulations = db.relationship(
        "Simulation", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    audit_logs = db.relationship("AuditLog", backref="user", lazy="dynamic")

    # Indexes for performance
    __table_args__ = (
        Index("idx_users_email_active", "email", "is_active"),
        Index("idx_users_username_active", "username", "is_active"),
        Index("idx_users_role_active", "role", "is_active"),
        Index("idx_users_created_at", "created_at"),
        CheckConstraint("length(username) >= 3", name="ck_username_length"),
        CheckConstraint("length(password_hash) >= 60", name="ck_password_hash_length"),
        CheckConstraint(
            "role IN ('analyst', 'researcher', 'admin')", name="ck_valid_role"
        ),
    )

    def set_password(self, password):
        """Set password hash with bcrypt."""
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256:260000"
        )
        self.password_changed_at = datetime.now(timezone.utc)

    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)

    def is_locked(self):
        """Check if account is locked."""
        if self.locked_until and self.locked_until > datetime.now(timezone.utc):
            return True
        return False

    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration."""
        self.locked_until = datetime.now(timezone.utc) + timedelta(
            minutes=duration_minutes
        )
        self.failed_login_attempts += 1

    def unlock_account(self):
        """Unlock account and reset failed attempts."""
        self.locked_until = None
        self.failed_login_attempts = 0

    def record_login(self, ip_address):
        """Record successful login."""
        self.last_login_at = datetime.now(timezone.utc)
        self.last_login_ip = ip_address
        self.failed_login_attempts = 0
        self.locked_until = None

    def set_preferences(self, preferences_dict):
        """Set user preferences as JSON string."""
        self.preferences = json.dumps(preferences_dict)

    def get_preferences(self):
        """Get user preferences as dictionary."""
        if self.preferences:
            try:
                return json.loads(self.preferences)
            except json.JSONDecodeError:
                return {}
        return {}

    @hybrid_property
    def full_name(self):
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary."""
        data = {
            "id": self.id,
            "uuid": str(self.uuid),
            "username": self.username,
            "email": (
                self.email if include_sensitive else "******"
            ),  # Mask email completely for non-sensitive output
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "organization": self.organization,
            "department": self.department,
            "timezone": self.timezone,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": (
                self.last_login_at.isoformat() if self.last_login_at else None
            ),
            "preferences": self.get_preferences(),
        }

        if include_sensitive:
            data.update(
                {
                    "last_login_ip": self.last_login_ip,
                    "failed_login_attempts": self.failed_login_attempts,
                    "is_locked": self.is_locked(),
                    "password_changed_at": (
                        self.password_changed_at.isoformat()
                        if self.password_changed_at
                        else None
                    ),
                }
            )

        return data


class Dataset(db.Model, TimestampMixin):
    """Dataset model for storing epidemiological data."""

    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    data_type = db.Column(db.String(50), nullable=False, index=True)
    source = db.Column(db.String(200))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.BigInteger)
    file_hash = db.Column(db.String(64))  # SHA-256 hash
    dataset_metadata = db.Column(db.Text)  # JSON string

    # Validation and processing
    is_validated = db.Column(db.Boolean, default=False, nullable=False, index=True)
    validation_errors = db.Column(db.Text)
    processing_status = db.Column(db.String(50), default="pending", index=True)
    processing_started_at = db.Column(db.DateTime)
    processing_completed_at = db.Column(db.DateTime)

    # Statistics
    total_records = db.Column(db.Integer, default=0)
    valid_records = db.Column(db.Integer, default=0)
    invalid_records = db.Column(db.Integer, default=0)

    # Date range of data
    data_start_date = db.Column(db.Date)
    data_end_date = db.Column(db.Date)

    # Access control
    is_public = db.Column(db.Boolean, default=False, index=True)
    is_archived = db.Column(db.Boolean, default=False, index=True)

    # Foreign keys
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )

    # Relationships
    data_points = db.relationship(
        "DataPoint",
        backref="dataset",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    simulations = db.relationship("Simulation", backref="dataset", lazy="dynamic")

    # Indexes for performance
    __table_args__ = (
        Index("idx_datasets_user_type", "user_id", "data_type"),
        Index("idx_datasets_user_created", "user_id", "created_at"),
        Index("idx_datasets_name_user", "name", "user_id"),
        Index("idx_datasets_status_created", "processing_status", "created_at"),
        Index("idx_datasets_public_type", "is_public", "data_type"),
        Index("idx_datasets_date_range", "data_start_date", "data_end_date"),
        CheckConstraint(
            "data_type IN ('time_series', 'cross_sectional', 'spatial')",
            name="ck_valid_data_type",
        ),
        CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_valid_processing_status",
        ),
        CheckConstraint("total_records >= 0", name="ck_total_records_positive"),
        CheckConstraint("valid_records >= 0", name="ck_valid_records_positive"),
        CheckConstraint("invalid_records >= 0", name="ck_invalid_records_positive"),
    )

    def set_metadata(self, metadata_dict):
        """Set metadata as JSON string."""
        self.dataset_metadata = json.dumps(metadata_dict, default=str)

    def get_metadata(self):
        """Get metadata as dictionary."""
        if self.dataset_metadata:
            try:
                return json.loads(self.dataset_metadata)
            except json.JSONDecodeError:
                return {}
        return {}

    def update_statistics(self):
        """Update dataset statistics from data points."""
        total = self.data_points.count()
        self.total_records = total

        # Count valid records (those with required fields)
        valid = self.data_points.filter(
            db.and_(DataPoint.timestamp.isnot(None), DataPoint.location.isnot(None))
        ).count()
        self.valid_records = valid
        self.invalid_records = total - valid

        # Update date range
        if total > 0:
            date_range = (
                db.session.query(
                    db.func.min(DataPoint.timestamp), db.func.max(DataPoint.timestamp)
                )
                .filter(DataPoint.dataset_id == self.id)
                .first()
            )

            if date_range[0] and date_range[1]:
                self.data_start_date = date_range[0].date()
                self.data_end_date = date_range[1].date()

    def to_dict(self, include_stats=True):
        """Convert to dictionary."""
        data = {
            "id": self.id,
            "uuid": str(self.uuid),
            "name": self.name,
            "description": self.description,
            "data_type": self.data_type,
            "source": self.source,
            "file_size": self.file_size,
            "metadata": self.get_metadata(),
            "is_validated": self.is_validated,
            "validation_errors": self.validation_errors,
            "processing_status": self.processing_status,
            "is_public": self.is_public,
            "is_archived": self.is_archived,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_stats:
            data.update(
                {
                    "total_records": self.total_records,
                    "valid_records": self.valid_records,
                    "invalid_records": self.invalid_records,
                    "data_start_date": (
                        self.data_start_date.isoformat()
                        if self.data_start_date
                        else None
                    ),
                    "data_end_date": (
                        self.data_end_date.isoformat() if self.data_end_date else None
                    ),
                    "processing_started_at": (
                        self.processing_started_at.isoformat()
                        if self.processing_started_at
                        else None
                    ),
                    "processing_completed_at": (
                        self.processing_completed_at.isoformat()
                        if self.processing_completed_at
                        else None
                    ),
                }
            )

        return data


class DataPoint(db.Model):
    """Individual data points for time series and spatial data."""

    __tablename__ = "data_points"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    location = db.Column(db.String(200), index=True)
    location_code = db.Column(db.String(50), index=True)  # ISO codes, FIPS, etc.
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # Epidemiological data fields
    susceptible = db.Column(db.Integer)
    exposed = db.Column(db.Integer)
    infectious = db.Column(db.Integer)
    recovered = db.Column(db.Integer)
    deaths = db.Column(db.Integer)
    new_cases = db.Column(db.Integer)
    new_deaths = db.Column(db.Integer)
    new_recoveries = db.Column(db.Integer)

    # Additional metrics
    population = db.Column(db.Integer)
    test_positivity_rate = db.Column(db.Float)
    hospitalization_rate = db.Column(db.Float)
    icu_occupancy = db.Column(db.Float)
    vaccination_rate = db.Column(db.Float)

    # Data quality indicators
    data_quality_score = db.Column(db.Float)  # 0-1 quality score
    is_interpolated = db.Column(db.Boolean, default=False)
    confidence_interval = db.Column(db.Float)

    # Custom data fields (JSON)
    custom_data = db.Column(db.Text)

    # Audit fields
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    source_line_number = db.Column(db.Integer)  # Line in original file

    # Foreign keys
    dataset_id = db.Column(
        db.Integer,
        db.ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_data_points_dataset_timestamp", "dataset_id", "timestamp"),
        Index("idx_data_points_location_timestamp", "location", "timestamp"),
        Index("idx_data_points_location_code_timestamp", "location_code", "timestamp"),
        Index("idx_data_points_coordinates", "latitude", "longitude"),
        Index("idx_data_points_dataset_location", "dataset_id", "location"),
        Index("idx_data_points_created_at", "created_at"),
        # Unique constraint to prevent duplicates
        UniqueConstraint(
            "dataset_id", "timestamp", "location", name="uq_dataset_timestamp_location"
        ),
        # Check constraints for data integrity
        CheckConstraint("susceptible >= 0", name="ck_susceptible_positive"),
        CheckConstraint("exposed >= 0", name="ck_exposed_positive"),
        CheckConstraint("infectious >= 0", name="ck_infectious_positive"),
        CheckConstraint("recovered >= 0", name="ck_recovered_positive"),
        CheckConstraint("deaths >= 0", name="ck_deaths_positive"),
        CheckConstraint("new_cases >= 0", name="ck_new_cases_positive"),
        CheckConstraint("new_deaths >= 0", name="ck_new_deaths_positive"),
        CheckConstraint("population >= 0", name="ck_population_positive"),
        CheckConstraint(
            "test_positivity_rate >= 0 AND test_positivity_rate <= 1",
            name="ck_test_positivity_rate_valid",
        ),
        CheckConstraint(
            "hospitalization_rate >= 0 AND hospitalization_rate <= 1",
            name="ck_hospitalization_rate_valid",
        ),
        CheckConstraint(
            "data_quality_score >= 0 AND data_quality_score <= 1",
            name="ck_data_quality_score_valid",
        ),
    )

    def set_custom_data(self, data_dict):
        """Set custom data as JSON string."""
        self.custom_data = json.dumps(data_dict, default=str)

    def get_custom_data(self):
        """Get custom data as dictionary."""
        if self.custom_data:
            try:
                return json.loads(self.custom_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def calculate_quality_score(self):
        """Calculate data quality score based on completeness and consistency."""
        score = 1.0

        # Required fields penalty
        required_fields = [self.timestamp, self.location]
        missing_required = sum(1 for field in required_fields if field is None)
        score -= missing_required * 0.5

        # Important fields penalty
        important_fields = [self.new_cases, self.new_deaths, self.population]
        missing_important = sum(1 for field in important_fields if field is None)
        score -= missing_important * 0.1

        # Consistency checks
        if self.new_cases is not None and self.new_cases < 0:
            score -= 0.2
        if self.new_deaths is not None and self.new_deaths < 0:
            score -= 0.2
        if self.new_deaths is not None and self.new_cases is not None:
            if self.new_deaths > self.new_cases:
                score -= 0.1  # Deaths shouldn't exceed cases on same day

        self.data_quality_score = max(0.0, min(1.0, score))
        return self.data_quality_score

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "location": self.location,
            "location_code": self.location_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "susceptible": self.susceptible,
            "exposed": self.exposed,
            "infectious": self.infectious,
            "recovered": self.recovered,
            "deaths": self.deaths,
            "new_cases": self.new_cases,
            "new_deaths": self.new_deaths,
            "new_recoveries": self.new_recoveries,
            "population": self.population,
            "test_positivity_rate": self.test_positivity_rate,
            "hospitalization_rate": self.hospitalization_rate,
            "icu_occupancy": self.icu_occupancy,
            "vaccination_rate": self.vaccination_rate,
            "data_quality_score": self.data_quality_score,
            "is_interpolated": self.is_interpolated,
            "confidence_interval": self.confidence_interval,
            "custom_data": self.get_custom_data(),
            "dataset_id": self.dataset_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Simulation(db.Model, TimestampMixin):
    """Simulation model for storing model runs and results."""

    __tablename__ = "simulations"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    model_type = db.Column(db.String(50), nullable=False, index=True)
    model_version = db.Column(db.String(20), default="1.0")

    # Status tracking
    status = db.Column(db.String(50), default="pending", nullable=False, index=True)
    priority = db.Column(db.Integer, default=5)  # 1=highest, 10=lowest

    # Execution timing
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    execution_time_seconds = db.Column(db.Float)

    # Task management
    task_id = db.Column(db.String(100), index=True)  # Celery task ID
    worker_node = db.Column(db.String(100))  # Which worker processed this

    # Configuration and results (JSON)
    parameters = db.Column(db.Text)  # Model parameters
    results = db.Column(db.Text)  # Simulation results
    metrics = db.Column(db.Text)  # Performance metrics

    # Resource usage
    memory_usage_mb = db.Column(db.Float)
    cpu_time_seconds = db.Column(db.Float)

    # Validation and quality
    is_validated = db.Column(db.Boolean, default=False)
    validation_errors = db.Column(db.Text)
    quality_score = db.Column(db.Float)  # 0-1 simulation quality score

    # Access and sharing
    is_public = db.Column(db.Boolean, default=False, index=True)
    is_archived = db.Column(db.Boolean, default=False, index=True)

    # Foreign keys
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"), index=True)

    # Relationships
    forecasts = db.relationship(
        "Forecast",
        backref="simulation",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_simulations_user_created", "user_id", "created_at"),
        Index("idx_simulations_user_status", "user_id", "status"),
        Index("idx_simulations_model_type_status", "model_type", "status"),
        Index("idx_simulations_status_created", "status", "created_at"),
        Index("idx_simulations_task_id", "task_id"),
        Index("idx_simulations_dataset_created", "dataset_id", "created_at"),
        Index("idx_simulations_public_type", "is_public", "model_type"),
        CheckConstraint(
            "model_type IN ('seir', 'agent_based', 'network', 'ml_forecast')",
            name="ck_valid_model_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_valid_status",
        ),
        CheckConstraint("priority >= 1 AND priority <= 10", name="ck_valid_priority"),
        CheckConstraint(
            "execution_time_seconds >= 0", name="ck_execution_time_positive"
        ),
        CheckConstraint("memory_usage_mb >= 0", name="ck_memory_usage_positive"),
        CheckConstraint(
            "quality_score >= 0 AND quality_score <= 1", name="ck_quality_score_valid"
        ),
    )

    def set_parameters(self, params_dict):
        """Set parameters as JSON string."""
        self.parameters = json.dumps(params_dict, default=str)

    def get_parameters(self):
        """Get parameters as dictionary."""
        if self.parameters:
            try:
                return json.loads(self.parameters)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_results(self, results_dict):
        """Set results as JSON string."""
        self.results = json.dumps(results_dict, default=str)

    def get_results(self):
        """Get results as dictionary."""
        if self.results:
            try:
                return json.loads(self.results)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_metrics(self, metrics_dict):
        """Set metrics as JSON string."""
        self.metrics = json.dumps(metrics_dict, default=str)

    def get_metrics(self):
        """Get metrics as dictionary."""
        if self.metrics:
            try:
                return json.loads(self.metrics)
            except json.JSONDecodeError:
                return {}
        return {}

    def calculate_execution_time(self):
        """Calculate and update execution time."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.execution_time_seconds = delta.total_seconds()
        return self.execution_time_seconds

    def calculate_quality_score(self):
        """Calculate simulation quality score."""
        score = 1.0

        # Penalize failed simulations
        if self.status == "failed":
            score = 0.0
        elif self.status != "completed":
            score = 0.1
        else:
            # Check if results are present and valid
            results = self.get_results()
            if not results:
                score -= 0.5
            elif "error" in results:
                score -= 0.3

            # Check execution time (penalize very long runs)
            if (
                self.execution_time_seconds and self.execution_time_seconds > 3600
            ):  # 1 hour
                score -= 0.1

            # Check if validation passed
            if not self.is_validated:
                score -= 0.2

        self.quality_score = max(0.0, min(1.0, score))
        return self.quality_score

    def to_dict(self, include_results=True):
        """Convert to dictionary."""
        data = {
            "id": self.id,
            "uuid": str(self.uuid),
            "name": self.name,
            "description": self.description,
            "model_type": self.model_type,
            "model_version": self.model_version,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "execution_time_seconds": self.execution_time_seconds,
            "parameters": self.get_parameters(),
            "metrics": self.get_metrics(),
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_time_seconds": self.cpu_time_seconds,
            "is_validated": self.is_validated,
            "validation_errors": self.validation_errors,
            "quality_score": self.quality_score,
            "is_public": self.is_public,
            "is_archived": self.is_archived,
            "user_id": self.user_id,
            "dataset_id": self.dataset_id,
            "task_id": self.task_id,
            "worker_node": self.worker_node,
        }

        if include_results:
            data["results"] = self.get_results()

        return data


class Forecast(db.Model):
    """Forecast model for storing prediction results."""

    __tablename__ = "forecasts"

    id = db.Column(db.Integer, primary_key=True)
    forecast_date = db.Column(db.DateTime, nullable=False, index=True)
    target_date = db.Column(db.DateTime, nullable=False, index=True)
    location = db.Column(db.String(200), index=True)
    location_code = db.Column(db.String(50), index=True)

    # Forecast values
    predicted_value = db.Column(db.Float, nullable=False)
    lower_bound = db.Column(db.Float)
    upper_bound = db.Column(db.Float)
    confidence_level = db.Column(db.Float, default=0.95)

    # Forecast metadata
    forecast_type = db.Column(
        db.String(50), index=True
    )  # cases, deaths, hospitalizations
    model_version = db.Column(db.String(50))
    forecast_horizon_days = db.Column(db.Integer)  # Days ahead from forecast_date

    # Quality metrics
    uncertainty_score = db.Column(db.Float)  # Measure of prediction uncertainty
    is_interpolated = db.Column(db.Boolean, default=False)

    # Audit
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Foreign keys
    simulation_id = db.Column(
        db.Integer,
        db.ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_forecasts_simulation_target", "simulation_id", "target_date"),
        Index("idx_forecasts_simulation_type", "simulation_id", "forecast_type"),
        Index("idx_forecasts_location_target", "location", "target_date"),
        Index("idx_forecasts_location_code_target", "location_code", "target_date"),
        Index("idx_forecasts_forecast_date", "forecast_date"),
        Index("idx_forecasts_type_target", "forecast_type", "target_date"),
        CheckConstraint("predicted_value >= 0", name="ck_predicted_value_positive"),
        CheckConstraint("lower_bound >= 0", name="ck_lower_bound_positive"),
        CheckConstraint("upper_bound >= 0", name="ck_upper_bound_positive"),
        CheckConstraint("lower_bound <= predicted_value", name="ck_lower_bound_valid"),
        CheckConstraint("upper_bound >= predicted_value", name="ck_upper_bound_valid"),
        CheckConstraint(
            "confidence_level > 0 AND confidence_level <= 1",
            name="ck_confidence_level_valid",
        ),
        CheckConstraint(
            "forecast_horizon_days >= 0", name="ck_forecast_horizon_positive"
        ),
    )

    def calculate_uncertainty_score(self):
        """Calculate uncertainty score based on confidence interval width."""
        if (
            self.lower_bound is not None
            and self.upper_bound is not None
            and self.predicted_value > 0
        ):
            interval_width = self.upper_bound - self.lower_bound
            relative_width = interval_width / self.predicted_value
            self.uncertainty_score = min(1.0, relative_width)
        else:
            self.uncertainty_score = 1.0  # Maximum uncertainty if no bounds
        return self.uncertainty_score

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "forecast_date": (
                self.forecast_date.isoformat() if self.forecast_date else None
            ),
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "location": self.location,
            "location_code": self.location_code,
            "predicted_value": self.predicted_value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "confidence_level": self.confidence_level,
            "forecast_type": self.forecast_type,
            "model_version": self.model_version,
            "forecast_horizon_days": self.forecast_horizon_days,
            "uncertainty_score": self.uncertainty_score,
            "is_interpolated": self.is_interpolated,
            "simulation_id": self.simulation_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ModelComparison(db.Model, TimestampMixin):
    """Model comparison results for ensemble analysis."""

    __tablename__ = "model_comparisons"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    comparison_name = db.Column(db.String(200), nullable=False)

    # Comparison metadata
    comparison_type = db.Column(
        db.String(50), default="performance"
    )  # performance, ensemble, validation
    comparison_criteria = db.Column(db.String(100))  # accuracy, speed, interpretability

    # Results
    comparison_results = db.Column(db.Text)  # JSON
    performance_metrics = db.Column(db.Text)  # JSON

    # Status
    status = db.Column(db.String(50), default="pending")

    # Foreign keys
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )

    # Indexes
    __table_args__ = (
        Index("idx_model_comparisons_user_created", "user_id", "created_at"),
        Index("idx_model_comparisons_type_created", "comparison_type", "created_at"),
        CheckConstraint(
            "comparison_type IN ('performance', 'ensemble', 'validation')",
            name="ck_valid_comparison_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_valid_comparison_status",
        ),
    )

    def set_comparison_results(self, results_dict):
        """Set comparison results as JSON string."""
        self.comparison_results = json.dumps(results_dict, default=str)

    def get_comparison_results(self):
        """Get comparison results as dictionary."""
        if self.comparison_results:
            try:
                return json.loads(self.comparison_results)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_performance_metrics(self, metrics_dict):
        """Set performance metrics as JSON string."""
        self.performance_metrics = json.dumps(metrics_dict, default=str)

    def get_performance_metrics(self):
        """Get performance metrics as dictionary."""
        if self.performance_metrics:
            try:
                return json.loads(self.performance_metrics)
            except json.JSONDecodeError:
                return {}
        return {}

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "uuid": str(self.uuid),
            "comparison_name": self.comparison_name,
            "comparison_type": self.comparison_type,
            "comparison_criteria": self.comparison_criteria,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "comparison_results": self.get_comparison_results(),
            "performance_metrics": self.get_performance_metrics(),
            "user_id": self.user_id,
        }


class AuditLog(db.Model):
    """Audit log for tracking user actions and system events."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # User and session info
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    session_id = db.Column(db.String(100))

    # Action details
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(50), index=True)
    resource_id = db.Column(db.Integer, index=True)

    # Request details
    ip_address = db.Column(db.String(45), index=True)
    user_agent = db.Column(db.String(500))
    request_method = db.Column(db.String(10))
    request_path = db.Column(db.String(500))

    # Additional context
    details = db.Column(db.Text)  # JSON string
    severity = db.Column(
        db.String(20), default="info"
    )  # debug, info, warning, error, critical

    # Result
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)

    # Performance metrics
    duration_ms = db.Column(db.Float)

    # Indexes for performance and compliance
    __table_args__ = (
        Index("idx_audit_logs_user_timestamp", "user_id", "timestamp"),
        Index("idx_audit_logs_action_timestamp", "action", "timestamp"),
        Index(
            "idx_audit_logs_resource_timestamp",
            "resource_type",
            "resource_id",
            "timestamp",
        ),
        Index("idx_audit_logs_ip_timestamp", "ip_address", "timestamp"),
        Index("idx_audit_logs_severity_timestamp", "severity", "timestamp"),
        Index("idx_audit_logs_success_timestamp", "success", "timestamp"),
        CheckConstraint(
            "severity IN ('debug', 'info', 'warning', 'error', 'critical')",
            name="ck_valid_severity",
        ),
        CheckConstraint("duration_ms >= 0", name="ck_duration_positive"),
    )

    def set_details(self, details_dict):
        """Set details as JSON string."""
        self.details = json.dumps(details_dict, default=str)

    def get_details(self):
        """Get details as dictionary."""
        if self.details:
            try:
                return json.loads(self.details)
            except json.JSONDecodeError:
                return {}
        return {}

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_method": self.request_method,
            "request_path": self.request_path,
            "details": self.get_details(),
            "severity": self.severity,
            "success": self.success,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
        }
