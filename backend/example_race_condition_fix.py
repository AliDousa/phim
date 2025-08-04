#!/usr/bin/env python3
"""
Example demonstrating the race condition fix implementation.

This example shows how to use the new atomic status update methods
to prevent race conditions in simulation management.
"""

from src.models.database import Simulation, ConcurrencyError, db
from src.main import create_app
import json

def demonstrate_race_condition_fix():
    """Demonstrate the proper way to handle simulation status updates."""
    
    print("🔧 Race Condition Fix Demo")
    print("=" * 40)
    
    # Create app context
    app = create_app('development')
    
    with app.app_context():
        # Assume we have a simulation (in real code, get from database)
        simulation = Simulation.query.filter_by(status='pending').first()
        
        if not simulation:
            print("No pending simulations found. Create one first.")
            return
        
        print(f"Working with simulation: {simulation.name} (ID: {simulation.id})")
        print(f"Initial status: {simulation.status}, version: {simulation.version}")
        
        # ========================================
        # OLD WAY (Race Condition Prone)
        # ========================================
        print("\\n❌ OLD WAY (Race Condition Prone):")
        print("# simulation.status = 'running'")
        print("# simulation.started_at = datetime.utcnow()")
        print("# db.session.commit()  # <- RACE CONDITION!")
        print("# Multiple workers could do this simultaneously!")
        
        # ========================================
        # NEW WAY (Race Condition Safe)
        # ========================================
        print("\\n✅ NEW WAY (Race Condition Safe):")
        
        try:
            # Attempt to start simulation atomically
            success = simulation.start_simulation(
                task_id="demo_task_123",
                worker_node="demo_worker"
            )
            
            if success:
                print("✅ Successfully started simulation!")
                print(f"   Status: {simulation.status}")
                print(f"   Version: {simulation.version}")
                print(f"   Task ID: {simulation.task_id}")
                print(f"   Worker: {simulation.worker_node}")
                print(f"   Started at: {simulation.started_at}")
                
                # Simulate some work...
                print("\\n🔄 Simulating work being done...")
                
                # Complete the simulation atomically
                results = {
                    "model_type": "demo",
                    "peak_infections": 15000,
                    "total_infected": 75000,
                    "r0": 2.5
                }
                
                metrics = {
                    "execution_time": 45.2,
                    "memory_usage_mb": 128.5,
                    "cpu_utilization": 0.85
                }
                
                simulation.complete_simulation(
                    results_dict=results,
                    metrics_dict=metrics
                )
                
                print("✅ Successfully completed simulation!")
                print(f"   Status: {simulation.status}")
                print(f"   Version: {simulation.version}")
                print(f"   Execution time: {simulation.execution_time_seconds}s")
                print(f"   Quality score: {simulation.quality_score}")
                
            else:
                print("❌ Could not start simulation (already running/completed)")
                print(f"   Current status: {simulation.status}")
                
        except ConcurrencyError as e:
            print(f"⚠️  Concurrency conflict detected: {e}")
            print("   This means another worker modified the simulation simultaneously")
            print("   The operation was safely aborted to prevent data corruption")
            
        except Exception as e:
            print(f"💥 Unexpected error: {e}")

def demonstrate_error_handling():
    """Demonstrate proper error handling with atomic updates."""
    
    print("\\n\\n🚨 Error Handling Demo")
    print("=" * 40)
    
    app = create_app('development')
    
    with app.app_context():
        # Find a running simulation to demonstrate failure handling
        simulation = Simulation.query.filter_by(status='running').first()
        
        if not simulation:
            print("No running simulations found for error demo.")
            return
            
        print(f"Simulating failure for: {simulation.name}")
        
        try:
            # Simulate a failure scenario
            simulation.fail_simulation(
                error_message="Division by zero in model calculation",
                error_details={
                    "line_number": 142,
                    "function": "calculate_transmission_rate",
                    "parameters": {"beta": 0, "population": 100000}
                }
            )
            
            print("✅ Failure recorded atomically!")
            print(f"   Status: {simulation.status}")
            print(f"   Version: {simulation.version}")
            print(f"   Error: {simulation.validation_errors}")
            print(f"   Quality score: {simulation.quality_score}")
            
            # Check the error details in results
            error_results = simulation.get_results()
            if 'error' in error_results:
                print(f"   Error details: {error_results['details']}")
                
        except ConcurrencyError as e:
            print(f"⚠️  Another process already updated this simulation: {e}")

def demonstrate_cancellation():
    """Demonstrate simulation cancellation."""
    
    print("\\n\\n🛑 Cancellation Demo")
    print("=" * 40)
    
    app = create_app('development')
    
    with app.app_context():
        # Find a pending or running simulation to cancel
        simulation = Simulation.query.filter(
            Simulation.status.in_(['pending', 'running'])
        ).first()
        
        if not simulation:
            print("No cancellable simulations found.")
            return
            
        print(f"Cancelling simulation: {simulation.name}")
        
        try:
            simulation.cancel_simulation(
                reason="User requested cancellation"
            )
            
            print("✅ Simulation cancelled atomically!")
            print(f"   Status: {simulation.status}")
            print(f"   Version: {simulation.version}")
            
            # Check cancellation details
            cancel_results = simulation.get_results()
            if 'cancelled_reason' in cancel_results:
                print(f"   Reason: {cancel_results['cancelled_reason']}")
                
        except ValueError as e:
            print(f"❌ Cannot cancel: {e}")
        except ConcurrencyError as e:
            print(f"⚠️  Concurrency conflict: {e}")

if __name__ == "__main__":
    print("🎯 Public Health Intelligence Platform")
    print("Race Condition Fix Demonstration")
    print("\\nThis demo shows how the new atomic status update methods")
    print("prevent race conditions in simulation management.")
    
    try:
        demonstrate_race_condition_fix()
        demonstrate_error_handling()
        demonstrate_cancellation()
        
        print("\\n\\n🎉 Demo completed successfully!")
        print("\\nKey Benefits of the Race Condition Fix:")
        print("✅ Atomic status updates prevent data corruption")
        print("✅ Optimistic locking handles concurrent access")
        print("✅ Clear error messages for concurrency conflicts")
        print("✅ Consistent database state guaranteed")
        print("✅ Better error handling and logging")
        
    except Exception as e:
        print(f"\\n💥 Demo failed: {e}")
        import traceback
        traceback.print_exc()