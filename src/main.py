from src import hello
import sys

if __name__ == "__main__":
    hello.world()
    for each_path in sys.path:
        print(each_path)
