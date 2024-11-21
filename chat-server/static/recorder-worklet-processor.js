class RecorderWorkletProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bufferChunks = [];
        this.port.onmessage = (event) => {
            if (event.data === 'flush') {
                this.flush();
            }
            if (event.data === "clear") {
                this.clear();
            }
        };
    }

    process(inputs) {
        const input = inputs[0];
        if (input.length > 0) {
            const channelData = input[0];
            const chunk = new Float32Array(channelData);
            this.bufferChunks.push(chunk);
        }
        return true;
    }

    flush() {
        if (this.bufferChunks.length > 0) {
            const wavBuffer = this.encodeWAV(this.bufferChunks, 24000);
            this.port.postMessage({ wavBuffer }, [wavBuffer]);
            this.bufferChunks = [];
        }
    }
    clear() {
        this.bufferChunks = [];
    }

    encodeWAV(samples, sampleRate) {
        const bufferLength = samples.reduce((acc, chunk) => acc + chunk.length, 0);
        const buffer = new ArrayBuffer(44 + bufferLength * 2);
        const view = new DataView(buffer);

        this.writeString(view, 0, 'RIFF');
        view.setUint32(4, 36 + bufferLength * 2, true);
        this.writeString(view, 8, 'WAVE');
        this.writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, 1, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * 2, true);
        view.setUint16(32, 2, true);
        view.setUint16(34, 16, true);
        this.writeString(view, 36, 'data');
        view.setUint32(40, bufferLength * 2, true);

        let offset = 44;
        for (let chunk of samples) {
            const int16Chunk = this.float32ToInt16(chunk);
            const int16View = new Int16Array(buffer, offset, int16Chunk.length);
            int16View.set(int16Chunk);
            offset += int16Chunk.length * 2;
        }

        return buffer;
    }


    float32ToInt16(float32Array) {
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return int16Array;
    }

    writeString(view, offset, string) {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }
}

registerProcessor('recorder-worklet-processor', RecorderWorkletProcessor);