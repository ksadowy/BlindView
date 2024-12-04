import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'pages/speech_to_text_page.dart';
import 'package:blind_view/streams/generate_stream.dart';
import 'package:blind_view/extensions/context_extension.dart';
import 'package:blind_view/l10n/l10n.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<Locale>(
        stream: GenerateStreams.languageStream.stream,
        builder: (context, snapshot) {
          return MaterialApp(
            title: 'Flutter Clean Code Demo',
            theme: ThemeData(primarySwatch: Colors.blue),
            home: SpeechToTextPage(selectedLocal: snapshot.data ?? const Locale('en')),
            supportedLocales: L10n.locals,
            locale: snapshot.data,
            localizationsDelegates: const [
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
              AppLocalizations.delegate,
            ],
          );
        }
    );

  }
}
