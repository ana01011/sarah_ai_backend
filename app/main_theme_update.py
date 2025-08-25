# Add these lines to /root/openhermes_backend/app/main.py

# Add this import at the top with other imports:
from app.api.v1.routers import theme_router

# Add this line after other router includes (around line 80-90):
app.include_router(theme_router.router, prefix="/api/v1")
