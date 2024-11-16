import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';

class SpeechService {
  final SpeechToText _speechToText = SpeechToText();
  bool isListening = false;
  bool isAvailable = false;

  Future<void> initialize() async {
    isAvailable = await _speechToText.initialize();
  }

  void startListening(Function(String) onResult) async {
    if (!isAvailable) return;
    await _speechToText.listen(
      onResult: (SpeechRecognitionResult result) {
        isListening = true;
        onResult(result.recognizedWords);
      },
    );
  }

  void stopListening() async {
    await _speechToText.stop();
    isListening = false;
  }

  void dispose() {
    _speechToText.stop();
  }
}