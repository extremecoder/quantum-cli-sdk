#!/usr/bin/env python3
"""
Quantum Job Management module for monitoring and controlling remote quantum execution jobs.

This module provides functionality to:
- List active and completed jobs
- Monitor job status and results
- Cancel running jobs
- Retrieve job execution details
"""

import os
import json
import uuid
import datetime
import time
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
import threading
import queue

logger = logging.getLogger(__name__)

# Job status constants
class JobStatus:
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"

@dataclass
class JobDetails:
    """Details about a quantum execution job."""
    job_id: str
    name: str
    provider: str
    backend: str
    creation_time: float
    status: str
    user_id: str
    circuit_id: str
    shots: int
    estimated_duration: float
    estimated_cost: Optional[float] = None
    queue_position: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "provider": self.provider,
            "backend": self.backend,
            "creation_time": self.creation_time,
            "status": self.status,
            "user_id": self.user_id,
            "circuit_id": self.circuit_id,
            "shots": self.shots,
            "estimated_duration": self.estimated_duration,
            "estimated_cost": self.estimated_cost,
            "queue_position": self.queue_position,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "result_url": self.result_url,
            "error_message": self.error_message,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobDetails':
        """Create a JobDetails from a dictionary."""
        return cls(
            job_id=data["job_id"],
            name=data["name"],
            provider=data["provider"],
            backend=data["backend"],
            creation_time=data["creation_time"],
            status=data["status"],
            user_id=data["user_id"],
            circuit_id=data["circuit_id"],
            shots=data["shots"],
            estimated_duration=data["estimated_duration"],
            estimated_cost=data.get("estimated_cost"),
            queue_position=data.get("queue_position"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            result_url=data.get("result_url"),
            error_message=data.get("error_message"),
            tags=data.get("tags"),
            metadata=data.get("metadata")
        )
    
    def elapsed_time(self) -> Optional[float]:
        """
        Calculate the elapsed time for this job.
        
        Returns:
            Elapsed time in seconds, or None if job hasn't started
        """
        if not self.start_time:
            return None
            
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def wait_time(self) -> Optional[float]:
        """
        Calculate the time spent waiting in the queue.
        
        Returns:
            Wait time in seconds, or None if job hasn't started
        """
        if not self.start_time:
            return time.time() - self.creation_time
            
        return self.start_time - self.creation_time
    
    def is_active(self) -> bool:
        """
        Check if the job is still active.
        
        Returns:
            True if job is queued or running, False otherwise
        """
        return self.status in [JobStatus.QUEUED, JobStatus.RUNNING]
    
    def __str__(self) -> str:
        """String representation of the job."""
        status_str = self.status.upper()
        time_str = datetime.datetime.fromtimestamp(self.creation_time).strftime("%Y-%m-%d %H:%M:%S")
        
        return f"Job {self.job_id[:8]} ({self.name}) - {status_str} - {self.provider}/{self.backend} - Created: {time_str}"


class JobManager:
    """Manages quantum execution jobs."""
    
    def __init__(self, storage_path: Optional[str] = None, user_id: Optional[str] = None):
        """
        Initialize the job manager.
        
        Args:
            storage_path: Path to store job data
            user_id: Current user ID
        """
        self.user_id = user_id or os.environ.get("USER", "unknown")
        self.storage_path = storage_path or os.path.expanduser("~/.quantum-cli/jobs")
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Dictionary to cache job details
        self.job_cache = {}
        
        # Job monitoring thread
        self.monitor_thread = None
        self.stop_monitor = threading.Event()
        self.monitor_queue = queue.Queue()
    
    def _get_job_path(self, job_id: str) -> str:
        """
        Get the path to the job file.
        
        Args:
            job_id: Job ID
            
        Returns:
            Path to the job file
        """
        return os.path.join(self.storage_path, f"{job_id}.json")
    
    def _save_job(self, job: JobDetails) -> bool:
        """
        Save job details to a file.
        
        Args:
            job: Job details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            job_path = self._get_job_path(job.job_id)
            
            with open(job_path, 'w') as f:
                json.dump(job.to_dict(), f, indent=2)
                
            # Update cache
            self.job_cache[job.job_id] = job
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save job {job.job_id}: {e}")
            return False
    
    def _load_job(self, job_id: str) -> Optional[JobDetails]:
        """
        Load job details from a file.
        
        Args:
            job_id: Job ID
            
        Returns:
            JobDetails if found, None otherwise
        """
        # Check cache first
        if job_id in self.job_cache:
            return self.job_cache[job_id]
            
        try:
            job_path = self._get_job_path(job_id)
            
            if not os.path.exists(job_path):
                return None
                
            with open(job_path, 'r') as f:
                job_data = json.load(f)
                
            job = JobDetails.from_dict(job_data)
            
            # Update cache
            self.job_cache[job_id] = job
            
            return job
            
        except Exception as e:
            logger.error(f"Failed to load job {job_id}: {e}")
            return None
    
    def _update_job_status(self, job_id: str, status: str, 
                          result_url: Optional[str] = None,
                          error_message: Optional[str] = None) -> bool:
        """
        Update the status of a job.
        
        Args:
            job_id: Job ID
            status: New status
            result_url: URL to the job results
            error_message: Error message if job failed
            
        Returns:
            True if successful, False otherwise
        """
        job = self._load_job(job_id)
        
        if not job:
            return False
            
        # Update status and timestamps
        job.status = status
        
        if status == JobStatus.RUNNING and not job.start_time:
            job.start_time = time.time()
            
        if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.end_time = time.time()
            
        if result_url:
            job.result_url = result_url
            
        if error_message:
            job.error_message = error_message
            
        # Save updated job
        return self._save_job(job)
    
    def create_job(self, 
                  name: str,
                  provider: str,
                  backend: str,
                  circuit_id: str,
                  shots: int,
                  estimated_duration: float,
                  estimated_cost: Optional[float] = None,
                  tags: Optional[List[str]] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create a new job.
        
        Args:
            name: Job name
            provider: Quantum provider
            backend: Backend name
            circuit_id: ID of the circuit to execute
            shots: Number of shots
            estimated_duration: Estimated job duration in seconds
            estimated_cost: Estimated job cost
            tags: List of tags
            metadata: Additional metadata
            
        Returns:
            Job ID if successful, None otherwise
        """
        try:
            job_id = str(uuid.uuid4())
            creation_time = time.time()
            
            job = JobDetails(
                job_id=job_id,
                name=name,
                provider=provider,
                backend=backend,
                creation_time=creation_time,
                status=JobStatus.QUEUED,
                user_id=self.user_id,
                circuit_id=circuit_id,
                shots=shots,
                estimated_duration=estimated_duration,
                estimated_cost=estimated_cost,
                queue_position=1,  # Initial position
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Save job
            if self._save_job(job):
                logger.info(f"Created job {job_id} ({name}) on {provider}/{backend}")
                return job_id
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to create job: {e}")
            return None
    
    def get_job(self, job_id: str) -> Optional[JobDetails]:
        """
        Get details of a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            JobDetails if found, None otherwise
        """
        return self._load_job(job_id)
    
    def list_jobs(self, 
                 active_only: bool = False, 
                 provider: Optional[str] = None,
                 limit: int = 100,
                 sort_by: str = "creation_time",
                 sort_order: str = "desc") -> List[JobDetails]:
        """
        List jobs.
        
        Args:
            active_only: Only list active jobs
            provider: Filter by provider
            limit: Maximum number of jobs to return
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            List of JobDetails
        """
        try:
            # Get all job files
            job_files = [f for f in os.listdir(self.storage_path) if f.endswith('.json')]
            jobs = []
            
            # Load each job
            for job_file in job_files:
                job_id = job_file.replace('.json', '')
                job = self._load_job(job_id)
                
                if job and job.user_id == self.user_id:
                    # Apply filters
                    if active_only and not job.is_active():
                        continue
                        
                    if provider and job.provider != provider:
                        continue
                        
                    jobs.append(job)
                    
                    # Stop if limit reached
                    if len(jobs) >= limit:
                        break
            
            # Sort jobs
            reverse = sort_order.lower() == "desc"
            jobs.sort(key=lambda j: getattr(j, sort_by), reverse=reverse)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return []
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            job = self._load_job(job_id)
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return False
                
            if not job.is_active():
                logger.warning(f"Job {job_id} is not active (status: {job.status})")
                return False
                
            # In a real implementation, this would send a cancellation request to the provider
            # For simulation, we'll just update the status
            
            return self._update_job_status(
                job_id=job_id,
                status=JobStatus.CANCELLED,
                error_message="Job cancelled by user"
            )
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get results of a completed job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job results if available, None otherwise
        """
        try:
            job = self._load_job(job_id)
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return None
                
            if job.status != JobStatus.COMPLETED:
                logger.warning(f"Job {job_id} is not completed (status: {job.status})")
                return None
                
            # In a real implementation, this would fetch results from the provider's API
            # For simulation, we'll generate sample results
            
            # Sample job results
            results = {
                "job_id": job.job_id,
                "backend": job.backend,
                "execution_time": job.elapsed_time(),
                "shots": job.shots,
                "measurement_counts": self._generate_sample_counts(job),
                "metadata": {
                    "execution_date": datetime.datetime.fromtimestamp(job.end_time).isoformat() if job.end_time else None,
                    "provider": job.provider,
                    "backend_version": "1.0.0",
                    "qiskit_version": "0.35.0"
                }
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get job results {job_id}: {e}")
            return None
    
    def _generate_sample_counts(self, job: JobDetails) -> Dict[str, int]:
        """
        Generate sample measurement counts.
        
        Args:
            job: Job details
            
        Returns:
            Dictionary mapping bitstrings to counts
        """
        # Simple simulation for demo purposes
        # In a real implementation, this would be actual results
        import random
        from collections import defaultdict
        
        # Generate sample counts based on job ID as seed
        random.seed(hash(job.job_id))
        
        # Estimate number of qubits based on circuit metadata
        num_qubits = job.metadata.get("num_qubits", 5)
        
        # Generate random distribution
        counts = defaultdict(int)
        for _ in range(job.shots):
            # Generate random bitstring
            bits = ''.join('1' if random.random() > 0.5 else '0' for _ in range(num_qubits))
            counts[bits] += 1
            
        # Return as regular dict
        return dict(counts)
    
    def start_monitoring(self, job_ids: List[str], interval: int = 5) -> bool:
        """
        Start monitoring jobs in a background thread.
        
        Args:
            job_ids: List of job IDs to monitor
            interval: Polling interval in seconds
            
        Returns:
            True if monitoring started, False otherwise
        """
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.warning("Job monitoring is already running")
            
            # Add jobs to the existing monitoring queue
            for job_id in job_ids:
                self.monitor_queue.put(job_id)
                
            return True
            
        # Reset the stop event
        self.stop_monitor.clear()
        
        # Start a new monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._job_monitor_thread,
            args=(job_ids, interval),
            daemon=True
        )
        self.monitor_thread.start()
        
        return True
    
    def stop_monitoring(self) -> bool:
        """
        Stop the job monitoring thread.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.monitor_thread or not self.monitor_thread.is_alive():
            logger.warning("No active job monitoring thread")
            return False
            
        # Signal the thread to stop
        self.stop_monitor.set()
        
        # Wait for the thread to finish
        self.monitor_thread.join(timeout=2.0)
        
        # Clear the thread reference
        self.monitor_thread = None
        
        logger.info("Job monitoring stopped")
        return True
    
    def _job_monitor_thread(self, job_ids: List[str], interval: int) -> None:
        """
        Background thread for monitoring jobs.
        
        Args:
            job_ids: List of job IDs to monitor
            interval: Polling interval in seconds
        """
        # Add initial jobs to monitor
        monitoring_jobs = set(job_ids)
        
        logger.info(f"Started monitoring {len(monitoring_jobs)} jobs")
        
        while not self.stop_monitor.is_set():
            # Check for new jobs to monitor
            while not self.monitor_queue.empty():
                try:
                    job_id = self.monitor_queue.get_nowait()
                    monitoring_jobs.add(job_id)
                except queue.Empty:
                    break
            
            # Remove completed jobs from the set
            jobs_to_remove = set()
            
            # Check each job
            for job_id in monitoring_jobs:
                job = self._load_job(job_id)
                
                if not job:
                    logger.warning(f"Job {job_id} not found, removing from monitoring")
                    jobs_to_remove.add(job_id)
                    continue
                    
                if not job.is_active():
                    logger.info(f"Job {job_id} is no longer active (status: {job.status}), removing from monitoring")
                    jobs_to_remove.add(job_id)
                    continue
                    
                # For demo purposes, we'll simulate status updates
                # In a real implementation, this would poll the provider's API
                self._simulate_job_progress(job)
            
            # Remove completed jobs
            monitoring_jobs -= jobs_to_remove
            
            # If no more jobs to monitor, exit the thread
            if not monitoring_jobs:
                logger.info("No more jobs to monitor, stopping thread")
                break
                
            # Wait for the next polling interval, or until we're signaled to stop
            self.stop_monitor.wait(interval)
            
        logger.info("Job monitoring thread exiting")
    
    def _simulate_job_progress(self, job: JobDetails) -> None:
        """
        Simulate job progress for demo purposes.
        
        Args:
            job: Job details
        """
        # Simple state machine to simulate job progression
        # In a real implementation, this would poll the provider's API
        
        if job.status == JobStatus.QUEUED:
            # Simulate queue progression
            if job.queue_position is None:
                job.queue_position = 5
            elif job.queue_position > 1:
                job.queue_position -= 1
            else:
                # Job at the front of queue, start running
                self._update_job_status(job.job_id, JobStatus.RUNNING)
                return
                
            # Update job with new queue position
            self._save_job(job)
            
        elif job.status == JobStatus.RUNNING:
            # Simulate job completion
            elapsed = job.elapsed_time()
            
            if elapsed and elapsed >= job.estimated_duration:
                # Job finished
                import random
                if random.random() < 0.9:  # 90% success rate
                    self._update_job_status(job.job_id, JobStatus.COMPLETED, result_url="https://example.com/results")
                else:
                    self._update_job_status(job.job_id, JobStatus.FAILED, error_message="Simulated random failure")


# Convenience functions for command-line use

def list_jobs(active_only: bool = False, 
             provider: Optional[str] = None, 
             limit: int = 20, 
             storage_path: Optional[str] = None,
             user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List quantum execution jobs."""
    manager = JobManager(storage_path, user_id)
    jobs = manager.list_jobs(active_only, provider, limit)
    return [job.to_dict() for job in jobs]

def get_job_details(job_id: str, 
                   storage_path: Optional[str] = None,
                   user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get details of a specific job."""
    manager = JobManager(storage_path, user_id)
    job = manager.get_job(job_id)
    return job.to_dict() if job else None

def get_job_results(job_id: str, 
                   storage_path: Optional[str] = None,
                   user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get results of a completed job."""
    manager = JobManager(storage_path, user_id)
    return manager.get_job_results(job_id)

def cancel_job(job_id: str, 
              storage_path: Optional[str] = None,
              user_id: Optional[str] = None) -> bool:
    """Cancel a running job."""
    manager = JobManager(storage_path, user_id)
    return manager.cancel_job(job_id)

def monitor_jobs(job_ids: List[str], 
                interval: int = 5,
                storage_path: Optional[str] = None,
                user_id: Optional[str] = None) -> bool:
    """Monitor jobs until they complete."""
    manager = JobManager(storage_path, user_id)
    manager.start_monitoring(job_ids, interval)
    
    try:
        # Keep the main thread running until all jobs complete
        while manager.monitor_thread and manager.monitor_thread.is_alive():
            time.sleep(1)
            
        return True
        
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
        manager.stop_monitoring()
        return False

def print_job_status(job: Dict[str, Any]) -> None:
    """
    Print a human-readable job status.
    
    Args:
        job: Job details dictionary
    """
    status = job["status"].upper()
    creation_time = datetime.datetime.fromtimestamp(job["creation_time"]).strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate times
    if job.get("start_time"):
        start_time = datetime.datetime.fromtimestamp(job["start_time"]).strftime("%Y-%m-%d %H:%M:%S")
        
        if job.get("end_time"):
            end_time = datetime.datetime.fromtimestamp(job["end_time"]).strftime("%Y-%m-%d %H:%M:%S")
            elapsed = job["end_time"] - job["start_time"]
            elapsed_str = f"{elapsed:.1f} seconds"
        else:
            end_time = "N/A"
            elapsed = time.time() - job["start_time"]
            elapsed_str = f"{elapsed:.1f} seconds (running)"
            
        wait_time = job["start_time"] - job["creation_time"]
        wait_str = f"{wait_time:.1f} seconds"
    else:
        start_time = "N/A"
        end_time = "N/A"
        elapsed_str = "N/A"
        
        if job["status"] == JobStatus.QUEUED:
            wait_time = time.time() - job["creation_time"]
            wait_str = f"{wait_time:.1f} seconds (in queue)"
        else:
            wait_str = "N/A"
    
    print(f"\nJob ID: {job['job_id']}")
    print(f"Name: {job['name']}")
    print(f"Status: {status}")
    print(f"Provider: {job['provider']}")
    print(f"Backend: {job['backend']}")
    print(f"Created: {creation_time}")
    print(f"Started: {start_time}")
    print(f"Completed: {end_time}")
    print(f"Wait Time: {wait_str}")
    print(f"Execution Time: {elapsed_str}")
    print(f"Shots: {job['shots']}")
    
    if job["status"] == JobStatus.QUEUED and job.get("queue_position"):
        print(f"Queue Position: {job['queue_position']}")
        
    if job["status"] == JobStatus.FAILED and job.get("error_message"):
        print(f"Error: {job['error_message']}")
        
    if job.get("estimated_cost"):
        print(f"Estimated Cost: ${job['estimated_cost']:.4f}")
        
    if job.get("tags"):
        print(f"Tags: {', '.join(job['tags'])}")
        
    if job.get("result_url"):
        print(f"Results: {job['result_url']}") 