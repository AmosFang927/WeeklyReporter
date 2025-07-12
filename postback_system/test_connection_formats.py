#!/usr/bin/env python3
"""
Test different connection string formats for asyncpg with Cloud SQL
"""

import os

# Current format (causing Connection refused)
current_format = "postgresql+asyncpg://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db"

# Alternative formats for asyncpg with Cloud SQL
formats = [
    # Format 1: Direct Unix socket path
    "postgresql+asyncpg://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?unix_sock=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db",
    
    # Format 2: Using host parameter without query
    "postgresql+asyncpg://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db/postback_db",
    
    # Format 3: Using socket directory
    "postgresql+asyncpg://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db/.s.PGSQL.5432",
    
    # Format 4: Standard PostgreSQL format for unix socket
    "postgresql+asyncpg://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db&port=5432",
]

print("Current format (causing Connection refused):")
print(current_format)
print("\nAlternative formats to try:")
for i, format_str in enumerate(formats, 1):
    print(f"{i}. {format_str}")

print("\nFor asyncpg with Cloud SQL, the correct format is typically:")
print("postgresql+asyncpg://user:password@/database?host=/cloudsql/instance-connection-name") 