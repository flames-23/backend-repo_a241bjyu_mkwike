import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Student, Lesson, Progress

app = FastAPI(title="PixieGarden English API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "PixieGarden English Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["collections"] = db.list_collection_names()
        else:
            response["database"] = "❌ Not Connected"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:120]}"
    return response

# Seed some default garden-themed lessons if none exist
@app.post("/seed")
def seed_lessons():
    try:
        existing = list(db["lesson"].find().limit(1)) if db else []
        if existing:
            return {"status": "ok", "message": "Lessons already seeded"}
        demo_lessons = [
            {
                "title": "Garden Friends",
                "theme": "Garden",
                "difficulty": "easy",
                "words": ["bee", "tree", "pond", "seed", "sun"],
                "description": "Meet friendly garden words in pixel style!",
                "cover": "🌻"
            },
            {
                "title": "Farm Picnic",
                "theme": "Farm",
                "difficulty": "easy",
                "words": ["milk", "egg", "bread", "honey", "jam"],
                "description": "Yummy picnic items from the farm.",
                "cover": "🧺"
            },
            {
                "title": "Weather Wizard",
                "theme": "Nature",
                "difficulty": "medium",
                "words": ["rain", "sunny", "wind", "cloud", "storm"],
                "description": "Cast weather words like spells!",
                "cover": "⛅"
            }
        ]
        for l in demo_lessons:
            create_document("lesson", l)
        return {"status": "ok", "inserted": len(demo_lessons)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Public endpoints for frontend
@app.get("/lessons")
def list_lessons(limit: int = 50):
    try:
        docs = get_documents("lesson", {}, min(limit, 100))
        # Cast ObjectId to string for JSON
        for d in docs:
            d["_id"] = str(d.get("_id"))
        return {"items": docs}
    except Exception as e:
        # If DB not available, return static fallback
        fallback = [
            {"_id": "1", "title": "Garden Friends", "theme": "Garden", "difficulty": "easy", "words": ["bee","tree","pond","seed","sun"], "description": "Meet friendly garden words in pixel style!", "cover": "🌻"},
            {"_id": "2", "title": "Farm Picnic", "theme": "Farm", "difficulty": "easy", "words": ["milk","egg","bread","honey","jam"], "description": "Yummy picnic items from the farm.", "cover": "🧺"}
        ]
        return {"items": fallback, "note": "database not available: " + str(e)[:80]}

class StartLessonRequest(BaseModel):
    student_name: str
    parent_email: Optional[str] = None
    lesson_id: str

@app.post("/start-lesson")
def start_lesson(payload: StartLessonRequest):
    try:
        # ensure student exists or create
        existing = db["student"].find_one({"name": payload.student_name}) if db else None
        student_id = None
        if existing:
            student_id = str(existing["_id"]) 
        else:
            student_id = create_document("student", {
                "name": payload.student_name,
                "parent_email": payload.parent_email or "parent@example.com",
                "level": 1
            })
        # verify lesson
        if db:
            oid = ObjectId(payload.lesson_id) if ObjectId.is_valid(payload.lesson_id) else None
            if not oid:
                raise HTTPException(status_code=400, detail="Invalid lesson id")
            lesson = db["lesson"].find_one({"_id": oid})
            if not lesson:
                raise HTTPException(status_code=404, detail="Lesson not found")
        else:
            lesson = None
        # create progress stub
        progress_id = create_document("progress", {
            "student_id": student_id,
            "lesson_id": payload.lesson_id,
            "score": 0,
            "stars": 0
        })
        return {"student_id": student_id, "progress_id": progress_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
