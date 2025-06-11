import pkgutil, importlib
from core.connector_base import BaseConnector

def discover_connectors():
    for _, mod_name, _ in pkgutil.iter_modules(['connectors']):
        mod = importlib.import_module(f"connectors.{mod_name}.connector")
        for obj in vars(mod).values():
            if isinstance(obj, type) and issubclass(obj, BaseConnector) and obj is not BaseConnector:
                yield obj()

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--connectors', nargs='*', help='Which connectors to run')
    args = p.parse_args()

    for conn in discover_connectors():
        if not args.connectors or conn.name in args.connectors:
            raw  = conn.extract()
            norm = conn.transform(raw)
            conn.load(norm)
