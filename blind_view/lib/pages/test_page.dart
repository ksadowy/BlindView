import 'package:flutter/material.dart';

class TestPage extends StatelessWidget {
  const TestPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Komendy')),
      body: const Center(
        child: Text('Tutaj będą komendy!', style: TextStyle(fontSize: 24)),
      ),
    );
  }
}
