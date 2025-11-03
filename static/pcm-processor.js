/**
 * AudioWorklet процессор для захвата PCM аудио
 */

class PCMProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bufferSize = 4096; // Размер буфера
        this.buffer = new Float32Array(this.bufferSize);
        this.bufferIndex = 0;
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];

        if (input.length > 0) {
            const inputChannel = input[0];

            for (let i = 0; i < inputChannel.length; i++) {
                this.buffer[this.bufferIndex++] = inputChannel[i];

                // Когда буфер заполнен, отправляем данные
                if (this.bufferIndex >= this.bufferSize) {
                    // Создаем копию буфера для отправки
                    const audioData = new Float32Array(this.buffer);

                    this.port.postMessage({
                        audioData: audioData
                    });

                    // Сбрасываем индекс
                    this.bufferIndex = 0;
                }
            }
        }

        return true; // Продолжаем обработку
    }
}

registerProcessor('pcm-processor', PCMProcessor);
