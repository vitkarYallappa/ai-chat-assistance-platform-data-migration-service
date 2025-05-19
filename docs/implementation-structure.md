# Data Migration Service - Structure & Architecture

## Repository Structure

```
data-migration-service/
│
├── README.md
├── pyproject.toml
├── setup.py
├── Dockerfile
├── .env.example
├── .gitignore
│
├── migrations/
│   ├── schema/
│   │   ├── mongodb/
│   │   └── postgres/
│   └── data/
│       ├── mongodb/
│       └── postgres/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   ├── security.py
│   │   └── metrics.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── endpoints/
│   │   ├── models/
│   │   └── dependencies.py
│   │
│   ├── coordinator/
│   │   ├── __init__.py
│   │   ├── planner.py
│   │   ├── orchestrator.py
│   │   ├── scheduler.py
│   │   ├── status_tracker.py
│   │   └── validation.py
│   │
│   ├── shard/
│   │   ├── __init__.py
│   │   ├── topology.py
│   │   ├── router.py
│   │   ├── consistency.py
│   │   └── balancer.py
│   │
│   ├── executors/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── mongodb.py
│   │   ├── postgres.py
│   │   ├── batch.py
│   │   └── parallel.py
│   │
│   ├── transformers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── message.py
│   │   ├── tenant.py
│   │   ├── channel.py
│   │   └── factory.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── postgres.py
│   │   └── mongodb.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── migration_service.py
│   │   ├── status_service.py
│   │   ├── backup_service.py
│   │   └── monitoring_service.py
│   │
│   ├── message_broker/
│   │   ├── __init__.py
│   │   ├── publisher.py
│   │   ├── consumer.py
│   │   ├── rabbitmq.py
│   │   └── kafka.py
│   │
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── mcp_client.py
│   │   ├── chat_client.py
│   │   └── adaptor_client.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── database.py
│       ├── retry.py
│       ├── validation.py
│       ├── async_utils.py
│       └── monitoring.py
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── tools/
│   ├── shard_simulator.py
│   ├── performance_analyzer.py
│   ├── migration_generator.py
│   └── status_dashboard/
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── migrations/
│   └── operations/
│
└── k8s/
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    └── secrets.yaml
```

## Key Component Implementation Details

### Core Components

#### 1. Shard Management (`app/shard/`)

The shard management system tracks and interacts with the database sharding topology.

**`topology.py`**
```python
class ShardTopology:
    """Manages the database shard topology."""
    
    def __init__(self, config):
        self.config = config
        self.shard_map = {}
        self._load_topology()
    
    async def _load_topology(self):
        """Load shard topology from configuration or discovery."""
        # Implementation details for loading shard topology
        
    async def get_shard_for_key(self, key, database_type):
        """Get the shard responsible for a given key."""
        # Implementation for routing a key to the appropriate shard
        
    async def get_all_shards(self, database_type):
        """Get all shards for a database type."""
        # Return all shards for MongoDB or PostgreSQL
        
    async def refresh_topology(self):
        """Refresh the shard topology (for dynamic sharding)."""
        # Implementation for refreshing topology
```

**`router.py`**
```python
class ShardRouter:
    """Routes operations to the appropriate shard."""
    
    def __init__(self, topology):
        self.topology = topology
    
    async def route_operation(self, operation, key=None, all_shards=False):
        """Route an operation to the appropriate shard(s)."""
        if all_shards:
            return await self._execute_on_all_shards(operation)
        else:
            shard = await self.topology.get_shard_for_key(key, operation.database_type)
            return await self._execute_on_shard(operation, shard)
    
    async def _execute_on_shard(self, operation, shard):
        """Execute an operation on a specific shard."""
        # Implementation for executing on a single shard
    
    async def _execute_on_all_shards(self, operation):
        """Execute an operation on all shards."""
        # Implementation for executing on all shards
```

#### 2. Migration Coordination (`app/coordinator/`)

The coordinator manages the execution of migrations across shards.

**`orchestrator.py`**
```python
class MigrationOrchestrator:
    """Orchestrates migrations across multiple shards."""
    
    def __init__(self, router, status_tracker, validator):
        self.router = router
        self.status_tracker = status_tracker
        self.validator = validator
        
    async def execute_migration_plan(self, plan):
        """Execute a migration plan across shards."""
        # Record migration start
        migration_id = await self.status_tracker.start_migration(plan)
        
        try:
            # 1. Schema migrations first (all shards)
            await self._execute_schema_migrations(plan)
            
            # 2. Data migrations
            await self._execute_data_migrations(plan)
            
            # 3. Validation
            validation_result = await self.validator.validate_migration(plan)
            if not validation_result.success:
                await self._handle_validation_failure(validation_result, plan)
                return False
                
            # Mark migration as complete
            await self.status_tracker.complete_migration(migration_id)
            return True
            
        except Exception as e:
            # Handle failure and rollback if necessary
            await self._handle_migration_failure(e, plan, migration_id)
            return False
            
    async def _execute_schema_migrations(self, plan):
        """Execute schema migrations across all relevant shards."""
        # Implementation for schema migrations
        
    async def _execute_data_migrations(self, plan):
        """Execute data migrations with proper sharding awareness."""
        # Implementation for data migrations
        
    async def _handle_validation_failure(self, validation_result, plan):
        """Handle validation failures."""
        # Implementation for validation failure handling
        
    async def _handle_migration_failure(self, exception, plan, migration_id):
        """Handle migration failures and initiate rollback if needed."""
        # Implementation for failure handling
```

**`planner.py`**
```python
class MigrationPlanner:
    """Creates optimized migration execution plans."""
    
    def __init__(self, topology):
        self.topology = topology
        
    async def create_plan(self, migration_requests):
        """Create a migration execution plan from requests."""
        plan = MigrationPlan()
        
        # 1. Group migrations by dependency
        groups = self._group_by_dependency(migration_requests)
        
        # 2. Order groups by dependency
        ordered_groups = self._order_groups(groups)
        
        # 3. Plan execution for each group
        for group in ordered_groups:
            await self._plan_group_execution(group, plan)
            
        return plan
        
    def _group_by_dependency(self, migration_requests):
        """Group migrations by their dependencies."""
        # Implementation for dependency grouping
        
    def _order_groups(self, groups):
        """Order groups by dependencies."""
        # Implementation for group ordering
        
    async def _plan_group_execution(self, group, plan):
        """Plan the execution of a group of migrations."""
        # Implementation for planning group execution
```

#### 3. Database Executors (`app/executors/`)

The executors handle the actual database operations.

**`mongodb.py`**
```python
class MongoDBExecutor(BaseExecutor):
    """Executes MongoDB migrations."""
    
    async def execute_schema_migration(self, migration, shard):
        """Execute a schema migration on a MongoDB shard."""
        # Connect to the shard
        client = await self._get_client(shard)
        
        try:
            # Execute the migration script
            migration_module = self._load_migration_module(migration)
            await migration_module.upgrade(client, self.context)
            
            # Record success
            await self.record_success(migration, shard)
            
        except Exception as e:
            # Record failure
            await self.record_failure(migration, shard, str(e))
            raise
            
    async def execute_data_migration(self, migration, shard, batch_size=1000):
        """Execute a data migration on a MongoDB shard."""
        # Implementation for data migration
        
    async def _get_client(self, shard):
        """Get a MongoDB client for the specified shard."""
        # Implementation for getting MongoDB client
        
    def _load_migration_module(self, migration):
        """Load the migration module."""
        # Implementation for loading migration module
```

**`postgres.py`**
```python
class PostgreSQLExecutor(BaseExecutor):
    """Executes PostgreSQL migrations."""
    
    async def execute_schema_migration(self, migration, shard):
        """Execute a schema migration on a PostgreSQL shard."""
        # Implementation for schema migration
        
    async def execute_data_migration(self, migration, shard, batch_size=1000):
        """Execute a data migration on a PostgreSQL shard."""
        # Implementation for data migration
        
    async def _get_connection(self, shard):
        """Get a PostgreSQL connection for the specified shard."""
        # Implementation for getting PostgreSQL connection
        
    def _load_migration_module(self, migration):
        """Load the migration module."""
        # Implementation for loading migration module
```

### Integration Components

#### 4. Service Clients (`app/clients/`)

The service clients integrate with other services in the architecture.

**`mcp_client.py`**
```python
class MCPClient:
    """Client for interacting with the MCP Service."""
    
    def __init__(self, config):
        self.base_url = config.mcp_service_url
        self.api_key = config.mcp_service_api_key
        self.http_client = httpx.AsyncClient()
        
    async def get_tenant_config(self, tenant_id):
        """Get tenant configuration from MCP Service."""
        url = f"{self.base_url}/api/tenants/{tenant_id}/config"
        response = await self.http_client.get(
            url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()
        return response.json()
        
    async def update_message_schema(self, tenant_id, schema_version):
        """Update message schema version for a tenant."""
        # Implementation for updating schema version
        
    async def notify_migration_complete(self, migration_id):
        """Notify MCP Service that a migration is complete."""
        # Implementation for notifying migration completion
```

#### 5. Message Broker Integration (`app/message_broker/`)

The message broker integration handles event-based migrations.

**`publisher.py`**
```python
class MigrationEventPublisher:
    """Publishes migration events to the message broker."""
    
    def __init__(self, broker_client):
        self.broker_client = broker_client
        
    async def publish_migration_started(self, migration_id, details):
        """Publish migration started event."""
        event = {
            "type": "migration.started",
            "migration_id": migration_id,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broker_client.publish("migrations", event)
        
    async def publish_migration_progress(self, migration_id, progress):
        """Publish migration progress event."""
        # Implementation for publishing progress event
        
    async def publish_migration_completed(self, migration_id, result):
        """Publish migration completed event."""
        # Implementation for publishing completion event
        
    async def publish_migration_failed(self, migration_id, error):
        """Publish migration failed event."""
        # Implementation for publishing failure event
```

**`consumer.py`**
```python
class MigrationEventConsumer:
    """Consumes migration events from the message broker."""
    
    def __init__(self, broker_client, migration_service):
        self.broker_client = broker_client
        self.migration_service = migration_service
        
    async def start_consuming(self):
        """Start consuming migration events."""
        await self.broker_client.subscribe("migrations", self._handle_event)
        
    async def _handle_event(self, event):
        """Handle a migration event."""
        event_type = event.get("type")
        
        if event_type == "migration.request":
            await self._handle_migration_request(event)
        elif event_type == "migration.cancel":
            await self._handle_migration_cancel(event)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            
    async def _handle_migration_request(self, event):
        """Handle a migration request event."""
        # Implementation for handling migration request
        
    async def _handle_migration_cancel(self, event):
        """Handle a migration cancel event."""
        # Implementation for handling migration cancel
```

### API Layer

#### 6. API Endpoints (`app/api/endpoints/`)

The API endpoints provide external control of migrations.

**`migrations.py`**
```python
router = APIRouter()

@router.post("/migrations", response_model=MigrationResponse)
async def create_migration(
    request: MigrationRequest,
    migration_service: MigrationService = Depends(get_migration_service)
):
    """Create a new migration."""
    migration_id = await migration_service.create_migration(request)
    return {"migration_id": migration_id, "status": "created"}

@router.get("/migrations/{migration_id}", response_model=MigrationStatusResponse)
async def get_migration_status(
    migration_id: str,
    status_service: StatusService = Depends(get_status_service)
):
    """Get migration status."""
    status = await status_service.get_migration_status(migration_id)
    return status

@router.post("/migrations/{migration_id}/start", response_model=MigrationResponse)
async def start_migration(
    migration_id: str,
    migration_service: MigrationService = Depends(get_migration_service)
):
    """Start a migration."""
    await migration_service.start_migration(migration_id)
    return {"migration_id": migration_id, "status": "running"}

@router.post("/migrations/{migration_id}/cancel", response_model=MigrationResponse)
async def cancel_migration(
    migration_id: str,
    migration_service: MigrationService = Depends(get_migration_service)
):
    """Cancel a migration."""
    await migration_service.cancel_migration(migration_id)
    return {"migration_id": migration_id, "status": "cancelled"}
```

### Database Tables and Collections

#### MongoDB Collections

The following MongoDB collections are managed by the Data Migration Service:

1. **`migration_state`**
   ```json
   {
     "_id": "migration_id",
     "name": "Migration Name",
     "type": "schema|data",
     "database": "mongodb|postgresql",
     "status": "pending|running|completed|failed",
     "start_time": ISODate("2025-05-20T12:00:00Z"),
     "end_time": ISODate("2025-05-20T12:05:30Z"),
     "affected_collections": ["messages", "deliveries"],
     "shard_status": [
       {
         "shard_id": "shard-001",
         "status": "completed",
         "items_processed": 15000
       },
       {
         "shard_id": "shard-002",
         "status": "completed",
         "items_processed": 12500
       }
     ],
     "error": null
   }
   ```

2. **`migration_events`**
   ```json
   {
     "_id": "event_id",
     "migration_id": "migration_id",
     "event_type": "started|progress|completed|failed",
     "timestamp": ISODate("2025-05-20T12:01:00Z"),
     "details": {
       "shard_id": "shard-001",
       "items_processed": 5000,
       "total_items": 15000,
       "error": null
     }
   }
   ```

3. **`migration_locks`**
   ```json
   {
     "_id": "lock_id",
     "resource": "collection_name|shard_id",
     "migration_id": "migration_id",
     "acquired_at": ISODate("2025-05-20T12:00:00Z"),
     "expires_at": ISODate("2025-05-20T12:30:00Z")
   }
   ```

#### PostgreSQL Tables

The following PostgreSQL tables are managed by the Data Migration Service:

1. **`migrations`**
   ```sql
   CREATE TABLE migrations (
     id VARCHAR(50) PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     version VARCHAR(50) NOT NULL,
     type VARCHAR(10) NOT NULL, -- 'schema' or 'data'
     database_type VARCHAR(20) NOT NULL, -- 'mongodb' or 'postgresql'
     status VARCHAR(20) NOT NULL, -- 'pending', 'running', 'completed', 'failed'
     created_at TIMESTAMP WITH TIME ZONE NOT NULL,
     started_at TIMESTAMP WITH TIME ZONE,
     completed_at TIMESTAMP WITH TIME ZONE,
     error TEXT,
     metadata JSONB
   );
   ```

2. **`migration_steps`**
   ```sql
   CREATE TABLE migration_steps (
     id VARCHAR(50) PRIMARY KEY,
     migration_id VARCHAR(50) REFERENCES migrations(id),
     step_number INT NOT NULL,
     description TEXT NOT NULL,
     status VARCHAR(20) NOT NULL, -- 'pending', 'running', 'completed', 'failed'
     started_at TIMESTAMP WITH TIME ZONE,
     completed_at TIMESTAMP WITH TIME ZONE,
     error TEXT
   );
   ```

3. **`shard_migrations`**
   ```sql
   CREATE TABLE shard_migrations (
     id VARCHAR(50) PRIMARY KEY,
     migration_id VARCHAR(50) REFERENCES migrations(id),
     shard_id VARCHAR(50) NOT NULL,
     status VARCHAR(20) NOT NULL, -- 'pending', 'running', 'completed', 'failed'
     items_processed BIGINT DEFAULT 0,
     total_items BIGINT,
     started_at TIMESTAMP WITH TIME ZONE,
     completed_at TIMESTAMP WITH TIME ZONE,
     error TEXT
   );
   ```

4. **`migration_history`**
   ```sql
   CREATE TABLE migration_history (
     id SERIAL PRIMARY KEY,
     migration_id VARCHAR(50) REFERENCES migrations(id),
     event_type VARCHAR(20) NOT NULL, -- 'created', 'started', 'progress', 'completed', 'failed'
     created_at TIMESTAMP WITH TIME ZONE NOT NULL,
     details JSONB
   );
   ```

## Migration Flow Architecture

The Data Migration Service follows a multi-stage migration process:

1. **Planning Stage**
   - Migration request received via API or message broker
   - Migration plan created based on dependencies and shard topology
   - Pre-checks performed to validate migration feasibility

2. **Schema Migration Stage**
   - Schema changes applied to all shards
   - Changes validated across shards
   - Schema migration status recorded

3. **Data Migration Stage**
   - Data transformation executed in batches
   - Progress tracked per shard
   - Batch size dynamically adjusted based on system load

4. **Verification Stage**
   - Data consistency checks performed
   - Post-migration validation executed
   - Results recorded and reported

5. **Completion/Rollback Stage**
   - Migration marked as complete if successful
   - Rollback initiated if verification fails
   - Notification sent to affected services

## Architecture Patterns

1. **Sharded Awareness Pattern**
   - All operations are aware of the shard topology
   - Operations are routed to appropriate shards
   - Results from shards are aggregated appropriately

2. **Stateful Migration Pattern**
   - Migrations maintain state throughout execution
   - Progress can be tracked at a granular level
   - Failed migrations can be resumed from the point of failure

3. **Batch Processing Pattern**
   - Data is processed in configurable batches
   - Batch size can be adjusted based on system load
   - Progress is tracked per batch

4. **Parallel Execution Pattern**
   - Independent operations are executed in parallel
   - Dependencies are respected
   - Execution is coordinated across shards

5. **Event-Driven Migration Pattern**
   - Long-running migrations are driven by events
   - Progress is reported via events
   - Services can react to migration events

6. **Transactional Migration Pattern**
   - Transactions are used where available (PostgreSQL)
   - Two-phase commit pattern for cross-shard operations
   - Rollback procedures for failed migrations
