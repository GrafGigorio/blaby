/**
 * Модуль управления пользовательским интерфейсом
 */

import { DOM_IDS, STATUS_TEXTS } from './config.js';

// Состояние UI
let currentState = 'idle';

/**
 * Получить элемент DOM по ID
 * @param {string} id - ID элемента
 * @returns {HTMLElement}
 */
function getElement(id) {
    return document.getElementById(id);
}

/**
 * Обновить статус приложения
 * @param {string} text - Текст статуса
 * @param {string} state - Состояние (idle, listening, processing, speaking)
 */
export function updateStatus(text, state) {
    const statusDiv = getElement(DOM_IDS.status);
    if (statusDiv) {
        statusDiv.textContent = text;
        statusDiv.className = `status ${state}`;
        currentState = state;
    }
}

/**
 * Получить текущее состояние
 * @returns {string}
 */
export function getCurrentState() {
    return currentState;
}

/**
 * Обновить промежуточный текст распознавания
 * @param {string} text - Распознанный текст
 */
export function updatePartialText(text) {
    const partialText = getElement(DOM_IDS.partialText);
    if (partialText) {
        partialText.textContent = text;
    }
}

/**
 * Очистить промежуточный текст
 */
export function clearPartialText() {
    updatePartialText('');
}

/**
 * Добавить сообщение в историю диалога
 * @param {string} role - Роль отправителя ('user' или 'assistant')
 * @param {string} text - Текст сообщения
 * @param {string} [audioUrl] - URL аудио файла (опционально)
 */
export function addMessage(role, text, audioUrl = null) {
    const conversationDiv = getElement(DOM_IDS.conversation);
    if (!conversationDiv) return;

    // Удаляем пустое состояние если оно есть
    const emptyState = conversationDiv.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }

    // Создаем элемент сообщения
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const labelDiv = document.createElement('div');
    labelDiv.className = 'message-label';
    labelDiv.textContent = role === 'user' ? 'Вы' : 'Ася';

    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = text;

    messageDiv.appendChild(labelDiv);
    messageDiv.appendChild(textDiv);

    // Добавляем аудио плеер если есть URL
    if (audioUrl && role === 'assistant') {
        const audioPlayer = document.createElement('audio');
        audioPlayer.controls = true;
        audioPlayer.className = 'audio-player';
        audioPlayer.src = audioUrl;
        messageDiv.appendChild(audioPlayer);
    }

    conversationDiv.appendChild(messageDiv);

    // Прокручиваем вниз
    conversationDiv.scrollTop = conversationDiv.scrollHeight;
}

/**
 * Обновить уровень громкости
 * @param {number} percent - Процент громкости (0-100)
 */
export function updateVolumeLevel(percent) {
    const volumeLevel = getElement(DOM_IDS.volumeLevel);
    if (volumeLevel) {
        volumeLevel.textContent = `${Math.round(percent)}%`;
    }
}

/**
 * Очистить историю диалога
 */
export function clearConversation() {
    const conversationDiv = getElement(DOM_IDS.conversation);
    if (!conversationDiv) return;

    conversationDiv.innerHTML = '<div class="empty-state">История диалога пуста</div>';
}

/**
 * Обновить состояние кнопок
 * @param {boolean} isActive - Активен ли диалог
 */
export function updateButtons(isActive) {
    const startBtn = getElement(DOM_IDS.startBtn);
    const stopBtn = getElement(DOM_IDS.stopBtn);

    if (startBtn) {
        startBtn.disabled = isActive;
        if (isActive) {
            startBtn.classList.add('active');
        } else {
            startBtn.classList.remove('active');
        }
    }

    if (stopBtn) {
        stopBtn.disabled = !isActive;
    }
}

/**
 * Обновить индикатор микрофона
 * @param {boolean} enabled - Включен ли микрофон
 */
export function updateMicIndicator(enabled) {
    const btn = getElement(DOM_IDS.micToggleBtn);
    if (btn) {
        btn.textContent = enabled ? '🎤 Микрофон' : '🔇 Микрофон';
        if (enabled) {
            btn.classList.remove('disabled');
        } else {
            btn.classList.add('disabled');
        }
    }
}

/**
 * Обновить индикатор звука
 * @param {boolean} enabled - Включен ли звук
 */
export function updateAudioIndicator(enabled) {
    const btn = getElement(DOM_IDS.audioToggleBtn);
    if (btn) {
        btn.textContent = enabled ? '🔊 Звук' : '🔇 Звук';
        if (enabled) {
            btn.classList.remove('disabled');
        } else {
            btn.classList.add('disabled');
        }
    }
}

/**
 * Обновить панель заявки
 * @param {Object} data - Данные заявки
 */
export function updateApplicationPanel(data) {
    const panel = getElement(DOM_IDS.applicationContent);
    if (!panel || !data) return;

    let html = '';

    // Отображаем stage если есть
    if (data.stage) {
        html += `
            <div class="application-stage">
                <div class="application-stage-label">Этап</div>
                <div class="application-stage-value">${data.stage}</div>
            </div>
        `;
    }

    // Отображаем собранные данные
    if (data.data && Object.keys(data.data).length > 0) {
        html += '<div class="application-data">';
        for (const [key, value] of Object.entries(data.data)) {
            const displayValue = value || '<span class="empty">Не указано</span>';
            html += `
                <div class="application-data-item">
                    <div class="application-data-label">${key}</div>
                    <div class="application-data-value${!value ? ' empty' : ''}">${displayValue}</div>
                </div>
            `;
        }
        html += '</div>';
    }

    // Отображаем статус завершения
    if (data.complete) {
        html += '<div class="application-complete">✅ Заявка заполнена</div>';
    }

    panel.innerHTML = html || '<div class="empty-state">Нет данных</div>';
}

/**
 * Загрузить список моделей
 */
export async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();

        if (data.status === 'success') {
            const selector = getElement(DOM_IDS.modelSelector);
            if (selector) {
                selector.innerHTML = '';
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    if (model === data.current_model) {
                        option.selected = true;
                    }
                    selector.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('❌ Ошибка загрузки моделей:', error);
    }
}

/**
 * Сменить модель LLM
 * @param {string} modelName - Имя модели
 */
export async function changeModel(modelName) {
    if (!modelName) {
        console.warn('⚠️ Модель не выбрана');
        return;
    }

    try {
        const response = await fetch('/api/set-model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model_name: modelName })
        });

        const data = await response.json();

        if (data.status === 'success') {
            updateStatus(`Модель изменена на ${modelName}`, 'idle');
            setTimeout(() => {
                updateStatus(STATUS_TEXTS.idle, 'idle');
            }, 2000);
        } else {
            console.error('❌ Ошибка смены модели:', data);
        }
    } catch (error) {
        console.error('❌ Ошибка при смене модели:', error);
    }
}

/**
 * Очистить историю на сервере
 */
export async function clearHistory() {
    try {
        await fetch('/api/clear-history', { method: 'POST' });
        clearConversation();
        updateStatus('История очищена', 'idle');
        setTimeout(() => {
            updateStatus(STATUS_TEXTS.idle, 'idle');
        }, 2000);
    } catch (error) {
        console.error('❌ Ошибка очистки истории:', error);
    }
}
