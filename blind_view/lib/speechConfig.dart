import 'package:flutter/material.dart'

void main() {
  runApp(MaterialApp(
    title: "Speech configuration",
    home: MyApp(),
  ));
}

class MyApp extends StatelessWidget{
  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(title: Text("Ustawienia")),
      body: Center(
        child: RaiseButton(
          child: Text("Komendy"),
          color: Colors.blue,
          onPressed:(){
            Navigator.push(context, MaterialPageRoute(builder: (context) => test()));
          },
        )
      )
    )
  }
}