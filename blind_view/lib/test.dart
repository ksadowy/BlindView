import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

class Test extends StatelessWidget{
  @override
  Widget build(BuildContext context){
    return MaterialApp(
      title: "test",
      home: Scaffold(
        appBar: AppBar(title: Text("Test"),),
        body: Center(
          child: ElevatedButton(
            child: Text("test"),
            //style: ElevatedButton.styleFrom(background: Colors.blue),
            onPressed: (){
              Navigator.pop(context);
            },
          ),
        ),
      ),
    );
  }
}
