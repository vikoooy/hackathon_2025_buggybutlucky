# backend/app/routers/report.py
from fastapi import APIRouter
from fastapi.responses import FileResponse
import pdfkit
import json
import uuid
import os

router = APIRouter(prefix="/report", tags=["report"])

@router.post("/generate")
async def generate_report():
    # 1. JSON laden (später ersetzt durch Echt-Daten)
    with open("report_template.json") as f:
        data = json.load(f)

    # 2. HTML generieren (hier Dummy, später Template)
    html = f"""
    <h1>Wargaming Report</h1>
    <p>Runde: {data['runde']}</p>
    <p>Attack Result: {data['attack']}</p>
    """

    # 3. Datei erzeugen
    filename = f"report_{uuid.uuid4()}.pdf"
    filepath = f"/tmp/{filename}"

    pdfkit.from_string(html, filepath)

    # 4. PDF zurückgeben
    return FileResponse(filepath, filename=filename, media_type="application/pdf")
