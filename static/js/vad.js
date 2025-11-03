/**
 * Модуль Voice Activity Detection (VAD)
 * Определение активности речи на основе громкости
 */

import {
    SPEECH_THRESHOLD,
    INTERRUPT_THRESHOLD,
    INTERRUPT_MIN_DURATION,
    INTERRUPT_GRACE_PERIOD,
    SILENCE_DURATION,
    MIN_SPEECH_DURATION
} from './config.js';
import { getVolumePercent } from './audio.js';

// Состояние VAD
let isSpeaking = false;
let silenceStart = null;
let speechStart = null;
let vadCheckInterval = null;
let interruptSpeechStart = null;
let interruptLastDetected = null;
let hasRecognizedText = false;
let isInterrupting = false;

// Callbacks
let onSpeechStartCallback = null;
let onSpeechEndCallback = null;
let onInterruptCallback = null;

/**
 * Запуск VAD
 * @param {Object} callbacks - Объект с callback функциями
 * @param {Function} callbacks.onSpeechStart - Вызывается при начале речи
 * @param {Function} callbacks.onSpeechEnd - Вызывается при конце речи
 * @param {Function} callbacks.onInterrupt - Вызывается при прерывании
 */
export function startVAD(callbacks = {}) {
    onSpeechStartCallback = callbacks.onSpeechStart;
    onSpeechEndCallback = callbacks.onSpeechEnd;
    onInterruptCallback = callbacks.onInterrupt;

    // Сбрасываем состояние
    isSpeaking = false;
    silenceStart = null;
    speechStart = null;
    interruptSpeechStart = null;
    interruptLastDetected = null;
    hasRecognizedText = false;
    isInterrupting = false;

    // Запускаем проверку каждые 100ms
    if (!vadCheckInterval) {
        vadCheckInterval = setInterval(checkVoiceActivity, 100);
    }
}

/**
 * Остановка VAD
 */
export function stopVAD() {
    if (vadCheckInterval) {
        clearInterval(vadCheckInterval);
        vadCheckInterval = null;
    }

    // Сбрасываем состояние
    isSpeaking = false;
    silenceStart = null;
    speechStart = null;
    interruptSpeechStart = null;
    interruptLastDetected = null;
    hasRecognizedText = false;
    isInterrupting = false;
}

/**
 * Установить флаг наличия распознанного текста
 * @param {boolean} hasText
 */
export function setHasRecognizedText(hasText) {
    hasRecognizedText = hasText;
}

/**
 * Установить флаг прерывания
 * @param {boolean} interrupting
 */
export function setIsInterrupting(interrupting) {
    isInterrupting = interrupting;
}

/**
 * Проверка голосовой активности
 * @param {string} currentState - Текущее состояние приложения
 */
function checkVoiceActivity(currentState) {
    const volumePercent = getVolumePercent();

    // Логика для состояния SPEAKING (возможность прерывания)
    if (currentState === 'speaking') {
        if (volumePercent > INTERRUPT_THRESHOLD) {
            const now = Date.now();

            if (!interruptSpeechStart) {
                interruptSpeechStart = now;
                interruptLastDetected = now;
            } else {
                interruptLastDetected = now;

                const interruptDuration = now - interruptSpeechStart;

                // Проверяем длительность громкого звука
                if (interruptDuration >= INTERRUPT_MIN_DURATION) {
                    // Прерывание подтверждено!
                    if (onInterruptCallback && !isInterrupting) {
                        isInterrupting = true;
                        onInterruptCallback();
                    }
                }
            }
        } else {
            // Звук ниже порога
            if (interruptLastDetected) {
                const timeSinceLastDetected = Date.now() - interruptLastDetected;

                if (timeSinceLastDetected > INTERRUPT_GRACE_PERIOD) {
                    // Сбрасываем счетчик если звук стих
                    interruptSpeechStart = null;
                    interruptLastDetected = null;
                }
            }
        }
        return;
    }

    // Логика для состояния LISTENING (детекция конца речи)
    if (currentState === 'listening') {
        if (volumePercent > SPEECH_THRESHOLD) {
            // Обнаружена речь
            if (!isSpeaking) {
                isSpeaking = true;
                speechStart = Date.now();
                silenceStart = null;

                if (onSpeechStartCallback) {
                    onSpeechStartCallback(volumePercent);
                }
            } else {
                // Продолжается речь, сбрасываем таймер тишины
                silenceStart = null;
            }
        } else {
            // Тишина
            if (isSpeaking) {
                if (!silenceStart) {
                    silenceStart = Date.now();
                }

                const silenceDuration = Date.now() - silenceStart;
                const speechDuration = speechStart ? Date.now() - speechStart : 0;

                // Проверяем условия для конца фразы
                if (silenceDuration >= SILENCE_DURATION) {
                    if (speechDuration >= MIN_SPEECH_DURATION && hasRecognizedText) {
                        // Конец фразы - достаточная длительность речи и есть распознанный текст
                        if (onSpeechEndCallback) {
                            onSpeechEndCallback(speechDuration, silenceDuration);
                        }
                    }

                    // Сбрасываем состояние речи
                    isSpeaking = false;
                    speechStart = null;
                    silenceStart = null;
                    hasRecognizedText = false;
                }
            }
        }
    }
}

/**
 * Получить текущее состояние речи
 * @returns {boolean}
 */
export function getIsSpeaking() {
    return isSpeaking;
}

/**
 * Принудительно сбросить состояние VAD
 */
export function resetVADState() {
    isSpeaking = false;
    silenceStart = null;
    speechStart = null;
    interruptSpeechStart = null;
    interruptLastDetected = null;
    hasRecognizedText = false;
    isInterrupting = false;
}
