/**
 * Конфигурация и константы для голосового ассистента
 */

// Пороги для Voice Activity Detection
export const SPEECH_THRESHOLD = 15; // Порог громкости для детекции речи (%)
export const INTERRUPT_THRESHOLD = 16; // Порог для прерывания
export const INTERRUPT_MIN_DURATION = 150; // Минимальная длительность громкого звука для прерывания (мс)
export const INTERRUPT_GRACE_PERIOD = 200; // Задержка перед сбросом счетчика прерывания (мс)
export const SILENCE_DURATION = 500; // Миллисекунды тишины для завершения фразы
export const MIN_SPEECH_DURATION = 300; // Минимальная длительность речи (мс)

// Настройки аудио
export const SAMPLE_RATE = 16000; // Частота дискретизации для Vosk
export const FFT_SIZE = 256; // Размер FFT для анализатора

// WebSocket
export const WS_URL = `ws://${window.location.host}/ws/voice`;

// ID элементов DOM
export const DOM_IDS = {
    status: 'status',
    conversation: 'conversation',
    partialText: 'partial-text',
    volumeLevel: 'volume-level',
    visualizer: 'visualizer',
    playbackVisualizer: 'playback-visualizer',
    startBtn: 'start-btn',
    stopBtn: 'stop-btn',
    micToggleBtn: 'mic-toggle-btn',
    audioToggleBtn: 'audio-toggle-btn',
    clearHistoryBtn: 'clear-history-btn',
    modelSelector: 'model-selector',
    applicationContent: 'application-content'
};

// Тексты статусов
export const STATUS_TEXTS = {
    idle: 'Нажмите "Начать диалог" для старта',
    listening: '🎤 Слушаю... (говорите или нажмите пробел для остановки)',
    processing: '⏳ Обрабатываю запрос...',
    speaking: '🔊 Говорю... (можно прервать речью)',
    error: '❌ Произошла ошибка'
};
