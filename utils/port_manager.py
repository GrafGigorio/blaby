"""
Утилиты для управления портами
"""
import os
import socket
import subprocess


def kill_process_on_port(port: int):
    """
    Завершает процесс, занимающий указанный порт

    Args:
        port: номер порта для проверки
    """
    try:
        # Проверяем если порт занят
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()

        if result == 0:
            # Порт занят, ищем и убиваем процесс
            print(f"⚠️  Порт {port} занят, пытаемся завершить процесс...")

            # Для macOS/Linux используем lsof
            if os.name == 'posix':
                try:
                    # Находим PID процесса на порту
                    result = subprocess.run(
                        ['lsof', '-ti', f':{port}'],
                        capture_output=True,
                        text=True,
                        check=False
                    )

                    if result.stdout.strip():
                        pids = result.stdout.strip().split('\n')
                        for pid in pids:
                            if pid:
                                print(f"🔪 Завершаем процесс PID: {pid}")
                                subprocess.run(['kill', '-9', pid], check=False)
                        print(f"✅ Процессы на порту {port} завершены")
                    else:
                        print(f"ℹ️  Процесс на порту {port} не найден")
                except Exception as e:
                    print(f"⚠️  Не удалось завершить процесс: {e}")

            # Для Windows используем netstat
            elif os.name == 'nt':
                try:
                    result = subprocess.run(
                        ['netstat', '-ano'],
                        capture_output=True,
                        text=True,
                        check=False
                    )

                    for line in result.stdout.split('\n'):
                        if f':{port}' in line and 'LISTENING' in line:
                            parts = line.split()
                            if len(parts) > 0:
                                pid = parts[-1]
                                print(f"🔪 Завершаем процесс PID: {pid}")
                                subprocess.run(['taskkill', '/F', '/PID', pid], check=False)
                                print(f"✅ Процесс на порту {port} завершен")
                                break
                except Exception as e:
                    print(f"⚠️  Не удалось завершить процесс: {e}")
    except Exception as e:
        print(f"⚠️  Ошибка проверки порта {port}: {e}")
