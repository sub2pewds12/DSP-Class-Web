#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # [SENTINEL] Safety Guard Injection
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        destructive_commands = ['flush', 'reset_db', 'drop_schema', 'nuke']
        
        if command in destructive_commands:
            try:
                import django
                django.setup()
                from apps.core.services.infrastructure import InfrastructureService
                InfrastructureService.validate_safe_operation(command)
            except PermissionError as e:
                print(str(e))
                sys.exit(1)
            except Exception:
                # If django setup fails here, execute_from_command_line will report it properly
                pass

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
