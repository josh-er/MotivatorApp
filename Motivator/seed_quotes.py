# Motivator/seed_quotes.py
from Motivator.db import SessionLocal, engine, Base
from Motivator.models import Quote

# Ensure tables exist
Base.metadata.create_all(bind=engine)

quotes = [
    {"text": "Boss up real quick"},
    {"text": "I can't help but grind it out"},
    {"text": "I cannot fathom waking up and not grinding"},
    {"text": "Good heavens! You simply have no choice but to grind"},
    {"text": "If you got food at home, make sure to check the expiration date"},
    {"text": "Nothing like some water"},
    {"text": "The pit in your stomach isn't going away via social media dawg"},
    {"text": "The pit in your stomach means you know what you have to do"},
    {"text": "This is a motivational quote (you've been motivated)"},
    {"text": "Only thing you need to worry about is how you'll grind it out today"},
    {"text": ""},
    {"text": "Imagine all the yummy burgers you'll eat if you keep grinding"},
    {"text": "Imagine all the trinkets you'll buy if you keep grinding"},
    {"text": "No monkeying around today, only grinding for the banana"},
    {"text": "What is that dog doing? he pondered"}
]

def seed():
    db = SessionLocal()
    for q in quotes:
        exists = db.query(Quote).filter(Quote.text == q["text"]).first()
        if not exists:
            db.add(Quote(text=q["text"]))
    db.commit()
    db.close()
    print(f"Seeded {len(quotes)} quotes!")

if __name__ == "__main__":
    seed()
