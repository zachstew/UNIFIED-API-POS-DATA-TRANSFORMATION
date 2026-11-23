# models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

Base = declarative_base()

class UnifiedRecord(Base):
    __tablename__ = 'unified_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String, nullable=False)  # 'items' or 'orders'
    sku_id = Column(String, nullable=True)  # CHANGED: now a String (e.g. "SPTBG-1")
    sku_name = Column(String)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float)
    total_price = Column(Float)
    currency = Column(String, default='USD')
    status = Column(String, default='pending')
    transaction_date = Column(DateTime)
    raw_payload_hash = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Create the SQLite database file
engine = create_engine('sqlite:///etl_staging.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)