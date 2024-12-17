import 'dart:async';
import 'package:flutter/material.dart';

class GenerateStreams{
  const GenerateStreams._();

  static StreamController<Locale> languageStream = StreamController.broadcast();

  //static void InitializeLocale(Locale initLocale){
  //  languageStream.add(initLocale);
  //}
}