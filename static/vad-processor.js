/**
 * AudioWorkletProcessor для Voice Activity Detection (VAD)
 * Заменяет устаревший ScriptProcessorNode
 */
class VadProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bufferSize = 4096;
        this.buffer = new Float32Array(this.bufferSize);
        this.bufferIndex = 0;
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];

        // Если нет входных данных, продолжаем работу
        if (!input || !input[0]) {
            return true;
        }

        const inputChannel = input[0];

        // Накапливаем данные в буфер
        for (let i = 0; i < inputChannel.length; i++) {
            this.buffer[this.bufferIndex] = inputChannel[i];
            this.bufferIndex++;

            // Когда буфер заполнен, отправляем данные в main thread
            if (this.bufferIndex >= this.bufferSize) {
                // Отправляем копию буфера
                this.port.postMessage({
                    audioData: this.buffer.slice()
                });
                this.bufferIndex = 0;
            }
        }

        // Продолжаем обработку
        return true;
    }
}

registerProcessor('vad-processor', VadProcessor);
