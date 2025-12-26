from fastapi import FastAPI, File, Form, UploadFile, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import ast
from pathlib import Path
import asyncio
import datetime
import re
import os
import json

from database import SessionLocal, engine, Base
from dynamic import Authenticate, Projects, Details
from sqlalchemy import text

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database initialized")
    except Exception as e:
        print(f"⚠ Database connection issue (non-critical): {e}")
        print("✓ Application will continue without database")

UPLOAD_FOLDER = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".py", ".java"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def validate_file(filename: str) -> Tuple[bool, str]:
    if not filename:
        return False, "Empty filename"
    name = Path(filename).name
    if ".." in name or name.startswith("."):
        return False, "Invalid filename"
    if Path(name).suffix.lower() not in ALLOWED_EXTENSIONS:
        return False, "Only .py and .java files"
    return True, name


def extract_functions_from_code(code: str, file_path: str) -> List[Dict]:
    """
    Extract individual functions from Python code using AST
    Returns list of function dictionaries with code, name, and metadata
    """
    functions = []
    try:
        tree = ast.parse(code, filename=file_path)
        source_lines = code.splitlines()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get function source code
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 10
                function_code = '\n'.join(source_lines[start_line:end_line])
                
                # Get function signature
                args = [arg.arg for arg in node.args.args]
                
                # Get docstring
                docstring = ast.get_docstring(node) or ""
                
                functions.append({
                    "name": node.name,
                    "code": function_code,
                    "args": args,
                    "docstring": docstring,
                    "line_start": node.lineno,
                    "line_end": node.end_lineno if hasattr(node, 'end_lineno') else None
                })
    except Exception as e:
        print(f"Error extracting functions: {e}")
    
    return functions

def analyze_java_code(code: str):
    """
    Analyze Java code using Regex patterns (since AST is Python specific)
    """
    stats = {
        "functions": 0, 
        "variables": 0, 
        "classes": 0, 
        "imports": 0, 
        "lines": 0, 
        "complexity": 0, 
        "FOR": 0, 
        "database": [], 
        'database_name': [], 
        'time_complexity': 'O(1)',
        'file_bytes': '',
        'function_details': []
    }
    
    try:
        # Basic stats
        stats["lines"] = len(code.splitlines())
        
        # Classes: class ClassName
        stats["classes"] = len(re.findall(r'\bclass\s+\w+', code))
        
        # Methods: simplified regex for method detection
        # public/private/protected void/Type name(args) {
        method_pattern = r'(public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\) *(\{?|[^;])'
        matches = re.findall(method_pattern, code)
        stats["functions"] = len(matches)
        
        # Capture function details (approximate)
        for match in matches:
            stats['function_details'].append({
                "name": match[1],
                "args": [],  
                "docstring": "",
                "line_start": 0, 
                "line_end": 0
            })
            
        # Variables (approximate)
        stats["variables"] = len(re.findall(r'\b(int|String|boolean|double|float|long|char|List|Map|Set)\s+\w+', code))
        
        # Imports
        stats["imports"] = len(re.findall(r'import\s+[\w\.]+', code))
        
        # Loops
        stats["FOR"] = len(re.findall(r'\bfor\s*\(', code)) + len(re.findall(r'\bwhile\s*\(', code))
        
        # DB Connections
        if "DriverManager.getConnection" in code or "DataSource" in code:
            stats["database"].append("JDBC")
            
        if "EntityManager" in code or "@Entity" in code:
             stats["database"].append("JPA/Hibernate")

        # DB Name (simple heuristic)
        db_match = re.search(r'jdbc:[\w]+://[^/]+/(\w+)', code)
        if db_match:
            stats['database_name'].append(db_match.group(1))

        # Complexity Estimation
        if re.search(r'for\s*\(.*for\s*\(.*for\s*\(', code, re.DOTALL):
            stats['time_complexity'] = "O(n³)"
        elif re.search(r'for\s*\(.*for\s*\(', code, re.DOTALL):
            stats['time_complexity'] = "O(n²)"
        elif stats["FOR"] > 0:
            stats['time_complexity'] = "O(n)"
        else:
             stats['time_complexity'] = "O(1)"
             
    except Exception as e:
        print(f"Error analyzing Java code: {e}")
        
    return stats

async def analyze_code(file_path: str):
    def parse(path: str):
        start = datetime.datetime.now() 
        stats = {
            "functions": 0, 
            "variables": 0, 
            "classes": 0, 
            "imports": 0, 
            "lines": 0, 
            "complexity": 0, 
            "FOR": 0, 
            "database": [], 
            'database_name': [], 
            'time_complexity': 'O(1)',
            'file_bytes': '',
            'function_details': []  # Store detailed function analysis
        }
        errors = []
        
        try:
            is_python = path.endswith('.py')
            
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            
            # Common file size calc
            file_size = os.path.getsize(path)
            if file_size <= 1024:
                ranges = f'{file_size} B'
            elif file_size > 1024 and file_size <= (1024 * 1024):
                ranges = f'{file_size / 1024:.2f} KB'
            else:
                ranges = f'{file_size / (1024 * 1024):.2f} MB'
            
            if not is_python:
                # Java Or other logic
                stats = analyze_java_code(code)
                stats['file_bytes'] = ranges
                stats["complexity"] = (datetime.datetime.now() - start).total_seconds()
                return stats, errors

            stats["lines"] = len(code.splitlines())
            
            stats['file_bytes'] = ranges
            
            keywords = ["mysql.connector.connect", "sqlite3.connect", "psycopg2.connect"]
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', code):
                    stats['database'].append(kw)
            
            def detect_db_name(code):
                match = re.search(
                    r"mysql\.connector\.connect\([^)]*database\s*=\s*['\"]([\w]+)['\"]",
                    code, re.DOTALL)
                if match:
                    return match.group(1)
                
                match = re.search(r"sqlite3\.connect\(\s*['\"]([\w\.-]+)['\"]\s*\)", code)
                if match:
                    return match.group(1)
                
                match = re.search(
                    r"psycopg2\.connect\([^)]*database\s*=\s*['\"]([\w]+)['\"]",
                    code, re.DOTALL)
                if match:
                    return match.group(1)
                
                return None
            
            db_name = detect_db_name(code)
            if db_name:
                stats['database_name'].append(db_name)
            
            tree = ast.parse(code, filename=path)
            

            def detect_time_complexity(tree):
                
                max_nesting = 0
                has_recursion = False
                
                def get_loop_depth(node, current_depth=0):
                    nonlocal max_nesting
                    
                    if isinstance(node, (ast.For, ast.While)):
                        current_depth += 1
                        max_nesting = max(max_nesting, current_depth)
                    
                    for child in ast.iter_child_nodes(node):
                        get_loop_depth(child, current_depth)
                
                def check_recursion(node):
                    nonlocal has_recursion
                    
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        for child in ast.walk(node):
                            if isinstance(child, ast.Call):
                                if isinstance(child.func, ast.Name) and child.func.id == func_name:
                                    has_recursion = True
                                    return
                
                for node in ast.walk(tree):
                    check_recursion(node)
                
                get_loop_depth(tree)
                
                if has_recursion:
                    return "O(2^n)"
                elif max_nesting == 0:
                    return "O(1)"
                elif max_nesting == 1:
                    return "O(n)"
                elif max_nesting == 2:
                    return "O(n²)"
                elif max_nesting == 3:
                    return "O(n³)"
                else:
                    return f"O(n^{max_nesting})"
            
            stats['time_complexity'] = detect_time_complexity(tree)
            
            # Extract and analyze functions
            extracted_functions = extract_functions_from_code(code, path)
            stats["functions"] = len(extracted_functions)
            
            # Store function details
            for func in extracted_functions:
                stats['function_details'].append({
                    "name": func["name"],
                    "args": func["args"],
                    "docstring": func["docstring"],
                    "line_start": func["line_start"],
                    "line_end": func["line_end"]
                })
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    stats["classes"] += 1
                elif isinstance(node, ast.For):
                    stats["FOR"] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    stats["imports"] += 1
                elif isinstance(node, ast.Assign):
                    stats["variables"] += 1
        except SyntaxError as e:
            errors.append(f"Syntax Error: line {e.lineno}")
        except Exception as e:
            errors.append(f"Error: {str(e)}")
        
        stats["complexity"] = (datetime.datetime.now() - start).total_seconds()
        return stats, errors
    
    # Run basic parsing
    stats, errors = await asyncio.to_thread(parse, file_path)
    
    return stats, errors

def find_main_file(paths: List[str]) -> Tuple[List[str], List[str]]:
    main_files, other_files = [], []
    for path in paths:
        if path.endswith('.java'):
            try:
                with open(path, "r") as f:
                    code = f.read()
                if "public static void main" in code:
                    main_files.append(path)
                else:
                    other_files.append(path)
            except:
                other_files.append(path)
            continue

        try:
            with open(path, "r") as f:
                code = f.read()
            tree = ast.parse(code)
            has_main = any(
                isinstance(node, ast.If) and
                isinstance(node.test, ast.Compare) and
                isinstance(node.test.left, ast.Name) and
                node.test.left.id == "__name__"
                for node in ast.walk(tree)
            )
            (main_files if has_main else other_files).append(path)
        except:
            other_files.append(path)
    return other_files, main_files

@app.get('/')
def root():
    """Root endpoint - redirects to home page"""
    return RedirectResponse(url='/home', status_code=303)

@app.get('/home', response_class=HTMLResponse)
def home(request: Request):
    """Home page"""
    return templates.TemplateResponse('home.html', {'request': request})

@app.get('/health')
def health_check():
    """Health check endpoint for API monitoring"""
    try:
        # Quick database check
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": "disconnected", "error": str(e)}

@app.get('/login', response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse('front.html', {'request': request})

@app.get('/signup', response_class=HTMLResponse)
def signup(request: Request):
    return templates.TemplateResponse('create.html', {'request': request})

@app.post('/register', response_class=HTMLResponse)
def register(request: Request, name: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Validate input
        if not name or not name.strip():
            return templates.TemplateResponse('create.html', {
                'request': request,
                'message': 'Username cannot be empty'
            })
        
        if not password:
            return templates.TemplateResponse('create.html', {
                'request': request,
                'msg': 'Password is required'
            })
        
        if len(password) < 4:
            return templates.TemplateResponse('create.html', {
                'request': request,
                'msg': 'Password min 4 chars'
            })
        
        # Check if user exists
        if db.query(Authenticate).filter(Authenticate.name == name.strip()).first():
            return templates.TemplateResponse('create.html', {
                'request': request,
                'message': 'Username exists'
            })
        
        # Create new user
        user = Authenticate(name=name.strip(), password=pwd_context.hash(password))
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return templates.TemplateResponse('front.html', {
            'request': request,
            'success': 'Account created!'
        })
    except Exception as e:
        db.rollback()
        print(f"Registration error: {e}")
        return templates.TemplateResponse('create.html', {
            'request': request,
            'message': f'Registration failed: {str(e)}'
        })

@app.post('/authenticate', response_class=HTMLResponse)
def authenticate(request: Request, name: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        user = db.query(Authenticate).filter(Authenticate.name == name).first()
        
        if not user:
            return templates.TemplateResponse('front.html', {
                'request': request,
                'error': 'User not found'
            })
        
        if not pwd_context.verify(password, user.password):
            return templates.TemplateResponse('front.html', {
                'request': request,
                'errors_password': 'Wrong password'
            })
        
        data = user.id  
        return templates.TemplateResponse('index.html', {
            'request': request,
            'username': name,
            'user_id': data 
        })
    
    except Exception as e:
        print(f"Authentication error: {e}")
        return templates.TemplateResponse('front.html', {
            'request': request,
            'error': f'Authentication failed: {str(e)}'
        })

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    files: List[UploadFile] = File(...),
    project_name: str = Form(...),
    username: str = Form('User'),
    user_id: int = Form(None),
    db: Session = Depends(get_db)
):
    """Analyze uploaded Python files and generate code statistics"""
    saved_files = []
    errors = []

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    for file in files:
        if not file.filename:
            errors.append("Empty filename provided")
            continue
            
        valid, result = validate_file(file.filename)
        if not valid:
            errors.append(f"{file.filename}: {result}")
            continue

        try:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                errors.append(f"{file.filename}: Too large (max {MAX_FILE_SIZE} bytes)")
                continue

            path = os.path.join(UPLOAD_FOLDER, result)
            with open(path, "wb") as f:
                f.write(content)
            saved_files.append(path)
        except Exception as e:
            errors.append(f"{file.filename}: Upload error - {str(e)}")
            continue

    if not saved_files:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "No files uploaded",
            "username": username,
            "user_id": user_id
        })

    try:
        sub, main = find_main_file(saved_files)

        results_main = {"main_file": [], "total_files": 0, "stats": {}, "errors": {}}
        if main:
            tasks = [analyze_code(p) for p in main]
            results = await asyncio.gather(*tasks)
            for i, (stats, errs) in enumerate(results, 1):
                results_main["stats"][f"main_file{i}"] = stats
                results_main["errors"][f"main_file{i}"] = errs
            results_main["main_file"] = [Path(p).name for p in main]
            results_main["total_files"] = len(main)

        results_sub = {"sub_files": [], "total_files": 0, "stats": {}, "errors": {}}
        if sub:
            tasks = [analyze_code(p) for p in sub]
            results = await asyncio.gather(*tasks)
            for i, (stats, errs) in enumerate(results, 1):
                results_sub["stats"][f"subfile{i}"] = stats
                results_sub["errors"][f"subfile{i}"] = errs
            results_sub["sub_files"] = [Path(p).name for p in sub]
            results_sub["total_files"] = len(sub)

        files_list = {"file_list": [Path(f).name for f in saved_files]}

        # Save project to database
        try:
            register = Projects(user_id=user_id, project_name=project_name)
            db.add(register)
            db.commit()
            db.refresh(register)
        except Exception as e:
            db.rollback()
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": f"Failed to save project: {str(e)}",
                "username": username,
                "user_id": user_id
            })
        
        # Prepare data for storage
        fetch = {
            "results_main": results_main,
            "results_sub": results_sub,
            "files_list": files_list,
            "upload_errors": errors,
            "project_name": project_name,
            "username": username,
            "user_id": user_id,
            "project_id": register.id
        }
        
        # Save project details to database
        try:
            # Test serialization to catch any issues
            json.dumps(fetch, default=str)
            # Pass dict directly to JSONB column
            detail = Details(project_id=register.id, data=fetch)
        except (TypeError, ValueError) as e:
            # Fallback: convert to JSON string if direct dict fails
            print(f"Warning: Converting data to JSON string due to serialization issue: {e}")
            dates = json.dumps(fetch, default=str)
            detail = Details(project_id=register.id, data=json.loads(dates))
        
        try:
            db.add(detail)
            db.commit()
            db.refresh(detail)
        except Exception as e:
            db.rollback()
            print(f"Warning: Failed to save project details: {e}")
            # Continue anyway - project is saved, just details failed

        return templates.TemplateResponse("results.html", {
            "request": request,
            "results_main": results_main,
            "results_sub": results_sub,
            "files_list": files_list,
            "upload_errors": errors,
            "project_name": project_name,
            "username": username,
            "user_id": user_id,
            "project_id": register.id
        })
    
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Analysis failed: {str(e)}",
            "username": username,
            "user_id": user_id
        })

@app.get('/logout')
def logout():
    return RedirectResponse(url='/', status_code=303)


def normalize_project_data(raw):
    """Normalize raw project data into a clean structure"""
    cleaned = {
        "project_name": raw.get("project_name", "Unknown"),
        "user_name": raw.get("username", raw.get("user_name", "Unknown")),
        "user_id": raw.get("user_id", ""),
        "project_id": raw.get("project_id", ""),
        "main_files": [],
        "sub_files": [],
        "all_files": raw.get("files_list", {}).get("file_list", []),
        "upload_errors": raw.get("upload_errors", []),
    }

    # ---------------- Main File Section ----------------
    main = raw.get("results_main", {}) or raw.get("result_main", {})
    main_files = main.get("main_file", [])
    main_stats = main.get("stats", {})

    for i, file_name in enumerate(main_files, start=1):
        stat_key = f"main_file{i}"
        stats = main_stats.get(stat_key, {})

        cleaned["main_files"].append({
            "file_name": file_name,
            "functions": stats.get("functions", 0),
            "variables": stats.get("variables", 0),
            "classes": stats.get("classes", 0),
            "imports": stats.get("imports", 0),
            "lines": stats.get("lines", 0),
            "complexity": stats.get("complexity", 0),
            "loops": stats.get("FOR", 0),
            "database_calls": stats.get("database", []),
            "database_name": stats.get("database_name", []),
            "time_complexity": stats.get("time_complexity", ""),
            "file_bytes": stats.get("file_bytes", ""),
            "function_details": stats.get("function_details", [])
        })

    # ---------------- Sub File Section ----------------
    sub = raw.get("results_sub", {}) or raw.get("result_sub", {})
    sub_files = sub.get("sub_files", [])
    sub_stats = sub.get("stats", {})

    for i, file_name in enumerate(sub_files, start=1):
        stat_key = f"subfile{i}"
        stats = sub_stats.get(stat_key, {})

        cleaned["sub_files"].append({
            "file_name": file_name,
            "functions": stats.get("functions", 0),
            "variables": stats.get("variables", 0),
            "classes": stats.get("classes", 0),
            "imports": stats.get("imports", 0),
            "lines": stats.get("lines", 0),
            "complexity": stats.get("complexity", 0),
            "loops": stats.get("FOR", 0),
            "database_calls": stats.get("database", []),
            "database_name": stats.get("database_name", []),
            "time_complexity": stats.get("time_complexity", ""),
            "file_bytes": stats.get("file_bytes", ""),
            "function_details": stats.get("function_details", [])
        })


    return cleaned

@app.get("/final/{store}", response_class=HTMLResponse)
async def final_page(request: Request, store: int, db: Session = Depends(get_db)):
    """Display all projects for a user"""
    try:
        # Validate user_id
        if not store or store <= 0:
            return templates.TemplateResponse(
                "final.html",
                {
                    "request": request,
                    "table_html": "<p>Invalid user ID</p>",
                    "saved": {},
                    "error_message": "Invalid user ID"
                }
            )

        # Fetch ALL projects for this user (not just the first one)
        projects = db.query(Projects).filter(Projects.user_id == store).order_by(Projects.id.desc()).all()

        if not projects:
            return templates.TemplateResponse(
                "final.html",
                {
                    "request": request,
                    "table_html": "<p>No data found</p>",
                    "saved": {},
                    "error_message": "No projects found for this user"
                }
            )

        # Fetch JSON details for ALL projects
        all_projects = []
        
        for project in projects:
            # Fetch details for each project
            details = db.query(Details).filter(Details.project_id == project.id).order_by(Details.id.desc()).first()
            
            if details and details.data:
                try:
                    # Parse the JSON data
                    if isinstance(details.data, str):
                        project_data = json.loads(details.data)
                    elif isinstance(details.data, dict):
                        project_data = details.data
                    else:
                        project_data = json.loads(str(details.data))
                    
                    # Normalize the project data
                    normalized = normalize_project_data(project_data)
                    # Ensure project_id and project_name are set
                    normalized['project_id'] = project.id
                    normalized['project_name'] = project.project_name
                    all_projects.append(normalized)
                except Exception as e:
                    print(f"Error parsing Details.data for project {project.id}: {e}")
                    # Continue to next project even if one fails
                    continue

        if not all_projects:
            return templates.TemplateResponse(
                "final.html",
                {
                    "request": request,
                    "table_html": "<p>No data found</p>",
                    "saved": {},
                    "error_message": "No project data available"
                }
            )

        # Prepare data for template
        saved_data = {
            "projects": all_projects,
            "total_projects": len(all_projects),
            "user_id": store
        }

        # Return template response
        return templates.TemplateResponse(
            "final.html",
            {
                "request": request,
                "table_html": "",
                "saved": saved_data,
                "projects": all_projects
            }
        )

    except Exception as e:
        import traceback
        traceback.print_exc()

        return HTMLResponse(
            f"<h1>Error</h1><pre>{str(e)}</pre>",
            status_code=500
        )
