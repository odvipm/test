def test_notify_calls_plyer_with_correct_args(mocker):
    mock_notify = mocker.patch("plyer.notification.notify")
    import notifier
    notifier.notify("Clocked in ✓", "Clocked in at 09:01")
    mock_notify.assert_called_once_with(
        title="Clocked in ✓",
        message="Clocked in at 09:01",
        app_name="Sprout Auto Clocker",
        timeout=10,
    )
