import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'core/theme.dart';
import 'services/api_service.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/onboarding_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiService().init();
  final prefs = await SharedPreferences.getInstance();
  runApp(
    HaazirCustomerApp(
      showOnboarding: !(prefs.getBool('customer_onboarding_complete') ?? false),
    ),
  );
}

class HaazirCustomerApp extends StatelessWidget {
  const HaazirCustomerApp({super.key, this.showOnboarding = false});

  final bool showOnboarding;

  @override
  Widget build(BuildContext context) {
    final bool isLoggedIn = ApiService().isAuthenticated;

    return MaterialApp(
      title: 'Haazir',
      debugShowCheckedModeBanner: false,
      theme: HaazirTheme.lightTheme,
      home: isLoggedIn
          ? const HomeScreen()
          : showOnboarding
          ? const CustomerOnboardingScreen()
          : const LoginScreen(),
    );
  }
}
