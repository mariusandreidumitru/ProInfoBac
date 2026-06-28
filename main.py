from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from supabase import create_client, Client
import requests
import random
import uuid
import os
import json
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
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============================================================
# STATIC FILES
# ============================================================
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend"), name="static")

# ============================================================
# CONFIGURARE SUPABASE
# ============================================================
SUPABASE_URL = "https://qjtxgtjyxosjkktamctm.supabase.co"
SUPABASE_KEY = "sb_publishable_Fx5UnIbVOm3Xr7pVAQkDjg_ox8zw7hV"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase conectat cu succes!")
except Exception as e:
    print(f"❌ Eroare la conectarea Supabase: {e}")
    supabase = None

# ============================================================
# CONFIGURARE JWT
# ============================================================
SECRET_KEY = "sb_secret_uEui0qLjgj74imc6iqBJBQ_U4tSsYpU"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalid sau expirat")

# ============================================================
# MODELE PYDANTIC
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
# FUNCȚIE BANC DE ÎNTREBĂRI
# ============================================================
def get_question_bank() -> List[dict]:
    return [
        {
            "id": 1,
            "category": "Vectori și tablouri",
            "difficulty": 3,
            "exercise_type": "cod",
            "question": "Scrie un program care citește un număr natural n și n elemente ale unui vector, apoi afișează elementele în ordine inversă.",
            "hint": "Folosește un tablou static de dimensiune suficientă și parcurge-l de la sfârșit spre început.",
            "code_stub": "#include <iostream>\nusing namespace std;\nint main() {\n    int n;\n    cin >> n;\n    int a[1000];\n    for (int i = 0; i < n; i++) {\n        cin >> a[i];\n    }\n    // afișează elementele în ordine inversă\n    return 0;\n}\n",
            "solution_code": "#include <iostream>\nusing namespace std;\nint main() {\n    int n;\n    cin >> n;\n    int a[1000];\n    for (int i = 0; i < n; i++) {\n        cin >> a[i];\n    }\n    for (int i = n - 1; i >= 0; i--) {\n        cout << a[i];\n        if (i > 0) cout << ' ';\n    }\n    cout << '\\n';\n    return 0;\n}\n",
            "answer": "Citești n, construiești vectorul în tabloul a și afișezi elementele începând de la n-1 până la 0."
        },
        {
            "id": 2,
            "category": "Șiruri de caractere",
            "difficulty": 4,
            "exercise_type": "grila",
            "question": "Care este valoarea afișată de următorul cod C++: string s = \"abc\"; cout << s.size();",
            "options": ["A. 3", "B. 2", "C. 4", "D. Nu se compilează"],
            "answer": "A. 3"
        },
        {
            "id": 3,
            "category": "Algoritmi și structuri de date",
            "difficulty": 5,
            "exercise_type": "scris",
            "question": "Se citește un vector de n numere naturale. Determină și afișează numărul de elemente pare din vector.",
            "answer": "Parcurgi vectorul, numeri elementele cu rest 0 la împărțire la 2 și afișezi rezultatul."
        },
        {
            "id": 4,
            "category": "Fișiere și matrici",
            "difficulty": 6,
            "exercise_type": "cod",
            "question": "Scrie un program care citește dintr-un fișier un tablou bidimensional m x n și afișează suma elementelor de pe diagonala principală.",
            "hint": "Stochează valorile într-un tablou 2D și adună doar pozițiile unde linia este egală cu coloana.",
            "code_stub": "#include <iostream>\nusing namespace std;\nint main() {\n    int m, n;\n    cin >> m >> n;\n    int a[100][100];\n    for (int i = 0; i < m; i++) {\n        for (int j = 0; j < n; j++) {\n            cin >> a[i][j];\n        }\n    }\n    int sum = 0;\n    // calculează suma diagonală\n    cout << sum << endl;\n    return 0;\n}\n",
            "solution_code": "#include <iostream>\nusing namespace std;\nint main() {\n    int m, n;\n    cin >> m >> n;\n    int a[100][100];\n    for (int i = 0; i < m; i++) {\n        for (int j = 0; j < n; j++) {\n            cin >> a[i][j];\n        }\n    }\n    int sum = 0;\n    int limit = (m < n ? m : n);\n    for (int i = 0; i < limit; i++) {\n        sum += a[i][i];\n    }\n    cout << sum << endl;\n    return 0;\n}\n",
            "answer": "Parcurgi linia i și coloana i și aduni elementele atunci când i == j."
        },
        {
            "id": 5,
            "category": "Grafuri",
            "difficulty": 7,
            "exercise_type": "grila",
            "question": "Care este structura de date cea mai potrivită pentru a implementa BFS într-un graf neorientat?",
            "options": ["A. Stivă", "B. Coada", "C. Arbore binar", "D. Hash map"],
            "answer": "B. Coada"
        },
        {
            "id": 6,
            "category": "Programare dinamică",
            "difficulty": 8,
            "exercise_type": "scris",
            "question": "Ce reprezintă memoizarea și cum se aplică la șirul Fibonacci?",
            "answer": "Memoizarea salvează rezultatele intermediate într-un vector sau tabel, evitând recalcularea subproblemelor."
        },
        {
            "id": 7,
            "category": "Vectori și tablouri",
            "difficulty": 5,
            "exercise_type": "cod",
            "question": "Scrie un program care citește n numere naturale și afișează numai numerele pare din șirul citit.",
            "hint": "Citește fiecare element și afișează-l doar dacă x % 2 == 0.",
            "code_stub": "#include <iostream>\nusing namespace std;\nint main() {\n    int n;\n    cin >> n;\n    for (int i = 0; i < n; i++) {\n        int x;\n        cin >> x;\n        // afișează doar numerele pare\n    }\n    cout << '\\n';\n    return 0;\n}\n",
            "solution_code": "#include <iostream>\nusing namespace std;\nint main() {\n    int n;\n    cin >> n;\n    for (int i = 0; i < n; i++) {\n        int x;\n        cin >> x;\n        if (x % 2 == 0) {\n            cout << x;\n            if (i < n - 1) cout << ' ';\n        }\n    }\n    cout << '\\n';\n    return 0;\n}\n",
            "answer": "Citește fiecare element și afișează-l doar dacă restul împărțirii la 2 este 0."
        }
    ]

# ============================================================
# API - USER
# ============================================================
@app.get("/api/user")
def get_user(payload: dict = Depends(verify_token)):
    try:
        user_email = payload.get("email")
        user_role = payload.get("role")
        user_id = payload.get("sub")
        
        if supabase:
            response = supabase.table("users").select("*").eq("id", user_id).execute()
            if response.data and len(response.data) > 0:
                user = response.data[0]
                return {
                    "id": user.get("id"),
                    "email": user.get("email"),
                    "role": user.get("role"),
                    "name": user.get("name") or user.get("email").split('@')[0]
                }
        
        return {
            "id": user_id,
            "email": user_email,
            "role": user_role,
            "name": user_email.split('@')[0]
        }
    except Exception as e:
        print(f"❌ Eroare la /api/user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Eroare: {str(e)}")

# ============================================================
# API - LOGIN
# ============================================================
@app.post("/login")
def login_user(login: UserLogin):
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase nu este conectat!")
    
    try:
        response = supabase.table("users").select("*").eq("email", login.email).eq("password_hash", login.password).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=401, detail="Email sau parola incorecte!")
        
        user = response.data[0]
        user_role = user.get("role", "student")
        user_email = user.get("email")
        user_id = user.get("id")
        
        token_data = {
            "sub": str(user_id),
            "email": user_email,
            "role": user_role
        }
        access_token = create_access_token(token_data)
        
        print(f"✅ Login: {user_email} cu rol {user_role}")
        
        return {
            "status": "success",
            "message": "Autentificare reușită!",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user_email,
                "role": user_role
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Eroare login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Eroare la autentificare: {str(e)}")

# ============================================================
# API - ÎNREGISTRARE
# ============================================================
@app.post("/register")
def register_user(user: UserRegister):
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase nu este conectat!")
    
    if user.role not in ["student", "teacher"]:
        raise HTTPException(status_code=400, detail="Rolul trebuie sa fie 'student' sau 'teacher'!")
    
    print(f"📝 Înregistrare: {user.email} cu rol {user.role}")
    
    try:
        check_response = supabase.table("users").select("*").eq("email", user.email).execute()
        
        if check_response.data and len(check_response.data) > 0:
            print(f"❌ Email deja existent: {user.email}")
            raise HTTPException(status_code=400, detail="Acest email este deja înregistrat!")
        
        user_data = {
            "email": user.email,
            "password_hash": user.password,
            "role": user.role,
            "created_at": datetime.now().isoformat()
        }
        
        response = supabase.table("users").insert(user_data).execute()
        
        if response.data and len(response.data) > 0:
            user_created = response.data[0]
            print(f"✅ Utilizator înregistrat: {user.email} cu rol {user.role}")
            
            return {
                "status": "success",
                "message": "Cont creat cu succes!",
                "user": {
                    "email": user_created.get("email"),
                    "role": user_created.get("role"),
                    "id": user_created.get("id")
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Eroare la salvarea utilizatorului!")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ EROARE: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Eroare la înregistrare: {str(e)}")

# ============================================================
# API - GENERARE TEST
# ============================================================
@app.post("/generate-test")
def generate_test(request: TestRequest):
    selected_types = [t for t in request.exercise_types if t in {"grila", "cod", "scris"}]
    if request.role == "student" and not selected_types:
        selected_types = ["grila", "cod", "scris"]

    questions = []
    try:
        if supabase:
            query = supabase.table("questions").select("*")
            if request.category:
                query = query.ilike("category", f"%{request.category}%")
            query = query.gte("difficulty", request.min_difficulty).lte("difficulty", request.max_difficulty).limit(request.count)
            response = query.execute()
            questions = response.data if response and response.data else []
    except Exception:
        questions = []

    if questions:
        for q in questions:
            q.setdefault("exercise_type", "scris")
        if request.randomize:
            random.shuffle(questions)
        questions = questions[: max(1, min(request.count, len(questions)))]
    else:
        fallback = get_question_bank()
        filtered = [
            q for q in fallback
            if (not request.category or request.category.lower() in q["category"].lower())
            and request.min_difficulty <= q["difficulty"] <= request.max_difficulty
            and (not selected_types or q["exercise_type"] in selected_types)
        ]
        if not filtered:
            filtered = [q for q in fallback if not selected_types or q["exercise_type"] in selected_types]
        if not filtered:
            filtered = fallback
        if request.randomize:
            random.shuffle(filtered)
        questions = filtered[: max(1, min(request.count, len(filtered)))]

    return {"questions": questions, "count": len(questions)}

# ============================================================
# API - COMPILARE COD (păstrează codul existent)
# ============================================================
# ... codul tău de compile ...

# ============================================================
# API - MEETING
# ============================================================
@app.post("/generate-meeting")
def generate_meeting_link(request: MeetingRequest):
    cod_unic = str(uuid.uuid4())[:8]
    nume_curat = request.nume_materie.replace(" ", "")
    room_name = f"BacInfo_{nume_curat}_{cod_unic}"
    meet_link = f"https://meet.jit.si/{room_name}"
    return {
        "status": "Sala a fost creata!",
        "link_intalnire": meet_link,
        "nume_camera": room_name
    }

# ============================================================
# RUTA PENTRU PAGINA DE RESURSE
# ============================================================
@app.get("/resurse")
def serve_resurse():
    return FileResponse(BASE_DIR / "frontend" / "resurse.html", media_type="text/html")

# ============================================================
# API - RESURSE (VERSIUNE SIMPLĂ CU BASE64)
# ============================================================

# ============================================================
# UPLOAD RESURSĂ
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
    
    try:
        valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.txt', '.doc', '.docx', 
                           '.ppt', '.pptx', '.xls', '.xlsx', '.zip', '.cpp', '.c', '.html']
        ext = os.path.splitext(file.filename)[1].lower()
        
        if ext not in valid_extensions:
            raise HTTPException(status_code=400, detail=f"Extensia {ext} nu este acceptată!")
        
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Fișierul este prea mare! Maxim 10 MB.")
        
        file_data = base64.b64encode(content).decode('utf-8')
        
        resource_data = {
            "titlu": titlu,
            "descriere": descriere or "",
            "capitol": capitol,
            "tip": tip,
            "original_name": file.filename,
            "file_data": file_data,
            "dimensiune": len(content),
            "uploaded_by": payload.get("email", "unknown"),
            "vizualizari": 0,
            "uploaded_at": datetime.now().isoformat()
        }
        
        response = supabase.table("resources").insert(resource_data).execute()
        
        if response.data and len(response.data) > 0:
            return {
                "status": "success",
                "message": "Fișierul a fost încărcat cu succes!",
                "resource": response.data[0]
            }
        else:
            raise HTTPException(status_code=500, detail="Eroare la salvarea resursei!")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Eroare upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# LISTEAZĂ RESURSE
# ============================================================
@app.get("/api/resurse")
async def get_resurse(payload: dict = Depends(verify_token)):
    try:
        print("📡 Interogare Supabase pentru resurse...")
        print(f"👤 Utilizator: {payload.get('email')} cu rol {payload.get('role')}")
        
        response = supabase.table("resources").select("*").order("uploaded_at", desc=True).execute()
        
        print(f"📊 Răspuns Supabase: {response}")
        print(f"✅ Resurse găsite: {len(response.data) if response.data else 0}")
        
        return {"resurse": response.data if response.data else []}
    except Exception as e:
        print(f"❌ Eroare la citirea resurselor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ȘTERGE RESURSĂ
# ============================================================
@app.delete("/api/resurse/{file_id}")
async def delete_resource(
    file_id: int,
    payload: dict = Depends(verify_token)
):
    if payload.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Doar profesorii pot șterge resurse!")
    
    try:
        check = supabase.table("resources").select("id").eq("id", file_id).execute()
        if not check.data or len(check.data) == 0:
            raise HTTPException(status_code=404, detail="Resursa nu a fost găsită")
        
        response = supabase.table("resources").delete().eq("id", file_id).execute()
        return {"status": "success", "message": "Resursa a fost ștearsă"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Eroare ștergere: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# DOWNLOAD RESURSĂ
# ============================================================
@app.get("/download-resource-token/{file_id}")
async def download_resource_token(
    file_id: int,
    token: str
):
    """Descarcă resursă folosind token din URL"""
    print(f"📥 Download request pentru ID: {file_id}")
    print(f"🔑 Token primit: {token[:20]}..." if token else "❌ Token lipsă")
    
    try:
        # Verifică token-ul
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"✅ Token valid pentru: {payload.get('email')}")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirat")
    except jwt.InvalidTokenError as e:
        print(f"❌ Token invalid: {e}")
        raise HTTPException(status_code=401, detail="Token invalid")
    
    try:
        # Caută resursa în Supabase
        response = supabase.table("resources").select("*").eq("id", file_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Resursa nu a fost găsită")
        
        resource = response.data[0]
        print(f"📄 Resursă găsită: {resource.get('original_name')}")
        
        # Incrementează vizualizările
        supabase.table("resources").update({
            "vizualizari": resource.get("vizualizari", 0) + 1
        }).eq("id", file_id).execute()
        
        # Decodifică din base64
        file_data = base64.b64decode(resource.get("file_data", ""))
        
        # Determină tipul MIME
        ext = os.path.splitext(resource["original_name"])[1].lower()
        media_type = "application/octet-stream"
        if ext == ".pdf": media_type = "application/pdf"
        elif ext in [".jpg", ".jpeg"]: media_type = "image/jpeg"
        elif ext == ".png": media_type = "image/png"
        elif ext == ".gif": media_type = "image/gif"
        elif ext == ".txt": media_type = "text/plain"
        elif ext in [".cpp", ".c", ".py", ".js", ".html", ".css"]: media_type = "text/plain"
        
        print(f"✅ Returnare fișier: {resource['original_name']} ({len(file_data)} bytes)")
        
        return StreamingResponse(
            BytesIO(file_data),
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename=\"{resource['original_name']}\"",
                "Content-Length": str(len(file_data))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Eroare download: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
# ============================================================
# DOWNLOAD RESURSĂ - ALTERNATIVĂ (CU HEADER)
# ============================================================
# ============================================================
# DOWNLOAD RESURSĂ - CU HEADER
# ============================================================
@app.get("/download-resource/{file_id}")
async def download_resource(
    file_id: int,
    payload: dict = Depends(verify_token)
):
    """Descarcă resursă folosind token din header"""
    print(f"📥 Download resource (header) pentru ID: {file_id}")
    print(f"👤 Utilizator: {payload.get('email')}")
    
    try:
        # Caută resursa în Supabase
        response = supabase.table("resources").select("*").eq("id", file_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Resursa nu a fost găsită")
        
        resource = response.data[0]
        print(f"📄 Resursă găsită: {resource.get('original_name')}")
        
        # Incrementează vizualizările
        supabase.table("resources").update({
            "vizualizari": resource.get("vizualizari", 0) + 1
        }).eq("id", file_id).execute()
        
        # Decodifică din base64
        file_data = base64.b64decode(resource.get("file_data", ""))
        
        # Determină tipul MIME
        ext = os.path.splitext(resource["original_name"])[1].lower()
        media_type = "application/octet-stream"
        if ext == ".pdf": media_type = "application/pdf"
        elif ext in [".jpg", ".jpeg"]: media_type = "image/jpeg"
        elif ext == ".png": media_type = "image/png"
        elif ext == ".gif": media_type = "image/gif"
        elif ext == ".txt": media_type = "text/plain"
        elif ext in [".cpp", ".c", ".py", ".js", ".html", ".css"]: media_type = "text/plain"
        
        return StreamingResponse(
            BytesIO(file_data),
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename=\"{resource['original_name']}\"",
                "Content-Length": str(len(file_data))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Eroare download: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# VIZUALIZARE PDF
# ============================================================
@app.get("/view-pdf/{file_id}")
async def view_pdf(
    file_id: int,
    token: str
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"✅ Vizualizare PDF pentru: {payload.get('email')}")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token invalid")
    
    try:
        response = supabase.table("resources").select("*").eq("id", file_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Resursa nu a fost găsită")
        
        resource = response.data[0]
        
        supabase.table("resources").update({
            "vizualizari": resource.get("vizualizari", 0) + 1
        }).eq("id", file_id).execute()
        
        file_data = base64.b64decode(resource.get("file_data", ""))
        
        return StreamingResponse(
            BytesIO(file_data),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=\"{resource['original_name']}\"",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Eroare vizualizare PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# API - VERIFICĂ TOKEN
# ============================================================
@app.get("/api/verify-token")
def verify_token_endpoint(payload: dict = Depends(verify_token)):
    return {
        "valid": True, 
        "user": {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
    }

# ============================================================
# RUTE PENTRU PAGINI HTML
# ============================================================
@app.get("/")
def serve_root():
    return FileResponse(BASE_DIR / "frontend" / "index.html", media_type="text/html")

@app.get("/login")
def serve_login():
    return FileResponse(BASE_DIR / "frontend" / "index.html", media_type="text/html")

@app.get("/signup")
def serve_signup():
    return FileResponse(BASE_DIR / "frontend" / "register.html", media_type="text/html")

@app.get("/dashboard")
def serve_dashboard():
    return FileResponse(BASE_DIR / "frontend" / "dashboard.html", media_type="text/html")

@app.get("/editor")
def serve_editor():
    return FileResponse(BASE_DIR / "frontend" / "editor.html", media_type="text/html")

@app.get("/meeting")
def serve_meeting():
    return FileResponse(BASE_DIR / "frontend" / "meeting.html", media_type="text/html")

@app.get("/tests")
def serve_tests():
    return FileResponse(BASE_DIR / "frontend" / "tests.html", media_type="text/html")

@app.get("/creator")
def serve_creator():
    return FileResponse(BASE_DIR / "frontend" / "creator.html", media_type="text/html")

# ============================================================
# TEST SUPABASE
# ============================================================
@app.get("/test-supabase")
def test_supabase():
    try:
        if supabase:
            response = supabase.table("users").select("*").limit(1).execute()
            return {"status": "✅ Conexiune Supabase funcționează!", "data": response.data}
        else:
            return {"status": "❌ Supabase nu este conectat!"}
    except Exception as e:
        return {"status": "❌ Eroare Supabase:", "error": str(e)}
    
# ============================================================
# DEBUG - VERIFICĂ TOKEN-UL
# ============================================================
@app.get("/debug-token")
async def debug_token(token: str = None):
    """Verifică dacă token-ul este valid"""
    if not token:
        return {"error": "Token lipsă", "suggestion": "Adaugă ?token=..."}
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"valid": True, "payload": payload}
    except Exception as e:
        return {"valid": False, "error": str(e)}

# ============================================================
# PORNIRE APLICAȚIE
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)