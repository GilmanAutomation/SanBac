import importlib
import pkgutil
import inspect
from pathlib import Path
from typing import Dict
from .base import BaseTool

def load_tools() -> Dict[str, BaseTool]:
    """
    Dynamically loads all tool modules in the current directory,
    finds any subclass of BaseTool, and returns an instantiated dictionary.
    """
    tools = {}
    package_dir = Path(__file__).resolve().parent

    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        if module_name in ("base", "__init__"):
            continue
        try:
            # Import the module relative to this package
            module = importlib.import_module(f".{module_name}", package=__name__)
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseTool)
                    and obj is not BaseTool
                ):
                    # Instantiate the tool class
                    tool_instance = obj()
                    tools[tool_instance.name] = tool_instance
        except Exception as e:
            print(f"Warning: Failed to load tool plugin '{module_name}': {e}")
            
    return tools
