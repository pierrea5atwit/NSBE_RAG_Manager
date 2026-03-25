import pytest
import sys
from pathlib import Path

# Add the workspace root directory to Python path so 'api' package is discoverable
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))
