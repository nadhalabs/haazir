import 'package:flutter/material.dart';
import 'core/theme.dart';
import 'services/api_service.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await PartnerApiService().init();
  runApp(const HaazirPartnerApp());
}

class HaazirPartnerApp extends StatelessWidget {
  const HaazirPartnerApp({super.key});

  @override
  Widget build(BuildContext context) {
    final bool isLoggedIn = PartnerApiService().isAuthenticated;

    return MaterialApp(
      title: 'Haazir Partner',
      debugShowCheckedModeBanner: false,
      theme: PartnerTheme.lightTheme,
      home: isLoggedIn
          ? const PartnerDashboardScreen()
          : const PartnerLoginScreen(),
    );
  }
}
