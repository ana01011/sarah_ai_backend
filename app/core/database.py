"""
Database connection and session management
"""
import asyncpg
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        
    async def connect(self):
        """Create database connection pool"""
        self.pool = await asyncpg.create_pool(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            user=os.getenv("POSTGRES_USER", "sarah_user"),
            password=os.getenv("POSTGRES_PASSWORD", "sarah_secure_2024"),
            database=os.getenv("POSTGRES_DB", "sarah_ai_fresh"),
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        print("✅ Database connected")
        
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            print("Database disconnected")
    
    async def execute(self, query: str, *args):
        """Execute a query"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """Fetch multiple rows"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """Fetch single row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """Fetch single value"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

# Global database instance
db = Database()
