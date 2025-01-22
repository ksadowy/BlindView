// Main imports
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

// Main page widget
class SpeechToTextPage extends StatefulWidget {
  const SpeechToTextPage({Key? key, required this.selectedLocal}) : super(key: key);

  final Locale selectedLocal;

  @override
  State<SpeechToTextPage> createState() => _SpeechToTextPageState();
}

class _SpeechToTextPageState extends State<SpeechToTextPage> {
  // Dependencies
  final SpeechService _speechService = SpeechService();
  final ChatGPTService _chatGPTService = ChatGPTService("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");

  // State variables
  String _lastWords = '';
  String _chatGPTResponse = '';

  @override
  void initState() {
    super.initState();
    // Initialize services and streams
    GenerateStreams.languageStream.add(widget.selectedLocal);
    _speechService.initialize();
  }

  @override
  void dispose() {
    // Dispose resources to avoid memory leaks
    GenerateStreams.languageStream.close();
    _speechService.dispose();
    super.dispose();
  }

  // Function to send user message to ChatGPT and handle the response
  Future<void> _sendToChatGPT(String userMessage) async {
    if (userMessage.isNotEmpty) {
      _speechService.stopListening();
      final response = await _chatGPTService.sendMessageToChatGPT(userMessage);
      setState(() {
        _chatGPTResponse = response;
      });
      _speechService.speak(response);
    }
  }

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<Locale>(
      stream: GenerateStreams.languageStream.stream,
      builder: (context, snapshot) {
        final locale = snapshot.data ?? const Locale('en');
        return MaterialApp(
          title: "ChatGPT App",
          supportedLocales: L10n.locals,
          locale: locale,
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
            AppLocalizations.delegate,
          ],
          home: _buildScaffold(context, locale),
        );
      },
    );
  }

  // Extracted scaffold widget for better readability
  Widget _buildScaffold(BuildContext context, Locale locale) {
    return Scaffold(
      appBar: _buildAppBar(),
      body: _buildBody(context, locale),
    );
  }

  // App bar with a logo
  AppBar _buildAppBar() {
    return AppBar(
      leading: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Image.asset(
          'assets/icon/Logo_blind_view.png',
          fit: BoxFit.contain,
        ),
      ),
      title: Text(AppLocalizations.of(context)?.commandsPageTitle ?? "Commands"),
    );
  }

  // Main body content
  Widget _buildBody(BuildContext context, Locale locale) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _buildInstructionText(),
          _buildSpeechResultDisplay(),
          _buildSpeechControl(context),
          _buildNavigationButton(context, locale),
        ],
      ),
    );
  }

  // Instruction text widget
  Widget _buildInstructionText() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Text(
        AppLocalizations.of(context)?.speechCapture ?? "Speak something",
        style: const TextStyle(fontSize: 20.0),
      ),
    );
  }

  // Display for speech recognition result
  Widget _buildSpeechResultDisplay() {
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Text(
          _speechService.isListening
              ? _lastWords
              : _speechService.isAvailable
              ? AppLocalizations.of(context)?.tapTheMicrophone ?? "Tap to start"
              : AppLocalizations.of(context)?.availableSpeech ?? "Speech not available",
        ),
      ),
    );
  }

  // Speech control widget
  Widget _buildSpeechControl(BuildContext context) {
    return SpeechControl(
      isListening: _speechService.isListening,
      onStart: () {
        _speechService.startListening((result) {
          setState(() {
            _lastWords = result;
          });
          _sendToChatGPT(result);
        });
      },
      onStop: _speechService.stopListening,
      onSpeak: () {
        _speechService.speak(
          _lastWords.isNotEmpty
              ? _lastWords
              : AppLocalizations.of(context)?.availableNoSpeech ?? "No speech detected",
        );
      },
    );
  }

  // Navigation button to test page
  Widget _buildNavigationButton(BuildContext context, Locale locale) {
    return ElevatedButton(
      onPressed: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => MyTest(selectedLocal: locale),
          ),
        );
      },
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 128, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      child: Text(
        AppLocalizations.of(context)?.settingsDownPage ?? "Settings",
        style: const TextStyle(fontSize: 18),
      ),
    );
  }
}
