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
  bool _isSpeaking = false; // Flaga do kontrolowania stanu TTS

  Future<void> initialize() async {
    isAvailable = await _speechToText.initialize();
    // Ustawienie callbacka, który będzie zmieniał stan _isSpeaking, kiedy TTS zakończy
    _flutterTts.setCompletionHandler(() {
      _isSpeaking = false;
      // Po zakończeniu TTS, wznawiamy nasłuchiwanie
      startListening((recognizedWords) {
        // Możesz dodać kod, aby przetwarzać wynik rozpoznawania mowy
      });
    });
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
    if (_isSpeaking) {
      return; // Jeśli już mówimy, nie rozpoczynaj nowej syntezacji mowy
    }

    _isSpeaking = true;
    await _flutterTts.setLanguage("en-US"); // Ustawienie języka
    await _flutterTts.setPitch(1.0);       // Wysokość głosu
    await _flutterTts.speak(text);
  }

  void dispose() {
    _speechToText.stop();
    _flutterTts.stop();
  }

  // Getter do sprawdzenia, czy TTS jest w trakcie mówienia
  bool get isSpeaking => _isSpeaking;
}
