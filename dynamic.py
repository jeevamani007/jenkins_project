from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB


class Authenticate(Base):
    __tablename__ = "authenticate"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    projects = relationship(
        "Projects",
        back_populates="owner",
        cascade="all, delete-orphan"
    )


class Projects(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("authenticate.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    project_name = Column(String, index=True, nullable=False)

    owner = relationship("Authenticate", back_populates="projects")

    details = relationship(
        "Details",
        back_populates="project",
        cascade="all, delete-orphan"
    )


class Details(Base):
    __tablename__ = "details"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    data = Column(JSONB, nullable=True)

    project = relationship("Projects", back_populates="details")