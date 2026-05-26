from app import create_app
from seeds import load_core_data


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        load_core_data()
