from plyer import notification

_APP_NAME = "Sprout Auto Clocker"


def notify(title: str, message: str) -> None:
    notification.notify(
        title=title,
        message=message,
        app_name=_APP_NAME,
        timeout=10,
    )
