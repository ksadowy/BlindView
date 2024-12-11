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
  const MyTest({super.key, required this.selectedLocal});

  final Locale selectedLocal;

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
          print(snapshot);
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
              appBar: AppBar(title: Text(context.localizations.settingsButton),),
              body: Center(
                child: Column(
                children:[
                  ElevatedButton(
                    child: Text(context.localizations.changeLanguage),
                    //style: ElevatedButton.styleFrom(background: Colors.blue),
                    onPressed: (){
                      GenerateStreams.languageStream.add(dropdownValueLocale);
                      print(snapshot.data);
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) =>
                            MyTest(selectedLocal: snapshot.data ?? dropdownValueLocale),
                        )
                      );
                    },
                  ),
                  DropdownButton<Locale>(
                    value: dropdownValueLocale,
                    items: L10n.locals.map((locale) {
                      return DropdownMenuItem<Locale>(
                        value: locale,
                        child: Text(
                          locale.languageCode
                        ),
                      );
                    }).toList(),
                    onChanged: (Locale? value) {
                      if (value != null) {
                        setState(() {
                          dropdownValueLocale = value;
                          GenerateStreams.languageStream.add(dropdownValueLocale);// Update the selected locale
                        });
                        print("dropdown: $dropdownValueLocale");
                        // configuration.SetLanguage(value.languageCode); // Uncomment and adjust as needed
                      }
                    },
                  ),

                  /*ElevatedButton(
                      onPressed: () async{
                        GenerateStreams.languageStream.add(
                          L10n.locals.firstWhere((element) => element != selectedLocal),
                        );
                      },
                      child: Text(context.localizations.changeLanguage))*/
                ]
                )
              ),
            ),
          );
        }
    );
  }

}