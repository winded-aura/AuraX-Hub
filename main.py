from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from luaparser import ast, astnodes
import random
import string

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str

PROTECTED_GLOBALS = ["game", "workspace", "script", "print", "wait", "task", "math", "string", "table", "pairs", "ipairs", "require", "Enum", "Instance", "Vector3", "CFrame", "Color3", "UDim2", "Health", "RunService"]

def generate_random_name():
    hex_chars = "0123456789abcdef"
    return "_0x" + "".join(random.choice(hex_chars) for _ in range(6))

stored_payloads = {}

def advanced_fallback(source_code, key=42):
    encrypted_bytes = [b ^ key for b in source_code.encode('utf-8')]
    hex_str = "".join(f"\\x{b:02x}" for b in encrypted_bytes)
    # We voegen een print toe zodat je ZEKER weet dat de code is geladen!
    lua_script = f'print("[Obfuscator] Script loaded!") local s="{hex_str}" local t={{}} for i=1,#s do t[i]=string.char(bit32.bxor(s:byte(i),{key})) end (loadstring or load)(table.concat(t))()'
    return lua_script

def obfuscate_lua(source_code: str):
    try:
        tree = ast.parse(source_code)
        name_mapping = {}

        for node in ast.walk(tree):
            if isinstance(node, astnodes.LocalAssign):
                for target in node.targets:
                    if isinstance(target, astnodes.Name):
                        orig_name = target.id
                        if orig_name not in PROTECTED_GLOBALS:
                            if orig_name not in name_mapping:
                                name_mapping[orig_name] = generate_random_name()
                            target.id = name_mapping[orig_name]
            
            elif isinstance(node, astnodes.Name):
                orig_name = node.id
                if orig_name not in PROTECTED_GLOBALS:
                    if orig_name not in name_mapping:
                        name_mapping[orig_name] = generate_random_name()
                    node.id = name_mapping[orig_name]
                    
            elif isinstance(node, astnodes.Function):
                for arg in node.args:
                    if isinstance(arg, astnodes.Name):
                        orig_name = arg.id
                        if orig_name not in PROTECTED_GLOBALS:
                            if orig_name not in name_mapping:
                                name_mapping[orig_name] = generate_random_name()
                            arg.id = name_mapping[orig_name]

        parsed_code = ast.to_lua_source(tree)
        return 'print("[Obfuscator] Script loaded!")\n' + parsed_code

    except Exception:
        return advanced_fallback(source_code)

@app.post("/api/obfuscate")
def obfuscate(request: CodeRequest):
    obfuscated_code = obfuscate_lua(request.code)
    payload_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    stored_payloads[payload_id] = obfuscated_code
    
    # ==== DE SIMPELE LOADSTRING (Zoals je wilde) ====
    loader_script = f"loadstring(game:HttpGet('http://127.0.0.1:8000/loader/{payload_id}'))()"
    
    return {"success": True, "code": loader_script}

@app.get("/loader/{payload_id}")
def get_loader(payload_id: str):
    if payload_id in stored_payloads:
        return stored_payloads[payload_id]
    return "print('Script niet gevonden of server is uit!')"