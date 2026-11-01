from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import Mapped,mapped_column,relationship
from .database import Base
class User(Base):
 __tablename__="users"
 id:Mapped[int]=mapped_column(primary_key=True)
 username:Mapped[str]=mapped_column(String,unique=True)
 password_hash:Mapped[str]=mapped_column(String)
 role:Mapped[str]=mapped_column(String,default="manager")
class Product(Base):
 __tablename__="products"
 id:Mapped[int]=mapped_column(primary_key=True)
 sku:Mapped[str]=mapped_column(String,unique=True,index=True)
 name:Mapped[str]=mapped_column(String)
 category:Mapped[str]=mapped_column(String,default="")
 unit_price:Mapped[float]=mapped_column(Float,default=0)
 reorder_level:Mapped[int]=mapped_column(Integer,default=0)
 active:Mapped[bool]=mapped_column(Boolean,default=True)
 inventory:Mapped["Inventory"]=relationship(back_populates="product",uselist=False,cascade="all,delete-orphan")
class Inventory(Base):
 __tablename__="inventory"
 id:Mapped[int]=mapped_column(primary_key=True)
 product_id:Mapped[int]=mapped_column(ForeignKey("products.id"),unique=True)
 quantity:Mapped[int]=mapped_column(Integer,default=0)
 updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
 product:Mapped[Product]=relationship(back_populates="inventory")
class Sale(Base):
 __tablename__="sales"
 id:Mapped[int]=mapped_column(primary_key=True)
 transaction_id:Mapped[str]=mapped_column(String,index=True)
 sale_date:Mapped[str]=mapped_column(String)
 sku:Mapped[str]=mapped_column(String,index=True)
 quantity:Mapped[int]=mapped_column(Integer)
 unit_price:Mapped[float]=mapped_column(Float)
 source_file:Mapped[str]=mapped_column(String,default="")
 __table_args__=(UniqueConstraint("transaction_id","sku"),)


class Forecast(Base):
 __tablename__="forecasts"
 id:Mapped[int]=mapped_column(primary_key=True)
 sku:Mapped[str]=mapped_column(String,index=True)
 generated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
 horizon_days:Mapped[int]=mapped_column(Integer)
 avg_daily_demand:Mapped[float]=mapped_column(Float)
 forecast_quantity:Mapped[float]=mapped_column(Float)
 method:Mapped[str]=mapped_column(String,default="moving_average")

class PurchaseOrder(Base):
 __tablename__="purchase_orders"
 id:Mapped[int]=mapped_column(primary_key=True)
 supplier:Mapped[str]=mapped_column(String,default="")
 status:Mapped[str]=mapped_column(String,default="draft")
 created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
 received_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
 notes:Mapped[str]=mapped_column(String,default="")
 items:Mapped[list["PurchaseOrderItem"]]=relationship(back_populates="order",cascade="all,delete-orphan")

class PurchaseOrderItem(Base):
 __tablename__="purchase_order_items"
 id:Mapped[int]=mapped_column(primary_key=True)
 order_id:Mapped[int]=mapped_column(ForeignKey("purchase_orders.id"))
 sku:Mapped[str]=mapped_column(String,index=True)
 quantity:Mapped[int]=mapped_column(Integer)
 unit_cost:Mapped[float]=mapped_column(Float,default=0)
 order:Mapped[PurchaseOrder]=relationship(back_populates="items")
