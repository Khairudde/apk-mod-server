
import os
import subprocess
import httpx
import logging
import shutil
import uvicorn
import re
import json
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("--- SERVER INITIALIZING ---")

app = FastAPI(
    title="AI APK Auto-Modder",
    description="Automated APK modification using Uncensored AI and Smart Patching with Taskade Callback."
)

# Taskade Webhook URL for callback
TASKADE_CALLBACK_URL = "https://www.taskade.com/webhooks/flow/01KYTC913RS4RAANYE45FP721P/sync"
APK_STORAGE_DIR = "/tmp/apk_storage"

@app.on_event("startup")
async def startup_event():
    if not os.path.exists(APK_STORAGE_DIR):
        os.makedirs(APK_STORAGE_DIR, exist_ok=True)
    logger.info(f"--- SERVER STARTED SUCCESSFULLY ON PORT {os.environ.get('PORT', '8080')} ---")

@app.get("/")
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Server is running"}

async def call_uncensored_ai(instructions: str):
    HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
    if not HUGGINGFACE_API_TOKEN:
        logger.warning("HUGGINGFACE_API_TOKEN is missing!")
        return None

    model_id = "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO" 
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    
    system_prompt = (
        "You are an expert Android reverse engineer. Translate user instructions into a JSON list of patches. "
        "Each patch must have: 'file_pattern' (regex for filename), 'find' (regex/string to find), and 'replace' (string to replace). "
        "Focus on smali code. Output ONLY the JSON object."
    )
    
    prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{instructions}<|im_end|>\n<|im_start|>assistant\n"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, headers=headers, json={"inputs": prompt, "parameters": {"max_new_tokens": 1000}}, timeout=60.0)
            result = response.json()
            text = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', '')
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
    except Exception as e:
        logger.error(f"AI Error: {e}")
    return None

def apply_patches(decompiled_dir, patches_data):
    if not patches_data or 'patches' not in patches_data:
        return False
    
    modified_count = 0
    for root, dirs, files in os.walk(decompiled_dir):
        for file in files:
            file_path = os.path.join(root, file)
            for patch in patches_data['patches']:
                try:
                    if re.search(patch['file_pattern'], file_path):
                        with open(file_path, 'r', errors='ignore') as f:
                            content = f.read()
                        new_content = re.sub(patch['find'], patch['replace'], content)
                        if new_content != content:
                            with open(file_path, 'w') as f:
                                f.write(new_content)
                            modified_count += 1
                            logger.info(f"Patched: {file_path}")
                except Exception as e:
                    logger.error(f"Patch error on {file_path}: {e}")
    return modified_count > 0

async def upload_to_file_io(file_path):
    try:
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                response = await client.post("https://file.io", files={"file": f})
                return response.json().get("link")
    except Exception as e:
        logger.error(f"Upload error: {e}")
    return None

async def send_callback_to_taskade(request_id, status, download_url):
    payload = {"request_id": request_id, "status": status, "download_url": download_url}
    logger.info(f"Sending callback to Taskade: {payload}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(TASKADE_CALLBACK_URL, json=payload, timeout=30.0)
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Taskade callback failed: {e}")
        return False

async def process_mod_task(request_id: str, nama_apk: str, instruksi: str, apk_file_path: str):
    decompiled_dir = os.path.join(APK_STORAGE_DIR, f"work_{request_id}")
    unsigned_apk = os.path.join(APK_STORAGE_DIR, f"{request_id}_unsigned.apk")
    download_url = None
    status = "error"

    try:
        logger.info(f"Processing mod for {nama_apk} (ID: {request_id})")
        subprocess.run(["apktool", "d", apk_file_path, "-o", decompiled_dir, "-f"], check=True)
        patches = await call_uncensored_ai(instruksi)
        if patches:
            apply_patches(decompiled_dir, patches)
        subprocess.run(["apktool", "b", decompiled_dir, "-o", unsigned_apk], check=True)
        subprocess.run(["java", "-jar", "/usr/local/bin/uber-apk-signer.jar", "--apks", unsigned_apk], check=True)
        
        signed_apk = None
        for f in os.listdir(APK_STORAGE_DIR):
            if f.startswith(f"{request_id}_unsigned") and f.endswith("-aligned-signed.apk"):
                signed_apk = os.path.join(APK_STORAGE_DIR, f)
                break
        
        if signed_apk:
            download_url = await upload_to_file_io(signed_apk)
            if download_url:
                status = "success"
    except Exception as e:
        logger.error(f"Background process failed: {e}")
    finally:
        await send_callback_to_taskade(request_id, status, download_url)
        try:
            if os.path.exists(apk_file_path): os.remove(apk_file_path)
            if os.path.exists(unsigned_apk): os.remove(unsigned_apk)
            if os.path.exists(decompiled_dir): shutil.rmtree(decompiled_dir)
            for f in os.listdir(APK_STORAGE_DIR):
                if f.startswith(f"{request_id}_unsigned"):
                    os.remove(os.path.join(APK_STORAGE_DIR, f))
        except Exception as cleanup_error:
            logger.error(f"Cleanup error: {cleanup_error}")

@app.post("/mod_apk")
async def mod_apk_endpoint(
    background_tasks: BackgroundTasks,
    nama_apk: str = Form(...),
    instruksi: str = Form(...),
    request_id: str = Form(...),
    apk_download_url: str | None = Form(None),
    apk_file: UploadFile | None = File(None)
):
    logger.info(f"Received request: request_id={request_id}")
    temp_apk_path = os.path.join(APK_STORAGE_DIR, f"{request_id}_temp.apk")
    try:
        if apk_file:
            with open(temp_apk_path, "wb") as f: shutil.copyfileobj(apk_file.file, f)
        elif apk_download_url:
            async with httpx.AsyncClient() as client:
                res = await client.get(apk_download_url)
                with open(temp_apk_path, "wb") as f: f.write(res.content)
        else:
            raise HTTPException(status_code=400, detail="No APK provided")
            
        background_tasks.add_task(process_mod_task, request_id, nama_apk, instruksi, temp_apk_path)
        return {"status": "processing", "request_id": request_id}
    except Exception as e:
        logger.error(f"Endpoint failed: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
