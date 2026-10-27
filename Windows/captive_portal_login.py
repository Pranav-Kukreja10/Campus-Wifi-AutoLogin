import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Campus Wi-Fi Auto-Login Controller")
    parser.add_argument("--config", "--gui", "-c", action="store_true", help="Launch settings GUI")
    parser.add_argument("--install", action="store_true", help="Register Windows Task Scheduler auto-trigger")
    parser.add_argument("--uninstall", action="store_true", help="Unregister Windows Task Scheduler auto-trigger")
    parser.add_argument("--test", action="store_true", help="Test portal authentication once")

    args = parser.parse_args()

    if args.config:
        from gui import launch_gui
        launch_gui()
        sys.exit(0)

    if args.install:
        from task_manager import register_task
        ok, msg = register_task()
        if ok:
            print("Successfully registered background Wi-Fi event trigger.")
            sys.exit(0)
        else:
            print(f"Failed to register task: {msg}")
            sys.exit(1)

    if args.uninstall:
        from task_manager import unregister_task
        from config_manager import clear_all_data
        ok = unregister_task()
        clear_all_data()
        if ok:
            print("Successfully removed background Wi-Fi event trigger and wiped all user data.")
            sys.exit(0)
        else:
            print("Background task was not active, but all local credentials and data were erased.")
            sys.exit(0)

    from config_manager import is_configured
    from engine import execute_auto_login

    if args.test:
        success = execute_auto_login(ignore_ssid=True)
        sys.exit(0 if success else 1)

    if not is_configured():
        from gui import launch_gui
        launch_gui()
        sys.exit(0)

    result = execute_auto_login()
    if result == "AUTH_FAILED":
        from gui import launch_gui
        launch_gui(prompt_reauth=True)
        sys.exit(1)

    sys.exit(0 if result is True else 1)


if __name__ == "__main__":
    main()
