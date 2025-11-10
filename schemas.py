"""
Database Schemas for PixieGarden English

Each Pydantic model represents a collection in MongoDB. Collection name is the
lowercase of the class name (e.g., Lesson -> "lesson").
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class Student(BaseModel):
    name: str = Field(..., description="Child's first name")
    parent_email: EmailStr = Field(..., description="Parent/guardian email")
    avatar: Optional[str] = Field(None, description="Optional avatar/pixel icon id")
    level: int = Field(1, ge=1, description="Current learning level")

class Lesson(BaseModel):
    title: str = Field(..., description="Lesson title")
    theme: str = Field(..., description="Thematic category, e.g., 'Garden' or 'Animals'")
    difficulty: str = Field('easy', description="easy | medium | hard")
    words: List[str] = Field(default_factory=list, description="Target vocabulary")
    description: Optional[str] = Field(None, description="Lesson summary")
    cover: Optional[str] = Field(None, description="Optional image/emoji cover")

class Progress(BaseModel):
    student_id: str = Field(..., description="Student ObjectId as string")
    lesson_id: str = Field(..., description="Lesson ObjectId as string")
    score: int = Field(0, ge=0, le=100, description="Score percentage")
    stars: int = Field(0, ge=0, le=3, description="Stars earned (0-3)")
    notes: Optional[str] = Field(None, description="Optional teacher/parent notes")
