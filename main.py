
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import os
import subprocess
import httpx
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="APK Modding Webhook Server",
    description="API to automate APK decompilation, modification, recompilation, and signing."
)

# Define the expected JSON payload structure for instructions
class APKInstructionPayload(BaseModel):
    nama_apk: str
    instruksi: str
    request_id: str
    apk_download_url: str | None = None

# Directory to store APKs and processed files
APK_STORAGE_DIR = "./apk_storage"

@app.on_event("startup")
async def startup_event():
    if not os.path.exists(APK_STORAGE_DIR):
        os.makedirs(APK_STORAGE_DIR, exist_ok=True)
    logging.info(f"APK storage directory ready: {APK_STORAGE_DIR}")

@app.get("/")
async def root():
    return {"message": "APK Modding Server is running", "status": "ok"}

@app.post("/mod_apk")
async def mod_apk_endpoint(
    payload: APKInstructionPayload = Form(...),
    apk_file: UploadFile | None = File(None)
):
    logging.info(f"Received request for APK modification: {payload.request_id}")
    
    apk_filename = payload.nama_apk
    instructions_text = payload.instruksi
    request_id = payload.request_id
    apk_download_url = payload.apk_download_url

    original_apk_path = os.path.join(APK_STORAGE_DIR, f"{request_id}_{apk_filename}")
    decompiled_output_dir = os.path.join(APK_STORAGE_DIR, f"decompiled_{request_id}")
    unsigned_apk_path = os.path.join(APK_STORAGE_DIR, f"unsigned_modded_{request_id}_{apk_filename}")

    try:
        if apk_file:
            with open(original_apk_path, "wb") as buffer:
                shutil.copyfileobj(apk_file.file, buffer)
        elif apk_download_url:
            async with httpx.AsyncClient() as client:
                response = await client.get(apk_download_url)
                response.raise_for_status() 
                with open(original_apk_path, "wb") as buffer:
                    buffer.write(response.content)
        else:
            raise HTTPException(status_code=400, detail="No APK provided.")
        
        logging.info(f"Decompiling {apk_filename}...")
        subprocess.run(["apktool", "d", original_apk_path, "-o", decompiled_output_dir, "-f"], check=True, capture_output=True, text=True)

        # Placeholder for modifications
        logging.info("Applying modifications...")

        logging.info("Recompiling...")
        subprocess.run(["apktool", "b", decompiled_output_dir, "-o", unsigned_apk_path], check=True, capture_output=True, text=True)

        logging.info("Signing...")
        subprocess.run(["java", "-jar", "/usr/local/bin/uber-apk-signer.jar", "--apks", unsigned_apk_path], check=True, capture_output=True, text=True)
        
        signed_apk_found = None
        for f in os.listdir(APK_STORAGE_DIR):
            if f.startswith(f"unsigned_modded_{request_id}_{apk_filename.replace('.apk', '')}") and f.endswith("-aligned-signed.apk"):
                signed_apk_found = os.path.join(APK_STORAGE_DIR, f)
                break
        
        if not signed_apk_found:
            raise HTTPException(status_code=500, detail="Signed APK not found.")

        return {"message": "Success", "request_id": request_id, "modded_apk_path": signed_apk_found}

    except subprocess.CalledProcessError as e:
        logging.error(f"Tool error: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Tool error: {e.stderr}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(original_apk_path): os.remove(original_apk_path)
        if os.path.exists(unsigned_apk_path): os.remove(unsigned_apk_path)
        if os.path.exists(decompiled_output_dir): shutil.rmtree(decompiled_output_dir)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
