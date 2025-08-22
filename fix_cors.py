# Fix CORS in main.py
import re

with open('/root/openhermes_backend/app/main.py', 'r') as f:
    content = f.read()

# Find and replace CORS middleware configuration
cors_pattern = r'app\.add_middleware\(\s*CORSMiddleware,[^)]+\)'
new_cors = '''app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://147.93.102.165:3001",
        "http://147.93.102.165:3000", 
        "http://147.93.102.165",
        "http://localhost:3001",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''

content = re.sub(cors_pattern, new_cors, content, flags=re.DOTALL)

with open('/root/openhermes_backend/app/main.py', 'w') as f:
    f.write(content)

print("CORS fixed!")
