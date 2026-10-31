import os
from pathlib import Path

# Define folders and files required by the project
DIRECTORIES = [
    "data",
    "model",
    "faiss_index",
    "templates",
    "static",
]

FILES = [
    "app.py",
    "main.py",
    "db.py",
    "vector.py",
    "train_model.py",
    "requirements.txt",
    ".env.example",
]

def create_project_structure():
    """Ensure all required project directories and placeholder files exist."""
    base_dir = Path(__file__).resolve().parent

    for folder in DIRECTORIES:
        folder_path = base_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"Verified directory: {folder}")

    for file_name in FILES:
        file_path = base_dir / file_name
        if not file_path.exists():
            file_path.touch()
            print(f"Created file: {file_name}")
        else:
            print(f"Verified file: {file_name}")

if __name__ == "__main__":
    create_project_structure()
    print("\nProject structure verified successfully!")
