"""
Performance Monitoring Dashboard
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import psutil
import json

app = FastAPI()

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return """
    <html>
    <head>
        <title>Sarah AI Performance</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body { font-family: monospace; background: #1a1a1a; color: #0f0; padding: 20px; }
            .metric { display: inline-block; margin: 10px; padding: 10px; border: 1px solid #0f0; }
        </style>
    </head>
    <body>
        <h1>Sarah AI Performance Dashboard</h1>
        <div id="metrics"></div>
        <script>
            fetch('/metrics')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('metrics').innerHTML = 
