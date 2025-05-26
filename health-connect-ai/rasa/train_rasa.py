import subprocess


def train_rasa():
    """Train the Rasa model using the provided config and data."""
    subprocess.run([
        "rasa", "train",
        "--domain", "domain.yml",
        "--config", "config.yml",
        "--data", "data/",
        "--out", "models/"
    ], check=True)


if __name__ == "__main__":
    train_rasa()
    print("Training complete. Model stored in models/ directory.")
