/**
 * Главный файл приложения - Voice AI Assistant
 * Инициализация и управление всеми модулями
 */

import { DOM_IDS, STATUS_TEXTS } from './config.js';
import {
    updateStatus,
    updateButtons,
    updateMicIndicator,
    updateAudioIndicator,
    loadModels,
    changeModel,
    clearHistory,
    clearConversation
} from './ui.js';
import {
    setupAudioCapture,
    setupVisualizer,
    startAudioRecording,
    stopAudioRecording,
    stopVisualizer,
    startPlaybackVisualizer,
    toggleMicrophone,
    toggleAudio,
    isMicrophoneEnabledState,
    isAudioEnabledState,
    setDialogActive
} from './audio.js';
import {
    initWebSocket,
    startDialog,
    stopDialog,
    sendAudioChunk,
    closeWebSocket
} from './websocket.js';

// Глобальное состояние приложения
let isDialogActive = false;

/**
 * Инициализация приложения
 */
async function initApp() {
    // Загружаем список моделей
    await loadModels();

    // Запускаем визуализатор воспроизведения
    startPlaybackVisualizer();

    // Устанавливаем обработчики событий
    setupEventListeners();

    // Устанавливаем начальное состояние
    updateStatus(STATUS_TEXTS.idle, 'idle');
    updateButtons(false);
    updateMicIndicator(true);
    updateAudioIndicator(true);
}

/**
 * Настройка обработчиков событий
 */
function setupEventListeners() {
    // Кнопка "Начать диалог"
    const startBtn = document.getElementById(DOM_IDS.startBtn);
    if (startBtn) {
        startBtn.addEventListener('click', handleStart);
    }

    // Кнопка "Остановить"
    const stopBtn = document.getElementById(DOM_IDS.stopBtn);
    if (stopBtn) {
        stopBtn.addEventListener('click', handleStop);
    }

    // Кнопка переключения микрофона
    const micBtn = document.getElementById(DOM_IDS.micToggleBtn);
    if (micBtn) {
        micBtn.addEventListener('click', handleMicToggle);
    }

    // Кнопка переключения звука
    const audioBtn = document.getElementById(DOM_IDS.audioToggleBtn);
    if (audioBtn) {
        audioBtn.addEventListener('click', handleAudioToggle);
    }

    // Кнопка очистки истории
    const clearBtn = document.getElementById(DOM_IDS.clearHistoryBtn);
    if (clearBtn) {
        clearBtn.addEventListener('click', handleClearHistory);
    }

    // Выбор модели
    const modelSelector = document.getElementById(DOM_IDS.modelSelector);
    if (modelSelector) {
        modelSelector.addEventListener('change', handleModelChange);
    }

    // Клавиша пробел для остановки/начала
    document.addEventListener('keydown', handleKeyPress);
}

/**
 * Обработка нажатия "Начать диалог"
 */
async function handleStart() {
    try {
        updateStatus('Инициализация...', 'processing');

        // Инициализируем WebSocket
        await initWebSocket();

        // Получаем доступ к микрофону
        const stream = await setupAudioCapture();

        // Настраиваем визуализатор
        setupVisualizer(stream);

        // Запускаем запись аудио
        await startAudioRecording((audioData) => {
            // Отправляем аудио чанки на сервер
            if (isDialogActive && isMicrophoneEnabledState()) {
                sendAudioChunk(audioData);
            }
        });

        // Начинаем диалог
        isDialogActive = true;
        setDialogActive(true);
        startDialog();

        // Обновляем UI
        updateButtons(true);

    } catch (error) {
        console.error('❌ Ошибка запуска:', error);
        updateStatus('Ошибка запуска. Проверьте доступ к микрофону.', 'idle');
        updateButtons(false);
    }
}

/**
 * Обработка нажатия "Остановить"
 */
function handleStop() {
    // Останавливаем диалог
    isDialogActive = false;
    setDialogActive(false);
    stopDialog();

    // Останавливаем запись
    stopAudioRecording();
    stopVisualizer();

    // Закрываем WebSocket
    closeWebSocket();

    // Обновляем UI
    updateStatus(STATUS_TEXTS.idle, 'idle');
    updateButtons(false);
}

/**
 * Обработка переключения микрофона
 */
function handleMicToggle() {
    const enabled = toggleMicrophone();
    updateMicIndicator(enabled);
}

/**
 * Обработка переключения звука
 */
function handleAudioToggle() {
    const enabled = toggleAudio();
    updateAudioIndicator(enabled);
}

/**
 * Обработка очистки истории
 */
async function handleClearHistory() {
    await clearHistory();
}

/**
 * Обработка смены модели
 * @param {Event} event
 */
async function handleModelChange(event) {
    const modelName = event.target.value;
    if (modelName) {
        await changeModel(modelName);
    }
}

/**
 * Обработка нажатия клавиш
 * @param {KeyboardEvent} event
 */
function handleKeyPress(event) {
    // Пробел для старта/стопа
    if (event.code === 'Space' && !event.repeat) {
        event.preventDefault();

        if (isDialogActive) {
            handleStop();
        } else {
            handleStart();
        }
    }
}

/**
 * Обработка закрытия страницы
 */
window.addEventListener('beforeunload', () => {
    if (isDialogActive) {
        handleStop();
    }
});

// Инициализация приложения при загрузке DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    // DOM уже загружен
    initApp();
}
