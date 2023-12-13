import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent / "src" / "gpt_function"
sys.path.append(str(src_dir))
