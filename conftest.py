# conftest.py
import sys, os

# __file__ aponta para ROOT/conftest.py
ROOT = os.path.dirname(__file__)

# Insere src/ no início dos módulos buscados
sys.path.insert(0, os.path.join(ROOT, "src"))
