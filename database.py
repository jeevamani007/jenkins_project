from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://detection_weh6_user:PlPGrnUDvYVuoUOn1yhN1EKrj0ZeRx2z@dpg-d56mhmp5pdvs738fr5cg-a/detection_weh6"

# Create engine
engine = create_engine(DATABASE_URL)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()
