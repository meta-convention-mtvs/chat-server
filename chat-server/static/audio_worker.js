self.onmessage = function (e) {
    const buffer = e.data;
    const wavBlob = new Blob([buffer], { type: 'audio/wav' });
    self.postMessage(wavBlob);
}
