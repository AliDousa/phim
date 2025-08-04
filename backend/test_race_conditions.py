#!/usr/bin/env python3
"""
Test script for race condition fixes in simulation management.

This script validates that the optimistic locking implementation
prevents race conditions when multiple processes try to update
the same simulation simultaneously.
"""

import os
import sys
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from src.models.database import db, Simulation, ConcurrencyError, User
from src.main import create_app
import json

def setup_test_environment():
    """Set up test environment with in-memory database."""
    app = create_app('testing')
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create test user
        test_user = User(
            username="test_user",
            email="test@example.com",
            role="researcher"
        )
        test_user.set_password("testpass123")
        db.session.add(test_user)
        db.session.commit()
        
        return app, test_user.id

def create_test_simulation(app, user_id):
    """Create a test simulation."""
    with app.app_context():
        simulation = Simulation(
            name="Race Condition Test",
            description="Testing concurrent access",
            model_type="seir",
            user_id=user_id,
            status="pending"
        )
        simulation.set_parameters({
            "beta": 0.5,
            "sigma": 0.2,
            "gamma": 0.1,
            "population": 100000
        })
        
        db.session.add(simulation)
        db.session.commit()
        
        return simulation.id

def concurrent_status_update_test(app, simulation_id, worker_id, new_status, delay=0):
    """
    Test function for concurrent status updates.
    
    Args:
        app: Flask application
        simulation_id: ID of simulation to update
        worker_id: Unique identifier for this worker
        new_status: Status to set
        delay: Delay before update (for timing control)
    
    Returns:
        dict: Result of the operation
    """
    if delay:
        time.sleep(delay)
        
    with app.app_context():
        try:
            simulation = Simulation.query.get(simulation_id)
            if not simulation:
                return {"worker_id": worker_id, "success": False, "error": "Simulation not found"}
            
            # Attempt atomic status update
            if new_status == "running":
                success = simulation.start_simulation(
                    task_id=f"task_{worker_id}",
                    worker_node=f"worker_{worker_id}"
                )
                return {
                    "worker_id": worker_id,
                    "success": success,
                    "status": simulation.status,
                    "version": simulation.version,
                    "operation": "start"
                }
            else:
                simulation.update_status_atomic(new_status)
                return {
                    "worker_id": worker_id,
                    "success": True,
                    "status": simulation.status,
                    "version": simulation.version,
                    "operation": "update"
                }
                
        except ConcurrencyError as e:
            return {
                "worker_id": worker_id,
                "success": False,
                "error": "ConcurrencyError",
                "message": str(e),
                "operation": "failed"
            }
        except Exception as e:
            return {
                "worker_id": worker_id,
                "success": False,
                "error": type(e).__name__,
                "message": str(e),
                "operation": "failed"
            }

def test_concurrent_simulation_start():
    """Test multiple workers trying to start the same simulation."""
    print("\\n=== Testing Concurrent Simulation Start ===")
    
    app, user_id = setup_test_environment()
    simulation_id = create_test_simulation(app, user_id)
    
    # Start 5 workers simultaneously trying to start the same simulation
    num_workers = 5
    results = []
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(
                concurrent_status_update_test,
                app, simulation_id, i, "running", delay=0
            )
            for i in range(num_workers)
        ]
        
        for future in as_completed(futures):
            results.append(future.result())
    
    # Analyze results
    successful_starts = [r for r in results if r["success"] and r["operation"] == "start"]
    failed_starts = [r for r in results if not r["success"]]
    
    print(f"Workers attempted to start simulation: {num_workers}")
    print(f"Successful starts: {len(successful_starts)}")
    print(f"Failed starts (expected): {len(failed_starts)}")
    
    # Verify only one worker succeeded
    assert len(successful_starts) == 1, f"Expected exactly 1 successful start, got {len(successful_starts)}"
    assert len(failed_starts) == num_workers - 1, f"Expected {num_workers-1} failed starts, got {len(failed_starts)}"
    
    # Check final simulation state
    with app.app_context():
        final_sim = Simulation.query.get(simulation_id)
        assert final_sim.status == "running", f"Expected status 'running', got '{final_sim.status}'"
        assert final_sim.task_id is not None, "Task ID should be set"
        assert final_sim.worker_node is not None, "Worker node should be set"
    
    print("✅ Concurrent simulation start test PASSED")
    
    # Print detailed results
    for result in results:
        status_icon = "✅" if result["success"] else "❌"
        print(f"  {status_icon} Worker {result['worker_id']}: {result.get('operation', 'unknown')}")

def test_concurrent_status_updates():
    """Test multiple workers trying to update simulation status."""
    print("\\n=== Testing Concurrent Status Updates ===")
    
    app, user_id = setup_test_environment()
    simulation_id = create_test_simulation(app, user_id)
    
    # First, set simulation to running state
    with app.app_context():
        sim = Simulation.query.get(simulation_id)
        sim.start_simulation(task_id="initial_task", worker_node="initial_worker")
    
    # Now try to complete/fail the simulation from multiple workers
    results = []
    
    def complete_simulation(app, simulation_id, worker_id):
        with app.app_context():
            try:
                simulation = Simulation.query.get(simulation_id)
                simulation.complete_simulation(
                    results_dict={"result": f"completed_by_worker_{worker_id}"},
                    metrics_dict={"worker": worker_id}
                )
                return {"worker_id": worker_id, "success": True, "operation": "complete"}
            except Exception as e:
                return {
                    "worker_id": worker_id,
                    "success": False,
                    "error": str(e),
                    "operation": "complete"
                }
    
    def fail_simulation(app, simulation_id, worker_id):
        with app.app_context():
            try:
                simulation = Simulation.query.get(simulation_id)
                simulation.fail_simulation(f"Failed by worker {worker_id}")
                return {"worker_id": worker_id, "success": True, "operation": "fail"}
            except Exception as e:
                return {
                    "worker_id": worker_id,
                    "success": False,
                    "error": str(e),
                    "operation": "fail"
                }
    
    # Start competing operations
    with ThreadPoolExecutor(max_workers=4) as executor:
        # 2 workers try to complete, 2 try to fail
        futures = [
            executor.submit(complete_simulation, app, simulation_id, 0),
            executor.submit(complete_simulation, app, simulation_id, 1),
            executor.submit(fail_simulation, app, simulation_id, 2),
            executor.submit(fail_simulation, app, simulation_id, 3),
        ]
        
        for future in as_completed(futures):
            results.append(future.result())
    
    # Analyze results
    successful_ops = [r for r in results if r["success"]]
    failed_ops = [r for r in results if not r["success"]]
    
    print(f"Workers attempted to update simulation: 4")
    print(f"Successful updates: {len(successful_ops)}")
    print(f"Failed updates (expected): {len(failed_ops)}")
    
    # Verify only one operation succeeded
    assert len(successful_ops) == 1, f"Expected exactly 1 successful update, got {len(successful_ops)}"
    assert len(failed_ops) == 3, f"Expected 3 failed updates, got {len(failed_ops)}"
    
    # Check final simulation state
    with app.app_context():
        final_sim = Simulation.query.get(simulation_id)
        assert final_sim.status in ["completed", "failed"], f"Expected final status 'completed' or 'failed', got '{final_sim.status}'"
        assert final_sim.version > 2, f"Expected version > 2, got {final_sim.version}"  # Started at 1, updated to running (2), then final update (3+)
    
    print("✅ Concurrent status updates test PASSED")
    
    # Print detailed results
    for result in results:
        status_icon = "✅" if result["success"] else "❌"
        print(f"  {status_icon} Worker {result['worker_id']}: {result['operation']}")

def test_version_increment():
    """Test that version numbers increment correctly."""
    print("\\n=== Testing Version Increment ===")
    
    app, user_id = setup_test_environment()
    simulation_id = create_test_simulation(app, user_id)
    
    with app.app_context():
        simulation = Simulation.query.get(simulation_id)
        
        # Initial version should be 1
        assert simulation.version == 1, f"Expected initial version 1, got {simulation.version}"
        
        # Start simulation - version should be 2
        simulation.start_simulation(task_id="test_task")
        assert simulation.version == 2, f"Expected version 2 after start, got {simulation.version}"
        
        # Complete simulation - version should be 3
        simulation.complete_simulation({"test": "result"})
        assert simulation.version == 3, f"Expected version 3 after completion, got {simulation.version}"
    
    print("✅ Version increment test PASSED")

def test_invalid_status_transitions():
    """Test that invalid status transitions are prevented."""
    print("\\n=== Testing Invalid Status Transitions ===")
    
    app, user_id = setup_test_environment()
    simulation_id = create_test_simulation(app, user_id)
    
    with app.app_context():
        simulation = Simulation.query.get(simulation_id)
        
        # Try to complete a pending simulation (should fail)
        try:
            simulation.complete_simulation({"test": "result"})
            assert False, "Should not be able to complete a pending simulation"
        except ValueError as e:
            assert "Cannot complete simulation in status: pending" in str(e)
        
        # Start the simulation properly
        simulation.start_simulation(task_id="test_task")
        
        # Try to start again (should fail)
        success = simulation.start_simulation(task_id="test_task_2")
        assert not success, "Should not be able to start an already running simulation"
        
        # Complete the simulation
        simulation.complete_simulation({"test": "result"})
        
        # Try to cancel completed simulation (should fail)
        try:
            simulation.cancel_simulation("test reason")
            assert False, "Should not be able to cancel a completed simulation"
        except ValueError as e:
            assert "Cannot cancel simulation in status: completed" in str(e)
    
    print("✅ Invalid status transitions test PASSED")

def run_all_tests():
    """Run all race condition tests."""
    print("🧪 Starting Race Condition Tests for Simulation Management")
    print("=" * 60)
    
    try:
        test_version_increment()
        test_invalid_status_transitions()
        test_concurrent_simulation_start()
        test_concurrent_status_updates()
        
        print("\\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("\\nThe race condition fixes are working correctly:")
        print("✅ Optimistic locking prevents concurrent modifications")
        print("✅ Only one worker can start a simulation")
        print("✅ Status transitions are atomic and consistent")
        print("✅ Version numbers increment correctly")
        print("✅ Invalid transitions are prevented")
        
    except AssertionError as e:
        print(f"\\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()