import 'package:flutter/material.dart';
import '../services/speech_service.dart';
import '../widgets/speech_control.dart';
import 'test_page.dart';

class SpeechToTextPage extends StatefulWidget {
  const SpeechToTextPage({Key? key}) : super(key: key);

  @override
  State<SpeechToTextPage> createState() => _SpeechToTextPageState();
}

class _SpeechToTextPageState extends State<SpeechToTextPage> {
  final SpeechService _speechService = SpeechService();
  String _lastWords = '';

  @override
  void initState() {
    super.initState();
    _speechService.initialize();
  }

  @override
  void dispose() {
    _speechService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Wydawanie komend')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Padding(
              padding: EdgeInsets.all(16.0),
              child: Text(
                'Przechwytywanie mowy:',
                style: TextStyle(fontSize: 20.0),
              ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Text(
                  _speechService.isListening
                      ? _lastWords
                      : _speechService.isAvailable
                      ? 'Tap the microphone to start listening...'
                      : 'Speech not available',
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
                });
              },
              onStop: _speechService.stopListening,
              onSpeak: () {
                _speechService.speak(_lastWords.isNotEmpty
                    ? _lastWords
                    : "No text available to speak");
              },
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const MyTest()),
                );
              },
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 128, vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text('Komendy', style: TextStyle(fontSize: 18)),
            ),
          ],
        ),
      ),
    );
  }
}
