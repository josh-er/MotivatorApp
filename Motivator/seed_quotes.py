from Motivator.db import SessionLocal, engine, Base
from Motivator.models import Quote

# Create tables if not already created
Base.metadata.create_all(bind=engine)

quotes = [
    {"text": "Keep your pockets full of small miracles; you’ll be surprised how often you’ll find exact change for luck.", "author": "Ray (night clerk)"},
    {"text": "If life hands you a broken neon sign, learn to read the glow — it’s still spelling out opportunity.", "author": "Marlene (early shift)"},
    {"text": "When everyone’s yelling for the exit, fold yourself into the crowd and learn which doors actually open.", "author": "Gus (corner diner)"},
    {"text": "Treat your mistakes like burned toast — scrape the worst off, butter what’s left, and keep eating.", "author": "Tina (cash register philosopher)"},
    {"text": "If the map is a mess, draw your own roads with a crayon and drive like you mean it.", "author": "Hector (station attendant)"},
    {"text": "Don’t be afraid to be an unfinished song; the chorus shows up for the ones who keep humming.", "author": "Lola (sandwich artist)"},
    {"text": "Be the kind of person who waters the sidewalk plants — nobody notices, but the street blooms anyway.", "author": "Old Man J (corner gardener)"},
    {"text": "Your luck is a stubborn cat; stop trying to herd it and start leaving windows open.", "author": "Nina (graveyard shift)"},
    {"text": "Sometimes the best plan is a ridiculous plan done with full conviction.", "author": "Dante (late-night poet)"},
    {"text": "Wear your weird like a coat — strangers will either admire it or move aside; either way you stay warm.", "author": "Bea (coffee stand)"},
    {"text": "Ambition is a small, persistent echo. It keeps coming back if you shout louder than doubt.", "author": "Moe (city bus)"},
    {"text": "If you’re stuck in the same loop, change one tiny thing — a button, a route, the cereal — and see the day rearrange.", "author": "Carla (24/7 cashier)"},
    {"text": "Count your tiny wins like rare coins. They add up faster than you expect.", "author": "Rico (late-night stocker)"},
    {"text": "When the plan collapses, smile — you just made room for a better disaster.", "author": "Fern (shift lead)"},
    {"text": "Do the small strange thing today. Later you’ll call it ‘the move’ and no one will ask how it worked.", "author": "Sam (odd-job handyman)"}
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
