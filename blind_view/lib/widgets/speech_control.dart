import 'package:flutter/material.dart';

class SpeechControl extends StatelessWidget {
  final bool isListening;
  final VoidCallback onStart;
  final VoidCallback onStop;

  const SpeechControl({
    Key? key,
    required this.isListening,
    required this.onStart,
    required this.onStop,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 330,
      height: 300,
      child: FloatingActionButton(
        onPressed: isListening ? onStop : onStart,
        tooltip: 'Listen',
        child: Icon(
          isListening ? Icons.mic : Icons.mic_off,
          size: 40,
        ),
      ),
    );
  }
}
