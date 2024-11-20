import 'dart:async';
import 'package:flutter/material.dart';

class GenerateStreams{
  const GenerateStreams._();

  static StreamController<Locale> languageStream = StreamController.broadcast();
}