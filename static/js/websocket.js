/**
 * Модуль WebSocket для потокового взаимодействия с сервером
 */

import { WS_URL, STATUS_TEXTS } from './config.js';
import {
    updateStatus,
    updatePartialText,
    clearPartialText,
    addMessage,
    updateApplicationPanel
} from './ui.js';
import {
    handleAudioChunk,
    stopAllAudio,
    setDialogActive
} from './audio.js';
import {
    startVAD,
    stopVAD,
    setHasRecognizedText,
    setIsInterrupting
} from './vad.js';

// WebSocket соединение
let ws = null;
let currentStreamingMessage = null;
let currentAudioChunks = [];
let speakingFinishedSent = false;

/**
 * Инициализация WebSocket соединения
 * @returns {Promise<WebSocket>}
 */
export function initWebSocket() {
    return new Promise((resolve, reject) => {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            resolve(ws);
        };

        ws.onmessage = async (event) => {
            try {
                const data = JSON.parse(event.data);
                await handleWebSocketMessage(data);
            } catch (error) {
                console.error('❌ Ошибка обработки сообщения:', error);
            }
        };

        ws.onerror = (error) => {
            console.error('❌ WebSocket ошибка:', error);
            reject(error);
        };

        ws.onclose = () => {
            // Переподключение можно добавить здесь
        };
    });
}

/**
 * Обработка сообщений от сервера
 * @param {Object} data - Данные от сервера
 */
async function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'state':
            await handleStateChange(data.state);
            break;

        case 'partial_transcript':
            handlePartialTranscript(data.text);
            break;

        case 'final_transcript':
            handleFinalTranscript(data.text);
            break;

        case 'stream_start':
            handleStreamStart();
            break;

        case 'text_chunk':
            handleTextChunk(data.text);
            break;

        case 'audio_chunk':
            await handleAudioChunkMessage(data.data);
            break;

        case 'stream_end':
            await handleStreamEnd(data.text);
            break;

        case 'action_data':
            handleActionData(data.data);
            break;

        case 'error':
            handleError(data.message);
            break;

        default:
            console.warn('⚠️ Неизвестный тип сообщения:', data.type);
    }
}

/**
 * Обработка изменения состояния
 * @param {string} state - Новое состояние
 */
async function handleStateChange(state) {
    switch (state) {
        case 'listening':
            updateStatus(STATUS_TEXTS.listening, 'listening');
            clearPartialText();

            // Запускаем VAD
            startVAD({
                onSpeechStart: () => {
                    // Речь началась
                },
                onSpeechEnd: () => {
                    // Отправляем серверу сигнал о конце речи
                    sendMessage({ type: 'speech_end' });
                },
                onInterrupt: () => {
                    // Прерывание
                    stopAllAudio();
                    sendMessage({ type: 'interrupt' });
                    setIsInterrupting(true);
                }
            });
            break;

        case 'processing':
            updateStatus(STATUS_TEXTS.processing, 'processing');
            stopVAD();
            break;

        case 'speaking':
            updateStatus(STATUS_TEXTS.speaking, 'speaking');
            speakingFinishedSent = false;

            // Запускаем VAD для детекции прерывания
            startVAD({
                onInterrupt: () => {
                    stopAllAudio();
                    sendMessage({ type: 'interrupt' });
                    setIsInterrupting(true);
                }
            });
            break;

        default:
            updateStatus(STATUS_TEXTS.idle, 'idle');
            break;
    }
}

/**
 * Обработка промежуточного текста распознавания
 * @param {string} text - Распознанный текст
 */
function handlePartialTranscript(text) {
    updatePartialText(text);
    setHasRecognizedText(true);
}

/**
 * Обработка финального текста распознавания
 * @param {string} text - Распознанный текст
 */
function handleFinalTranscript(text) {
    addMessage('user', text);
    clearPartialText();
}

/**
 * Обработка начала потока
 */
function handleStreamStart() {
    currentStreamingMessage = {
        role: 'assistant',
        text: ''
    };
    currentAudioChunks = [];
}

/**
 * Обработка текстового чанка
 * @param {string} text - Текст от LLM
 */
function handleTextChunk(text) {
    if (currentStreamingMessage) {
        currentStreamingMessage.text += text;
    }
}

/**
 * Обработка аудио чанка
 * @param {string} base64Data - Аудио данные в base64
 */
async function handleAudioChunkMessage(base64Data) {
    try {
        await handleAudioChunk(base64Data, currentAudioChunks);
    } catch (error) {
        console.error('❌ Ошибка обработки аудио:', error);
    }
}

/**
 * Обработка конца потока
 * @param {string} fullText - Полный текст ответа
 */
async function handleStreamEnd(fullText) {
    if (currentStreamingMessage) {
        // Добавляем сообщение в историю
        addMessage('assistant', fullText || currentStreamingMessage.text);
    }

    // Ждем окончания воспроизведения
    await waitForAudioToFinish();

    // Отправляем сигнал о завершении воспроизведения
    if (!speakingFinishedSent) {
        sendSpeakingFinished('stream_end');
    }

    currentStreamingMessage = null;
}

/**
 * Ожидание завершения воспроизведения аудио
 */
async function waitForAudioToFinish() {
    const maxAttempts = 50; // 5 секунд максимум
    let attempts = 0;

    while (attempts < maxAttempts) {
        // Проверяем что больше нет чанков и воспроизведение завершено
        if (currentAudioChunks.length === 0 && !isPlayingAudio) {
            return;
        }

        await new Promise(resolve => setTimeout(resolve, 100));
        attempts++;
    }
}

/**
 * Отправка сигнала speaking_finished серверу
 * @param {string} source - Источник вызова
 */
function sendSpeakingFinished(source) {
    if (speakingFinishedSent) {
        return;
    }

    speakingFinishedSent = true;
    sendMessage({ type: 'speaking_finished' });
}

/**
 * Обработка данных действия (для панели заявки)
 * @param {Object} data - Данные действия
 */
function handleActionData(data) {
    updateApplicationPanel(data);
}

/**
 * Обработка ошибки
 * @param {string} message - Сообщение об ошибке
 */
function handleError(message) {
    console.error('❌ Ошибка от сервера:', message);
    updateStatus(`${STATUS_TEXTS.error}: ${message}`, 'idle');
}

/**
 * Отправка сообщения серверу
 * @param {Object} data - Данные для отправки
 */
export function sendMessage(data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
    } else {
        console.error('❌ WebSocket не готов');
    }
}

/**
 * Отправка аудио чанка серверу
 * @param {Float32Array} audioData - Аудио данные
 */
export function sendAudioChunk(audioData) {
    // Конвертируем Float32Array в Int16Array для отправки
    const int16Array = new Int16Array(audioData.length);
    for (let i = 0; i < audioData.length; i++) {
        const s = Math.max(-1, Math.min(1, audioData[i]));
        int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }

    // Конвертируем в base64
    const bytes = new Uint8Array(int16Array.buffer);
    const base64 = btoa(String.fromCharCode.apply(null, bytes));

    sendMessage({
        type: 'audio_chunk',
        data: base64
    });
}

/**
 * Начать диалог
 */
export function startDialog() {
    setDialogActive(true);
    sendMessage({ type: 'start_listening' });
}

/**
 * Остановить диалог
 */
export function stopDialog() {
    setDialogActive(false);
    stopVAD();
    stopAllAudio();
    sendMessage({ type: 'stop' });
}

/**
 * Закрыть WebSocket соединение
 */
export function closeWebSocket() {
    if (ws) {
        ws.close();
        ws = null;
    }
}

/**
 * Получить состояние WebSocket
 * @returns {number}
 */
export function getWebSocketState() {
    return ws ? ws.readyState : WebSocket.CLOSED;
}
