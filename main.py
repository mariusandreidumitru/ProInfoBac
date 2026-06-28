from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from supabase import create_client, Client
import random
import uuid
import os
import subprocess
import tempfile
import shutil
import base64
from datetime import datetime, timedelta
import jwt
from io import BytesIO

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI()

# ============================================================
# CORS MIDDLEWARE
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://proinfobac.vercel.app",
        "https://proinfobac.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend"), name="static")

# ============================================================
# SUPABASE
# ============================================================
SUPABASE_URL = "https://qjtxgtjyxosjkktamctm.supabase.co"
SUPABASE_KEY = "sb_publishable_Fx5UnIbVOm3Xr7pVAQkDjg_ox8zw7hV"
STORAGE_BUCKET = "resources"  # numele bucket-ului creat în Supabase Storage

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase conectat cu succes!")
except Exception as e:
    print(f"❌ Eroare la conectarea Supabase: {e}")
    supabase = None

def get_supabase():
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase nu este conectat!")
    return supabase

# ============================================================
# JWT
# ============================================================
SECRET_KEY = "sb_secret_uEui0qLjgj74imc6iqBJBQ_U4tSsYpU"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        return jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalid sau expirat")

# ============================================================
# MODELE
# ============================================================
class UserRegister(BaseModel):
    email: str
    password: str
    role: str

class UserLogin(BaseModel):
    email: str
    password: str

class CodeSubmission(BaseModel):
    code: str
    language: str = "cpp"
    stdin: str = ""

class TestRequest(BaseModel):
    category: str = ""
    count: int = 5
    min_difficulty: int = 1
    max_difficulty: int = 10
    role: str = "student"
    exercise_types: List[str] = []
    randomize: bool = True

class MeetingRequest(BaseModel):
    nume_materie: str

# ============================================================
# HELPER MIME TYPE
# ============================================================
def get_mime_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".txt": "text/plain", ".cpp": "text/plain",
        ".c": "text/plain", ".py": "text/plain",
        ".js": "text/plain", ".html": "text/html",
    }.get(ext, "application/octet-stream")

# ============================================================
# UPLOAD RESURSĂ — folosește Supabase Storage
# ============================================================
@app.post("/upload-resource")
async def upload_resource(
    titlu: str = Form(...),
    descriere: str = Form(None),
    capitol: str = Form(...),
    tip: str = Form(...),
    file: UploadFile = File(...),
    payload: dict = Depends(verify_token)
):
    if payload.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Doar profesorii pot încărca resurse!")
 
    db = get_supabase()
 
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.txt', '.doc',
                        '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.zip', '.cpp', '.c', '.html']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in valid_extensions:
        raise HTTPException(status_code=400, detail=f"Extensia {ext} nu este acceptată!")
 
    content = await file.read()
    print(f"📁 Fișier primit: {file.filename}, dimensiune: {len(content)} bytes")
 
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fișierul este prea mare! Maxim 10 MB.")
 
    file_url = None
    storage_path = None
 
    # Încearcă upload în Supabase Storage
    try:
        unique_name = f"{uuid.uuid4()}{ext}"
        print(f"📤 Încerc upload în Storage: {unique_name}")
 
        mime = get_mime_type(file.filename)
 
        response = db.storage.from_(STORAGE_BUCKET).upload(
            path=unique_name,
            file=content,
            file_options={"content-type": mime, "upsert": "false"}
        )
 
        print(f"✅ Storage response: {response}")
 
        storage_path = unique_name
        file_url = db.storage.from_(STORAGE_BUCKET).get_public_url(unique_name)
        print(f"🔗 URL public: {file_url}")
 
    except Exception as storage_err:
        print(f"⚠️ Storage upload eșuat: {storage_err}")
        print(f"   Tip eroare: {type(storage_err).__name__}")
        # Fallback: salvează ca base64 în DB (metoda veche)
        file_url = None
        storage_path = None
 
    # Construiește datele pentru tabel
    resource_data = {
        "titlu": titlu,
        "descriere": descriere or "",
        "capitol": capitol,
        "tip": tip,
        "original_name": file.filename,
        "dimensiune": len(content),
        "uploaded_by": payload.get("email", "unknown"),
        "vizualizari": 0,
        "uploaded_at": datetime.now().isoformat()
    }
 
    if storage_path and file_url:
        # Calea fericită: fișierul e în Storage
        resource_data["storage_path"] = storage_path
        resource_data["file_url"] = file_url
        print("✅ Salvez metadate cu file_url în DB")
    else:
        # Fallback: salvează base64 în DB
        resource_data["file_data"] = base64.b64encode(content).decode('utf-8')
        print("⚠️ Salvez ca base64 în DB (fallback)")
 
    try:
        print(f"💾 Insert în tabel resources...")
        insert_response = db.table("resources").insert(resource_data).execute()
        print(f"✅ Insert OK: {insert_response.data}")
 
        if insert_response.data:
            return {
                "status": "success",
                "message": "Fișierul a fost încărcat cu succes!",
                "resource": insert_response.data[0],
                "storage_used": storage_path is not None
            }
        else:
            raise HTTPException(status_code=500, detail="Eroare la salvarea în baza de date!")
 
    except HTTPException:
        raise
    except Exception as db_err:
        print(f"❌ Eroare DB insert: {db_err}")
        print(f"   Tip eroare: {type(db_err).__name__}")
        raise HTTPException(status_code=500, detail=f"Eroare DB: {str(db_err)}")

# ============================================================
# LISTEAZĂ RESURSE
# ============================================================
@app.get("/api/resurse")
async def get_resurse(payload: dict = Depends(verify_token)):
    db = get_supabase()
    try:
        # Selectăm tot FĂRĂ file_data (care nu mai există) — răspuns instant
        response = db.table("resources").select(
            "id, titlu, descriere, capitol, tip, original_name, file_url, storage_path, dimensiune, uploaded_by, vizualizari, uploaded_at"
        ).order("uploaded_at", desc=True).execute()
        return {"resurse": response.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ȘTERGE RESURSĂ
# ============================================================
@app.delete("/api/resurse/{file_id}")
async def delete_resource(file_id: int, payload: dict = Depends(verify_token)):
    if payload.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Doar profesorii pot șterge resurse!")

    db = get_supabase()
    try:
        check = db.table("resources").select("id, storage_path").eq("id", file_id).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Resursa nu a fost găsită")

        storage_path = check.data[0].get("storage_path")

        # Șterge din Storage
        if storage_path:
            db.storage.from_(STORAGE_BUCKET).remove([storage_path])

        # Șterge din tabel
        db.table("resources").delete().eq("id", file_id).execute()
        return {"status": "success", "message": "Resursa a fost ștearsă"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# DOWNLOAD / PREVIEW — redirect direct la URL din Storage
# Browserul descarcă direct din Supabase Storage, nu prin serverul tău!
# ============================================================
@app.get("/download-resource/{file_id}")
async def download_resource(file_id: int, payload: dict = Depends(verify_token)):
    db = get_supabase()
    resource = db.table("resources").select("file_url, original_name, vizualizari").eq("id", file_id).execute()
    if not resource.data:
        raise HTTPException(status_code=404, detail="Resursa nu a fost găsită")

    r = resource.data[0]
    db.table("resources").update({"vizualizari": r.get("vizualizari", 0) + 1}).eq("id", file_id).execute()

    # Redirect direct la URL-ul din Storage — instant, fără să treci prin server
    return RedirectResponse(url=r["file_url"])

@app.get("/download-resource-token/{file_id}")
async def download_resource_token(file_id: int, token: str):
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirat")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalid")

    db = get_supabase()
    resource = db.table("resources").select("file_url, original_name, vizualizari").eq("id", file_id).execute()
    if not resource.data:
        raise HTTPException(status_code=404, detail="Resursa nu a fost găsită")

    r = resource.data[0]
    db.table("resources").update({"vizualizari": r.get("vizualizari", 0) + 1}).eq("id", file_id).execute()
    return RedirectResponse(url=r["file_url"])

@app.get("/view-pdf/{file_id}")
async def view_pdf(file_id: int, token: str):
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalid")

    db = get_supabase()
    resource = db.table("resources").select("file_url, original_name, vizualizari").eq("id", file_id).execute()
    if not resource.data:
        raise HTTPException(status_code=404, detail="Resursa nu a fost găsită")

    r = resource.data[0]
    db.table("resources").update({"vizualizari": r.get("vizualizari", 0) + 1}).eq("id", file_id).execute()
    return RedirectResponse(url=r["file_url"])

# ============================================================
# COMPILE COD C++
# ============================================================
@app.post("/compile")
async def compile_code(submission: CodeSubmission):
    if submission.language != "cpp":
        raise HTTPException(status_code=400, detail="Doar C++ este suportat momentan.")

    tmp_dir = tempfile.mkdtemp()
    try:
        src_path = os.path.join(tmp_dir, "main.cpp")
        bin_path = os.path.join(tmp_dir, "main")

        with open(src_path, "w") as f:
            f.write(submission.code)

        compile_result = subprocess.run(
            ["g++", "-o", bin_path, src_path, "-std=c++17"],
            capture_output=True, text=True, timeout=15
        )

        if compile_result.returncode != 0:
            return {"success": False, "error": compile_result.stderr, "output": ""}

        run_result = subprocess.run(
            [bin_path], input=submission.stdin,
            capture_output=True, text=True, timeout=10
        )
        return {"success": True, "output": run_result.stdout, "error": run_result.stderr, "returncode": run_result.returncode}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timpul de execuție a depășit limita (10s).", "output": ""}
    except Exception as e:
        return {"success": False, "error": str(e), "output": ""}
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

# ============================================================
# AUTH
# ============================================================
@app.get("/api/user")
def get_user(payload: dict = Depends(verify_token)):
    db = get_supabase()
    try:
        user_id = payload.get("sub")
        response = db.table("users").select("*").eq("id", user_id).execute()
        if response.data:
            user = response.data[0]
            return {"id": user.get("id"), "email": user.get("email"), "role": user.get("role"),
                    "name": user.get("name") or user.get("email").split('@')[0]}
        return {"id": user_id, "email": payload.get("email"), "role": payload.get("role"),
                "name": payload.get("email", "").split('@')[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
def login_user(login: UserLogin):
    db = get_supabase()
    try:
        response = db.table("users").select("*").eq("email", login.email).eq("password_hash", login.password).execute()
        if not response.data:
            raise HTTPException(status_code=401, detail="Email sau parola incorecte!")
        user = response.data[0]
        token = create_access_token({"sub": str(user["id"]), "email": user["email"], "role": user.get("role", "student")})
        return {"status": "success", "message": "Autentificare reușită!", "access_token": token,
                "token_type": "bearer", "user": {"id": user["id"], "email": user["email"], "role": user.get("role")}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register")
def register_user(user: UserRegister):
    db = get_supabase()
    if user.role not in ["student", "teacher"]:
        raise HTTPException(status_code=400, detail="Rolul trebuie sa fie 'student' sau 'teacher'!")
    try:
        if db.table("users").select("id").eq("email", user.email).execute().data:
            raise HTTPException(status_code=400, detail="Acest email este deja înregistrat!")
        response = db.table("users").insert({
            "email": user.email, "password_hash": user.password,
            "role": user.role, "created_at": datetime.now().isoformat()
        }).execute()
        if response.data:
            u = response.data[0]
            return {"status": "success", "message": "Cont creat cu succes!",
                    "user": {"email": u.get("email"), "role": u.get("role"), "id": u.get("id")}}
        raise HTTPException(status_code=500, detail="Eroare la salvarea utilizatorului!")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# GENERARE TEST
# ============================================================
def get_question_bank() -> List[dict]:
    return [
        {"id": 1, "category": "Vectori și tablouri", "difficulty": 3, "exercise_type": "cod",
         "question": "Scrie un program care citește un număr natural n și n elemente ale unui vector, apoi afișează elementele în ordine inversă.",
         "hint": "Folosește un tablou static de dimensiune suficientă și parcurge-l de la sfârșit spre început.",
         "code_stub": "#include <iostream>\nusing namespace std;\nint main() {\n    int n;\n    cin >> n;\n    int a[1000];\n    for (int i = 0; i < n; i++) {\n        cin >> a[i];\n    }\n    // afișează elementele în ordine inversă\n    return 0;\n}\n",
         "answer": "Citești n, construiești vectorul și afișezi de la n-1 la 0."},
        {"id": 2, "category": "Șiruri de caractere", "difficulty": 4, "exercise_type": "grila",
         "question": "Care este valoarea afișată: string s = \"abc\"; cout << s.size();",
         "options": ["A. 3", "B. 2", "C. 4", "D. Nu se compilează"], "answer": "A. 3"},
        {"id": 3, "category": "Algoritmi și structuri de date", "difficulty": 5, "exercise_type": "scris",
         "question": "Se citește un vector de n numere naturale. Determină numărul de elemente pare.",
         "answer": "Parcurgi vectorul și numeri elementele cu rest 0 la împărțire la 2."},
        {"id": 5, "category": "Grafuri", "difficulty": 7, "exercise_type": "grila",
         "question": "Structura de date cea mai potrivită pentru BFS?",
         "options": ["A. Stivă", "B. Coada", "C. Arbore binar", "D. Hash map"], "answer": "B. Coada"},
        {"id": 6, "category": "Programare dinamică", "difficulty": 8, "exercise_type": "scris",
         "question": "Ce reprezintă memoizarea și cum se aplică la șirul Fibonacci?",
         "answer": "Memoizarea salvează rezultatele intermediate, evitând recalcularea subproblemelor."},
    ]

@app.post("/generate-test")
def generate_test(request: TestRequest):
    selected_types = [t for t in request.exercise_types if t in {"grila", "cod", "scris"}]
    if not selected_types:
        selected_types = ["grila", "cod", "scris"]

    questions = []
    try:
        if supabase:
            query = supabase.table("questions").select("*")
            if request.category:
                query = query.ilike("category", f"%{request.category}%")
            query = query.gte("difficulty", request.min_difficulty).lte("difficulty", request.max_difficulty).limit(request.count)
            response = query.execute()
            questions = response.data or []
    except Exception:
        questions = []

    if not questions:
        fallback = get_question_bank()
        filtered = [q for q in fallback
                    if (not request.category or request.category.lower() in q["category"].lower())
                    and request.min_difficulty <= q["difficulty"] <= request.max_difficulty
                    and q["exercise_type"] in selected_types]
        questions = filtered or fallback

    if request.randomize:
        random.shuffle(questions)
    questions = questions[:max(1, min(request.count, len(questions)))]
    return {"questions": questions, "count": len(questions)}

# ============================================================
# MEETING
# ============================================================
@app.post("/generate-meeting")
def generate_meeting_link(request: MeetingRequest):
    room_name = f"BacInfo_{request.nume_materie.replace(' ', '')}_{str(uuid.uuid4())[:8]}"
    return {"status": "Sala a fost creata!", "link_intalnire": f"https://meet.jit.si/{room_name}", "nume_camera": room_name}

# ============================================================
# PAGINI HTML
# ============================================================
@app.get("/")
def serve_root(): return FileResponse(BASE_DIR / "frontend" / "index.html")
@app.get("/login")
def serve_login(): return FileResponse(BASE_DIR / "frontend" / "index.html")
@app.get("/signup")
def serve_signup(): return FileResponse(BASE_DIR / "frontend" / "register.html")
@app.get("/dashboard")
def serve_dashboard(): return FileResponse(BASE_DIR / "frontend" / "dashboard.html")
@app.get("/editor")
def serve_editor(): return FileResponse(BASE_DIR / "frontend" / "editor.html")
@app.get("/meeting")
def serve_meeting_page(): return FileResponse(BASE_DIR / "frontend" / "meeting.html")
@app.get("/tests")
def serve_tests(): return FileResponse(BASE_DIR / "frontend" / "tests.html")
@app.get("/creator")
def serve_creator(): return FileResponse(BASE_DIR / "frontend" / "creator.html")
@app.get("/resurse")
def serve_resurse(): return FileResponse(BASE_DIR / "frontend" / "resurse.html")

@app.get("/api/verify-token")
def verify_token_endpoint(payload: dict = Depends(verify_token)):
    return {"valid": True, "user": {"id": payload.get("sub"), "email": payload.get("email"), "role": payload.get("role")}}

@app.get("/test-supabase")
def test_supabase_endpoint():
    try:
        if supabase:
            r = supabase.table("users").select("*").limit(1).execute()
            return {"status": "✅ OK", "data": r.data}
        return {"status": "❌ Supabase nu este conectat"}
    except Exception as e:
        return {"status": "❌ Eroare", "error": str(e)}

@app.get("/debug-token")
async def debug_token(token: str = None):
    if not token:
        return {"error": "Token lipsă"}
    try:
        return {"valid": True, "payload": jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])}
    except Exception as e:
        return {"valid": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)