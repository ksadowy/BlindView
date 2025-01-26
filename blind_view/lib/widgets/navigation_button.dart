import 'package:flutter/material.dart';

class NavigationButton extends StatelessWidget {
  final VoidCallback onPressed;
  final String text;
  final EdgeInsetsGeometry padding;
  final double borderRadius;
  final double fontSize;

  const NavigationButton({
    Key? key,
    required this.onPressed,
    required this.text,
    this.padding = const EdgeInsets.symmetric(horizontal: 128, vertical: 16),
    this.borderRadius = 12,
    this.fontSize = 18,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        padding: padding,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(borderRadius),
        ),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: fontSize),
      ),
    );
  }
}