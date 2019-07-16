import sys
from atlassian_tools import hello

def main():
    hello.world()
    for each_path in sys.path:
        print(each_path)

if __name__ == "__main__":
    main()
