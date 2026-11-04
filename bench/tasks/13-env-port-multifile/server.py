from config import parse_port


def server_config(environ):
    return {"host": "127.0.0.1", "port": parse_port(environ.get("APP_PORT"))}
