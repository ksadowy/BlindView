import 'package:flutter/material.dart';
import 'pages/speech_to_text_page.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Clean Code Demo',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const SpeechToTextPage(),
    );
  }
}
