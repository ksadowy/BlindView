import 'package:flutter/material.dart';

class InstructionText extends StatelessWidget {
  final String text;
  final TextStyle? textStyle;
  final EdgeInsetsGeometry padding;

  const InstructionText({
    Key? key,
    required this.text,
    this.textStyle,
    this.padding = const EdgeInsets.all(16.0),
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: padding,
      child: Text(
        text,
        style: textStyle ?? Theme.of(context).textTheme.titleMedium,
        textAlign: TextAlign.center,
      ),
    );
  }
}