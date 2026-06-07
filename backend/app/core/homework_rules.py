import json


ALLOWED_HOMEWORK_SUBJECTS = ("语文", "数学")
HOMEWORK_SUBJECTS_JSON = json.dumps(ALLOWED_HOMEWORK_SUBJECTS, ensure_ascii=False)


def is_allowed_homework_subject(subject: str | None) -> bool:
    return bool(subject) and subject in ALLOWED_HOMEWORK_SUBJECTS
