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
from .models import User,Product,Inventory,Sale,Forecast,PurchaseOrder,PurchaseOrderItem
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


# ---------------- Phase 2: forecasting and inventory optimization ----------------
def _daily_demand(db:Session, sku:str, lookback_days:int=30):
 cutoff=(datetime.utcnow()-timedelta(days=lookback_days)).date().isoformat()
 rows=db.query(Sale.sale_date,func.sum(Sale.quantity)).filter(Sale.sku==sku,Sale.sale_date>=cutoff).group_by(Sale.sale_date).all()
 total=sum(float(q or 0) for _,q in rows)
 # Include days with no sales in the denominator to avoid overstating demand.
 return total/max(lookback_days,1), int(total), len(rows)

def _forecast_payload(f):
 return {"id":f.id,"sku":f.sku,"generated_at":f.generated_at.isoformat(),"horizon_days":f.horizon_days,"avg_daily_demand":round(f.avg_daily_demand,3),"forecast_quantity":round(f.forecast_quantity,2),"method":f.method}

@app.post("/api/forecast/generate")
def generate_forecasts(x:dict={},db:Session=Depends(get_db),u=Depends(auth)):
 lookback=max(7,min(int(x.get("lookback_days",30)),365));horizon=max(1,min(int(x.get("horizon_days",14)),90))
 products=db.query(Product).filter_by(active=True).all();generated=[]
 for p in products:
  avg,total,active_days=_daily_demand(db,p.sku,lookback)
  # Insufficient history fallback: same moving-average method, clearly flagged.
  method="moving_average" if total>0 else "fallback_zero_history"
  f=Forecast(sku=p.sku,horizon_days=horizon,avg_daily_demand=avg,forecast_quantity=avg*horizon,method=method)
  db.add(f);generated.append(f)
 db.commit()
 for f in generated:db.refresh(f)
 return {"generated":len(generated),"lookback_days":lookback,"horizon_days":horizon,"forecasts":[_forecast_payload(f) for f in generated]}

@app.get("/api/forecast")
def list_forecasts(sku:str="",limit:int=100,db:Session=Depends(get_db),u=Depends(auth)):
 q=db.query(Forecast)
 if sku:q=q.filter(Forecast.sku==sku)
 return [_forecast_payload(f) for f in q.order_by(Forecast.generated_at.desc()).limit(min(limit,500)).all()]

@app.get("/api/inventory/recommendations")
def recommendations(lookback_days:int=30,lead_time_days:int=7,safety_stock_days:int=3,db:Session=Depends(get_db),u=Depends(auth)):
 lookback=max(7,min(lookback_days,365));lead=max(1,min(lead_time_days,90));safety=max(0,min(safety_stock_days,90));out=[]
 for p in db.query(Product).filter_by(active=True).all():
  avg,total,_=_daily_demand(db,p.sku,lookback)
  target=int(round(avg*(lead+safety)))
  stock=p.inventory.quantity if p.inventory else 0
  qty=max(0,target-stock)
  out.append({"sku":p.sku,"name":p.name,"current_stock":stock,"avg_daily_demand":round(avg,3),"lead_time_days":lead,"safety_stock_days":safety,"target_stock":target,"recommended_order_quantity":qty,"status":"REORDER" if qty>0 else "OK"})
 return out

@app.post("/api/purchase-orders",status_code=201)
def create_purchase_order(x:dict,db:Session=Depends(get_db),u=Depends(auth)):
 items=x.get("items",[])
 if not items:raise HTTPException(400,"At least one item is required")
 order=PurchaseOrder(supplier=str(x.get("supplier","")),notes=str(x.get("notes","")),status="draft")
 for item in items:
  sku=str(item.get("sku","")).strip();qty=int(item.get("quantity",0));cost=float(item.get("unit_cost",0))
  p=db.query(Product).filter_by(sku=sku,active=True).first()
  if not p:raise HTTPException(400,f"Unknown SKU: {sku}")
  if qty<=0 or cost<0:raise HTTPException(400,"Quantity must be positive and cost non-negative")
  order.items.append(PurchaseOrderItem(sku=sku,quantity=qty,unit_cost=cost))
 db.add(order);db.commit();db.refresh(order)
 return _po_payload(order)

def _po_payload(o):
 return {"id":o.id,"supplier":o.supplier,"status":o.status,"created_at":o.created_at.isoformat(),"received_at":o.received_at.isoformat() if o.received_at else None,"notes":o.notes,"items":[{"sku":i.sku,"quantity":i.quantity,"unit_cost":i.unit_cost} for i in o.items]}

@app.get("/api/purchase-orders")
def list_purchase_orders(db:Session=Depends(get_db),u=Depends(auth)):
 return [_po_payload(o) for o in db.query(PurchaseOrder).order_by(PurchaseOrder.id.desc()).all()]

@app.post("/api/purchase-orders/{order_id}/receive")
def receive_purchase_order(order_id:int,db:Session=Depends(get_db),u=Depends(auth)):
 o=db.get(PurchaseOrder,order_id)
 if not o:raise HTTPException(404,"Purchase order not found")
 if o.status=="received":raise HTTPException(409,"Purchase order already received")
 if o.status=="cancelled":raise HTTPException(409,"Cancelled order cannot be received")
 for item in o.items:
  p=db.query(Product).filter_by(sku=item.sku).first()
  if not p or not p.inventory:raise HTTPException(400,f"Inventory missing for {item.sku}")
  p.inventory.quantity+=item.quantity
 o.status="received";o.received_at=datetime.utcnow();db.commit();db.refresh(o)
 return _po_payload(o)

@app.post("/api/purchase-orders/{order_id}/cancel")
def cancel_purchase_order(order_id:int,db:Session=Depends(get_db),u=Depends(auth)):
 o=db.get(PurchaseOrder,order_id)
 if not o:raise HTTPException(404,"Purchase order not found")
 if o.status=="received":raise HTTPException(409,"Received order cannot be cancelled")
 o.status="cancelled";db.commit();db.refresh(o);return _po_payload(o)

@app.get("/api/forecast/evaluation")
def evaluate_forecast(sku:str,forecast_days:int=14,db:Session=Depends(get_db),u=Depends(auth)):
 # Evaluate simple rolling forecast against the most recent available daily sales.
 days=max(1,min(forecast_days,90));avg,_,_=_daily_demand(db,sku,30)
 cutoff=(datetime.utcnow()-timedelta(days=days)).date().isoformat()
 actual=float(db.query(func.coalesce(func.sum(Sale.quantity),0)).filter(Sale.sku==sku,Sale.sale_date>=cutoff).scalar() or 0)
 predicted=avg*days
 mape=None if actual==0 else round(abs(actual-predicted)/actual*100,2)
 return {"sku":sku,"period_days":days,"actual_quantity":actual,"predicted_quantity":round(predicted,2),"mape_percent":mape,"note":"MAPE is omitted when actual demand is zero; this is a simple baseline evaluation."}
