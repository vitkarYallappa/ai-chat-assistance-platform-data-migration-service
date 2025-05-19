
#!/bin/bash
set -e

# Wait for dependencies to be ready
function wait_for_service() {
  echo "Waiting for $1:$2..."
  while ! nc -z $1 $2; do
    sleep 1
  done
  echo "$1:$2 is available!"
}

# Wait for PostgreSQL
if [ -n "$POSTGRES_SERVER" ] && [ -n "$POSTGRES_PORT" ]; then
  wait_for_service $POSTGRES_SERVER $POSTGRES_PORT
fi

# Wait for MongoDB
if [ -n "$MONGODB_HOST" ] && [ -n "$MONGODB_PORT" ]; then
  wait_for_service $MONGODB_HOST $MONGODB_PORT
fi

# Wait for RabbitMQ if configured
if [ "$MESSAGE_BROKER_TYPE" = "rabbitmq" ] && [ -n "$RABBITMQ_HOST" ] && [ -n "$RABBITMQ_PORT" ]; then
  wait_for_service $RABBITMQ_HOST $RABBITMQ_PORT
fi

# Wait for Kafka if configured
if [ "$MESSAGE_BROKER_TYPE" = "kafka" ] && [ -n "$KAFKA_HOST" ] && [ -n "$KAFKA_PORT" ]; then
  wait_for_service $KAFKA_HOST $KAFKA_PORT
fi

exec "$@"