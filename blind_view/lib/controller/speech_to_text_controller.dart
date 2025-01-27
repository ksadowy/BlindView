import 'dart:async';
import 'dart:ui';
import 'package:blind_view/services/data_service.dart';
import 'package:blind_view/services/speech_service.dart';
import 'package:blind_view/services/chatgpt_service.dart';
import 'package:blind_view/streams/generate_stream.dart';

class SpeechToTextController {
  final SpeechService _speechService = SpeechService();
  final ChatGPTService _chatGPTService;
  final DataService _dataService;

  StreamSubscription<Map<String, dynamic>>? _dataSubscription;
  String _lastWords = '';
  String _chatGPTResponse = '';

  SpeechToTextController({
    required Locale selectedLocal,
    required String apiKey,
  })  : _chatGPTService = ChatGPTService(apiKey),
        _dataService = DataService(baseUrl: 'https://your-api-base-url.com') {
    _initialize(selectedLocal);
  }

  void _initialize(Locale selectedLocal) {
    GenerateStreams.languageStream.add(selectedLocal);
    _speechService.initialize();
    _dataService.startService();
    _dataSubscription = _dataService.dataStream.listen(_processSensorData);
  }

  void _processSensorData(Map<String, dynamic> sensorData) {
    final prompt = "Provide navigation instructions...";
    _chatGPTService.sendMessageToChatGPT(prompt).then((response) {
      _chatGPTResponse = response;
      _speechService.speak(response);
    }).catchError((error) {
      print('ChatGPT Error: $error');
      _speechService.speak("Error generating directions");
    });
  }

  void startListening(void Function(String result) onResult) {
    _speechService.startListening((result) {
      _lastWords = result;
      onResult(result);
      _sendToChatGPT(result);
    });
  }

  Future<void> _sendToChatGPT(String userMessage) async {
    if (userMessage.isNotEmpty) {
      _speechService.stopListening();
      final response = await _chatGPTService.sendMessageToChatGPT(userMessage);
      _chatGPTResponse = response;
      _speechService.speak(response);
    }
  }

  void speak(String text) => _speechService.speak(text);
  void stopListening() => _speechService.stopListening();

  bool get isListening => _speechService.isListening;
  bool get isAvailable => _speechService.isAvailable;
  String get lastWords => _lastWords;

  void dispose() {
    _dataSubscription?.cancel();
    _dataService.stopService();
    GenerateStreams.languageStream.close();
    _speechService.dispose();
  }
}