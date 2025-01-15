import 'package:blind_view/streams/generate_stream.dart';
import 'package:blind_view/extensions/context_extension.dart';
import 'package:blind_view/l10n/l10n.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import '../services/speech_service.dart';
import '../widgets/speech_control.dart';
import 'test_page.dart';
import '../services/chatgpt_service.dart';

class SpeechToTextPage extends StatefulWidget {
  const SpeechToTextPage({Key? key, required this.selectedLocal}) : super(key: key);
  final Locale selectedLocal;

  @override
  State<SpeechToTextPage> createState() => _SpeechToTextPageState();
}

class _SpeechToTextPageState extends State<SpeechToTextPage> {
  final SpeechService _speechService = SpeechService();
  final ChatGPTService _chatGPTService = ChatGPTService(
      "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");

  String _lastWords = '';
  String _chatGPTResponse = '';

  @override
  void initState() {
    super.initState();
    GenerateStreams.languageStream.add(widget.selectedLocal);
    _speechService.initialize();
  }

  @override
  void dispose() {
    GenerateStreams.languageStream.close();
    _speechService.dispose();
    super.dispose();
  }

  bool _isRequesting = false;

  void _sendToChatGPT(String userMessage) async {
    if (userMessage.isNotEmpty) {
      // Zatrzymanie nasłuchiwania przed wysłaniem zapytania
      _speechService.stopListening();

      final response = await _chatGPTService.sendMessageToChatGPT(userMessage);
      setState(() {
        _chatGPTResponse = response;
      });

      // Po zakończeniu wysyłania zapytania i odczytania odpowiedzi, wznawiamy nasłuchiwanie
      _speechService.speak(response);
    }
  }

  void _speakResponse(String response) {
    // Sprawdzamy, czy TTS nie jest w trakcie mówienia, aby nie uruchomić go ponownie
    if (!_speechService.isSpeaking && response.isNotEmpty) {
      _speechService.speak(response);
    }
  }

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<Locale>(
      stream: GenerateStreams.languageStream.stream,
      builder: (BuildContext innerContext, snapshot) {
        return MaterialApp(
          title: "ChatGPT App",
          supportedLocales: L10n.locals,
          locale: snapshot.data,
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
            AppLocalizations.delegate,
          ],
          home: Scaffold(
            appBar: AppBar(title: Text(context.localizations.commandsPageTitle)),
            body: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Text(
                      context.localizations.speechCapture,
                      style: const TextStyle(fontSize: 20.0),
                    ),
                  ),
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Text(
                        _speechService.isListening
                            ? _lastWords
                            : _speechService.isAvailable
                            ? context.localizations.tapTheMicrophone
                            : context.localizations.availableSpeech,
                      ),
                    ),
                  ),
                  SpeechControl(
                    isListening: _speechService.isListening,
                    onStart: () {
                      _speechService.startListening((result) {
                        setState(() {
                          _lastWords = result;
                        });
                        _sendToChatGPT(result);  // Automatyczne wysłanie zapytania
                      });
                    },
                    onStop: _speechService.stopListening,
                    onSpeak: () {
                      _speechService.speak(_lastWords.isNotEmpty
                          ? _lastWords
                          : context.localizations.availableNoSpeech);
                    },
                  ),
                  ElevatedButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) =>
                            MyTest(selectedLocal: snapshot.data ?? const Locale('en'))),
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 128, vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: Text(
                        context.localizations.settingsDownPage, style: const TextStyle(fontSize: 18)),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}