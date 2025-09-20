from .db import engine, SessionLocal
from .models import Base, Quote

# Starter quotes
quotes = [
    "Why do we feen Master Bruce? So we can chief that skrong. - Motivator",
    "Wax melts when heated so it can serve another purpose. Are you melting or becoming something new? - Motivator",
    "Jarvis, give this fella props because they're grinding for the life they want. - Motivator",
    "You can tell who really bout this Fammy Guy stuff and who not. - Motivator",
    "I'm the motivational quote guy! Consider this your motivational quote! Oy vey. - Motivator"
]

def init_db():
    # WARNING: this wipes all existing tables/data
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database schema reset and created.")

def seed_quotes():
    db = SessionLocal()
    for q in quotes:
        # Add only if not already present
        if not db.query(Quote).filter_by(text=q).first():
            db.add(Quote(text=q))
    db.commit()
    db.close()
    print("Quotes table seeded.")

if __name__ == "__main__":
    init_db()
    seed_quotes()
