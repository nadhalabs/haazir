import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'core/theme.dart';
import 'services/api_service.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/onboarding_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await PartnerApiService().init();
  final prefs = await SharedPreferences.getInstance();
  runApp(
    HaazirPartnerApp(
      showOnboarding: !(prefs.getBool('partner_onboarding_complete') ?? false),
    ),
  );
}

class HaazirPartnerApp extends StatelessWidget {
  const HaazirPartnerApp({super.key, this.showOnboarding = false});

  final bool showOnboarding;

  @override
  Widget build(BuildContext context) {
    final bool isLoggedIn = PartnerApiService().isAuthenticated;

    return MaterialApp(
      title: 'Haazir Partner',
      debugShowCheckedModeBanner: false,
      theme: PartnerTheme.lightTheme,
      home: isLoggedIn
          ? const PartnerDashboardScreen()
          : showOnboarding
          ? const PartnerOnboardingScreen()
          : const PartnerLoginScreen(),
    );
  }
}
