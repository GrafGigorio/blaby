"""
State Manager для управления состояниями диалогового режима
"""
from enum import Enum
from datetime import datetime
from typing import Optional


class DialogState(Enum):
    """Состояния диалога"""
    IDLE = "idle"  # Ожидание
    LISTENING = "listening"  # Слушает пользователя
    PROCESSING = "processing"  # Обрабатывает запрос (STT + LLM + TTS)
    SPEAKING = "speaking"  # Воспроизводит ответ


class StateManager:
    """Менеджер состояний для непрерывного диалога"""

    def __init__(self):
        self.current_state = DialogState.IDLE
        self.previous_state = None
        self.state_change_time = datetime.now()
        self.conversation_history = []
        self.current_transcript = ""  # Текущая промежуточная расшифровка
        self.silence_start_time = None  # Время начала тишины

    def transition_to(self, new_state: DialogState):
        """
        Переход в новое состояние

        Args:
            new_state: новое состояние
        """
        if self.current_state != new_state:
            print(f"[StateManager] {self.current_state.value} → {new_state.value}")
            self.previous_state = self.current_state
            self.current_state = new_state
            self.state_change_time = datetime.now()

    def can_interrupt(self) -> bool:
        """
        Проверить, можно ли прервать текущее состояние

        Returns:
            bool: True если можно прервать (например, во время SPEAKING)
        """
        return self.current_state == DialogState.SPEAKING

    def reset(self):
        """Сброс состояния в IDLE"""
        self.transition_to(DialogState.IDLE)
        self.current_transcript = ""
        self.silence_start_time = None

    def start_listening(self):
        """Начать слушать пользователя"""
        self.transition_to(DialogState.LISTENING)
        self.current_transcript = ""

    def start_processing(self):
        """Начать обработку запроса"""
        self.transition_to(DialogState.PROCESSING)

    def start_speaking(self):
        """Начать воспроизведение ответа"""
        self.transition_to(DialogState.SPEAKING)

    def update_transcript(self, text: str, is_partial: bool = True):
        """
        Обновить текущую транскрипцию

        Args:
            text: распознанный текст
            is_partial: промежуточный результат или финальный
        """
        if is_partial:
            self.current_transcript = text
        else:
            # Финальный результат - добавляем к истории
            self.current_transcript = text

    def get_current_transcript(self) -> str:
        """Получить текущую транскрипцию"""
        return self.current_transcript

    def add_to_history(self, role: str, text: str):
        """
        Добавить сообщение в историю

        Args:
            role: роль (user/assistant)
            text: текст сообщения
        """
        self.conversation_history.append({
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat()
        })

    def get_history(self):
        """Получить историю разговора"""
        return self.conversation_history

    def clear_history(self):
        """Очистить историю разговора"""
        self.conversation_history = []

    def mark_silence_start(self):
        """Отметить начало тишины"""
        self.silence_start_time = datetime.now()

    def get_silence_duration(self) -> Optional[float]:
        """
        Получить длительность тишины в секундах

        Returns:
            float: длительность тишины или None если тишина не началась
        """
        if self.silence_start_time:
            return (datetime.now() - self.silence_start_time).total_seconds()
        return None

    def reset_silence(self):
        """Сбросить таймер тишины"""
        self.silence_start_time = None

    def get_state_info(self):
        """
        Получить информацию о текущем состоянии

        Returns:
            dict: информация о состоянии
        """
        return {
            "current_state": self.current_state.value,
            "previous_state": self.previous_state.value if self.previous_state else None,
            "state_duration": (datetime.now() - self.state_change_time).total_seconds(),
            "current_transcript": self.current_transcript,
            "history_length": len(self.conversation_history),
            "silence_duration": self.get_silence_duration()
        }
