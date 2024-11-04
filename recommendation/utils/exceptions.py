class TranslationError(Exception):
    def __init__(self, message, source_text=None):
        self.source_text = source_text
        super().__init__(message)

    def __str__(self):
        return f"{super().__str__()}. Source text: {self.source_text}"