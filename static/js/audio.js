/**
 * Модуль работы с аудио (запись, воспроизведение, визуализация)
 */

import { SAMPLE_RATE, FFT_SIZE } from './config.js';
import { updateVolumeLevel } from './ui.js';

// Глобальные переменные для аудио
export let audioContext = null;
export let analyser = null;
export let audioSourceNode = null;
export let dataArray = null;
export let animationId = null;
export let mediaStream = null;
export let audioWorkletNode = null;

// Переменные для воспроизведения
export let playbackAudioContext = null;
export let playbackAnalyser = null;
export let playbackDataArray = null;
export let playbackAnimationId = null;
export let isPlayingAudio = false;
export let currentAudioElements = [];
export let processAudioChunksPromise = null;
export let currentPlayingElement = null;

// Флаги
let isDialogActive = false;
let isMicrophoneEnabled = true;
let isAudioEnabled = true;

/**
 * Установить активность диалога
 * @param {boolean} active
 */
export function setDialogActive(active) {
    isDialogActive = active;
}

/**
 * Получить активность диалога
 * @returns {boolean}
 */
export function isDialogActiveState() {
    return isDialogActive;
}

/**
 * Настройка визуализатора записи
 * @param {MediaStream} stream - Поток аудио
 */
export function setupVisualizer(stream) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: SAMPLE_RATE
    });
    analyser = audioContext.createAnalyser();
    audioSourceNode = audioContext.createMediaStreamSource(stream);
    audioSourceNode.connect(analyser);
    analyser.fftSize = FFT_SIZE;

    const bufferLength = analyser.frequencyBinCount;
    dataArray = new Uint8Array(bufferLength);

    drawVisualizer();
}

/**
 * Рисование визуализатора записи
 */
function drawVisualizer() {
    if (!isDialogActive || !analyser) return;

    animationId = requestAnimationFrame(drawVisualizer);
    analyser.getByteFrequencyData(dataArray);

    const canvas = document.getElementById('visualizer');
    if (!canvas) return;

    const canvasCtx = canvas.getContext('2d');
    const WIDTH = canvas.width;
    const HEIGHT = canvas.height;

    canvasCtx.fillStyle = 'rgb(245, 245, 245)';
    canvasCtx.fillRect(0, 0, WIDTH, HEIGHT);

    const barWidth = (WIDTH / dataArray.length) * 2.5;
    let x = 0;

    // Вычисляем среднюю громкость
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
    }
    const average = sum / dataArray.length;
    const volumePercent = (average / 255) * 100;
    updateVolumeLevel(volumePercent);

    // Рисуем бары
    for (let i = 0; i < dataArray.length; i++) {
        const barHeight = (dataArray[i] / 255) * HEIGHT;
        canvasCtx.fillStyle = `rgb(${dataArray[i] + 100}, 50, 150)`;
        canvasCtx.fillRect(x, HEIGHT - barHeight, barWidth, barHeight);
        x += barWidth + 1;
    }
}

/**
 * Остановка визуализатора записи
 */
export function stopVisualizer() {
    if (animationId) {
        cancelAnimationFrame(animationId);
        animationId = null;
    }
}

/**
 * Запуск визуализатора воспроизведения
 */
export function startPlaybackVisualizer() {
    if (playbackAnimationId) {
        return;
    }

    if (!playbackAudioContext) {
        try {
            playbackAudioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.error('❌ Ошибка создания AudioContext для воспроизведения:', e);
            return;
        }
    }

    playbackAnalyser = playbackAudioContext.createAnalyser();
    playbackAnalyser.fftSize = FFT_SIZE;
    const bufferLength = playbackAnalyser.frequencyBinCount;
    playbackDataArray = new Uint8Array(bufferLength);

    drawPlaybackVisualizer();
}

/**
 * Рисование визуализатора воспроизведения
 */
function drawPlaybackVisualizer() {
    playbackAnimationId = requestAnimationFrame(drawPlaybackVisualizer);

    if (playbackAnalyser) {
        playbackAnalyser.getByteFrequencyData(playbackDataArray);
    }

    const canvas = document.getElementById('playback-visualizer');
    if (!canvas) return;

    const canvasCtx = canvas.getContext('2d');
    const WIDTH = canvas.width;
    const HEIGHT = canvas.height;

    canvasCtx.fillStyle = 'rgb(232, 245, 233)';
    canvasCtx.fillRect(0, 0, WIDTH, HEIGHT);

    if (!playbackDataArray) return;

    const barWidth = (WIDTH / playbackDataArray.length) * 2.5;
    let x = 0;

    for (let i = 0; i < playbackDataArray.length; i++) {
        const barHeight = (playbackDataArray[i] / 255) * HEIGHT;
        canvasCtx.fillStyle = `rgb(76, ${playbackDataArray[i] + 100}, 76)`;
        canvasCtx.fillRect(x, HEIGHT - barHeight, barWidth, barHeight);
        x += barWidth + 1;
    }
}

/**
 * Остановка визуализатора воспроизведения
 */
export function stopPlaybackVisualizer() {
    if (playbackAnimationId) {
        cancelAnimationFrame(playbackAnimationId);
        playbackAnimationId = null;
    }
}

/**
 * Получить громкость из анализатора
 * @returns {number} Процент громкости (0-100)
 */
export function getVolumePercent() {
    if (!analyser || !dataArray) return 0;

    analyser.getByteFrequencyData(dataArray);
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
    }
    const average = sum / dataArray.length;
    return (average / 255) * 100;
}

/**
 * Настройка захвата аудио
 * @returns {Promise<MediaStream>}
 */
export async function setupAudioCapture() {
    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: SAMPLE_RATE
            }
        });
        return mediaStream;
    } catch (error) {
        console.error('❌ Ошибка доступа к микрофону:', error);
        throw error;
    }
}

/**
 * Запуск записи аудио через AudioWorklet
 * @param {Function} onDataCallback - Callback для обработки аудио данных
 */
export async function startAudioRecording(onDataCallback) {
    try {
        if (!audioContext) {
            throw new Error('AudioContext не инициализирован');
        }

        // Останавливаем старый процессор если есть
        if (audioWorkletNode) {
            audioWorkletNode.disconnect();
            audioWorkletNode = null;
        }

        // Проверяем поддержку AudioWorklet
        if (!audioContext.audioWorklet) {
            throw new Error('AudioWorklet не поддерживается в этом браузере');
        }

        // Добавляем процессор (предполагается что файл уже зарегистрирован)
        await audioContext.audioWorklet.addModule('/static/pcm-processor.js');

        // Создаем AudioWorkletNode
        const source = audioContext.createMediaStreamSource(mediaStream);
        audioWorkletNode = new AudioWorkletNode(audioContext, 'pcm-processor');

        // Обработка сообщений от процессора
        audioWorkletNode.port.onmessage = (event) => {
            if (event.data.audioData) {
                onDataCallback(event.data.audioData);
            }
        };

        // Подключаем источник к процессору
        source.connect(audioWorkletNode);
        audioWorkletNode.connect(audioContext.destination);

    } catch (error) {
        console.error('❌ Ошибка создания AudioWorklet:', error);
        throw error;
    }
}

/**
 * Остановка записи аудио
 */
export function stopAudioRecording() {
    if (audioWorkletNode) {
        audioWorkletNode.disconnect();
        audioWorkletNode = null;
    }
}

/**
 * Обработка аудио чанка для воспроизведения
 * @param {string} base64Data - Аудио данные в base64
 * @param {Array} audioChunksBuffer - Буфер для накопления чанков
 */
export async function handleAudioChunk(base64Data, audioChunksBuffer) {
    try {
        const bytes = Uint8Array.from(atob(base64Data), c => c.charCodeAt(0));
        audioChunksBuffer.push(bytes);

        // Если еще не воспроизводится, начинаем
        if (!isPlayingAudio && audioChunksBuffer.length > 0) {
            await processAudioChunks(audioChunksBuffer);
        }
    } catch (error) {
        console.error('❌ Ошибка обработки аудио чанка:', error);
    }
}

/**
 * Обработка и воспроизведение накопленных аудио чанков
 * @param {Array} audioChunksBuffer - Буфер с аудио чанками
 */
export async function processAudioChunks(audioChunksBuffer) {
    if (isPlayingAudio || audioChunksBuffer.length === 0) {
        return;
    }

    isPlayingAudio = true;

    try {
        while (audioChunksBuffer.length > 0 && isDialogActive) {
            // Берем несколько чанков для воспроизведения
            const chunksToPlay = audioChunksBuffer.splice(0, Math.min(5, audioChunksBuffer.length));

            if (!isAudioEnabled) {
                continue;
            }

            // Объединяем чанки
            const totalSize = chunksToPlay.reduce((sum, chunk) => sum + chunk.length, 0);
            const combined = new Uint8Array(totalSize);
            let offset = 0;
            for (const chunk of chunksToPlay) {
                combined.set(chunk, offset);
                offset += chunk.length;
            }

            // Создаем Blob и воспроизводим
            const blob = new Blob([combined], { type: 'audio/wav' });
            if (blob.size === 0) {
                continue;
            }

            const audioUrl = URL.createObjectURL(blob);
            const audioElement = new Audio(audioUrl);

            // Подключаем к визуализатору
            if (playbackAudioContext && playbackAnalyser) {
                try {
                    const source = playbackAudioContext.createMediaElementSource(audioElement);
                    source.connect(playbackAnalyser);
                    playbackAnalyser.connect(playbackAudioContext.destination);
                } catch (e) {
                    // Элемент уже подключен, игнорируем
                }
            }

            // Воспроизводим
            try {
                await audioElement.play();
                currentAudioElements.push(audioElement);

                // Ждем окончания воспроизведения
                await new Promise((resolve, reject) => {
                    audioElement.onended = resolve;
                    audioElement.onerror = reject;
                });
            } catch (error) {
                console.error('❌ Ошибка воспроизведения:', error);
            } finally {
                URL.revokeObjectURL(audioUrl);
            }
        }
    } finally {
        isPlayingAudio = false;
    }
}

/**
 * Остановка всех воспроизведений
 */
export function stopAllAudio() {
    currentAudioElements.forEach(audio => {
        try {
            audio.pause();
            audio.currentTime = 0;
        } catch (e) {
            // Игнорируем ошибки
        }
    });
    currentAudioElements = [];
    isPlayingAudio = false;
}

/**
 * Переключение микрофона
 * @returns {boolean} Новое состояние
 */
export function toggleMicrophone() {
    isMicrophoneEnabled = !isMicrophoneEnabled;

    if (mediaStream) {
        mediaStream.getAudioTracks().forEach(track => {
            track.enabled = isMicrophoneEnabled;
        });
    }

    return isMicrophoneEnabled;
}

/**
 * Переключение звука
 * @returns {boolean} Новое состояние
 */
export function toggleAudio() {
    isAudioEnabled = !isAudioEnabled;

    if (!isAudioEnabled) {
        stopAllAudio();
    }

    return isAudioEnabled;
}

/**
 * Получить состояние микрофона
 * @returns {boolean}
 */
export function isMicrophoneEnabledState() {
    return isMicrophoneEnabled;
}

/**
 * Получить состояние звука
 * @returns {boolean}
 */
export function isAudioEnabledState() {
    return isAudioEnabled;
}
