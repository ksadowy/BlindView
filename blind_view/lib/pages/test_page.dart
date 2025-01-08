import 'package:blind_view/pages/speech_to_text_page.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_tts/flutter_tts.dart';
import '../services/speech_language_config.dart';
import 'package:blind_view/extensions/context_extension.dart';
import 'package:blind_view/l10n/l10n.dart';
import 'package:blind_view/streams/generate_stream.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

/*class TestPage extends StatelessWidget {
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
}*/
class MyTest extends StatefulWidget{
  MyTest({super.key, required this.selectedLocal});

  Locale selectedLocal;

  @override
  State<MyTest> createState() => _TestTTS();
}

class _TestTTS extends State<MyTest>{

  /*FlutterTts _flutterTts = FlutterTts();
  List<Map> _voices = [];
  List<Map> _voices2 = [];
  Map? _currentVoice;
  late Config configuration;*/
  //configuration.SetLanguage("pl-PL");

/*
  List<Locale> allLocales = L10n.locals;
*/

  @override
  void initState() {
    // TODO: implement initState
    super.initState();
    GenerateStreams.languageStream.add(widget.selectedLocal);
/*
    initTTS();
*/
  }

  void dispose(){
/*
    GenerateStreams.languageStream.close();
*/
    super.dispose();
  }

  /*void initTTS() {
    _flutterTts.getVoices.then((data){
      try{
        _voices = List<Map>.from(data);

        *//*print(_voices);*//*
        setState(() {
          _voices = _voices.where((_voice) => _voice["name"].contains("en")).toList();
          //_voices2 = _voices.where((_voice) => _voice["name"].contains("pl")).toList();
          _voices.addAll(_voices2);
          _currentVoice = _voices.first;
          setVoice(_currentVoice!);
        });
      }
      catch (e){
        //print(e);
      }
    });
  }*/

  /*void setVoice(Map voice){
    _flutterTts.setVoice({"name": voice["name"], "locale": voice["locale"]});
  }*/

  @override
  Widget build(BuildContext context){
    print("Widget build: ");
    print(widget.selectedLocal);
    Locale dropdownValueLocale = widget.selectedLocal;
    return StreamBuilder<Locale>(
        stream: GenerateStreams.languageStream.stream,
        builder: (context, snapshot){
          print("TextPage snapshot.data");
          print(snapshot.data);
          return MaterialApp(
            title: "test",
            supportedLocales: L10n.locals,
            locale: snapshot.data,
            localizationsDelegates: const [
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
              AppLocalizations.delegate,
            ],
            home: Scaffold(
              appBar: AppBar(
                title: Text(context.localizations.changeLanguage),
              ),
              body: Stack(
                children: [
                  Column(
                    children: [
                      SizedBox(
                        height: 100,
                        width: 400,
                        child: DropdownButton<Locale>(
                          value: dropdownValueLocale,
                          items: L10n.locals.map((locale) {
                            return DropdownMenuItem<Locale>(
                              value: locale,
                              child: Padding(
                                padding: const EdgeInsets.all(9.0), // Przesunięcie tekstu w dół
                                child: Text(
                                  locale.languageCode,
                                  style: const TextStyle(
                                    fontSize: 60, // Rozmiar czcionki
                                    fontWeight: FontWeight.bold, // Grubość tekstu
                                    color: Colors.black,
                                  ),
                                ),
                              ),
                            );
                          }).toList(),
                          onChanged: (Locale? value) {
                            if (value != null) {
                              setState(() {
                                dropdownValueLocale = value;
                                widget.selectedLocal = value;
                                GenerateStreams.languageStream.add(dropdownValueLocale);
                              });
                            }
                          },
                          style: const TextStyle(
                            color: Colors.blue,
                            fontSize: 50,
                          ),
                          dropdownColor: Colors.white,
                          icon: const Icon(
                            Icons.arrow_drop_down,
                            color: Colors.blue,
                            size: 30,
                          ),
                          underline: Container(
                            height: 1,
                            color: Colors.blue,
                          ),
                        ),
                      ),
                    ],
                  ),
                  Positioned(
                    bottom: 10, // Odległość od dołu ekranu
                    left: 16,   // Odległość od lewej krawędzi
                    right: 16,  // Odległość od prawej krawędzi
                    child: ElevatedButton(
                      child: Text(
                        context.localizations.changeLanguage,
                        style: const TextStyle(
                          fontSize: 30,
                          fontWeight: FontWeight.bold,
                          color: Colors.black,
                        ),
                      ),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                        minimumSize: const Size(375, 150),
                        backgroundColor: Colors.purple[50],
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      onPressed: () {
                        GenerateStreams.languageStream.add(dropdownValueLocale);
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => SpeechToTextPage(
                              selectedLocal: snapshot.data ?? dropdownValueLocale,
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          );
                  /*ElevatedButton(
                      onPressed: () async{
                        GenerateStreams.languageStream.add(
                          L10n.locals.firstWhere((element) => element != selectedLocal),
                        );
                      },
                      child: Text(context.localizations.changeLanguage))*/


        }
    );
  }

}