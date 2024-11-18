import 'package:flutter/material.dart';

class SpeechControl extends StatelessWidget {
  final bool isListening;
  final VoidCallback onStart;
  final VoidCallback onStop;
  final VoidCallback onSpeak;

  const SpeechControl({
    Key? key,
    required this.isListening,
    required this.onStart,
    required this.onStop,
    required this.onSpeak,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SizedBox(
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
        ),
        const SizedBox(height: 20),
        ElevatedButton.icon(
          onPressed: onSpeak,
          icon: const Icon(Icons.volume_up),
          label: const Text("Speak"),
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          ),
        ),
      ],
    );
  }
}
