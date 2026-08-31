"""Bounded deterministic GLB standardization for already-normalized static props.

The separate img2threejs-to-static-projection seam is intentionally not implemented here.
"""
from __future__ import annotations
import hashlib, json, math, re, struct
from pathlib import Path
from typing import Any, Mapping

CAPABILITY_ID = "game.three.asset.static_glb_standardize"
CAPABILITY_VERSION = "1.0.0"
STATIC_CONTRACT = "p2p-static-glb-asset/1"
SUPPORTED_MATERIALS = {"MeshBasicMaterial", "MeshLambertMaterial", "MeshPhongMaterial", "MeshStandardMaterial"}
_NAME = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")
class StaticGlbError(ValueError): pass

def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value): raise StaticGlbError(f"{field}: finite number required")
    return float(value)
def _vec(value: Any, field: str, n=3) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != n: raise StaticGlbError(f"{field}: {n} numbers required")
    return [_number(x, field) for x in value]
def _align(data: bytes, fill=b"\0") -> bytes: return data + fill * ((4 - len(data) % 4) % 4)
def _require_index(value: Any, size: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < size: raise StaticGlbError(f"{field}: index invalid")
    return value

def _validate_input(asset: Mapping[str, Any]):
    if not isinstance(asset, Mapping): raise StaticGlbError("INPUT_NOT_OBJECT")
    name = asset.get("name")
    if not isinstance(name, str) or not _NAME.fullmatch(name): raise StaticGlbError("ASSET_NAME_INVALID")
    if asset.get("units") != "meters" or asset.get("up_axis") != "Y": raise StaticGlbError("STATIC_CONVENTION_INVALID")
    if "transform" not in asset: raise StaticGlbError("TRANSFORM_REQUIRED")
    transform = asset["transform"]
    if not isinstance(transform, Mapping) or transform.get("space", "flat") != "flat": raise StaticGlbError("TRANSFORM_SPACE_UNSUPPORTED")
    for key, default in (("position", [0,0,0]), ("rotation", [0,0,0]), ("scale", [1,1,1])): _vec(transform.get(key, default), f"transform.{key}")
    if any(abs(x) > 1e6 for key in ("position", "rotation") for x in _vec(transform.get(key, [0,0,0]), f"transform.{key}")) or any(x <= 0 or x > 1e4 for x in _vec(transform.get("scale", [1,1,1]), "transform.scale")): raise StaticGlbError("TRANSFORM_SANITY_FAILED")
    for key in ("skin", "skeleton", "bones", "animations", "children", "parent", "matrix"):
        if asset.get(key): raise StaticGlbError("STATIC_ASSET_MUST_NOT_REQUIRE_SKIN" if key in {"skin","skeleton","bones","animations"} else "TRANSFORM_HIERARCHY_UNSUPPORTED")
    meshes = asset.get("meshes")
    if not isinstance(meshes, list) or not meshes: raise StaticGlbError("MESH_GEOMETRY_MISSING")
    return name, transform, meshes

def _material(material: Any) -> tuple[str, dict[str, Any]]:
    if material is None: material = {"type":"MeshStandardMaterial", "color":[1,1,1], "roughness":1, "metalness":0}
    if not isinstance(material, Mapping) or material.get("type") not in SUPPORTED_MATERIALS: raise StaticGlbError("MATERIAL_UNSUPPORTED")
    color = _vec(material.get("color", [1,1,1]), "material.color"); opacity = _number(material.get("opacity", 1), "material.opacity")
    metal = _number(material.get("metalness", 0), "material.metalness"); rough = _number(material.get("roughness", 1), "material.roughness")
    if any(not 0 <= x <= 1 for x in color + [opacity, metal, rough]): raise StaticGlbError("MATERIAL_FACTOR_OUT_OF_RANGE")
    out = {"name":"", "pbrMetallicRoughness":{"baseColorFactor":color+[opacity], "metallicFactor":metal, "roughnessFactor":rough}}
    return json.dumps(dict(material), sort_keys=True, separators=(",", ":")), out

def _document(name: str, transform: Mapping[str, Any], meshes: list[Mapping[str, Any]]):
    raw=bytearray(); views=[]; accessors=[]; out_meshes=[]; materials=[]; material_ids={}; vertices=indices=0
    for mi, mesh in enumerate(meshes):
        if not isinstance(mesh, Mapping): raise StaticGlbError("MESH_INVALID")
        positions=mesh.get("positions")
        if not isinstance(positions,list) or not positions or len(positions)%3: raise StaticGlbError("MESH_POSITIONS_INVALID")
        vals=[_number(x,"positions") for x in positions]; vcount=len(vals)//3
        idx=mesh.get("indices", list(range(vcount)))
        if not isinstance(idx,list) or not idx: raise StaticGlbError("MESH_INDICES_INVALID")
        if len(idx)%3: raise StaticGlbError("TRIANGLE_INDEX_COUNT_INVALID")
        if any(isinstance(x,bool) or not isinstance(x,int) or x<0 or x>=vcount for x in idx): raise StaticGlbError("MESH_INDICES_INVALID")
        mkey, mat = _material(mesh.get("material"))
        if mkey not in material_ids: material_ids[mkey]=len(materials); mat["name"]=f"material_{len(materials):02d}"; materials.append(mat)
        while len(raw)%4: raw.append(0)
        po=len(raw); raw.extend(struct.pack("<%sf"%len(vals),*vals)); pv=len(views); views.append({"buffer":0,"byteOffset":po,"byteLength":len(vals)*4,"target":34962})
        pa=len(accessors); accessors.append({"bufferView":pv,"componentType":5126,"count":vcount,"type":"VEC3","min":[min(vals[i::3]) for i in range(3)],"max":[max(vals[i::3]) for i in range(3)]})
        while len(raw)%4: raw.append(0)
        io=len(raw); raw.extend(struct.pack("<%sI"%len(idx),*idx)); iv=len(views); views.append({"buffer":0,"byteOffset":io,"byteLength":len(idx)*4,"target":34963})
        ia=len(accessors); accessors.append({"bufferView":iv,"componentType":5125,"count":len(idx),"type":"SCALAR","min":[min(idx)],"max":[max(idx)]})
        out_meshes.append({"name":mesh.get("name",f"mesh_{mi:02d}"),"primitives":[{"attributes":{"POSITION":pa},"indices":ia,"material":material_ids[mkey],"mode":4}]}); vertices+=vcount; indices+=len(idx)
    rx,ry,rz=_vec(transform.get("rotation",[0,0,0]),"transform.rotation"); cx,sx,cy,sy,cz,sz=[math.cos(rx/2),math.sin(rx/2),math.cos(ry/2),math.sin(ry/2),math.cos(rz/2),math.sin(rz/2)]
    q=[sx*cy*cz-cx*sy*sz,cx*sy*cz+sx*cy*sz,cx*cy*sz-sx*sy*cz,cx*cy*cz+sx*sy*sz]
    nt={"translation":_vec(transform.get("position",[0,0,0]),"transform.position"),"rotation":q,"scale":_vec(transform.get("scale",[1,1,1]),"transform.scale")}
    doc={"asset":{"version":"2.0","generator":"P2P static GLB standardizer"},"scene":0,"scenes":[{"name":name,"nodes":list(range(len(out_meshes)))}],"nodes":[{"name":m["name"],"mesh":i,**nt} for i,m in enumerate(out_meshes)],"meshes":out_meshes,"materials":materials,"buffers":[{"byteLength":len(raw)}],"bufferViews":views,"accessors":accessors}
    return doc,bytes(raw),{"status":"VALID","contract":STATIC_CONTRACT,"asset_name":name,"mesh_count":len(out_meshes),"vertex_count":vertices,"index_count":indices,"material_count":len(materials),"skin":False,"skeleton":False,"gltf_version":"2.0"}

def _encode(doc, binary):
    # glTF JSON chunks use ASCII spaces; BIN padding uses zero bytes.
    js=_align(json.dumps(doc,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode(),b" "); bn=_align(binary)
    total=12+8+len(js)+8+len(bn)
    return struct.pack("<4sII",b"glTF",2,total)+struct.pack("<I4s",len(js),b"JSON")+js+struct.pack("<I4s",len(bn),b"BIN\0")+bn

def standardize_static_glb(asset: Mapping[str, Any], output_path: str|Path, *, generating_capability: str, run_id: str):
    if not isinstance(generating_capability,str) or not generating_capability or not isinstance(run_id,str) or not run_id: raise StaticGlbError("PROVENANCE_BINDING_INVALID")
    name,transform,meshes=_validate_input(asset); doc,binary,evidence=_document(name,transform,meshes); dest=Path(output_path)
    if dest.suffix.lower()!=".glb": raise StaticGlbError("OUTPUT_MUST_BE_GLB")
    dest.parent.mkdir(parents=True,exist_ok=True); data=_encode(doc,binary); dest.write_bytes(data); digest=hashlib.sha256(data).hexdigest()
    provenance={"schema":"p2p-static-asset-provenance/1","capability_id":CAPABILITY_ID,"capability_version":CAPABILITY_VERSION,"generating_capability":generating_capability,"run_id":run_id,"asset_name":name,"glb_sha256":digest,"contract":STATIC_CONTRACT}
    pp=dest.with_suffix(".asset-provenance.json"); pp.write_text(json.dumps(provenance,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return {"status":"STANDARDIZED","glb_path":str(dest),"provenance_path":str(pp),"glb_sha256":digest,"validation":evidence,"provenance":provenance}

def _parse(path: Path):
    data=path.read_bytes()
    if len(data)<20: raise StaticGlbError("GLB_HEADER_INVALID")
    magic,version,total=struct.unpack_from("<4sII",data,0)
    if magic!=b"glTF" or version!=2 or total!=len(data): raise StaticGlbError("GLB_HEADER_INVALID")
    off=12; doc=None; binary=None
    while off<total:
        if off+8>total: raise StaticGlbError("GLB_CHUNK_HEADER_INVALID")
        length,typ=struct.unpack_from("<I4s",data,off); off+=8
        if length%4 or off+length>total: raise StaticGlbError("GLB_CHUNK_INVALID")
        payload=data[off:off+length]; off+=length
        if typ==b"JSON":
            if doc is not None: raise StaticGlbError("GLB_MULTIPLE_JSON_CHUNKS")
            try: doc=json.loads(payload.rstrip(b" \\t\\r\\n\\0").decode())
            except (UnicodeError,json.JSONDecodeError) as e: raise StaticGlbError("GLB_JSON_INVALID") from e
        elif typ==b"BIN\0":
            if binary is not None: raise StaticGlbError("GLB_MULTIPLE_BIN_CHUNKS")
            binary=payload
        else: raise StaticGlbError("GLB_UNKNOWN_CHUNK")
    if not isinstance(doc,dict) or binary is None: raise StaticGlbError("GLB_LOADABILITY_INVALID")
    return data,doc,binary

def _structural(doc,binary):
    buffers=doc.get("buffers"); views=doc.get("bufferViews"); accessors=doc.get("accessors"); nodes=doc.get("nodes"); meshes=doc.get("meshes"); scenes=doc.get("scenes")
    if not all(isinstance(x,list) and x for x in (buffers,views,accessors,nodes,meshes,scenes)): raise StaticGlbError("GLB_REQUIRED_ARRAY_INVALID")
    for b in buffers:
        if not isinstance(b,dict) or b.get("byteLength")!=len(binary): raise StaticGlbError("GLB_BUFFER_LENGTH_INVALID")
    for v in views:
        if not isinstance(v,dict) or _require_index(v.get("buffer"),len(buffers),"bufferView.buffer")!=0: raise StaticGlbError("GLB_BUFFERVIEW_INVALID")
        off=v.get("byteOffset",0); length=v.get("byteLength")
        if not isinstance(off,int) or not isinstance(length,int) or off<0 or length<0 or off+length>len(binary) or off%4: raise StaticGlbError("GLB_BUFFERVIEW_BOUNDS_INVALID")
    for a in accessors:
        if not isinstance(a,dict) or "bufferView" not in a: raise StaticGlbError("GLB_ACCESSOR_INVALID")
        _require_index(a.get("bufferView"),len(views),"accessor.bufferView")
        if a.get("componentType") not in {5121,5123,5125,5126} or a.get("type") not in {"SCALAR","VEC2","VEC3","VEC4"} or not isinstance(a.get("count"),int) or a["count"]<=0: raise StaticGlbError("GLB_ACCESSOR_INVALID")
        components={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}[a["type"]]; width={5121:1,5123:2,5125:4,5126:4}[a["componentType"]]
        view=views[a["bufferView"]]
        aoffset=a.get("byteOffset",0)
        if not isinstance(aoffset,int) or aoffset < 0 or aoffset+a["count"]*components*width > view["byteLength"]: raise StaticGlbError("GLB_ACCESSOR_BOUNDS_INVALID")
    for mesh in meshes:
        if not isinstance(mesh,dict) or not mesh.get("primitives"): raise StaticGlbError("GLB_MESH_PRIMITIVES_INVALID")
        for p in mesh["primitives"]:
            if not isinstance(p,dict) or p.get("mode",4)!=4 or not isinstance(p.get("attributes"),dict) or "POSITION" not in p["attributes"]: raise StaticGlbError("GLB_PRIMITIVE_INVALID")
            pa=accessors[_require_index(p["attributes"]["POSITION"],len(accessors),"POSITION")]
            if pa.get("type")!="VEC3" or pa.get("componentType")!=5126: raise StaticGlbError("GLB_POSITION_INVALID")
            if p.get("material") is not None: _require_index(p["material"],len(doc.get("materials",[])),"material")
            if "indices" in p:
                ia=accessors[_require_index(p["indices"],len(accessors),"indices")]
                if ia.get("type")!="SCALAR" or ia.get("componentType") not in {5121,5123,5125} or ia["count"]%3: raise StaticGlbError("GLB_INDEX_INVALID")
                view=views[ia["bufferView"]]; start=view.get("byteOffset",0); size={5121:1,5123:2,5125:4}[ia["componentType"]]; raw=binary[start:start+view["byteLength"]]
                vals=struct.unpack("<%s%s"%(ia["count"],{5121:"B",5123:"H",5125:"I"}[ia["componentType"]]),raw[:ia["count"]*size])
                if any(x>=pa["count"] for x in vals): raise StaticGlbError("GLB_INDEX_OUT_OF_RANGE")
            elif pa["count"]%3: raise StaticGlbError("GLB_TRIANGLE_VERTEX_COUNT_INVALID")
    for n in nodes:
        if not isinstance(n,dict) or "mesh" not in n: raise StaticGlbError("GLB_NODE_INVALID")
        _require_index(n["mesh"],len(meshes),"node.mesh")
    scene_index=doc.get("scene")
    _require_index(scene_index,len(scenes),"scene")
    roots=scenes[scene_index].get("nodes") if isinstance(scenes[scene_index],dict) else None
    if not isinstance(roots,list) or not roots: raise StaticGlbError("GLB_SCENE_ROOTS_INVALID")
    seen=set(); visiting=set(); reachable_meshes=set()
    def visit(i):
        i=_require_index(i,len(nodes),"scene.node")
        if i in visiting: raise StaticGlbError("GLB_NODE_CYCLE")
        if i in seen: return
        visiting.add(i); node=nodes[i]
        if not isinstance(node,dict): raise StaticGlbError("GLB_NODE_INVALID")
        reachable_meshes.add(_require_index(node.get("mesh"),len(meshes),"node.mesh"))
        children=node.get("children",[])
        if not isinstance(children,list): raise StaticGlbError("GLB_NODE_CHILDREN_INVALID")
        for child in children: visit(child)
        visiting.remove(i); seen.add(i)
    for root in roots: visit(root)
    if not any("mesh" in nodes[i] for i in seen): raise StaticGlbError("GLB_SCENE_MESH_MISSING")
    if len(seen) != len(nodes): raise StaticGlbError("GLB_UNREACHABLE_NODE")
    if reachable_meshes != set(range(len(meshes))): raise StaticGlbError("GLB_UNREACHABLE_MESH")
    return {"status":"STRUCTURALLY_VALID","gltf_version":"2.0","reachable_nodes":len(seen),"reachable_meshes":len(reachable_meshes)}

def validate_static_glb_output(glb_path: str|Path, provenance_path: str|Path, *, expected_asset_name: str|None=None, expected_generating_capability: str|None=None, expected_run_id: str|None=None) -> dict[str,Any]:
    glb=Path(glb_path); data,doc,binary=_parse(glb)
    pp=Path(provenance_path)
    if pp.name!=f"{glb.stem}.asset-provenance.json": raise StaticGlbError("PROVENANCE_NAMING_INVALID")
    try: p=json.loads(pp.read_text(encoding="utf-8"))
    except (OSError,UnicodeError,json.JSONDecodeError) as e: raise StaticGlbError("PROVENANCE_UNREADABLE") from e
    required={"schema","capability_id","capability_version","generating_capability","run_id","asset_name","glb_sha256","contract"}
    if not isinstance(p,dict) or set(p)!=required: raise StaticGlbError("PROVENANCE_FIELDS_INVALID")
    if p["schema"]!="p2p-static-asset-provenance/1" or p["capability_id"]!=CAPABILITY_ID or p["capability_version"]!=CAPABILITY_VERSION or p["contract"]!=STATIC_CONTRACT: raise StaticGlbError("PROVENANCE_CAPABILITY_DRIFT")
    if p["glb_sha256"]!=hashlib.sha256(data).hexdigest(): raise StaticGlbError("PROVENANCE_HASH_MISMATCH")
    if expected_asset_name is None or expected_generating_capability is None or expected_run_id is None: raise StaticGlbError("TRUSTED_PROVENANCE_EXPECTATIONS_REQUIRED")
    if (p["asset_name"],p["generating_capability"],p["run_id"])!=(expected_asset_name,expected_generating_capability,expected_run_id): raise StaticGlbError("PROVENANCE_EVIDENCE_MISMATCH")
    structural=_structural(doc,binary)
    return {**structural,"glb_sha256":p["glb_sha256"],"provenance":p}

__all__=["CAPABILITY_ID","CAPABILITY_VERSION","STATIC_CONTRACT","StaticGlbError","standardize_static_glb","validate_static_glb_output"]
