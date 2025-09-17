from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = {'schema': 'dbo'} 
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(36), unique=True, index=True)
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    image = relationship("Image", back_populates="task", uselist=False)

class Image(Base):
    __tablename__ = "images"
    __table_args__ = {'schema': 'dbo'}  
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey('dbo.tasks.task_id'), unique=True, index=True) 
    image_data = Column(Text, nullable=True)
    prompt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    task = relationship("Task", back_populates="image")