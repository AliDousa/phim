"""
Dataset management API routes.
"""

from flask import Blueprint, request, jsonify
import pandas as pd
import json
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename

# Import with fallback for different execution contexts
try:
    from ..models.database import Dataset, DataPoint, User, db, AuditLog
    from ..auth import token_required, PermissionManager
except ImportError:
    from models.database import Dataset, DataPoint, User, db, AuditLog
    from auth import token_required, PermissionManager

datasets_bp = Blueprint("datasets", __name__)

# Configuration
ALLOWED_EXTENSIONS = {"csv", "json"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


def allowed_file(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_and_insert_data(df, dataset_id, column_mapping):
    """
    Parses a DataFrame using a user-provided column map and inserts data points.

    Args:
        df: Pandas DataFrame with the data
        dataset_id: ID of the dataset to associate with
        column_mapping: Dictionary mapping internal column names to user column names

    Returns:
        Number of data points inserted

    Raises:
        ValueError: If required columns are missing or data is invalid
    """
    data_points = []

    # Validate required mappings
    required_mappings = [
        "timestamp_col",
        "location_col",
        "new_cases_col",
        "new_deaths_col",
    ]
    missing_mappings = [req for req in required_mappings if req not in column_mapping]
    if missing_mappings:
        raise ValueError(
            f"Missing required column mappings: {', '.join(missing_mappings)}"
        )

    # Map user-provided column names to our internal names
    rename_map = {}
    for internal_name, user_col_name in column_mapping.items():
        if user_col_name and user_col_name in df.columns:
            # Map from user column name to internal name
            if internal_name == "timestamp_col":
                rename_map[user_col_name] = "timestamp"
            elif internal_name == "location_col":
                rename_map[user_col_name] = "location"
            elif internal_name == "new_cases_col":
                rename_map[user_col_name] = "new_cases"
            elif internal_name == "new_deaths_col":
                rename_map[user_col_name] = "new_deaths"
            elif internal_name == "population_col":
                rename_map[user_col_name] = "population"

    # Check if all required source columns exist in the DataFrame
    missing_columns = [
        user_col
        for user_col in column_mapping.values()
        if user_col and user_col not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Mapped columns not found in file: {', '.join(missing_columns)}"
        )

    # Rename columns
    df_renamed = df.rename(columns=rename_map)

    # Validate that we have the required columns after renaming
    required_columns = ["timestamp", "location", "new_cases", "new_deaths"]
    missing_required = [
        col for col in required_columns if col not in df_renamed.columns
    ]
    if missing_required:
        raise ValueError(
            f"Required data missing after mapping: {', '.join(missing_required)}"
        )

    # Process each row
    for index, row in df_renamed.iterrows():
        try:
            # Parse timestamp
            timestamp = pd.to_datetime(row["timestamp"], errors="coerce")
            if pd.isna(timestamp):
                continue  # Skip rows with invalid timestamps

            # Create data point
            data_point = DataPoint(
                dataset_id=dataset_id,
                timestamp=timestamp.to_pydatetime(),
                location=str(row.get("location", "")),
                new_cases=pd.to_numeric(row.get("new_cases"), errors="coerce"),
                new_deaths=pd.to_numeric(row.get("new_deaths"), errors="coerce"),
                population=pd.to_numeric(row.get("population"), errors="coerce"),
            )
            data_points.append(data_point)

        except Exception as e:
            # Log the error but continue processing other rows
            print(f"Error processing row {index}: {e}")
            continue

    if not data_points:
        raise ValueError("No valid data points could be created from the file")

    # Bulk insert for better performance
    try:
        db.session.bulk_save_objects(data_points)
        db.session.commit()
        return len(data_points)
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Database error while inserting data: {str(e)}")


@datasets_bp.route("/get-headers", methods=["POST"])
@token_required
def get_file_headers():
    """Reads a CSV/JSON file and returns its column headers."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"error": "No selected file"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Unsupported file type. Use CSV or JSON."}), 400

        # Read file headers
        try:
            if file.filename.lower().endswith(".csv"):
                df = pd.read_csv(
                    file.stream, nrows=5
                )  # Read a few rows to detect headers
            elif file.filename.lower().endswith(".json"):
                # Try different JSON formats
                file_content = file.stream.read()
                try:
                    # Try regular JSON
                    data = json.loads(file_content)
                    if isinstance(data, list) and len(data) > 0:
                        df = pd.DataFrame(data[:5])
                    else:
                        return (
                            jsonify(
                                {"error": "JSON file must contain an array of objects"}
                            ),
                            400,
                        )
                except json.JSONDecodeError:
                    # Try newline-delimited JSON
                    file.stream.seek(0)
                    df = pd.read_json(file.stream, lines=True, nrows=5)
            else:
                return jsonify({"error": "Unsupported file type"}), 400

            headers = [str(col) for col in df.columns]
            return jsonify({"headers": headers}), 200

        except Exception as e:
            return jsonify({"error": f"Failed to parse file: {str(e)}"}), 400

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@datasets_bp.route("/", methods=["GET"])
@token_required
def get_datasets():
    """Get all datasets for the current user."""
    try:
        user = request.current_user

        if user.role == "admin":
            datasets = Dataset.query.all()
        else:
            datasets = Dataset.query.filter_by(user_id=user.id).all()

        datasets_data = []
        for dataset in datasets:
            dataset_dict = dataset.to_dict()
            # Ensure record_count is included
            if "record_count" not in dataset_dict:
                dataset_dict["record_count"] = len(dataset.data_points)
            datasets_data.append(dataset_dict)

        return jsonify({"datasets": datasets_data}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve datasets: {str(e)}"}), 500


@datasets_bp.route("/", methods=["POST"])
@token_required
def create_dataset():
    """Create a new dataset from an uploaded file using column mapping."""
    try:
        user = request.current_user
        form_data = request.form

        # Validate required fields
        required_fields = ["name", "data_type", "column_mapping"]
        for field in required_fields:
            if field not in form_data or not form_data[field]:
                return jsonify({"error": f"{field} is required"}), 400

        if "file" not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"error": "No file selected for uploading"}), 400

        # Validate file type
        if not allowed_file(file.filename):
            return (
                jsonify(
                    {"error": "Invalid file type. Only CSV and JSON files are allowed."}
                ),
                400,
            )

        # Parse column mapping
        try:
            column_mapping = json.loads(form_data["column_mapping"])
            if not isinstance(column_mapping, dict):
                raise ValueError("Column mapping must be a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            return jsonify({"error": f"Invalid column mapping format: {str(e)}"}), 400

        # Validate data type
        valid_data_types = ["time_series", "cross_sectional", "spatial"]
        if form_data["data_type"] not in valid_data_types:
            return (
                jsonify(
                    {
                        "error": f"Invalid data type. Must be one of: {', '.join(valid_data_types)}"
                    }
                ),
                400,
            )

        # Create dataset record
        dataset = Dataset(
            name=form_data["name"].strip(),
            description=form_data.get("description", "").strip(),
            data_type=form_data["data_type"],
            source=secure_filename(file.filename),
            user_id=user.id,
            is_validated=False,
        )

        # Set metadata
        metadata = {
            "file_size": file.content_length if hasattr(file, "content_length") else 0,
            "column_mapping": column_mapping,
            "upload_timestamp": datetime.utcnow().isoformat(),
        }
        dataset.set_metadata(metadata)

        db.session.add(dataset)
        db.session.flush()  # Get the ID

        # Process file data
        try:
            file.stream.seek(0)  # Reset file pointer

            if file.filename.lower().endswith(".csv"):
                df = pd.read_csv(file.stream)
            elif file.filename.lower().endswith(".json"):
                file_content = file.stream.read()
                try:
                    # Try regular JSON
                    data = json.loads(file_content)
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    else:
                        return (
                            jsonify(
                                {"error": "JSON file must contain an array of objects"}
                            ),
                            400,
                        )
                except json.JSONDecodeError:
                    # Try newline-delimited JSON
                    file.stream.seek(0)
                    df = pd.read_json(file.stream, lines=True)

            # Validate DataFrame
            if df.empty:
                db.session.rollback()
                return jsonify({"error": "File contains no data"}), 400

            # Parse and insert data
            points_added = parse_and_insert_data(df, dataset.id, column_mapping)

            # Mark as validated if successful
            dataset.is_validated = True
            dataset.validation_errors = None

        except ValueError as ve:
            db.session.rollback()
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to process file: {str(e)}"}), 500

        db.session.commit()

        # Create audit log
        try:
            audit_log = AuditLog(
                user_id=user.id,
                action="dataset_created",
                resource_type="dataset",
                resource_id=dataset.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )
            audit_log.set_details(
                {
                    "dataset_name": dataset.name,
                    "filename": file.filename,
                    "points_added": points_added,
                    "column_mapping": column_mapping,
                }
            )
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:
            # Don't fail the whole operation if audit logging fails
            print(f"Audit logging failed: {e}")

        return (
            jsonify(
                {
                    "message": "Dataset created successfully",
                    "dataset": dataset.to_dict(),
                    "points_added": points_added,
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@datasets_bp.route("/<int:dataset_id>", methods=["GET"])
@token_required
def get_dataset(dataset_id):
    """Get specific dataset by ID."""
    try:
        user = request.current_user

        if not PermissionManager.can_access_dataset(user, dataset_id):
            return jsonify({"error": "Access denied"}), 403

        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({"error": "Dataset not found"}), 404

        return jsonify({"dataset": dataset.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve dataset: {str(e)}"}), 500


@datasets_bp.route("/<int:dataset_id>", methods=["DELETE"])
@token_required
def delete_dataset(dataset_id):
    """Delete dataset and all associated data."""
    try:
        user = request.current_user

        if not PermissionManager.can_access_dataset(user, dataset_id):
            return jsonify({"error": "Access denied"}), 403

        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({"error": "Dataset not found"}), 404

        dataset_name = dataset.name

        # Delete dataset (cascade will handle data points)
        db.session.delete(dataset)
        db.session.commit()

        # Create audit log
        try:
            audit_log = AuditLog(
                user_id=user.id,
                action="dataset_deleted",
                resource_type="dataset",
                resource_id=dataset_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )
            audit_log.set_details({"dataset_name": dataset_name})
            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:
            print(f"Audit logging failed: {e}")

        return jsonify({"message": "Dataset deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete dataset: {str(e)}"}), 500


@datasets_bp.route("/<int:dataset_id>/data", methods=["GET"])
@token_required
def get_dataset_data(dataset_id):
    """Get data points for a specific dataset."""
    try:
        user = request.current_user

        if not PermissionManager.can_access_dataset(user, dataset_id):
            return jsonify({"error": "Access denied"}), 403

        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({"error": "Dataset not found"}), 404

        # Get pagination parameters
        page = request.args.get("page", 1, type=int)
        per_page = min(
            request.args.get("per_page", 100, type=int), 1000
        )  # Max 1000 per page

        # Query data points with pagination
        data_points = (
            DataPoint.query.filter_by(dataset_id=dataset_id)
            .order_by(DataPoint.timestamp)
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return (
            jsonify(
                {
                    "data": [dp.to_dict() for dp in data_points.items],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": data_points.total,
                        "pages": data_points.pages,
                        "has_next": data_points.has_next,
                        "has_prev": data_points.has_prev,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve dataset data: {str(e)}"}), 500
