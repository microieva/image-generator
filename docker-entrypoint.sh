#!/bin/bash
set -e

echo "🔄 Waiting for SQL Server to be ready..."
while ! /opt/mssql-tools/bin/sqlcmd -S mssql -U sa -P "YourStrong@Password123" -Q "SELECT 1" > /dev/null 2>&1; do
    echo "⏳ SQL Server not ready yet..."
    sleep 5
done

echo "✅ SQL Server is ready"

echo "🔄 Creating database if it doesn't exist..."
/opt/mssql-tools/bin/sqlcmd -S mssql -U sa -P "YourStrong@Password123" -Q "IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = 'ImageGeneratorDB') CREATE DATABASE ImageGeneratorDB"

echo "✅ Database setup complete"

echo "🚀 Starting FastAPI application..."
exec "$@"