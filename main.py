from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
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
from datetime import datetime, timedelta
import jwt

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
        "https://proinfobac.vercel.app",  # URL-ul tău Vercel
        "https://proinfobac.onrender.com",  # URL-ul tău Render
        "*"  # Pentru testare, dar în producție pune URL-urile exacte
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
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 ore

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
# API - USER (returnează utilizatorul autentificat)
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
# API - COMPILARE COD
# ============================================================
@app.post("/compile")
def compile_and_run(submission: CodeSubmission):
    def dbg(msg):
        try:
            with open('compile_debug.log', 'a', encoding='utf-8') as lf:
                lf.write(msg + '\n')
        except Exception:
            pass
    
    dbg('=== compile_and_run start')
    payload = {
        "language": submission.language,
        "version": "10.2.0",
        "files": [
            {
                "name": "main.cpp",
                "content": submission.code
            }
        ],
        "stdin": submission.stdin or ""
    }

    try:
        response = None
        data = None
        try:
            dbg('calling piston')
            response = requests.post("https://emkc.org/api/v2/piston/execute", json=payload, timeout=0)
            try:
                data = response.json()
            except ValueError:
                data = None
                dbg('piston returned invalid json')
        except requests.RequestException as exc:
            dbg(f'piston request failed: {exc}')
        except Exception as exc:
            dbg(f'piston unexpected exception: {exc}')

        response_status = response.status_code if response is not None else None
        dbg(f'piston status={response_status}')

        if response is not None and response.ok and data and "run" in data:
            run_info = data["run"]
            if run_info.get("code", 0) != 0 and not run_info.get("stdout") and not run_info.get("stderr"):
                return {"output": "", "error": "", "exit_code": run_info.get("code", 0), "piston_payload": data}
            else:
                return {
                    "output": run_info.get("stdout", ""),
                    "error": run_info.get("stderr", ""),
                    "exit_code": run_info.get("code", 0)
                }

        if response is None or response_status == 401 or (data and isinstance(data.get("message"), str) and "whitelist" in data.get("message").lower()) or (response is not None and not response.ok):
            dbg('piston unusable or whitelist - falling back to local compile')
            import shutil, subprocess, tempfile, os

            gpp = shutil.which("g++")
            msys_gpp = r"C:\\msys64\\mingw64\\bin\\g++.exe"
            dbg(f'located gpp={gpp} msys_gpp_exists={os.path.exists(msys_gpp)}')
            if not gpp and os.path.exists(msys_gpp):
                gpp = msys_gpp
            msys_bin = os.path.dirname(gpp) if gpp and os.path.isabs(gpp) else None

            if not gpp:
                raise HTTPException(status_code=502, detail="Piston API refuză accesul și nu a fost găsit 'g++' local.")

            with tempfile.TemporaryDirectory() as td:
                cpp_file = os.path.join(td, "main.cpp")
                exe_file = os.path.join(td, "main.exe")
                with open(cpp_file, "w", encoding="utf-8") as f:
                    f.write(submission.code)

                compile_env = os.environ.copy()
                if msys_bin:
                    compile_env['PATH'] = msys_bin + os.pathsep + compile_env.get('PATH', '')
                src_name = os.path.basename(cpp_file)
                out_name = os.path.basename(exe_file)
                compile_proc = subprocess.run([gpp, src_name, "-std=c++17", "-O2", "-o", out_name], capture_output=True, text=True, timeout=30, env=compile_env, cwd=td)
                
                if compile_proc.returncode != 0:
                    dbg('compile failed')
                    return {"output": "", "error": compile_proc.stderr, "exit_code": compile_proc.returncode}

                run_env = os.environ.copy()
                msys_bin = os.path.dirname(gpp) if os.path.isabs(gpp) else None
                if msys_bin and msys_bin not in run_env.get('PATH', ''):
                    run_env['PATH'] = msys_bin + os.pathsep + run_env.get('PATH', '')

                try:
                    run_proc = subprocess.run([exe_file], input=submission.stdin or "", capture_output=True, text=True, timeout=10, env=run_env, cwd=td)
                    return {"output": run_proc.stdout, "error": run_proc.stderr, "exit_code": run_proc.returncode}
                except OSError as oe:
                    try:
                        wsl = shutil.which('wsl') or os.path.exists(r'C:\\Windows\\System32\\wsl.exe')
                    except Exception:
                        wsl = None

                    if wsl:
                        def win_to_wsl(p: str) -> str:
                            drive, rest = os.path.splitdrive(p)
                            if not drive:
                                return p.replace('\\\\', '/')
                            drive_letter = drive.rstrip(':').lower()
                            rest = rest.replace('\\', '/')
                            return f"/mnt/{drive_letter}{rest}"

                        wsl_cpp = win_to_wsl(cpp_file)
                        wsl_out = win_to_wsl(os.path.join(td, "main.out"))
                        wsl_cmd = f'g++ "{wsl_cpp}" -std=c++17 -O2 -o "{wsl_out}" && "{wsl_out}"'
                        try:
                            wproc = subprocess.run(["wsl", "bash", "-lc", wsl_cmd], capture_output=True, text=True, timeout=30)
                            return {"output": wproc.stdout, "error": wproc.stderr, "exit_code": wproc.returncode}
                        except Exception as wex:
                            raise HTTPException(status_code=502, detail=f"Exec blocked on Windows (OSError: {oe}) and WSL fallback failed: {str(wex)}")

                    raise HTTPException(status_code=502, detail=f"Exec blocked on Windows (OSError: {oe}).")

        raise HTTPException(status_code=502, detail={"status_code": response.status_code, "response": data or response.text})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare la comunicarea cu compilatorul: {str(e)}")

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
# API - RESURSE (UPLOAD FIȘIERE) - CU AUTENTIFICARE
# ============================================================
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ============================================================
# RUTA PENTRU PAGINA DE RESURSE - CU AUTENTIFICARE
# ============================================================
@app.get("/resurse")
def serve_resurse():
    resurse_path = BASE_DIR / "frontend" / "resurse.html"
    if resurse_path.exists():
        return FileResponse(resurse_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Pagina resurse.html nu a fost găsită")

@app.get("/resurse.html")
def serve_resurse_html():
    resurse_path = BASE_DIR / "frontend" / "resurse.html"
    if resurse_path.exists():
        return FileResponse(resurse_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Pagina resurse.html nu a fost găsită")

# ============================================================
# UPLOAD RESURSĂ - CU AUTENTIFICARE ȘI VERIFICARE ROL
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
    """Upload resursă - necesită autentificare și rol de profesor"""
    # Verifică dacă utilizatorul este profesor
    if payload.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Doar profesorii pot încărca resurse!")
    
    try:
        valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.txt', '.doc', '.docx', 
                           '.ppt', '.pptx', '.xls', '.xlsx', '.zip', '.cpp', '.c', '.html']
        ext = os.path.splitext(file.filename)[1].lower()
        
        if ext not in valid_extensions:
            raise HTTPException(status_code=400, detail=f"Extensia {ext} nu este acceptată!")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{file.filename}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Salvează fișierul
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Citește metadatele existente
        metadata_file = UPLOAD_DIR / "metadata.json"
        metadata = []
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        
        # Adaugă noua resursă
        new_resource = {
            "id": len(metadata) + 1,
            "titlu": titlu,
            "descriere": descriere or "",
            "capitol": capitol,
            "tip": tip,
            "filename": unique_filename,
            "original_name": file.filename,
            "data_incarcare": datetime.now().isoformat(),
            "dimensiune": os.path.getsize(file_path),
            "vizualizari": 0,
            "uploaded_by": payload.get("email", "unknown"),
            "uploader_role": payload.get("role", "unknown")
        }
        
        metadata.append(new_resource)
        
        # Salvează metadatele
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "message": "Fișierul a fost încărcat cu succes!",
            "filename": unique_filename,
            "id": len(metadata),
            "resource": new_resource
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Eroare upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# LISTEAZĂ RESURSE - CU AUTENTIFICARE
# ============================================================
@app.get("/api/resurse")
async def get_resurse(payload: dict = Depends(verify_token)):
    """Listează toate resursele - necesită autentificare"""
    try:
        metadata_file = UPLOAD_DIR / "metadata.json"
        if not metadata_file.exists():
            return {"resurse": []}
        
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        # Adaugă informații despre utilizatorul curent
        return {
            "resurse": metadata,
            "current_user": {
                "email": payload.get("email"),
                "role": payload.get("role")
            }
        }
    except Exception as e:
        print(f"❌ Eroare la citirea resurselor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ȘTERGE RESURSĂ - CU AUTENTIFICARE ȘI VERIFICARE ROL
# ============================================================
@app.delete("/api/resurse/{file_id}")
async def delete_resource(
    file_id: int,
    payload: dict = Depends(verify_token)
):
    """Șterge resursă - necesită autentificare și rol de profesor"""
    # Verifică dacă utilizatorul este profesor
    if payload.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Doar profesorii pot șterge resurse!")
    
    try:
        metadata_file = UPLOAD_DIR / "metadata.json"
        if not metadata_file.exists():
            raise HTTPException(status_code=404, detail="Metadatele nu au fost găsite")
        
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        # Găsește și elimină resursa
        resource = None
        for i, r in enumerate(metadata):
            if r["id"] == file_id:
                resource = metadata.pop(i)
                break
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resursa nu a fost găsită")
        
        # Șterge fișierul fizic
        file_path = UPLOAD_DIR / resource["filename"]
        if file_path.exists():
            os.remove(file_path)
            print(f"🗑️ Fișier șters: {resource['filename']}")
        
        # Salvează metadatele actualizate
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success", 
            "message": "Resursa a fost ștearsă",
            "deleted_resource": resource
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Eroare ștergere: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# DOWNLOAD RESURSĂ - CU AUTENTIFICARE
# ============================================================
# ============================================================
# DOWNLOAD RESURSĂ - CU AUTENTIFICARE (acceptă token și din query)
# ============================================================
# ============================================================
# DOWNLOAD RESURSĂ - CU AUTENTIFICARE
# ============================================================
@app.get("/download-resource/{file_id}")
async def download_resource(
    file_id: int,
    token: Optional[str] = None,  # Acceptă token din query params
    authorization: Optional[str] = None  # Acceptă token din header
):
    """Descarcă resursă - necesită autentificare"""
    
    # Verifică token-ul: mai întâi din header, apoi din query
    final_token = None
    
    # Verifică header-ul Authorization
    if authorization and authorization.startswith("Bearer "):
        final_token = authorization.replace("Bearer ", "")
    elif token:
        final_token = token
    
    if not final_token:
        # Verifică și în request headers direct
        try:
            from fastapi import Request
            request = Request
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                final_token = auth_header.replace("Bearer ", "")
        except:
            pass
    
    if not final_token:
        raise HTTPException(status_code=401, detail="Token lipsă")
    
    # Validează token-ul
    try:
        payload = jwt.decode(final_token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"✅ Token valid pentru user: {payload.get('email')} cu rol {payload.get('role')}")
    except jwt.PyJWTError as e:
        print(f"❌ Token invalid: {e}")
        raise HTTPException(status_code=401, detail="Token invalid sau expirat")
    
    try:
        metadata_file = UPLOAD_DIR / "metadata.json"
        if not metadata_file.exists():
            raise HTTPException(status_code=404, detail="Metadatele nu au fost găsite")
        
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        resource = None
        for r in metadata:
            if r["id"] == file_id:
                resource = r
                break
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resursa nu a fost găsită")
        
        file_path = UPLOAD_DIR / resource["filename"]
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Fișierul nu a fost găsit pe server")
        
        resource["vizualizari"] += 1
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return FileResponse(
            path=file_path,
            filename=resource["original_name"],
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Eroare download: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
# ============================================================
# API - VERIFICĂ TOKEN
# ============================================================
@app.get("/api/verify-token")
def verify_token_endpoint(payload: dict = Depends(verify_token)):
    """Verifică dacă token-ul este valid"""
    return {
        "valid": True, 
        "user": {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
    }

# ============================================================
# RUTE PENTRU PAGINI HTML (NEPROTEJATE)
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

# ============================================================
# RUTE PENTRU PAGINI HTML (PROTEJATE)
# ============================================================
@app.get("/dashboard")
def serve_dashboard():
    """Dashboard - pagina HTML este accesibilă, dar conținutul se încarcă prin API"""
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
# PORNIRE APLICAȚIE
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)