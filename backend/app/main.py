import os,csv,io
from datetime import datetime,timedelta,timezone
from fastapi import *
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import func
from jose import jwt,JWTError
from passlib.context import CryptContext
from .database import Base,engine,get_db
from .models import User,Product,Inventory,Sale
Base.metadata.create_all(engine)
app=FastAPI(title="SmartStock Phase 1 API")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
pwd=CryptContext(schemes=["bcrypt"],deprecated="auto"); secret=os.getenv("JWT_SECRET","local-dev-change-me"); oauth=OAuth2PasswordBearer(tokenUrl="/api/auth/login")
def seed():
 db=next(get_db())
 if not db.query(User).filter_by(username="admin").first():
  db.add(User(username="admin",password_hash=pwd.hash("admin123"),role="manager"));db.commit()
 db.close()
seed()
def auth(token=Depends(oauth),db:Session=Depends(get_db)):
 try: uid=int(jwt.decode(token,secret,algorithms=["HS256"])["sub"])
 except Exception: raise HTTPException(401,"Invalid token")
 u=db.get(User,uid)
 if not u: raise HTTPException(401,"User not found")
 return u
def pd(p): return dict(id=p.id,sku=p.sku,name=p.name,category=p.category,unit_price=p.unit_price,reorder_level=p.reorder_level,active=p.active,stock_quantity=p.inventory.quantity if p.inventory else 0)
@app.get("/api/health")
def health(): return {"status":"ok"}
@app.post("/api/auth/login")
def login(form:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
 u=db.query(User).filter_by(username=form.username).first()
 if not u or not pwd.verify(form.password,u.password_hash): raise HTTPException(401,"Incorrect username or password")
 tok=jwt.encode({"sub":str(u.id),"exp":datetime.now(timezone.utc)+timedelta(hours=8)},secret,algorithm="HS256")
 return {"access_token":tok,"token_type":"bearer","user":{"username":u.username,"role":u.role}}
@app.get("/api/products")
def products(q:str="",db:Session=Depends(get_db),u=Depends(auth)):
 query=db.query(Product).filter_by(active=True)
 if q: query=query.filter((Product.sku.ilike(f"%{q}%"))|(Product.name.ilike(f"%{q}%")))
 return [pd(p) for p in query.order_by(Product.name).all()]
@app.post("/api/products",status_code=201)
def add_product(x:dict,db:Session=Depends(get_db),u=Depends(auth)):
 required=["sku","name"]
 if any(not str(x.get(k,"")).strip() for k in required): raise HTTPException(400,"SKU and name are required")
 if db.query(Product).filter_by(sku=x["sku"].strip()).first(): raise HTTPException(409,"SKU already exists")
 p=Product(sku=x["sku"].strip(),name=x["name"].strip(),category=x.get("category",""),unit_price=float(x.get("unit_price",0)),reorder_level=int(x.get("reorder_level",0)))
 p.inventory=Inventory(quantity=int(x.get("initial_stock",0)));db.add(p);db.commit();db.refresh(p);return pd(p)
@app.patch("/api/products/{pid}")
def update(pid:int,x:dict,db:Session=Depends(get_db),u=Depends(auth)):
 p=db.get(Product,pid)
 if not p: raise HTTPException(404,"Product not found")
 for k in ["name","category","unit_price","reorder_level","active"]:
  if k in x:setattr(p,k,x[k])
 db.commit();db.refresh(p);return pd(p)
@app.delete("/api/products/{pid}",status_code=204)
def delete(pid:int,db:Session=Depends(get_db),u=Depends(auth)):
 p=db.get(Product,pid)
 if not p: raise HTTPException(404,"Product not found")
 p.active=False;db.commit()
@app.post("/api/inventory/{pid}/adjust")
def adjust(pid:int,x:dict,db:Session=Depends(get_db),u=Depends(auth)):
 p=db.get(Product,pid)
 if not p or not p.active:raise HTTPException(404,"Product not found")
 change=int(x.get("quantity_change",0));new=p.inventory.quantity+change
 if new<0:raise HTTPException(400,"Stock cannot become negative")
 p.inventory.quantity=new;db.commit();db.refresh(p);return pd(p)
@app.post("/api/sales/upload")
async def upload(file:UploadFile=File(...),db:Session=Depends(get_db),u=Depends(auth)):
 if not file.filename.lower().endswith(".csv"):raise HTTPException(400,"Upload CSV only")
 try: reader=csv.DictReader(io.StringIO((await file.read()).decode("utf-8-sig")))
 except:raise HTTPException(400,"CSV must be UTF-8")
 required={"transaction_id","sale_date","sku","quantity","unit_price"}
 headers={h.strip().lower() for h in (reader.fieldnames or [])}
 if not required.issubset(headers):raise HTTPException(400,"Required columns: "+", ".join(sorted(required)))
 rows=[];seen=set()
 for n,r in enumerate(reader,2):
  r={k.strip().lower():(v or "").strip() for k,v in r.items() if k}
  try:
   tid,date,sku=r["transaction_id"],r["sale_date"],r["sku"];qty=int(r["quantity"]);price=float(r["unit_price"])
   datetime.fromisoformat(date[:10])
   if not tid or not sku or qty<=0 or price<0:raise ValueError()
   if not db.query(Product).filter_by(sku=sku,active=True).first():raise ValueError("Unknown SKU "+sku)
   if (tid,sku) in seen or db.query(Sale).filter_by(transaction_id=tid,sku=sku).first():raise HTTPException(409,f"Duplicate transaction/SKU at row {n}")
   seen.add((tid,sku));rows.append((tid,date,sku,qty,price))
  except HTTPException:raise
  except Exception as e:raise HTTPException(400,f"Invalid CSV row {n}: {e}")
 try:
  for tid,date,sku,qty,price in rows:
   p=db.query(Product).filter_by(sku=sku).first()
   if p.inventory.quantity<qty:raise HTTPException(400,f"Insufficient stock for {sku}; nothing imported")
   p.inventory.quantity-=qty;db.add(Sale(transaction_id=tid,sale_date=date,sku=sku,quantity=qty,unit_price=price,source_file=file.filename))
  db.commit()
 except:db.rollback();raise
 return {"accepted_records":len(rows),"message":"Sales imported; inventory updated"}
@app.get("/api/sales")
def sales(limit:int=100,db:Session=Depends(get_db),u=Depends(auth)):
 return [dict(id=s.id,transaction_id=s.transaction_id,sale_date=s.sale_date,sku=s.sku,quantity=s.quantity,unit_price=s.unit_price,source_file=s.source_file) for s in db.query(Sale).order_by(Sale.id.desc()).limit(min(limit,500))]
@app.get("/api/dashboard")
def dashboard(db:Session=Depends(get_db),u=Depends(auth)):
 return {"product_count":db.query(Product).filter_by(active=True).count(),"total_stock_units":db.query(func.coalesce(func.sum(Inventory.quantity),0)).scalar() or 0,"sales_records":db.query(Sale).count(),"low_stock_products":db.query(Product).join(Inventory).filter(Product.active==True,Inventory.quantity<=Product.reorder_level).count(),"sales_value":round(db.query(func.coalesce(func.sum(Sale.quantity*Sale.unit_price),0)).scalar() or 0,2)}
