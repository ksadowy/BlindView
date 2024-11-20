import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';

import 'speech_language_config.dart';


class SpeechService {
  final SpeechToText _speechToText = SpeechToText();
  final FlutterTts _flutterTts = FlutterTts();
  late Config configuration;
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

  Future<void> speak(String text) async {
    //await _flutterTts.setLanguage(configuration.GetLanguage()); // Ustawienie języka
    await _flutterTts.setLanguage("en-US"); // Ustawienie języka
    await _flutterTts.setPitch(1.0);       // Wysokość głosu
    await _flutterTts.speak(text);
  }

  void dispose() {
    _speechToText.stop();
    _flutterTts.stop();
  }
}
