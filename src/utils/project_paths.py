from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT/"src"
UTILS_ROOT = SRC_ROOT/"utils"
POLICY_ROOT = UTILS_ROOT/"policies"
if __name__ == "__main__":
    print("root: ", PROJECT_ROOT)
    print("utils_root: ", UTILS_ROOT)
