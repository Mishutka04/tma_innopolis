import re
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse




router = APIRouter()



@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    return