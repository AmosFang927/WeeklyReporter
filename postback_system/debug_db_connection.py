#!/usr/bin/env python3
"""
Debug script to test database connection
"""

import asyncio
import asyncpg
import os
from urllib.parse import urlparse, parse_qs

async def test_direct_asyncpg_connection():
    """Test direct asyncpg connection"""
    database_url = "postgresql+asyncpg://postback_admin:ByteC2024PostBack_CloudSQL_20250708@/postback_db?host=/cloudsql/solar-idea-463423-h8:asia-southeast1:bytec-postback-db"
    
    # Parse the URL
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    print(f"Parsed URL: {parsed}")
    print(f"Query params: {query_params}")
    print(f"Host from query: {query_params.get('host', [''])[0]}")
    
    # Try different connection approaches
    approaches = [
        # Approach 1: Direct asyncpg with host parameter
        {
            "name": "Direct asyncpg with host parameter",
            "params": {
                "host": query_params.get('host', [''])[0],
                "database": parsed.path.lstrip('/'),
                "user": parsed.username,
                "password": parsed.password
            }
        },
        # Approach 2: Try with Unix socket format
        {
            "name": "Unix socket format",
            "params": {
                "host": query_params.get('host', [''])[0],
                "database": parsed.path.lstrip('/'),
                "user": parsed.username,
                "password": parsed.password
            }
        },
        # Approach 3: Try with direct connection string
        {
            "name": "Direct connection string",
            "dsn": database_url.replace("+asyncpg", "")
        }
    ]
    
    for approach in approaches:
        try:
            print(f"\n--- Testing {approach['name']} ---")
            
            if 'dsn' in approach:
                print(f"DSN: {approach['dsn']}")
                # This might not work directly, but let's see
                conn = await asyncpg.connect(approach['dsn'])
            else:
                print(f"Connection params: {approach['params']}")
                conn = await asyncpg.connect(**approach['params'])
            
            # Test the connection
            result = await conn.fetchval("SELECT 1")
            print(f"✅ Success! Result: {result}")
            
            await conn.close()
            break
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            print(f"Error type: {type(e)}")

if __name__ == "__main__":
    asyncio.run(test_direct_asyncpg_connection()) 