import os

def start():
    print("Starting UTE System...")

    if not os.path.exists("ute.db"):
        print("Database will be created automatically.")

    print("System Ready")

if __name__ == "__main__":
    start()
