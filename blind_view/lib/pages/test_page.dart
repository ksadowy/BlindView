import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import '../services/speech_language_config.dart';

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
  const MyTest({super.key});

  @override
  State<MyTest> createState() => _TestTTS();
}

class _TestTTS extends State<MyTest>{

  FlutterTts _flutterTts = FlutterTts();
  List<Map> _voices = [];
  List<Map> _voices2 = [];
  Map? _currentVoice;
  late Config configuration;
  //configuration.SetLanguage("pl-PL");

  @override
  void initState() {
    // TODO: implement initState
    super.initState();
    initTTS();
  }


  void initTTS() {
    _flutterTts.getVoices.then((data){
      try{
        _voices = List<Map>.from(data);

        /*print(_voices);*/
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
  }

  void setVoice(Map voice){
    _flutterTts.setVoice({"name": voice["name"], "locale": voice["locale"]});
  }

  @override
  Widget build(BuildContext context){
    return MaterialApp(
      title: "test",
      home: Scaffold(
        appBar: AppBar(title: Text("Test"),),
        body: Center(
          child: Column(
          children:[
            ElevatedButton(
              child: Text("test"),
              //style: ElevatedButton.styleFrom(background: Colors.blue),
              onPressed: (){
                Navigator.pop(context);
              },
            ),
            DropdownButton(
              value: _currentVoice,
              items: _voices.map((_voice) => DropdownMenuItem(
                value: _voice,
                child: Text(
                  _voice["name"]
                  ,)
                ,)
                ,)
                  .toList(),
                onChanged: (value){
                 //configuration.SetLanguage(_currentVoice!["name"]);
                })
          ]
          )
        ),
      ),
    );
  }

}