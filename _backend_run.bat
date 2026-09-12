@echo off
cd /d "D:\Angels\ai-dengue-diagnosis\backend"
python -m uvicorn main:app --reload --port 8000
