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

datasets_bp = Blueprint('datasets', __name__)


@datasets_bp.route('/', methods=['GET'])
@token_required
def get_datasets():
    """Get all datasets for the current user."""
    try:
        user = request.current_user
        
        # Admin can see all datasets, others see only their own
        if user.role == 'admin':
            datasets = Dataset.query.all()
        else:
            datasets = Dataset.query.filter_by(user_id=user.id).all()
        
        return jsonify({
            'datasets': [dataset.to_dict() for dataset in datasets]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve datasets: {str(e)}'}), 500


@datasets_bp.route('/<int:dataset_id>', methods=['GET'])
@token_required
def get_dataset(dataset_id):
    """Get specific dataset by ID."""
    try:
        user = request.current_user
        
        # Check permissions
        if not PermissionManager.can_access_dataset(user, dataset_id):
            return jsonify({'error': 'Access denied'}), 403
        
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        return jsonify({'dataset': dataset.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve dataset: {str(e)}'}), 500


@datasets_bp.route('/', methods=['POST'])
@token_required
def create_dataset():
    """Create a new dataset."""
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'data_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate data_type
        valid_data_types = ['time_series', 'cross_sectional', 'spatial']
        if data['data_type'] not in valid_data_types:
            return jsonify({'error': f'data_type must be one of: {valid_data_types}'}), 400
        
        # Create dataset
        dataset = Dataset(
            name=data['name'],
            description=data.get('description', ''),
            data_type=data['data_type'],
            source=data.get('source', ''),
            user_id=user.id
        )
        
        # Set metadata if provided
        if 'metadata' in data:
            dataset.set_metadata(data['metadata'])
        
        db.session.add(dataset)
        db.session.commit()
        
        # Log dataset creation
        audit_log = AuditLog(
            user_id=user.id,
            action='dataset_created',
            resource_type='dataset',
            resource_id=dataset.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        audit_log.set_details({'dataset_name': dataset.name, 'data_type': dataset.data_type})
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'Dataset created successfully',
            'dataset': dataset.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create dataset: {str(e)}'}), 500


@datasets_bp.route('/<int:dataset_id>', methods=['PUT'])
@token_required
def update_dataset(dataset_id):
    """Update dataset metadata."""
    try:
        user = request.current_user
        
        # Check permissions
        if not PermissionManager.can_access_dataset(user, dataset_id):
            return jsonify({'error': 'Access denied'}), 403
        
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            dataset.name = data['name']
        if 'description' in data:
            dataset.description = data['description']
        if 'source' in data:
            dataset.source = data['source']
        if 'metadata' in data:
            dataset.set_metadata(data['metadata'])
        
        db.session.commit()
        
        # Log dataset update
        audit_log = AuditLog(
            user_id=user.id,
            action='dataset_updated',
            resource_type='dataset',
            resource_id=dataset.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'Dataset updated successfully',
            'dataset': dataset.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update dataset: {str(e)}'}), 500


@datasets_bp.route('/<int:dataset_id>', methods=['DELETE'])
@token_required
def delete_dataset(dataset_id):
    """Delete dataset and all associated data."""
    try:
        user = request.current_user
        
        # Check permissions
        if not PermissionManager.can_access_dataset(user, dataset_id):
            return jsonify({'error': 'Access denied'}), 403
        
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Log dataset deletion before deleting
        audit_log = AuditLog(
            user_id=user.id,
            action='dataset_deleted',
            resource_type='dataset',
            resource_id=dataset.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        audit_log.set_details({'dataset_name': dataset.name})
        db.session.add(audit_log)
        
        # Delete dataset (cascade will delete data points)
        db.session.delete(dataset)
        db.session.commit()
        
        return jsonify({'message': 'Dataset deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete dataset: {str(e)}'}), 500


@datasets_bp.route('/<int:dataset_id>/data', methods=['GET'])
@token_required
def get_dataset_data(dataset_id):
    """Get data points for a dataset."""
    try:
        user = request.current_user
        
        # Check permissions
        if not PermissionManager.can_access_dataset(user, dataset_id):
            return jsonify({'error': 'Access denied'}), 403
        
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Get query parameters
        limit = request.args.get('limit', 1000, type=int)
        offset = request.args.get('offset', 0, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        location = request.args.get('location')
        
        # Build query
        query = DataPoint.query.filter_by(dataset_id=dataset_id)
        
        # Apply filters
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(DataPoint.timestamp >= start_dt)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use ISO format.'}), 400
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(DataPoint.timestamp <= end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use ISO format.'}), 400
        
        if location:
            query = query.filter(DataPoint.location.ilike(f'%{location}%'))
        
        # Apply pagination
        data_points = query.order_by(DataPoint.timestamp.desc()).offset(offset).limit(limit).all()
        total_count = query.count()
        
        return jsonify({
            'data_points': [dp.to_dict() for dp in data_points],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve data: {str(e)}'}), 500


@datasets_bp.route('/<int:dataset_id>/data', methods=['POST'])
@token_required
def add_dataset_data(dataset_id):
    """Add data points to a dataset."""
    try:
        user = request.current_user
        
        # Check permissions
        if not PermissionManager.can_access_dataset(user, dataset_id):
            return jsonify({'error': 'Access denied'}), 403
        
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        data = request.get_json()
        
        # Validate data format
        if 'data_points' not in data or not isinstance(data['data_points'], list):
            return jsonify({'error': 'data_points array is required'}), 400
        
        added_points = []
        errors = []
        
        for i, point_data in enumerate(data['data_points']):
            try:
                # Validate required fields
                if 'timestamp' not in point_data:
                    errors.append(f'Point {i}: timestamp is required')
                    continue
                
                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(point_data['timestamp'].replace('Z', '+00:00'))
                except ValueError:
                    errors.append(f'Point {i}: Invalid timestamp format')
                    continue
                
                # Create data point
                data_point = DataPoint(
                    dataset_id=dataset_id,
                    timestamp=timestamp,
                    location=point_data.get('location'),
                    latitude=point_data.get('latitude'),
                    longitude=point_data.get('longitude'),
                    susceptible=point_data.get('susceptible'),
                    exposed=point_data.get('exposed'),
                    infectious=point_data.get('infectious'),
                    recovered=point_data.get('recovered'),
                    deaths=point_data.get('deaths'),
                    new_cases=point_data.get('new_cases'),
                    new_deaths=point_data.get('new_deaths'),
                    population=point_data.get('population'),
                    test_positivity_rate=point_data.get('test_positivity_rate'),
                    hospitalization_rate=point_data.get('hospitalization_rate')
                )
                
                # Set custom data if provided
                if 'custom_data' in point_data:
                    data_point.set_custom_data(point_data['custom_data'])
                
                db.session.add(data_point)
                added_points.append(data_point)
                
            except Exception as e:
                errors.append(f'Point {i}: {str(e)}')
        
        if added_points:
            db.session.commit()
            
            # Log data addition
            audit_log = AuditLog(
                user_id=user.id,
                action='data_added',
                resource_type='dataset',
                resource_id=dataset.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            audit_log.set_details({'points_added': len(added_points), 'errors': len(errors)})
            db.session.add(audit_log)
            db.session.commit()
        
        return jsonify({
            'message': f'Added {len(added_points)} data points',
            'added_count': len(added_points),
            'error_count': len(errors),
            'errors': errors
        }), 201 if added_points else 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to add data: {str(e)}'}), 500


@datasets_bp.route('/<int:dataset_id>/validate', methods=['POST'])
@token_required
def validate_dataset(dataset_id):
    """Validate dataset for completeness and consistency."""
    try:
        user = request.current_user
        
        # Check permissions
        if not PermissionManager.can_access_dataset(user, dataset_id):
            return jsonify({'error': 'Access denied'}), 403
        
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Get all data points
        data_points = DataPoint.query.filter_by(dataset_id=dataset_id).all()
        
        validation_errors = []
        warnings = []
        
        if not data_points:
            validation_errors.append('Dataset contains no data points')
        else:
            # Check for missing timestamps
            missing_timestamps = [dp.id for dp in data_points if not dp.timestamp]
            if missing_timestamps:
                validation_errors.append(f'Missing timestamps in {len(missing_timestamps)} data points')
            
            # Check for negative values in epidemiological data
            for dp in data_points:
                negative_fields = []
                for field in ['susceptible', 'exposed', 'infectious', 'recovered', 'deaths', 'new_cases', 'new_deaths']:
                    value = getattr(dp, field)
                    if value is not None and value < 0:
                        negative_fields.append(field)
                
                if negative_fields:
                    warnings.append(f'Negative values in data point {dp.id}: {negative_fields}')
            
            # Check for data consistency (S + E + I + R should not exceed population)
            for dp in data_points:
                if all(getattr(dp, field) is not None for field in ['susceptible', 'exposed', 'infectious', 'recovered', 'population']):
                    total_seir = dp.susceptible + dp.exposed + dp.infectious + dp.recovered
                    if total_seir > dp.population:
                        warnings.append(f'SEIR total ({total_seir}) exceeds population ({dp.population}) in data point {dp.id}')
            
            # Check for temporal consistency
            sorted_points = sorted(data_points, key=lambda x: x.timestamp)
            for i in range(1, len(sorted_points)):
                prev_point = sorted_points[i-1]
                curr_point = sorted_points[i]
                
                # Check if recovered count decreases (should be monotonic)
                if (prev_point.recovered is not None and curr_point.recovered is not None and 
                    prev_point.location == curr_point.location and 
                    curr_point.recovered < prev_point.recovered):
                    warnings.append(f'Recovered count decreased from {prev_point.recovered} to {curr_point.recovered} between {prev_point.timestamp} and {curr_point.timestamp}')
        
        # Update dataset validation status
        dataset.is_validated = len(validation_errors) == 0
        dataset.validation_errors = json.dumps({
            'errors': validation_errors,
            'warnings': warnings,
            'validated_at': datetime.utcnow().isoformat()
        })
        
        db.session.commit()
        
        # Log validation
        audit_log = AuditLog(
            user_id=user.id,
            action='dataset_validated',
            resource_type='dataset',
            resource_id=dataset.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        audit_log.set_details({
            'is_valid': dataset.is_validated,
            'error_count': len(validation_errors),
            'warning_count': len(warnings)
        })
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'is_valid': dataset.is_validated,
            'errors': validation_errors,
            'warnings': warnings,
            'data_point_count': len(data_points)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500


@datasets_bp.route('/<int:dataset_id>/export', methods=['GET'])
@token_required
def export_dataset(dataset_id):
    """Export dataset as CSV or JSON."""
    try:
        user = request.current_user
        
        # Check permissions
        if not PermissionManager.can_access_dataset(user, dataset_id):
            return jsonify({'error': 'Access denied'}), 403
        
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({'error': 'Dataset not found'}), 404
        
        # Get export format
        export_format = request.args.get('format', 'json').lower()
        if export_format not in ['json', 'csv']:
            return jsonify({'error': 'Format must be json or csv'}), 400
        
        # Get data points
        data_points = DataPoint.query.filter_by(dataset_id=dataset_id).order_by(DataPoint.timestamp).all()
        
        if export_format == 'json':
            export_data = {
                'dataset': dataset.to_dict(),
                'data_points': [dp.to_dict() for dp in data_points]
            }
            return jsonify(export_data), 200
        
        else:  # CSV format
            # Convert to pandas DataFrame for CSV export
            data_list = []
            for dp in data_points:
                row = dp.to_dict()
                # Flatten custom_data
                if row['custom_data']:
                    for key, value in row['custom_data'].items():
                        row[f'custom_{key}'] = value
                del row['custom_data']
                data_list.append(row)
            
            if data_list:
                df = pd.DataFrame(data_list)
                csv_data = df.to_csv(index=False)
                
                return csv_data, 200, {
                    'Content-Type': 'text/csv',
                    'Content-Disposition': f'attachment; filename=dataset_{dataset_id}.csv'
                }
            else:
                return "No data to export", 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

