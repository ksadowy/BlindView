import 'package:flutter/material.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final String logoPath;

  const CustomAppBar({
    Key? key,
    required this.title,
    this.logoPath = 'assets/icon/Logo_blind_view.png',
  }) : super(key: key);

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      leading: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Image.asset(
          logoPath,
          fit: BoxFit.contain,
          errorBuilder: (context, error, stackTrace) =>
          const Icon(Icons.accessible_forward),
        ),
      ),
      title: Text(title),
      centerTitle: true,
    );
  }
}