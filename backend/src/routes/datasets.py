"""
Dataset management API routes.
"""

from flask import Blueprint, request, jsonify
from src.models.database import Dataset, DataPoint, User, db, AuditLog
from src.auth import token_required, PermissionManager
import pandas as pd
import json
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename

datasets_bp = Blueprint("datasets", __name__)


# --- ADVANCED HELPER: Parse and insert data with dynamic column mapping ---
def parse_and_insert_data(df, dataset_id, column_mapping):
    """
    Parses a DataFrame using a user-provided column map and inserts data points.
    """
    data_points = []

    # Map user-provided column names to our internal names
    rename_map = {
        user_col_name: internal_name
        for internal_name, user_col_name in column_mapping.items()
    }

    # Check if all required source columns exist in the DataFrame
    for user_col_name in rename_map.values():
        if user_col_name not in df.columns:
            raise ValueError(
                f"Mapped column '{user_col_name}' not found in the uploaded file."
            )

    df = df.rename(columns=rename_map)

    # Check if all internal columns are now present after renaming
    required_internal_cols = ["timestamp", "location", "new_cases", "new_deaths"]
    if not all(col in df.columns for col in required_internal_cols):
        missing = [col for col in required_internal_cols if col not in df.columns]
        raise ValueError(
            f"Mapping is incomplete. The following required data is missing: {', '.join(missing)}"
        )

    for _, row in df.iterrows():
        try:
            timestamp = pd.to_datetime(row["timestamp"])
        except Exception:
            continue

        data_point = DataPoint(
            dataset_id=dataset_id,
            timestamp=timestamp,
            location=row.get("location"),
            new_cases=pd.to_numeric(row.get("new_cases"), errors="coerce"),
            new_deaths=pd.to_numeric(row.get("new_deaths"), errors="coerce"),
            population=pd.to_numeric(
                row.get(column_mapping.get("population_col", "population")),
                errors="coerce",
            ),
        )
        data_points.append(data_point)

    db.session.bulk_save_objects(data_points)
    return len(data_points)


# --- Endpoint to get headers of an uploaded file for mapping ---
@datasets_bp.route("/get-headers", methods=["POST"])
@token_required
def get_file_headers():
    """Reads a CSV/JSON file and returns its column headers."""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    # FIX: Check if a file was actually selected
    if not file or not file.filename:
        return jsonify({"error": "No selected file"}), 400

    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file.stream, nrows=1)
        elif file.filename.endswith(".json"):
            # Assuming newline-delimited JSON for robust parsing of large files
            df = pd.read_json(file.stream, lines=True, nrows=1)
        else:
            return jsonify({"error": "Unsupported file type. Use CSV or JSON."}), 400

        return jsonify({"headers": list(df.columns)}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to parse file headers: {str(e)}"}), 400


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

        return jsonify({"datasets": [dataset.to_dict() for dataset in datasets]}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve datasets: {str(e)}"}), 500


@datasets_bp.route("/", methods=["POST"])
@token_required
def create_dataset():
    """Create a new dataset from an uploaded file using column mapping."""
    try:
        user = request.current_user
        form_data = request.form

        required_fields = ["name", "data_type", "column_mapping"]
        for field in required_fields:
            if field not in form_data or not form_data[field]:
                return jsonify({"error": f"{field} is required"}), 400

        if "file" not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "No file selected for uploading"}), 400

        try:
            column_mapping = json.loads(form_data["column_mapping"])
        except json.JSONDecodeError:
            return (
                jsonify(
                    {
                        "error": "Invalid format for column_mapping. Must be a JSON string."
                    }
                ),
                400,
            )

        dataset = Dataset(
            name=form_data["name"],
            description=form_data.get("description", ""),
            data_type=form_data["data_type"],
            source=file.filename,
            user_id=user.id,
        )
        db.session.add(dataset)
        db.session.flush()

        # FIX: Ensure filename is not None before processing
        filename = secure_filename(file.filename or "")

        try:
            file.stream.seek(0)
            if filename.endswith(".csv"):
                df = pd.read_csv(file.stream)
            else:
                df = pd.read_json(file.stream)

            points_added = parse_and_insert_data(df, dataset.id, column_mapping)

        except ValueError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to process file: {str(e)}"}), 500

        db.session.commit()

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
                "filename": filename,
                "points_added": points_added,
                "column_mapping": column_mapping,
            }
        )
        db.session.add(audit_log)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Dataset created successfully",
                    "dataset": dataset.to_dict(),
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

        db.session.delete(dataset)
        db.session.commit()

        return jsonify({"message": "Dataset deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete dataset: {str(e)}"}), 500
