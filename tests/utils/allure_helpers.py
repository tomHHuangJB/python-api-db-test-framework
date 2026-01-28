import json
from pathlib import Path

import allure


def attach_json(name: str, payload: dict | list):
    allure.attach(json.dumps(payload, indent=2), name, allure.attachment_type.JSON)


def attach_text(name: str, text: str):
    allure.attach(text, name, allure.attachment_type.TEXT)


def attach_file(name: str, path: str):
    file_path = Path(path)
    allure.attach(file_path.read_bytes(), name, allure.attachment_type.BINARY)
