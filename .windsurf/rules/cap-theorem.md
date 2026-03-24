---
description: CAP theorem compliance validation for Tax AI Agent distributed system design and data consistency patterns
trigger: always_on
---

# CAP Theorem Rules

Enforcement rules for CAP theorem compliance in Tax AI Agent project, ensuring proper handling of consistency, availability, and partition tolerance in distributed system design.

## CAP Theorem Overview

This rule set enforces understanding and proper implementation of:
- **Consistency (C)** - Data consistency across distributed nodes
- **Availability (A)** - System availability despite failures
- **Partition Tolerance (P)** - System resilience to network partitions
- **Trade-off decisions** - Appropriate CAP choices for different scenarios

## Consistency Rules

### Data Consistency Patterns

#### ✅ Strong Consistency Implementation
```python
# services/document_consistency_service.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json

@dataclass
class DocumentVersion:
    """Document version with consistency metadata."""
    document_id: str
    version: int
    content: str
    timestamp: datetime
    checksum: str
    node_id: str

class DocumentConsistencyService:
    """Service ensuring document data consistency across nodes."""
    
    def __init__(self, node_id: str, replication_factor: int = 3):
        self.node_id = node_id
        self.replication_factor = replication_factor
        self.local_storage = {}
        self.version_vector = {}
        self.lock_manager = DistributedLockManager()
    
    async def create_document(self, document_id: str, content: str) -> DocumentVersion:
        """Create document with strong consistency guarantees."""
        
        # Acquire distributed lock for write operation
        async with self.lock_manager.acquire_lock(f"write_{document_id}"):
            # Generate version with vector clock
            version = self._generate_version(document_id)
            
            # Create document with checksum
            checksum = self._calculate_checksum(content)
            doc_version = DocumentVersion(
                document_id=document_id,
                version=version,
                content=content,
                timestamp=datetime.utcnow(),
                checksum=checksum,
                node_id=self.node_id
            )
            
            # Write to local storage
            self.local_storage[document_id] = doc_version
            
            # Synchronously replicate to all nodes
            await self._replicate_to_all_nodes(doc_version)
            
            # Verify replication success
            await self._verify_replication(document_id, version)
            
            return doc_version
    
    async def read_document(self, document_id: str) -> Optional[DocumentVersion]:
        """Read document with consistency guarantees."""
        
        # Check local version
        local_version = self.local_storage.get(document_id)
        
        if not local_version:
            # Fetch from other nodes with quorum read
            return await self._quorum_read(document_id)
        
        # Verify version is up-to-date
        latest_version = await self._get_latest_version(document_id)
        
        if latest_version.version > local_version.version:
            # Update local version
            self.local_storage[document_id] = latest_version
            return latest_version
        
        return local_version
    
    async def update_document(self, document_id: str, content: str) -> DocumentVersion:
        """Update document with strong consistency."""
        
        async with self.lock_manager.acquire_lock(f"write_{document_id}"):
            # Read current version
            current = await self.read_document(document_id)
            if not current:
                raise DocumentNotFoundError(document_id)
            
            # Create new version
            new_version = DocumentVersion(
                document_id=document_id,
                version=current.version + 1,
                content=content,
                timestamp=datetime.utcnow(),
                checksum=self._calculate_checksum(content),
                node_id=self.node_id
            )
            
            # Update local storage
            self.local_storage[document_id] = new_version
            
            # Replicate to all nodes
            await self._replicate_to_all_nodes(new_version)
            
            # Verify replication
            await self._verify_replication(document_id, new_version.version)
            
            return new_version
    
    async def _replicate_to_all_nodes(self, doc_version: DocumentVersion) -> None:
        """Replicate document to all nodes synchronously."""
        
        replication_tasks = []
        for node_id in self._get_peer_nodes():
            task = self._replicate_to_node(node_id, doc_version)
            replication_tasks.append(task)
        
        # Wait for all replications to complete
        results = await asyncio.gather(*replication_tasks, return_exceptions=True)
        
        # Check for replication failures
        failures = [r for r in results if isinstance(r, Exception)]
        if failures:
            raise ReplicationError(f"Failed to replicate to {len(failures)} nodes")
    
    async def _quorum_read(self, document_id: str) -> Optional[DocumentVersion]:
        """Read from quorum of nodes for consistency."""
        
        quorum_size = (self.replication_factor // 2) + 1
        read_tasks = []
        
        for node_id in self._get_peer_nodes(include_self=True):
            task = self._read_from_node(node_id, document_id)
            read_tasks.append(task)
        
        results = await asyncio.gather(*read_tasks, return_exceptions=True)
        
        # Filter successful reads
        successful_reads = [r for r in results if not isinstance(r, Exception) and r is not None]
        
        if len(successful_reads) < quorum_size:
            raise QuorumError(f"Insufficient nodes for quorum read: {len(successful_reads)}/{quorum_size}")
        
        # Return latest version
        return max(successful_reads, key=lambda x: x.version)
    
    def _calculate_checksum(self, content: str) -> str:
        """Calculate checksum for content integrity."""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _generate_version(self, document_id: str) -> int:
        """Generate next version number."""
        current = self.version_vector.get(document_id, 0)
        self.version_vector[document_id] = current + 1
        return current + 1
```

#### ❌ Consistency Violations
```python
# Bad: Eventual consistency without proper handling
class InconsistentDocumentService:
    """Service with consistency issues."""
    
    def __init__(self):
        self.storage = {}
        self.cache = {}
    
    def create_document(self, document_id: str, content: str):
        """Create document without consistency guarantees."""
        # Direct write without replication
        self.storage[document_id] = {
            'content': content,
            'timestamp': time.time()
        }
        
        # Async replication without verification
        asyncio.create_task(self._replicate_async(document_id))
        
        # Return immediately - may not be consistent
        return {'status': 'created'}
    
    def read_document(self, document_id: str):
        """Read without consistency checks."""
        # Read from cache without validation
        if document_id in self.cache:
            return self.cache[document_id]
        
        # Read from storage without version check
        return self.storage.get(document_id)
    
    def update_document(self, document_id: str, content: str):
        """Update without proper locking."""
        # No lock - race conditions possible
        self.storage[document_id]['content'] = content
        self.storage[document_id]['timestamp'] = time.time()
        
        # Cache invalidation not atomic
        if document_id in self.cache:
            del self.cache[document_id]
```

### Consistency Validation Rules

#### Transaction Management
```python
# ✅ Proper transaction handling
class DocumentTransactionService:
    """Service with proper transaction management."""
    
    def __init__(self):
        self.transaction_manager = DistributedTransactionManager()
    
    async def process_documents_batch(self, document_ids: List[str]) -> Dict[str, Any]:
        """Process batch with transaction guarantees."""
        
        # Start distributed transaction
        transaction = await self.transaction_manager.begin_transaction()
        
        try:
            results = {}
            
            for document_id in document_ids:
                # Process within transaction
                result = await self._process_document_in_transaction(
                    document_id, transaction
                )
                results[document_id] = result
            
            # Commit transaction (two-phase commit)
            await self.transaction_manager.commit_transaction(transaction)
            
            return {
                'status': 'success',
                'results': results,
                'transaction_id': transaction.id
            }
        
        except Exception as e:
            # Rollback on any failure
            await self.transaction_manager.rollback_transaction(transaction)
            raise TransactionError(f"Batch processing failed: {e}")
    
    async def _process_document_in_transaction(self, document_id: str, transaction) -> Dict[str, Any]:
        """Process single document within transaction."""
        
        # Lock document within transaction
        await transaction.lock_resource(document_id)
        
        # Read consistent state
        document = await self._read_consistent(document_id, transaction)
        
        # Process document
        result = await self._process_document_logic(document)
        
        # Write changes to transaction log
        await transaction.log_operation(document_id, 'update', result)
        
        return result
```

## Availability Rules

### High Availability Implementation

#### ✅ Availability Patterns
```python
# services/high_availability_service.py
from typing import List, Dict, Optional
import asyncio
import random
from dataclasses import dataclass

@dataclass
class NodeHealth:
    """Node health status."""
    node_id: str
    is_healthy: bool
    last_check: datetime
    response_time: float
    error_count: int

class HighAvailabilityService:
    """Service implementing high availability patterns."""
    
    def __init__(self, node_id: str, peer_nodes: List[str]):
        self.node_id = node_id
        self.peer_nodes = peer_nodes
        self.health_checker = HealthChecker()
        self.load_balancer = LoadBalancer()
        self.circuit_breaker = CircuitBreaker()
    
    async def process_request(self, request: DocumentProcessingRequest) -> Dict[str, Any]:
        """Process request with high availability guarantees."""
        
        # Try local processing first
        try:
            if await self._is_local_healthy():
                return await self._process_locally(request)
        except Exception as e:
            print(f"Local processing failed: {e}")
        
        # Try peer nodes with circuit breaker
        available_nodes = await self._get_healthy_nodes()
        
        for node_id in available_nodes:
            try:
                # Use circuit breaker to prevent cascading failures
                if self.circuit_breaker.is_closed(node_id):
                    result = await self._process_on_node(node_id, request)
                    self.circuit_breaker.record_success(node_id)
                    return result
                else:
                    print(f"Circuit breaker open for node {node_id}")
            except Exception as e:
                print(f"Processing on node {node_id} failed: {e}")
                self.circuit_breaker.record_failure(node_id)
        
        # All nodes failed - return degraded service
        return await self._handle_degraded_service(request)
    
    async def _process_locally(self, request: DocumentProcessingRequest) -> Dict[str, Any]:
        """Process request locally with timeout."""
        
        try:
            # Set timeout to prevent hanging
            result = await asyncio.wait_for(
                self._do_process_request(request),
                timeout=30.0  # 30 second timeout
            )
            return result
        
        except asyncio.TimeoutError:
            raise ServiceTimeoutError("Local processing timeout")
    
    async def _get_healthy_nodes(self) -> List[str]:
        """Get list of healthy peer nodes."""
        
        healthy_nodes = []
        
        for node_id in self.peer_nodes:
            health = await self.health_checker.check_node_health(node_id)
            if health.is_healthy:
                healthy_nodes.append(node_id)
        
        return healthy_nodes
    
    async def _handle_degraded_service(self, request: DocumentProcessingRequest) -> Dict[str, Any]:
        """Handle service degradation gracefully."""
        
        # Queue request for later processing
        queue_id = await self._queue_request(request)
        
        return {
            'status': 'degraded',
            'message': 'Service temporarily unavailable, request queued',
            'queue_id': queue_id,
            'retry_after': 30
        }

class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.circuit_states = {}  # node_id -> CircuitState
    
    def is_closed(self, node_id: str) -> bool:
        """Check if circuit is closed for node."""
        
        state = self.circuit_states.get(node_id)
        if not state:
            return True  # New node, assume closed
        
        if state.is_open:
            # Check if recovery timeout has passed
            if (datetime.utcnow() - state.opened_at).total_seconds() > self.recovery_timeout:
                state.is_open = False
                state.failure_count = 0
                return True
            return False
        
        return True
    
    def record_success(self, node_id: str):
        """Record successful operation."""
        
        state = self.circuit_states.setdefault(node_id, CircuitState())
        state.failure_count = 0
        state.is_open = False
    
    def record_failure(self, node_id: str):
        """Record failed operation."""
        
        state = self.circuit_states.setdefault(node_id, CircuitState())
        state.failure_count += 1
        
        if state.failure_count >= self.failure_threshold:
            state.is_open = True
            state.opened_at = datetime.utcnow()

@dataclass
class CircuitState:
    """Circuit breaker state."""
    failure_count: int = 0
    is_open: bool = False
    opened_at: Optional[datetime] = None
```

#### ❌ Availability Violations
```python
# Bad: Single point of failure
class SinglePointOfFailureService:
    """Service with availability issues."""
    
    def __init__(self):
        self.database = SingleDatabaseConnection()  # Single point of failure
        self.processor = DocumentProcessor()        # Single instance
    
    def process_document(self, document_id: str):
        """Process with no availability guarantees."""
        # No timeout - can hang indefinitely
        result = self.database.get_document(document_id)
        
        # No error handling for database failures
        processed = self.processor.process(result)
        
        # No fallback or retry logic
        return processed
    
    def health_check(self):
        """Health check that can fail."""
        # Single point of failure in health check
        return self.database.is_healthy()  # Can hang or fail
```

### Availability Validation Rules

#### Redundancy and Failover
```python
# ✅ Proper redundancy implementation
class RedundantServiceManager:
    """Manager for redundant service instances."""
    
    def __init__(self, primary_nodes: List[str], backup_nodes: List[str]):
        self.primary_nodes = primary_nodes
        self.backup_nodes = backup_nodes
        self.failover_manager = FailoverManager()
        self.health_monitor = HealthMonitor()
    
    async def process_with_failover(self, request: DocumentProcessingRequest) -> Dict[str, Any]:
        """Process with automatic failover."""
        
        # Try primary nodes
        for node_id in self.primary_nodes:
            try:
                if await self.health_monitor.is_healthy(node_id):
                    result = await self._process_on_node(node_id, request)
                    return result
            except Exception as e:
                print(f"Primary node {node_id} failed: {e}")
                continue
        
        # Failover to backup nodes
        print("Primary nodes failed, initiating failover")
        await self.failover_manager.initiate_failover()
        
        for node_id in self.backup_nodes:
            try:
                if await self.health_monitor.is_healthy(node_id):
                    result = await self._process_on_node(node_id, request)
                    return result
            except Exception as e:
                print(f"Backup node {node_id} failed: {e}")
                continue
        
        # All nodes failed
        raise ServiceUnavailableError("All nodes unavailable")
```

## Partition Tolerance Rules

### Network Partition Handling

#### ✅ Partition Tolerance Implementation
```python
# services/partition_tolerance_service.py
from typing import Set, Dict, List
import asyncio
from datetime import datetime, timedelta

class PartitionToleranceService:
    """Service handling network partitions gracefully."""
    
    def __init__(self, node_id: str, all_nodes: List[str]):
        self.node_id = node_id
        self.all_nodes = all_nodes
        self.partition_detector = PartitionDetector()
        self.quorum_manager = QuorumManager()
        self.operation_queue = OperationQueue()
    
    async def handle_partitioned_operation(self, operation: DocumentOperation) -> Dict[str, Any]:
        """Handle operation during network partition."""
        
        # Detect current partition state
        partition_state = await self.partition_detector.detect_partition()
        
        if partition_state.is_partitioned:
            return await self._handle_partitioned_operation(operation, partition_state)
        else:
            return await self._handle_normal_operation(operation)
    
    async def _handle_partitioned_operation(self, operation: DocumentOperation, 
                                          partition_state: PartitionState) -> Dict[str, Any]:
        """Handle operation when partition is detected."""
        
        # Check if we're in majority partition
        if partition_state.in_majority_partition:
            # Continue operations with quorum
            return await self._handle_with_quorum(operation, partition_state)
        else:
            # We're in minority partition - handle gracefully
            return await self._handle_minority_partition(operation, partition_state)
    
    async def _handle_with_quorum(self, operation: DocumentOperation, 
                                partition_state: PartitionState) -> Dict[str, Any]:
        """Handle operation with quorum in majority partition."""
        
        reachable_nodes = partition_state.reachable_nodes
        
        # Check if we have quorum
        quorum_size = (len(self.all_nodes) // 2) + 1
        if len(reachable_nodes) >= quorum_size:
            # Can proceed with operation
            try:
                result = await self._execute_with_quorum(operation, reachable_nodes)
                return result
            except QuorumError as e:
                # Quorum lost during operation
                return await self._queue_for_later(operation)
        else:
            # Not enough nodes for quorum
            return await self._queue_for_later(operation)
    
    async def _handle_minority_partition(self, operation: DocumentOperation,
                                       partition_state: PartitionState) -> Dict[str, Any]:
        """Handle operation in minority partition."""
        
        # In minority partition, we can only serve read-only operations
        if operation.is_read_only:
            try:
                # Serve from local cache if available
                result = await self._serve_from_cache(operation)
                return result
            except CacheMissError:
                return {
                    'status': 'unavailable',
                    'message': 'Service unavailable due to network partition',
                    'retry_after': 30
                }
        else:
            # Write operations must be queued
            queue_id = await self.operation_queue.enqueue(operation)
            return {
                'status': 'queued',
                'message': 'Operation queued due to network partition',
                'queue_id': queue_id,
                'retry_after': 60
            }
    
    async def _execute_with_quorum(self, operation: DocumentOperation, 
                                reachable_nodes: List[str]) -> Dict[str, Any]:
        """Execute operation with quorum consensus."""
        
        quorum_size = (len(self.all_nodes) // 2) + 1
        
        if operation.is_read:
            # Read operation - need read quorum
            return await self._read_quorum(operation, reachable_nodes, quorum_size)
        else:
            # Write operation - need write quorum
            return await self._write_quorum(operation, reachable_nodes, quorum_size)
    
    async def _read_quorum(self, operation: DocumentOperation, 
                         reachable_nodes: List[str], quorum_size: int) -> Dict[str, Any]:
        """Execute read with quorum."""
        
        # Collect responses from reachable nodes
        read_tasks = []
        for node_id in reachable_nodes:
            task = self._read_from_node(node_id, operation)
            read_tasks.append(task)
        
        responses = await asyncio.gather(*read_tasks, return_exceptions=True)
        
        # Filter successful responses
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        
        if len(successful_responses) < quorum_size:
            raise QuorumError(f"Insufficient responses for read quorum: {len(successful_responses)}/{quorum_size}")
        
        # Resolve conflicts and return latest version
        return self._resolve_read_conflicts(successful_responses)
    
    async def _write_quorum(self, operation: DocumentOperation, 
                          reachable_nodes: List[str], quorum_size: int) -> Dict[str, Any]:
        """Execute write with quorum."""
        
        # Prepare write operation
        write_data = self._prepare_write_data(operation)
        
        # Write to reachable nodes
        write_tasks = []
        for node_id in reachable_nodes:
            task = self._write_to_node(node_id, write_data)
            write_tasks.append(task)
        
        results = await asyncio.gather(*write_tasks, return_exceptions=True)
        
        # Count successful writes
        successful_writes = [r for r in results if not isinstance(r, Exception)]
        
        if len(successful_writes) < quorum_size:
            # Rollback successful writes
            await self._rollback_writes(successful_writes, write_data)
            raise QuorumError(f"Insufficient nodes for write quorum: {len(successful_writes)}/{quorum_size}")
        
        return {
            'status': 'success',
            'operation_id': operation.id,
            'nodes_written': len(successful_writes)
        }

class PartitionDetector:
    """Detects network partitions."""
    
    def __init__(self):
        self.gossip_protocol = GossipProtocol()
        self.heartbeat_tracker = HeartbeatTracker()
    
    async def detect_partition(self) -> PartitionState:
        """Detect current partition state."""
        
        # Check heartbeat status of all nodes
        node_status = await self.heartbeat_tracker.get_all_node_status()
        
        reachable_nodes = [node_id for node_id, status in node_status.items() 
                          if status.is_reachable]
        
        unreachable_nodes = [node_id for node_id, status in node_status.items() 
                           if not status.is_reachable]
        
        # Determine if we're in majority partition
        total_nodes = len(node_status)
        in_majority = len(reachable_nodes) > (total_nodes // 2)
        
        return PartitionState(
            is_partitioned=len(unreachable_nodes) > 0,
            reachable_nodes=reachable_nodes,
            unreachable_nodes=unreachable_nodes,
            in_majority_partition=in_majority,
            detected_at=datetime.utcnow()
        )

@dataclass
class PartitionState:
    """Current partition state."""
    is_partitioned: bool
    reachable_nodes: List[str]
    unreachable_nodes: List[str]
    in_majority_partition: bool
    detected_at: datetime
```

#### ❌ Partition Tolerance Violations
```python
# Bad: No partition handling
class PartitionUnawareService:
    """Service that doesn't handle partitions."""
    
    def __init__(self):
        self.peers = ['node1', 'node2', 'node3']
    
    async def write_document(self, document_id: str, content: str):
        """Write without partition awareness."""
        
        # Try to write to all peers without checking connectivity
        for peer in self.peers:
            try:
                await self._write_to_peer(peer, document_id, content)
            except Exception as e:
                # Ignore failures - can lead to inconsistency
                print(f"Failed to write to {peer}: {e}")
                continue
        
        # Return success even if writes failed
        return {'status': 'success'}
    
    async def read_document(self, document_id: str):
        """Read without partition handling."""
        
        # Read from first peer without checking if it's reachable
        peer = self.peers[0]
        try:
            return await self._read_from_peer(peer, document_id)
        except Exception as e:
            # Fail completely if first peer is unreachable
            raise ServiceError(f"Cannot read document: {e}")
```

## CAP Trade-off Analysis

### Scenario-Based CAP Choices

#### ✅ Appropriate CAP Trade-offs
```python
# services/cap_strategy_service.py
from enum import Enum
from typing import Dict, Any

class CAPStrategy(Enum):
    """CAP strategy choices for different scenarios."""
    CP = "CP"  # Consistency and Partition Tolerance
    AP = "AP"  # Availability and Partition Tolerance
    CA = "CA"  # Consistency and Availability (no partitions)

class CAPStrategyService:
    """Service implementing appropriate CAP strategies."""
    
    def __init__(self):
        self.strategies = {
            'document_processing': CAPStrategy.CP,  # Need consistency
            'template_management': CAPStrategy.CA,  # Can sacrifice partition tolerance
            'user_sessions': CAPStrategy.AP,         # Need availability
            'analytics': CAPStrategy.AP              # Need availability
        }
    
    def get_strategy_for_operation(self, operation_type: str) -> CAPStrategy:
        """Get appropriate CAP strategy for operation type."""
        return self.strategies.get(operation_type, CAPStrategy.CP)
    
    async def execute_with_strategy(self, operation: Operation) -> Dict[str, Any]:
        """Execute operation with appropriate CAP strategy."""
        
        strategy = self.get_strategy_for_operation(operation.type)
        
        if strategy == CAPStrategy.CP:
            return await self._execute_cp(operation)
        elif strategy == CAPStrategy.AP:
            return await self._execute_ap(operation)
        elif strategy == CAPStrategy.CA:
            return await self._execute_ca(operation)
    
    async def _execute_cp(self, operation: Operation) -> Dict[str, Any]:
        """Execute with CP strategy - prioritize consistency."""
        
        try:
            # Check for partition
            partition_state = await self.partition_detector.detect_partition()
            
            if partition_state.is_partitioned and not partition_state.in_majority_partition:
                # In minority partition - cannot maintain consistency
                return {
                    'status': 'unavailable',
                    'message': 'Service unavailable to maintain consistency',
                    'strategy': 'CP'
                }
            
            # Execute with strong consistency
            return await self._execute_with_consistency(operation)
        
        except ConsistencyError as e:
            return {
                'status': 'error',
                'message': f'Consistency cannot be maintained: {e}',
                'strategy': 'CP'
            }
    
    async def _execute_ap(self, operation: Operation) -> Dict[str, Any]:
        """Execute with AP strategy - prioritize availability."""
        
        try:
            # Always try to serve the request
            if operation.is_read:
                # Serve from local cache if needed
                return await self._serve_with_availability(operation)
            else:
                # Queue writes if partitioned
                return await self._queue_with_availability(operation)
        
        except Exception as e:
            # Return degraded service rather than failing
            return {
                'status': 'degraded',
                'message': f'Degraded service due to: {e}',
                'strategy': 'AP'
            }
    
    async def _execute_ca(self, operation: Operation) -> Dict[str, Any]:
        """Execute with CA strategy - assume no partitions."""
        
        # This strategy works in controlled environments
        # where network partitions are extremely rare
        
        try:
            # Execute with both consistency and availability
            return await self._execute_optimal(operation)
        
        except Exception as e:
            # CA strategy fails when partition occurs
            return {
                'status': 'error',
                'message': f'CA strategy failed (possible partition): {e}',
                'strategy': 'CA'
            }
```

## Validation Rules

### Automated CAP Compliance Checking

#### CAP Compliance Analyzer
```bash
# Run CAP compliance analysis
python - << 'EOF'
import ast
import re
from pathlib import Path
from typing import Dict, List, Set

class CAPComplianceAnalyzer:
    """Analyze CAP theorem compliance in code."""
    
    def __init__(self):
        self.issues = []
        self.compliance_scores = {
            'consistency': 0,
            'availability': 0,
            'partition_tolerance': 0
        }
    
    def analyze_consistency_patterns(self, tree: ast.AST, file_path: str, content: str) -> None:
        """Analyze consistency patterns."""
        
        consistency_score = 0
        
        # Check for distributed locks
        if 'lock' in content.lower() and 'distributed' in content.lower():
            consistency_score += 20
        elif 'lock' in content.lower():
            consistency_score += 10
        
        # Check for version vectors
        if 'version' in content.lower() and 'vector' in content.lower():
            consistency_score += 20
        elif 'version' in content.lower():
            consistency_score += 10
        
        # Check for quorum reads/writes
        if 'quorum' in content.lower():
            consistency_score += 25
        
        # Check for replication
        if 'replicate' in content.lower() or 'replication' in content.lower():
            consistency_score += 15
        
        # Check for transactions
        if 'transaction' in content.lower():
            consistency_score += 10
        
        # Check for consistency violations
        violations = []
        
        # Direct writes without replication
        if re.search(r'storage\[.*\]\s*=', content):
            violations.append("Direct write without replication")
        
        # Reads without version checking
        if re.search(r'def.*read.*:\s*return.*storage\[', content):
            violations.append("Read without version checking")
        
        # No lock on write operations
        if 'def.*write' in content and 'lock' not in content.lower():
            violations.append("Write operation without locking")
        
        for violation in violations:
            self.issues.append({
                'file': file_path,
                'type': 'Consistency Violation',
                'issue': violation,
                'severity': 'HIGH'
                consistency_score -= 15
            })
        
        self.compliance_scores['consistency'] += max(0, consistency_score)
    
    def analyze_availability_patterns(self, tree: ast.AST, file_path: str, content: str) -> None:
        """Analyze availability patterns."""
        
        availability_score = 0
        
        # Check for circuit breakers
        if 'circuit' in content.lower() and 'breaker' in content.lower():
            availability_score += 25
        
        # Check for timeouts
        if 'timeout' in content.lower():
            availability_score += 15
        
        # Check for retries
        if 'retry' in content.lower():
            availability_score += 15
        
        # Check for failover
        if 'failover' in content.lower() or 'fallback' in content.lower():
            availability_score += 20
        
        # Check for health checks
        if 'health' in content.lower():
            availability_score += 15
        
        # Check for availability violations
        violations = []
        
        # No timeout on external calls
        if re.search(r'await.*\.(get|post|put|delete)\(', content) and 'timeout' not in content.lower():
            violations.append("External call without timeout")
        
        # No error handling
        if 'def.*async' in content and 'try:' not in content:
            violations.append("Async function without error handling")
        
        # Single point of failure
        if re.search(r'self\.\w+\s*=\s*\w+\(\)', content):
            violations.append("Single point of dependency")
        
        for violation in violations:
            self.issues.append({
                'file': file_path,
                'type': 'Availability Issue',
                'issue': violation,
                'severity': 'MEDIUM'
            })
            availability_score -= 10
        
        self.compliance_scores['availability'] += max(0, availability_score)
    
    def analyze_partition_tolerance_patterns(self, tree: ast.AST, file_path: str, content: str) -> None:
        """Analyze partition tolerance patterns."""
        
        partition_score = 0
        
        # Check for partition detection
        if 'partition' in content.lower():
            partition_score += 25
        
        # Check for gossip protocols
        if 'gossip' in content.lower():
            partition_score += 20
        
        # Check for quorum management
        if 'quorum' in content.lower():
            partition_score += 20
        
        # Check for eventual consistency
        if 'eventual' in content.lower() and 'consistency' in content.lower():
            partition_score += 15
        
        # Check for partition violations
        violations = []
        
        # Assume all nodes reachable
        if 'for node in nodes:' in content and 'partition' not in content.lower():
            violations.append("Assumes all nodes reachable")
        
        # No partition handling
        if 'def.*process' in content and 'partition' not in content.lower():
            violations.append("No partition handling in process function")
        
        for violation in violations:
            self.issues.append({
                'file': file_path,
                'type': 'Partition Tolerance Issue',
                'issue': violation,
                'severity': 'MEDIUM'
            })
            partition_score -= 10
        
        self.compliance_scores['partition_tolerance'] += max(0, partition_score)
    
    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            self.analyze_consistency_patterns(tree, str(file_path), content)
            self.analyze_availability_patterns(tree, str(file_path), content)
            self.analyze_partition_tolerance_patterns(tree, str(file_path), content)
        
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def generate_report(self) -> str:
        """Generate CAP compliance report."""
        
        total_files = len([f for f in Path('.').rglob('*.py') if 'venv' not in str(f)])
        
        # Normalize scores
        for key in self.compliance_scores:
            self.compliance_scores[key] = min(100, self.compliance_scores[key] / max(total_files, 1))
        
        report = "# CAP Theorem Compliance Report\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "## Compliance Scores\n\n"
        report += f"- **Consistency (C):** {self.compliance_scores['consistency']:.1f}%\n"
        report += f"- **Availability (A):** {self.compliance_scores['availability']:.1f}%\n"
        report += f"- **Partition Tolerance (P):** {self.compliance_scores['partition_tolerance']:.1f}%\n\n"
        
        # Overall assessment
        avg_score = sum(self.compliance_scores.values()) / 3
        report += f"**Overall CAP Compliance:** {avg_score:.1f}%\n\n"
        
        # Issues by type
        issues_by_type = {}
        for issue in self.issues:
            issue_type = issue['type']
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        report += "## Issues by Category\n\n"
        for issue_type, issues in issues_by_type.items():
            report += f"### {issue_type} ({len(issues)})\n\n"
            for issue in issues[:5]:  # Show first 5
                report += f"**File:** {issue['file']}\n"
                report += f"**Issue:** {issue['issue']}\n"
                report += f"**Severity:** {issue['severity']}\n\n"
        
        # Recommendations
        report += "## Recommendations\n\n"
        
        if self.compliance_scores['consistency'] < 70:
            report += "### Consistency Improvements\n"
            report += "1. Implement distributed locking for write operations\n"
            report += "2. Add version vectors for conflict resolution\n"
            report += "3. Use quorum reads/writes for critical data\n"
            report += "4. Implement proper transaction management\n\n"
        
        if self.compliance_scores['availability'] < 70:
            report += "### Availability Improvements\n"
            report += "1. Add circuit breakers for external services\n"
            report += "2. Implement proper timeout handling\n"
            report += "3. Add retry logic with exponential backoff\n"
            report += "4. Implement failover mechanisms\n\n"
        
        if self.compliance_scores['partition_tolerance'] < 70:
            report += "### Partition Tolerance Improvements\n"
            report += "1. Add partition detection mechanisms\n"
            report += "2. Implement quorum-based operations\n"
            report += "3. Add gossip protocols for node discovery\n"
            report += "4. Handle minority partitions gracefully\n\n"
        
        return report

# Run CAP compliance analysis
analyzer = CAPComplianceAnalyzer()

print("Analyzing CAP theorem compliance...")
for py_file in Path('.').rglob('*.py'):
    if 'venv' in str(py_file) or '.pytest_cache' in str(py_file):
        continue
    analyzer.analyze_file(py_file)

# Generate report
cap_report = analyzer.generate_report()
Path('reports/cap-compliance-report.md').write_text(cap_report)
print("CAP compliance report generated: reports/cap-compliance-report.md")

# Print summary
for category, score in analyzer.compliance_scores.items():
    print(f"{category.title()}: {score:.1f}%")

print(f"Total issues found: {len(analyzer.issues)}")
EOF
```

## Best Practices Summary

1. **Choose appropriate CAP strategy** based on use case requirements
2. **Implement proper consistency** for critical operations (CP strategy)
3. **Ensure high availability** for user-facing services (AP strategy)
4. **Handle partitions gracefully** with proper detection and recovery
5. **Use quorum-based operations** for distributed consensus
6. **Implement circuit breakers** to prevent cascading failures
7. **Add proper timeouts** and retry logic for resilience
8. **Monitor partition states** and handle minority partitions
9. **Design for eventual consistency** when appropriate
10. **Test partition scenarios** regularly in staging environment

## CAP Trade-off Decision Matrix

| Scenario | Priority | Recommended Strategy | Reasoning |
|----------|----------|---------------------|-----------|
| Financial transactions | Consistency | CP | Data accuracy is critical |
| User sessions | Availability | AP | User experience priority |
| Analytics data | Availability | AP | Approximate results acceptable |
| Configuration management | Consistency | CP | System stability depends on consistency |
| Caching layer | Availability | AP | Cache misses acceptable |
| Document processing | Availability | AP | Processing can be retried |

This comprehensive CAP theorem rule set ensures that the Tax AI Agent properly handles distributed system challenges with appropriate consistency, availability, and partition tolerance strategies.
