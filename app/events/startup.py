from app.config import DEVICE
from app.utils.database import Base, create_database_if_not_exists, get_engine

async def start_up():
    print(f"💡 Tips: {'GPU' if DEVICE == 'cuda' else 'CPU'} optimized settings applied")
    try:
        create_database_if_not_exists()
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
